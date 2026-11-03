"""One suggested action per school, chosen by simple rules.

The rules are checked in order and the first match wins, so the CRC can always
be told why this action was suggested. The LLM may reword an action but never
chooses it. Every action is something a CRC can do on one visit or one call.
"""
from .lang import class_name, month_name

SHARP_DROP = 10        # attendance points lost vs the previous months
TEACHER_LOW = 85       # teacher attendance %
SCHOOL_WIDE_LOW = 45   # school average score %: below this, the whole school needs remedial time
WEAK_CLASS = 40        # a single class average % below this is flagged even in a Low-priority school
LOW_ATTENDANCE = 80    # student attendance %


def choose_action(entry):
    """Pick exactly one action for a scored (or not-enough-data) school entry."""
    weakest = entry["weakest_class"]
    target = {"grade": weakest["grade"], "subject": weakest["subject"]} if weakest else {}
    if entry["status"] == "not_enough_data":
        return {"code": "check_data", "month": entry["month"]}
    indicators = entry["indicators"]
    if indicators["attendance_drop"]["value"] >= SHARP_DROP:
        return {"code": "attendance_drop", "month": entry["month"]}
    teacher = entry["teacher_attendance_pct"]
    if teacher is not None and teacher < TEACHER_LOW:
        return {"code": "teacher_availability", **target}
    if indicators["learning_level"]["value"] < SCHOOL_WIDE_LOW:
        return {"code": "school_remedial"}
    if weakest and weakest["avg_score_pct"] < WEAK_CLASS:
        return {"code": "class_remedial", **target}
    if indicators["student_attendance"]["value"] < LOW_ATTENDANCE:
        return {"code": "attendance_follow_up"}
    if entry["priority"] != "Low" and weakest:
        return {"code": "class_remedial", **target}
    return {"code": "routine"}


TEXT = {
    "check_data": {
        "en": "Call the head teacher to find out why {month} data is missing, and help get it uploaded.",
        "gu": "{month}ની માહિતી કેમ નથી આવી તે જાણવા આચાર્યને ફોન કરો અને અપલોડ કરવામાં મદદ કરો.",
    },
    "attendance_drop": {
        "en": "Meet the head teacher and SMC to list children absent in {month}, check the reasons "
              "(for example migration, illness or festivals) and plan follow-up with their families.",
        "gu": "આચાર્ય અને SMC સાથે મળીને {month}માં ગેરહાજર બાળકોની યાદી બનાવો, કારણો તપાસો "
              "(જેમ કે સ્થળાંતર, બીમારી કે તહેવાર) અને તેમના પરિવારો સાથે ફોલો-અપનું આયોજન કરો.",
    },
    "teacher_availability": {
        "en": "Ask the head teacher how classes are covered when teachers are away on leave or official duty, "
              "and agree on support for {class_name}.",
        "gu": "શિક્ષકો રજા કે સરકારી ફરજ પર હોય ત્યારે વર્ગો કેવી રીતે ચાલે છે તે અંગે આચાર્ય સાથે વાત કરો "
              "અને {class_name} માટે મદદ નક્કી કરો.",
    },
    "school_remedial": {
        "en": "Observe classes and help the teachers start a daily 30-minute remedial period "
              "in small groups for reading and maths.",
        "gu": "વર્ગોનું નિરીક્ષણ કરો અને શિક્ષકો સાથે મળીને વાચન અને ગણિત માટે નાના જૂથોમાં "
              "રોજ 30 મિનિટનો ઉપચારાત્મક તાસ શરૂ કરાવો.",
    },
    "class_remedial": {
        "en": "Observe {class_name} and help the teacher start this activity: {activity}.",
        "gu": "{class_name}ના વર્ગનું નિરીક્ષણ કરો અને શિક્ષક સાથે આ પ્રવૃત્તિ શરૂ કરાવો: {activity}.",
    },
    "attendance_follow_up": {
        "en": "Go through the attendance register with the head teacher, find the children absent most often, "
              "and agree on follow-up with parents through the SMC.",
        "gu": "આચાર્ય સાથે હાજરી પત્રક જુઓ, વારંવાર ગેરહાજર રહેતાં બાળકો શોધો "
              "અને SMC દ્વારા વાલીઓ સાથે ફોલો-અપ નક્કી કરો.",
    },
    "routine": {
        "en": "No urgent concern in the data. Continue regular support.",
        "gu": "માહિતીમાં કોઈ તાત્કાલિક ચિંતા નથી. નિયમિત સહયોગ ચાલુ રાખો.",
    },
}

# Short classroom activities by subject; Maths differs for Grades 3-5 and 6-8.
ACTIVITIES = {
    ("Maths", "lower"): {
        "en": "a daily 20-minute place value and number practice with bundles and sticks or local objects",
        "gu": "બંડલ-સળીઓ કે સ્થાનિક વસ્તુઓ વડે રોજ 20 મિનિટ સ્થાનકિંમત અને સંખ્યાનો મહાવરો",
    },
    ("Maths", "upper"): {
        "en": "a short daily practice on fractions and ratios using paper folding and worked examples",
        "gu": "કાગળ વાળીને અને ઉદાહરણો સાથે અપૂર્ણાંક અને ગુણોત્તરનો રોજ ટૂંકો મહાવરો",
    },
    ("Gujarati", None): {
        "en": "a daily 15-minute reading period in small groups with story cards",
        "gu": "નાના જૂથોમાં વાર્તા-કાર્ડ સાથે રોજ 15 મિનિટનું વાચન",
    },
    ("EVS", None): {
        "en": "a hands-on activity linked to the village, for example a walk to the village water source",
        "gu": "ગામ સાથે જોડાયેલી પ્રવૃત્તિ, જેમ કે ગામના પાણીના સ્ત્રોતની મુલાકાત",
    },
    ("Science", None): {
        "en": "a simple experiment with local materials, after which children explain what they saw",
        "gu": "સ્થાનિક સામગ્રીથી સાદો પ્રયોગ, પછી બાળકો પોતે જે જોયું તે સમજાવે",
    },
}


def activity_for(grade, subject, lang="en"):
    level = ("lower" if grade <= 5 else "upper") if subject == "Maths" else None
    return ACTIVITIES[(subject, level)][lang]


def render_action(action, lang="en"):
    """The action as one sentence in the given language."""
    params = {}
    if "month" in action:
        params["month"] = month_name(action["month"], lang)
    if "grade" in action:
        params["class_name"] = class_name(action["grade"], action["subject"], lang)
        params["activity"] = activity_for(action["grade"], action["subject"], lang)
    else:
        params["class_name"] = {"en": "the most affected class", "gu": "સૌથી વધુ અસરગ્રસ્ત વર્ગ"}[lang]
    return TEXT[action["code"]][lang].format(**params)
