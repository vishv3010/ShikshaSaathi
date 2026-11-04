"""Turn a typed question into a structured request, without any LLM.

This is the fallback "understand" step (PLAN.md section 1, step 1) and the
reference the LLM's own understanding is checked against. It only finds
*what* is being asked (question type, school, grade, subject, month, how
many schools). It never computes an answer.

Works on English, Gujarati script and Hindi (Devanagari) text. Gujarati and
Devanagari digits are read as normal digits.
"""
import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher

DEFAULT_LIMIT = 3
MAX_LIMIT = 10
FUZZY_CUTOFF = 0.8       # how close a typed word must be to a village name ("Rampur" -> "Rampura")
AMBIGUOUS_MARGIN = 0.05  # two villages this close in similarity -> ask which one
DATA_YEAR = 2026

DIGITS = str.maketrans("૦૧૨૩૪૫૬૭૮૯०१२३४५६७८९", "01234567890123456789")
DEVANAGARI_TO_GUJARATI = 0x0A80 - 0x0900   # the two Unicode blocks share one layout
# Spelling-insensitive name key: long and short vowels count as one, and ળ (common in Gujarati names)
# as ल, the way Hindi writes it. "अंबालिया" and "આંબલિયા" (Ambaliya) give the same key.
VOWEL_BASE = str.maketrans("આઈઊઐઔળ", "અઇઉએઓલ")
MIN_SKELETON = 4    # shorter keys ("નવલ" for Navli) could match ordinary words, so they are not used


@dataclass
class Question:
    text: str
    lang: str                                   # language the question was written in: en / gu / hi
    intent: str
    school_ids: list = field(default_factory=list)
    unknown_school: str | None = None           # a school name that is not in this cluster
    grade: int | None = None
    subject: str | None = None
    month: str | None = None                    # "2026-10"; None means the latest month
    limit: int = 3
    reply_lang: str | None = None               # set when she asks for a language ("reply in Gujarati")


def normalize(text):
    """NFC, ASCII digits, lower case, one space between words, common Gujarati spelling variants merged."""
    text = unicodedata.normalize("NFC", text).translate(DIGITS)
    text = text.replace("ઑ", "ઓ").replace("ૉ", "ો").replace("’", "'")
    return " ".join(text.lower().split())


def to_gujarati_script(text):
    """Devanagari letters -> Gujarati letters, so a name typed in Hindi script ("रामपुरा") is found."""
    return "".join(chr(ord(ch) + DEVANAGARI_TO_GUJARATI) if "\u0900" <= ch <= "\u097f" else ch for ch in text)


# Common words of Gujarati and Hindi typed in English letters. Two or more mark the language, so the
# reply comes in her language even when the rules, not Gemini, read the question.
ROMAN_GU = {"che", "chhe", "shu", "kem", "ma", "ni", "nu", "na", "kai", "kayi", "shala", "hajri", "ochhi", "ochhu",
            "batavo", "mate", "athvadiye", "dhoran", "ganit", "levi", "joie", "joiye", "kevu", "kevi", "nathi",
            "ane", "pan", "badhi", "mari", "tamari", "aaje", "kale", "mahine", "nabdu", "nabli", "ghati"}
ROMAN_HI = {"hai", "hain", "kya", "kaun", "kis", "kin", "kyun", "kyon", "nahi", "nahin", "mein", "ka", "ki", "ke",
            "aaya", "aayi", "batao", "bataiye", "chahiye", "kaksha", "haajri", "sabse", "kam", "jaana", "jana",
            "dekhna", "konsi", "konsa", "kaunsi", "kaunsa", "pehle", "hafte", "aur", "kaise", "kaisa"}


def detect_language(text):
    gu = sum("\u0a80" <= ch <= "\u0aff" for ch in text)
    hi = sum("\u0900" <= ch <= "\u097f" for ch in text)
    if gu or hi:
        return "gu" if gu >= hi else "hi"
    words = set(re.findall(r"[a-z]+", text.lower()))
    gu_words, hi_words = len(words & ROMAN_GU), len(words & ROMAN_HI)
    if max(gu_words, hi_words) >= 2:
        return "gu" if gu_words > hi_words else "hi"
    return "en"


