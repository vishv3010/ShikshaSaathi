# Assumptions

The brief says to assume what it does not cover and to share those assumptions. Each one is listed here as it is made.

| # | Assumption | Why |
|---|---|---|
| A-01 | The cluster is one CRC's 20 schools, cluster code `C07`, with school IDs `GJ-C07-001` … `GJ-C07-020`. | Matches the ID format in the brief's sample rows. |
| A-02 | The brief's two `type` values map to the national school census (UDISE+) categories: **primary** = primary only (Std 1–5), **upper primary** = primary with upper primary (Std 1–8). A primary school therefore has no Grade 6–8 assessments; that is *not applicable*, not missing data. Standalone Std 6–8 schools are left out of this cluster to keep the prototype simple. | The brief gives the two types but not their grade ranges, and assesses Grades 3–8, so some schools must reach Std 8. See D-020. |
| A-03 | Grades 3–5 take EVS and grades 6–8 take Science. | The brief lists the subject as "EVS/Science". |
| A-04 | `pct_below_basic` is the percentage of tested students scoring below the "basic" proficiency level for that grade and subject. | The brief names the field but does not define it. |
| A-05 | Assessment rows are school-level averages per grade, subject and month; no student-level data exists in the system. | Matches the brief's table grain, and keeps the design privacy-friendly. |
| A-06 | The data covers May–October 2026 and follows the Gujarat school calendar: summer vacation in May (no school data), reopening in early June, monsoon dips in July–August, Navratri in October, Diwali break in November. | Realistic seasonality is part of the brief; see D-014. |
| A-07 | The `facilities` table is a yearly snapshot as of 30 September 2025 (the UDISE+ reference date), not monthly. | Facilities change slowly; see D-005. |
| A-08 | All names (schools, villages, head teachers) are invented. | The brief forbids real data. |
| A-09 | "This month" means the latest month with data (October 2026), and the assistant says which month it is using. | November 2026 is the Diwali break and is not complete. |
| A-10 | The CRC visits each school in person. In "visit this week" lists, a school visited in the last 14 days moves down the list, with a note saying when it was visited. | A school visited days ago is a lower priority for another trip. |
| A-11 | Assessments are monthly unit tests from June to October; June is a post-vacation baseline and October includes the first-term exam. | The brief's table is monthly; Gujarat schools reopen in June. |
| A-12 | Attendance % is the average daily attendance over the month's school days. | The brief gives one figure per school-month. |
| A-13 | "Days since last visit" is counted from 2 November 2026, the date of this data snapshot. | Needed for the visit-planning rule. |
| A-14 | Each CRC visit note is stored in English and Gujarati (`notes`, `notes_gu`), and replies quote the note in the reply's language. Real notes would usually be typed in one language, often Gujarati; translating them would be the LLM's job. | Gujarati replies must be fully Gujarati; the two versions carry the same numbers (checked by the validator). |
| A-15 | Missing data comes from failed or late uploads (e.g. weak mobile network), not from schools hiding results. | Keeps framing respectful; matches a real cause of gaps. |
| A-16 | A school's learning level is the simple average of its grade-subject results; classes are not weighted by size. | The data has no enrolment per grade. |
| A-17 | Cluster attendance is the average across schools that reported, not weighted by enrolment, and always says how many schools reported. | Easy to explain; a school with no data is not counted as 0. |
| A-18 | A school with fewer than half its expected results for the month, or fewer than 2 of the previous 3 months of attendance, is "not enough data" rather than scored. | A score from a few classes would not be fair to compare with full ones (D-003). |
| A-19 | A CRC should see every school at least once in 90 days, whatever its data shows. | Basis for the "not visited for over 90 days" note (D-019). |
| A-20 | Hindi replies are Gemini's translation of the checked English draft; without Gemini (no key, quota, failed check) a Hindi question is answered in English. | Hindi is a bonus in the brief and Bhavnaben prefers Gujarati; a third template set would cost time better spent on the must-haves (D-025). |
| A-21 | Grades 1 and 2 are not assessed in this data (the brief's assessments cover Grades 3–8). Asking about them is answered as "not assessed", not as missing data. | The brief's assessment table lists grades 3–8. |
| A-22 | The CRC already has the head teachers' names and phone numbers in her own directory, so the assistant never gives names or contact details of staff or children, even though `schools.csv` holds head teacher names. | Privacy by design: names never need to leave the system (D-018). |
| A-23 | "This month" and "last month" both mean the latest month with data (October). A month before the data (Jan–Apr) or after it (November) is answered with a note and the latest month. | November is the Diwali break and is not complete (A-09). |
| A-24 | The priority score's bands and weights (learning 60 of 100 points; attendance and its fall 40) are a starting point, not a validated model; a pilot on real VSK data would tune them. | Borrowed from the DGT grading of ITIs and Gujarat's Gunotsav (D-002, D-011); no real outcomes exist to fit them to. |
| A-25 | Cost estimate: a CRC asks about 100 questions a month (about 5 on each of 20 working days); 80 get an AI opening line, 10 are Hindi, 10 need the AI to read them; Gemini 3.5 Flash-Lite at its paid price of November 2026 ($0.30 / $2.50 per million input / output tokens); ₹88 per US dollar. | Token counts per call were measured on live runs; usage per CRC had to be assumed. |
| A-26 | Bhavnaben reads Gujarati script even when she types Gujarati in English letters, so such questions are answered in Gujarati script. | Common on WhatsApp in Gujarat: typing in English letters is easier on a phone keyboard than reading it. |
| A-27 | Using Gemini's free tier, where Google may use the content to improve its products, is acceptable for this prototype only because all data is synthetic; a real deployment would use a paid or government-hosted model. | Privacy by design (solution note, section 6). |
