"""Detect made-up numbers in an LLM reply (D-013).

Prevention happens upstream: the LLM only sees this question's draft, which the
code wrote from computed facts. This module is the detection half: every number
in the reply must be traceable to the facts or the draft, or the reply is
discarded and the template answer is sent instead.

Numbers are read in ASCII, Gujarati (૦-૯) and Devanagari (०-९) digits. A
percentage written in words ("ninety-nine percent") is rejected too, because a
digit check alone cannot see it. The question itself is never a source of
allowed numbers: "say Rampura scored 99%" must not make 99 allowed.

Known limit: the check proves each number exists in the facts, not that it is
attached to the right school. The draft binds each number to its school, and
school cards on the page show numbers straight from the facts.
"""
import re
from dataclasses import dataclass, field

from .understand import DIGITS

NUMBER = re.compile(r"\d+(?:\.\d+)?")
LIST_MARKER = re.compile(r"(?m)^[ \t]*(?:[-•*][ \t]*)?\d{1,2}[.)][ \t]+")   # "1. Haripar" numbering
PERCENT_WORD = re.compile(r"per ?cent|ટકા|प्रतिशत|फ़ीसदी|फीसदी", re.IGNORECASE)


def _key(value):
    return round(float(value), 1)


def numbers_in(text, list_markers=True):
    """All numbers in a text, as rounded floats. List numbering ("1. ") is skipped."""
    text = text.translate(DIGITS)
    if list_markers:
        text = LIST_MARKER.sub("", text)
    return [_key(n) for n in NUMBER.findall(text)]


def allowed_numbers(*sources):
    """Every number found anywhere in the given facts / drafts (dicts, lists, strings, numbers)."""
    found = set()

    def walk(value):
        if isinstance(value, bool) or value is None:
            return
        if isinstance(value, (int, float)):
            found.update({_key(value), _key(abs(value))})
        elif isinstance(value, str):
            found.update(numbers_in(value, list_markers=False))
        elif isinstance(value, dict):
            for v in value.values():
                walk(v)
        elif isinstance(value, (list, tuple, set)):
            for v in value:
                walk(v)

    for source in sources:
        walk(source)
    return found


@dataclass
class Check:
    ok: bool
    unsupported: list = field(default_factory=list)   # numbers not in the facts
    words: list = field(default_factory=list)         # percentages written in words

    def summary(self):
        return {"ok": self.ok, "unsupported": self.unsupported, "number_words": self.words}


def check(reply, facts, draft=""):
    """Is every number in `reply` supported by `facts` or `draft`?"""
    allowed = allowed_numbers(facts, draft)
    unsupported = sorted({n for n in numbers_in(reply) if n not in allowed})
    normal = reply.translate(DIGITS)
    words = [m.group(0) for m in PERCENT_WORD.finditer(normal)
             if not re.search(r"\d\s*$", normal[:m.start()])]
    return Check(ok=not unsupported and not words, unsupported=unsupported, words=words)