def _any(text, patterns):
    return any(re.search(p, text) for p in patterns)


# --- Words that signal each kind of question ---------------------------------------------
# English patterns use word boundaries. Gujarati and Hindi words are matched as plain
# substrings, because endings attach to the word ("રામપુરામાં" = "in Rampura").

NOT_ALLOWED = [  # attempts to change the rules or the data, or to get made-up figures
    r"\bignore (?:all |your |the |any |previous |above |earlier |these )*(?:rules|instructions|prompt|data|guidelines)",
    r"\bforget (?:all |your |the )*(?:rules|instructions)", r"\bsystem prompt", r"\bjailbreak",
    r"\bdeveloper mode", r"\bpretend\b", r"\byou are now\b",
    r"\b(?:say|claim|write|announce|state)\b(?: that)?.{0,40}\b(?:scored|score is|score of|got|achieved)\b.{0,20}\d+ ?%",
    r"\b(?:change|set|edit|update|overwrite|mark)\b.{0,40}\bto \d+ ?%",
    r"\bmake up (?:a |the |some )?(?:numbers?|figures?|data|scores?)", r"\binvent\b", r"\bjust guess\b",
    r"\bguess (?:the |a |its |their )?(?:numbers?|figures?|scores?|attendance|marks|data|percentage)",
    "નિયમ ભૂલ", "નિયમો ભૂલ", "નિયમ અવગણ", "સૂચના ભૂલ", "અંદાજે કહો", "અંદાજ લગાવ",
    "नियम भूल", "निर्देश भूल", "नियम अनदेखा", "अंदाज़ा लगा", "अंदाजा लगा",
]
PEOPLE = [r"\bteachers?\b", r"\bhead ?teachers?\b", r"\bprincipals?\b", r"\bhm\b", r"\bstaff\b", r"\bheadmaster",
          "શિક્ષક", "આચાર્ય", "શિક્ષિકા", "સ્ટાફ", "शिक्षक", "अध्यापक", "प्रधानाचार्य", "हेडमास्टर"]
CHILDREN = [r"\bstudents?\b", r"\bchild(?:ren)?\b", r"\bkids?\b", r"\bpupils?\b", "વિદ્યાર્થી", "બાળક", "छात्र", "बच्च"]
# Always a judgement of a person.
JUDGEMENT = [r"\blazy\b", r"\buseless\b", r"\bblame", r"\bpunish", r"\bfire\b", r"\bsuspend", r"\bincompetent",
             r"\bfault\b", r"\bcareless", r"\bshirk", r"\bnot doing (?:their|his|her) job", r"\bdisciplin",
             "આળસુ", "નકામ", "દોષ", "સજા", "બેદરકાર", "કામ નથી કર", "आलसी", "निकम्म", "दोषी", "सजा", "लापरवाह",
             "काम नहीं कर"]
# A judgement unless the question is about attendance ("worst teacher attendance" is a pattern).
JUDGEMENT_SOFT = [r"\bbad\b", r"\bworst\b", r"\bresponsible\b", "ખરાબ", "જવાબદાર", "खराब", "जिम्मेदार", "ज़िम्मेदार"]
PERSONAL = [r"\bnames?\b", r"\bphone", r"\bmobile", r"\bcontact", r"\baddress", r"\bwhatsapp", r"\blist of\b",
            r"\bwhich (?:student|child|kid|teacher)", r"\bwho (?:is|are) (?:the )?(?:students?|child|teachers?|head ?teachers?|principal|hm)\b",
            "કોણ છે", "कौन है", "कौन हैं",
            "નામ", "ફોન", "મોબાઇલ", "મોબાઈલ", "સરનામ", "नाम", "फोन", "फ़ोन", "मोबाइल"]

