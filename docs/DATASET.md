# Dataset notes

Synthetic data for one cluster (`GJ-C07`) of 20 schools, May–October 2026. Every name is invented; any match with a real school, village or person is a coincidence.

## How it was generated

`scripts/generate_data.py` builds every table from a written-down design rather than pure randomness:

1. **Each school has a profile:** base student attendance, base teacher attendance and base learning level (a strong / average / weak mix).
2. **Shared month effects follow the Gujarat calendar:** no data in May (summer vacation), lower attendance and a post-vacation learning dip in June, monsoon dips in July–August, a Navratri dip in October.
3. **Subject and grade effects:** Maths a little lower, Gujarati a little higher, scores ease down slightly in higher grades.
4. **Seven schools carry a designed story** (below), so there are real patterns for the assistant to find.
5. **Seeded random noise** on top (seed 7), so the data looks natural and **every run produces byte-identical files.**
6. **Missing values are added on purpose,** both a systematic gap and a few random ones.

`pct_below_basic` is derived from the average score with noise, fitted to the brief's own sample rows. The three sample rows printed in the brief (GJ-C07-014 and GJ-C07-009, August 2026) are reproduced exactly.

`scripts/validate_data.py` checks the result before anything uses it: required columns, unknown or duplicate IDs, values outside 0–100, rows in vacation months, grades a school does not have, subjects not taught in a grade, visit notes that mention grades a school does not have, and expected vs actual row counts. It was tested on a deliberately corrupted copy of the data and caught all five planted errors.

```
.venv/Scripts/python scripts/generate_data.py
.venv/Scripts/python scripts/validate_data.py
```

## Tables

| File | Rows | Grain | Columns |
|---|---|---|---|
| `schools.csv` | 20 | school | school_id, name, name_gu, village, village_gu, type, enrolment, head_teacher |
| `calendar.csv` | 6 | month | month, school_open, note |
| `attendance.csv` | 99 | school × month | school_id, month, student_attendance_pct, teacher_attendance_pct |
| `assessments.csv` | 1,315 | school × month × grade × subject | school_id, month, grade, subject, avg_score_pct, pct_below_basic |
| `visits.csv` | 39 | CRC visit | school_id, visit_date, focus_area, notes |
| `facilities.csv` | 20 | school (snapshot 30 Sep 2025) | school_id, as_of_date, teacher_posts_sanctioned, teachers_in_position, multigrade_classes, drinking_water, girls_toilet, electricity |

- 10 primary schools (Std 1–5, assessed in Grades 3–5) and 10 upper primary schools (Std 1–8, assessed in Grades 3–8).
- Subjects: Gujarati, Maths, and EVS (Grades 3–5) or Science (Grades 6–8).
- Gujarati names (`name_gu`, `village_gu`) let replies in Gujarati use the right script without the LLM transliterating.
- Files are UTF-8 with a BOM, so Gujarati displays correctly when opened in Excel.

## The designed stories

| School | Story | What the data shows |
|---|---|---|
| GJ-C07-003 Chandrapur | Seasonal migration | Student attendance about 80% until September, then 64.9% in October. September visit note: families expected to leave for sugarcane harvesting after Navratri. |
| GJ-C07-006 Haripar | Low on everything, long unvisited | Attendance about 70%, average score 38%, 41% below basic. Last visit 3 July. Facilities: 1 of 3 teacher posts vacant, multigrade classes, girls' toilet and drinking water not functional. |
| GJ-C07-008 Kesarpura | Improving | Average score 34% in June rising to 55% in October, after a remedial programme noted in the July visit. |
| GJ-C07-011 Manekpur | Slow decline, teachers on duty | Attendance and scores ease down from August. Teacher attendance 80% and 77% in September and October; visit note says two teachers are deputed on election (BLO) duty. |
| GJ-C07-014 Rampura | One weak class | Fine overall, but Grade 5 Maths falls from 45% to 36% while Grade 5 Gujarati is 58–63%. Visit notes: place value and division weak; Grades 4 and 5 taught together. |
| GJ-C07-017 Umarvada | Data gaps | September student attendance missing, October not uploaded, only Gujarati results for September, none for October. Visit note: the attendance app does not sync on the weak mobile network. |
| GJ-C07-019 Ambaliya | High need, just visited | Attendance about 74%, average score about 39%, but visited on 28 October. |

The other 13 schools are average to strong with natural variation.

## Missing values (on purpose)

| What | Where |
|---|---|
| Whole attendance row absent | GJ-C07-017, October |
| Student attendance blank | GJ-C07-017, September |
| Teacher attendance blank | 2 random school-months |
| Assessment rows absent | GJ-C07-017 September (except Gujarati) and October, plus about 1.5% of other rows at random |
| `pct_below_basic` blank | 2 random rows |
| Electricity not reported | GJ-C07-017 |
| **Not missing, but not applicable** | Grades 6–8 at primary schools; all school data in May (vacation) |

## Sanity check against the planned score

A throwaway run of the score in `PLAN.md` §3 on October data ranks Haripar (78), Chandrapur (75), Ambaliya (71) and Manekpur (66) highest, and marks Umarvada "not enough data". Rampura scores only 34 overall even though its Grade 5 Maths is 36%, which is why the plan also reports each school's weakest grade-subject. Banded points produce ties (several schools on 34, 24 and 14), so the scoring code needs a tie-breaker.
