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


def date_text(iso_date, lang="en", year=False):
    """'2026-10-07' -> '7 October' / '7 ઑક્ટોબર' (with the year if asked)."""
    y, m, d = iso_date.split("-")
    text = f"{int(d)} {MONTHS[lang][int(m) - 1]}"
    return f"{text} {y}" if year else text


def join(items, lang="en"):
    """['a', 'b', 'c'] -> 'a, b and c' / 'a, b અને c'."""
    items = list(items)
    if len(items) < 2:
        return "".join(items)
    return f"{', '.join(items[:-1])} {AND[lang]} {items[-1]}"


AND = {"en": "and", "gu": "અને"}
TO = {"en": "to", "gu": "થી"}


def grades_text(grades, lang="en"):
    """[3, 4, 5, 6, 7, 8] -> '3 to 8' / '3 થી 8'; [4, 5] -> '4 and 5'."""
    grades = sorted(grades)
    if len(grades) > 2 and grades == list(range(grades[0], grades[-1] + 1)):
        return f"{grades[0]} {TO[lang]} {grades[-1]}"
    return join(map(str, grades), lang)