MISSING = [r"\bmissing\b", r"\bgaps?\b", r"\bno data\b", r"\bincomplete\b", r"\bupload",
           r"\b(?:hasn'?t|haven'?t|not|never) (?:come|came|arrived)\b(?! (?:down|up|back))",
           r"\byet to (?:come|arrive|upload|send|report)", r"\bnot (?:in|here) yet\b",
           r"\bnot (?:been )?(?:uploaded|received|reported|submitted|sent)", r"\bhaven'?t (?:uploaded|reported|sent)",
           r"\bdata (?:is |are )?(?:not|missing|pending)", r"\bpending data",
           "ખૂટ", "માહિતી નથી", "ડેટા નથી", "અપલોડ", "મળી નથી", "આવી નથી", "નથી આવી", "નથી આવ્યો", "ગુમ",
           "गायब", "नहीं आया", "नहीं आई", "डेटा नहीं", "अधूरा", "अधूरी"]
# These name the block officer, so they win even when a school is named.
OFFICER_STRONG = [r"\bofficer", r"\bbrc\b", r"\bbeo\b", r"\bblock\b", r"\bforward", r"\bsupervisor", r"\bboss\b",
                  "અધિકારી", "બીઆરસી", "બી.આર.સી", "अधिकारी"]
OFFICER = OFFICER_STRONG + [r"\bsummary\b", r"\breport\b", "સારાંશ", "રિપોર્ટ", "सारांश", "रिपोर्ट"]
RECENT_VISITS = [r"\blast visit", r"\bwhen did i (?:last )?visit", r"\bwhen was .{0,30}visited",
                 r"\b(?:not|never|haven'?t|hasn'?t|wasn'?t|been) (?:been )?visited", r"\bnot visit",
                 r"\bvisit history", r"\bprevious visits?", r"\bpast visits?", r"\bhow long since",
                 r"\bvisited (?:recently|last)", r"\bhow many visits",
                 "છેલ્લી મુલાકાત", "છેલ્લે ક્યારે", "ક્યારે મુલાકાત", "મુલાકાત ક્યારે", "મુલાકાત લીધી",
                 "મુલાકાત નથી", "आखिरी", "आख़िरी", "कब गई", "कब गया", "दौरा कब", "कब दौरा",
                 r"\b(?:did|have) i (?:already )?visit(?:ed)?\b", r"\bi (?:have )?visited\b",
                 "दौरा किया", "विज़िट की", "विजिट की"]
ATTENDANCE = [r"\battend", r"\babsent", r"\babsence",
              r"\b(?:hajri|haajri|hajari|haziri|haaziri|hazri|upasthiti|gerhajar|gairhazir)\b",
              "હાજરી", "ગેરહાજર", "उपस्थिति", "हाजिरी", "हाज़िरी",
              "गैरहाजिर", "अनुपस्थित"]
PRIORITY = [r"\bwhich (?:\d+ |one |two |three |four |five )?schools?\b", r"\bvisit", r"\battention\b",
            r"\bwhere (?:should|do|shall) i go\b",
            r"\b(?:kai|kayi|kaun ?se|kaunsi|kaunsa|konsi|konsa|kon si|kis|kin) (?:shala|school)",
            r"\bpriorit", r"\btop \d", r"\btop\b.{0,10}\bschools?", r"\bfocus\b", r"\bstruggl", r"\bweak",
            r"\bworst\b", r"\bthis week\b", r"\bconcern", r"\bworr(?:y|ied|ies)\b", r"\burgent", r"\bat risk\b",
            r"\bschools?\b.{0,40}\b(?:need|needs|support|help|first|low|poor|lagging|behind)\b",
            "કઈ શાળ", "કઇ શાળ", "કયી શાળ", "ધ્યાન", "મુલાકાત", "પ્રાથમિકતા", "નબળી", r"શાળા.{0,30}જરૂર",
            r"જરૂર.{0,30}શાળા", "कौन से स्कूल", "कौनसे स्कूल", "किन स्कूल", "किस स्कूल", "ध्यान", "प्राथमिकता",
            "विज़िट", "विजिट", "दौरा", "कमजोर", "कमज़ोर", r"स्कूल.{0,30}(?:ज़रूरत|जरूरत)"]
