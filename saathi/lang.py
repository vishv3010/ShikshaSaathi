"""Words that appear inside replies, in each supported language."""

LANGS = ["en", "gu"]

MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"],
    "gu": ["જાન્યુઆરી", "ફેબ્રુઆરી", "માર્ચ", "એપ્રિલ", "મે", "જૂન",
           "જુલાઈ", "ઑગસ્ટ", "સપ્ટેમ્બર", "ઑક્ટોબર", "નવેમ્બર", "ડિસેમ્બર"],
}

SUBJECTS = {
    "en": {"Gujarati": "Gujarati", "Maths": "Maths", "EVS": "EVS", "Science": "Science"},
    "gu": {"Gujarati": "ગુજરાતી", "Maths": "ગણિત", "EVS": "પર્યાવરણ", "Science": "વિજ્ઞાન"},
}

GRADE = {"en": "Grade {grade}", "gu": "ધોરણ {grade}"}


def month_name(month, lang="en"):
    """'2026-10' -> 'October' / 'ઑક્ટોબર'."""
    return MONTHS[lang][int(month.split("-")[1]) - 1]


def class_name(grade, subject, lang="en"):
    """(5, 'Maths') -> 'Grade 5 Maths' / 'ધોરણ 5 ગણિત'."""
    return f"{GRADE[lang].format(grade=grade)} {SUBJECTS[lang][subject]}"