# "Which schools are in my cluster?": the whole list (D-037), unless the question asks about need
# ("List the schools that need help" and "Which primary schools need help?" stay the visit plan).
LIST_STRONG = [r"\ball (?:the |my |of my |of the |our )?schools?\b", r"\bevery school\b",
               r"\b(?:list|names?) (?:of )?(?:all )?(?:the |my |our )?(?:all )?schools?\b", r"\bschools?'? (?:names?|list)\b",
               r"\blist (?:out )?(?:all |every |the |my )+.{0,12}schools?\b", r"\bhow many schools\b", r"\bnumber of schools\b", r"\btotal (?:no\.? of |number of )?schools?\b",
               r"\b(?:which|what) schools? (?:are|is|do i have) (?:there )?(?:in|under) (?:my|the|this) cluster\b",
               r"\bschools? (?:are )?(?:there )?(?:in|under) (?:my|the|this) cluster\s*\??$",
               r"\b(?:rank|ranking|sort|order)\b.{0,30}\bschools?\b", r"\bschools?\b.{0,25}\b(?:ranked|ranking|by score|by need)\b",
               "બધી શાળા", "તમામ શાળા", "દરેક શાળા", "શાળાઓની યાદી", "શાળાની યાદી", "શાળાઓના નામ", "શાળાઓનાં નામ",
               "શાળાના નામ", "શાળાનાં નામ", "કેટલી શાળા", "કુલ શાળા", "ક્લસ્ટરની શાળાઓ", "ક્લસ્ટરમાં કઈ શાળાઓ છે",
               "सभी स्कूल", "सारे स्कूल", "सब स्कूल", "स्कूलों की सूची", "स्कूलों की लिस्ट", "स्कूलों के नाम", "स्कूल के नाम",
               "कितने स्कूल", "कुल स्कूल", r"\b(?:badhi|tamam|darek) shala", r"\bshala(?:o|on)? (?:na|ni|nu|nan) (?:naam|nam|yadi|list)\b",
               r"\b(?:sabhi|saare|sare|sab) (?:schools?|skool)\b", r"\bkitne (?:schools?|skool)\b", r"\bkitni shala", r"\bkul (?:schools?|skool|shala)",
               r"\bschool(?:on)? (?:ke naam|ki list|ki suchi)\b",
               # "which ones": the question word said twice asks for the whole list (कौन-कौन, કઈ-કઈ)
               r"\bkaun[- ]kaun\b", r"\bkai[- ]kai\b", "कौन कौन", "कौन-कौन", "કઈ કઈ", "કઇ કઇ", "કઈ-કઈ",
               r"\bschools?\b.{0,12}\b(?:i|we) (?:look after|manage|handle|cover|oversee|am responsible for|have)\b"]
LIST_WEAK = [r"\b(?:doing|performing) (?:the )?(?:best|well|good|fine)\b", r"\bbest (?:performing )?schools?\b",
             r"\bgood schools?\b", r"\b(?:high|medium|low)[- ]priority\b", r"\bdoing fine\b",
             r"\b(?:upper )?primary schools?\b", r"\bwhich schools? (?:are|is) (?:upper )?primary\b", r"\bschool types?\b",
             r"\btypes? of schools?\b", "પ્રાથમિક શાળાઓ", "સારી શાળા", "प्राथमिक स्कूल", "अच्छे स्कूल",
             r"\b(?:show|see|view|display|give)(?: me)?(?: all)?(?: my| our| the)? schools?\b", r"^(?:my|our) schools?\s*\??$",
             "શાળાઓ બતાવ", "મારી શાળાઓ", "स्कूल दिखा", "मेरे स्कूल"]
NEED = [r"\bneeds?\b", r"\bhelp\b(?! me)", r"\bsupport\b", r"\battention\b", r"\bvisit", r"\bweak", r"\bstruggl", r"\bfocus\b",
        r"\burgent", r"\bconcern", r"\blow (?:marks|scores?|results?)\b", "જરૂર", "મદદ", "મુલાકાત", "ध्यान", "मदद", "ज़रूरत", "जरूरत",
        r"\bmadad\b", r"\b(?:jaroor|jarur|zaroor|zarur|jaruri|zaruri)\b", r"\bdhyan\b", r"\bmulakat\b"]
SCHOOL_TYPE = [r"\bprimary\b", r"\btypes?\b", "પ્રાથમિક", "प्राथमिक"]
HELP = [r"^(?:hi|hello|hey|namaste|namaskar|good (?:morning|afternoon|evening))\b", r"\bhelp\b",
        r"\bwhat can you\b", r"\bwhat (?:can|should) i ask\b", r"\bhow (?:can|do) you help\b",
        r"\bhow do i use\b", r"\bwho are you\b",
        "નમસ્તે", "નમસ્કાર", "મદદ", "કેમ છો", "શું કરી શક", "नमस्ते", "नमस्कार", "मदद", "क्या कर सक"]

SUBJECTS = {
    "Maths": [r"\bmath", r"\bganit\b", "ગણિત", "गणित"],
    "Gujarati": [r"\bgujarati\b", "ગુજરાતી", "गुजराती"],
    "EVS": [r"\bevs\b", r"\benvironment", "પર્યાવરણ", "पर्यावरण"],
    "Science": [r"\bscience\b", "વિજ્ઞાન", "विज्ञान"],
}

REPLY_LANGUAGE = [  # (pattern, language code or None to read it from the match)
    (r"\b(?:reply|answer|respond|write|explain|speak|talk|tell me)\b[^.?!]{0,15}\bin (gujarati|english|hindi)\b", None),
    (r"ગુજરાતીમાં (?:જવાબ|કહો|જણાવો|લખો|સમજાવો)", "gu"),
    (r"(?:અંગ્રેજીમાં|ઇંગ્લિશમાં) (?:જવાબ|કહો|જણાવો|લખો)", "en"),
    (r"(?:हिंदी|हिन्दी) में (?:जवाब|बताओ|बताइए|बताएं|लिखो)", "hi"),
    (r"गुजराती में (?:जवाब|बताओ|बताइए|बताएं|लिखो)", "gu"),
]
LANG_CODES = {"gujarati": "gu", "english": "en", "hindi": "hi"}

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "એક": 1, "બે": 2, "ત્રણ": 3, "ચાર": 4, "પાંચ": 5, "છ": 6, "સાત": 7, "આઠ": 8, "નવ": 9, "દસ": 10,
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "छह": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10,
}
ORDINALS = [  # (word, grade, word that must follow it)
    *[(w, g, "ધોરણ") for w, g in [("પહેલા", 1), ("બીજા", 2), ("ત્રીજા", 3), ("ચોથા", 4), ("પાંચમા", 5),
                                  ("છઠ્ઠા", 6), ("સાતમા", 7), ("આઠમા", 8)]],
    *[(w, g, "कक्षा") for w, g in [("पहली", 1), ("दूसरी", 2), ("तीसरी", 3), ("चौथी", 4), ("पांचवीं", 5),
                                   ("पाँचवीं", 5), ("पांचवी", 5), ("छठी", 6), ("सातवीं", 7), ("आठवीं", 8)]],
]

MONTH_WORDS = {
    1: ["january", "jan", "જાન્યુઆરી", "जनवरी"],
    2: ["february", "feb", "ફેબ્રુઆરી", "फरवरी", "फ़रवरी"],
    3: ["march", "માર્ચ", "मार्च"],
    4: ["april", "apr", "એપ્રિલ", "अप्रैल"],
    5: ["मई"],                       # English "may" and Gujarati "મે" are also common words: see _month_in
    6: ["june", "jun", "જૂન", "જુન", "जून"],
    7: ["july", "jul", "જુલાઈ", "જુલાઇ", "जुलाई"],
    8: ["august", "aug", "ઓગસ્ટ", "ઓગષ્ટ", "अगस्त"],
    9: ["september", "sept", "sep", "સપ્ટેમ્બર", "सितंबर", "सितम्बर"],
    10: ["october", "oct", "ઓક્ટોબર", "अक्टूबर", "अक्तूबर"],
    11: ["november", "nov", "નવેમ્બર", "नवंबर", "नवम्बर"],
    12: ["december", "dec", "ડિસેમ્બર", "दिसंबर", "दिसम्बर"],
}
MAY = [r"\b(?:in|of|for|during|since|from|till|until|last|this) may\b", r"\bmay (?:20\d\d|month)\b",
       r"(?:^|\s)મે(?:\s*મહિન|માં|\s*20\d\d)"]

# Words in front of "school" that are not school names ("which school", "my schools").
NOT_A_NAME = {
    "which", "what", "these", "those", "every", "each", "other", "primary", "your", "their", "this", "that",
    "good", "best", "worst", "weak", "weakest", "many", "some", "more", "most", "three", "four", "five",
    "seven", "eight", "nine", "the", "all", "any", "need", "needs", "government", "village", "cluster",
    "upper", "local", "high", "have", "visit", "about", "struggling", "same", "another", "center", "centre",
    "first", "next", "last", "whole", "lowest", "highest", "attendance", "secondary", "public", "private",
    "model", "data", "maths", "math", "science", "gujarati", "english", "hindi", "grade", "class", "visits",
    "missing", "schools", "school", "children", "students", "teachers", "teacher", "trend", "priority",
    "results", "result", "scores", "score", "month", "week", "today", "list", "everything", "them",
    # question words and determiners in Gujarati or Hindi typed in English letters ("konsi school")
    "konsi", "konsa", "kaunsi", "kaunsa", "kaunse", "kaun", "kis", "kin", "kai", "kayi", "kaya", "kya",
    "badhi", "badha", "mari", "mara", "mere", "meri", "sabhi", "koi", "koni", "aapni",
}
NOT_A_NAME_CAPITALISED = {w.capitalize() for w in NOT_A_NAME} | {
    "Std", "Standard", "Mathematics", "EVS", "My", "Block", "Diwali", "Navratri", "Monsoon", "June", "July",
    "August", "September", "October", "November", "December", "January", "February", "March", "April", "May",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "Please", "Total", "Gujarat",
    "India", "Shiksha", "Saathi", "Hello", "Namaste",
}
# Gujarati words before "શાળા" are only treated as an unknown village name when they end like
# a place name; otherwise "ઓછી હાજરીવાળી શાળાઓ" ("schools with low attendance") would look like one.
PLACE_ENDINGS = ("પુર", "પુરા", "નગર", "ગામ", "વાડા", "વાડી", "પરા", "ગઢ", "પાર", "પર", "સર", "પાદર", "ઓદ")
GU_ENDINGS = ("ની", "નો", "ના", "નું", "માં", "થી", "ને")


def skeleton(word):
    """Consonant key of a Gujarati-script word: vowel signs and nasal marks dropped, vowels merged."""
    return "".join(ch for ch in word.translate(VOWEL_BASE) if not unicodedata.category(ch).startswith("M"))


def _school_keys(data):
    """Searchable names per school: English village, Gujarati village, and the Gujarati name
    without its final vowel sign (so "રામપુર" finds "રામપુરા")."""
    keys = []
    for s in data.schools.itertuples():
        gu = s.village_gu
        gu_stem = gu[:-1] if unicodedata.category(gu[-1]).startswith("M") else gu
        keys.append((s.school_id, s.village.lower(), {gu, gu_stem}))
    return keys


def find_schools(text, data):
    """Return (school ids found, ids that are equally likely for one typed word, unknown name or None)."""
    norm = normalize(text)
    native = to_gujarati_script(norm)
    found, ambiguous, matched_words = [], [], set()

    for number in re.findall(r"\bgj-?c07-?(\d{3})\b", norm):
        if data.has_school(f"GJ-C07-{number}"):
            found.append(f"GJ-C07-{number}")

    keys = _school_keys(data)
    villages = {village: school_id for school_id, village, _ in keys}
    for school_id, village, gu_names in keys:
        if re.search(rf"\b{re.escape(village)}", norm) or any(g in native for g in gu_names if len(g) >= 3):
            found.append(school_id)
            matched_words.add(village)

    # Other spellings in Gujarati or Hindi script: "अंबालिया" -> આંબલિયા (Ambaliya).
    if not found:
        keys_by_skeleton = {skeleton(g): school_id for school_id, _, names in keys for g in names
                            if len(skeleton(g)) >= MIN_SKELETON}
        for word in re.findall(r"[\u0A80-\u0AFF]+", native):
            if skeleton(word) in keys_by_skeleton:
                found.append(keys_by_skeleton[skeleton(word)])

    # Typos in English letters: "Rampur" -> Rampura, "Chandrpur" -> Chandrapur.
    for word in sorted(set(re.findall(r"[a-z]{5,}", norm))):
        if any(word.startswith(v) for v in matched_words):
            continue
        scores = sorted(((SequenceMatcher(None, word, v).ratio(), v) for v in villages), reverse=True)
        best_score, best = scores[0]
        if best_score < FUZZY_CUTOFF:
            continue
        close = [v for score, v in scores if score >= FUZZY_CUTOFF and best_score - score < AMBIGUOUS_MARGIN]
        if len(close) > 1:
            ambiguous += [villages[v] for v in close]
        else:
            found.append(villages[best])

    found = list(dict.fromkeys(found))
    unknown = None if found or ambiguous else _unknown_school_name(text, norm, native, villages)
    return found, list(dict.fromkeys(ambiguous)), unknown


def _unknown_school_name(text, norm, native, villages):
    """A word used as a school name that is not one of this cluster's schools ("Khanpur school")."""
    english = re.findall(r"\b([a-z]{4,})\s+(?:primary\s+|pay center\s+)?(?:school|shala|vidyalaya)\b", norm)
    english += re.findall(r"\b(?:about|how is|how's|details of|info on|news from)\s+([a-z]{4,})\b", norm)
    english += [w.lower() for w in re.findall(r"\b(?:in|at|visit|visited|for|of)\s+([A-Z][a-z]{3,})\b", text)
                if w not in NOT_A_NAME_CAPITALISED]
    for word in english:
        if word not in NOT_A_NAME and word not in villages and word not in NUMBER_WORDS and not _month_in(word):
            typed = re.search(rf"\b{re.escape(word)}\b", text, re.IGNORECASE)
            return typed.group(0) if typed else word      # echo the name as she typed it
    # Hindi was converted letter by letter, so positions in `native` match `norm`: the
    # name is returned as she typed it.
    for m in re.finditer(r"(\S+)\s*(?:પ્રાથમિક\s*)?(?:શાળા|સ્કૂલ)", native):
        word, start = m.group(1), m.start(1)
        for ending in GU_ENDINGS:
            if word.endswith(ending) and word[:-len(ending)].endswith(PLACE_ENDINGS):
                word = word[:-len(ending)]
        if word.endswith(PLACE_ENDINGS) and word not in NOT_A_NAME:
            return norm[start:start + len(word)]
    return None


def find_grade(norm):
    patterns = [r"\b(?:grade|class|std\.?|standard|dhoran|dhoranu|kaksha)\s*(\d{1,2})\b",
                # an ordinal is a grade only next to a class word or a subject: "2nd week" is not Grade 2
                r"\b(\d{1,2})\s*(?:st|nd|rd|th)[\s-]*(?:grade|graders?|class|std|standard)\b",
                r"\b([1-8])(?:st|nd|rd|th)\s+(?:maths?|mathematics|gujarati|evs|science)\b",
                r"(?:ધોરણ|ધો\.?)\s*(\d{1,2})", r"(\d{1,2})\s*(?:મા|માં|મું|મી)?\s*ધોરણ",
                r"(?:कक्षा|क्लास)\s*(\d{1,2})", r"(\d{1,2})\s*(?:वीं|वी)"]
    for p in patterns:
        m = re.search(p, norm)
        if m:
            return int(m.group(1))
    for word, grade, follows in ORDINALS:
        if re.search(rf"{word}\s*{follows}", norm):
            return grade
    return None


def find_subject(norm):
    """The first subject mentioned, by position in the question."""
    hits = []
    for subject, patterns in SUBJECTS.items():
        for p in patterns:
            m = re.search(p, norm)
            if m:
                hits.append((m.start(), subject))
    return min(hits)[1] if hits else None


def _native_word_in(word, text):
    """A Gujarati or Hindi word as a whole word. Case endings may follow ("ઓક્ટોબરની"), but not a vowel
    sign, which would make it a different word ("જૂની" = old, "જૂનાગઢ" = Junagadh, not "જૂન" = June)."""
    for m in re.finditer(re.escape(word), text):
        before, after = text[m.start() - 1:m.start()], text[m.end():m.end() + 1]
        if before and unicodedata.category(before)[0] in "LM":
            continue
        if after and unicodedata.category(after)[0] == "M":
            continue
        return True
    return False


def _month_in(norm):
    if _any(norm, MAY):
        return 5
    for month, words in MONTH_WORDS.items():
        for word in words:
            if re.search(rf"\b{word}\b", norm) if word.isascii() else _native_word_in(word, norm):
                return month
    return None


def find_month(norm):
    month = _month_in(norm)
    return f"{DATA_YEAR}-{month:02d}" if month else None


def find_limit(norm):
    words = "|".join(sorted(map(re.escape, NUMBER_WORDS), key=len, reverse=True))
    patterns = [rf"(?:^|\s)(\d{{1,2}}|{words})\s*(?:schools?\b|શાળા|સ્કૂલ|स्कूल|विद्यालय)",
                rf"\btop\s*(\d{{1,2}}|{words})\b"]
    for p in patterns:
        m = re.search(p, norm)
        if m:
            value = m.group(1)
            n = int(value) if value.isdigit() else NUMBER_WORDS[value]
            return max(1, min(n, MAX_LIMIT))
    return DEFAULT_LIMIT


def find_reply_language(norm):
    """("gu", text without the request) when she asks for a language, else (None, text)."""
    for pattern, code in REPLY_LANGUAGE:
        m = re.search(pattern, norm)
        if m:
            return code or LANG_CODES[m.group(1)], (norm[:m.start()] + " " + norm[m.end():]).strip()
    return None, norm


def asks_school_type(text):
    """"Which schools are primary?": the list goes by school type instead of by need."""
    return _any(normalize(text), SCHOOL_TYPE)


def parse(text, data, school_id=None):
    """Read a question. `school_id` pins the school (used when she picks from a "which school?" list)."""
    q = Question(text=text, lang=detect_language(text), intent="out_of_scope")
    q.reply_lang, norm = find_reply_language(normalize(text))
    q.grade, q.subject = find_grade(norm), find_subject(norm)
    q.month, q.limit = find_month(norm), find_limit(norm)

    if school_id and data.has_school(school_id):
        q.school_ids, ambiguous, unknown = [school_id], [], None
    else:
        q.school_ids, ambiguous, unknown = find_schools(text, data)

    q.intent = _intent(norm, q, ambiguous, unknown)
    if ambiguous:
        q.school_ids = ambiguous
    q.unknown_school = unknown if q.intent == "school_not_found" else None
    return q


def _intent(norm, q, ambiguous, unknown):
    """Rules in order; the first that matches decides."""
    if not norm.strip("?.! "):
        return "help"
    if _any(norm, NOT_ALLOWED):
        return "not_allowed"
    about_people = _any(norm, PEOPLE)
    if about_people and (_any(norm, JUDGEMENT) or (_any(norm, JUDGEMENT_SOFT) and not _any(norm, ATTENDANCE))):
        return "people_judgement"
    if (about_people or _any(norm, CHILDREN)) and _any(norm, PERSONAL):
        return "personal_info"
    if ambiguous or len(q.school_ids) > 1:
        return "clarify_school"
    if unknown:
        return "school_not_found"

    one_school = len(q.school_ids) == 1
    if _any(norm, MISSING):
        return "missing_data"
    if _any(norm, OFFICER_STRONG) or (not one_school and _any(norm, OFFICER)):
        return "officer_summary"
    if _any(norm, RECENT_VISITS):
        return "recent_visits"
    if q.subject or (q.grade is not None and not _any(norm, ATTENDANCE)):
        return "subject_analysis" if one_school else "class_overview"
    if _any(norm, ATTENDANCE):
        return "attendance_trend"
    if one_school:
        return "school_summary"
    if (_any(norm, LIST_STRONG) or _any(norm, LIST_WEAK)) and not _any(norm, NEED):
        return "list_schools"
    if _any(norm, PRIORITY):
        return "top_priority_schools"
    if _any(norm, HELP):
        return "help"
    return "out_of_scope"
