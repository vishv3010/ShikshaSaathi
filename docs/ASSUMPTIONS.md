# Assumptions

The brief says to assume what it does not cover and to share those assumptions. Each one is listed below with its reason, in the order it was made. A plain-language summary of the 10 that shape the answers most was emailed to the reviewer on 3 Nov, before the project was shown.

## By perspective

The same assumptions, grouped by whose point of view they come from, so each reader can find theirs.

| Perspective | Assumptions |
|---|---|
| Bhavnaben, the CRC (the user) | A-09, A-10, A-13, A-19, A-22, A-23, A-26, A-28, A-29, A-38, A-40 |
| Teachers and head teachers | A-15, A-30, A-31, A-33, A-35 |
| Children and parents | A-04, A-05, A-32 |
| Block officer and the education department | A-02, A-07, A-24, A-33, A-34, A-39 |
| The data | A-01, A-03, A-06, A-08, A-11, A-12, A-14, A-16, A-17, A-18, A-21, A-41 |
| The AI | A-20, A-27, A-36 |
| The builder (scope and time) | A-37 |
| Cost and privacy at scale | A-25, A-27 |

## All assumptions

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
| A-09 | "This month" means the latest month with data (October 2026), and the assistant says which month it is using. | On 2 November only two school days of November have passed, and schools close for Diwali from 5 to 25 November (Gujarat calendar 2026-27). |
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
| A-28 | One CRC looks after one cluster and should see only her own schools; in a real deployment her login would decide which cluster she sees. The prototype holds one cluster and has no login. | The brief describes one CRC with 15–25 schools; logins are outside this timebox. |
| A-29 | Lists of schools default to 3, about what a CRC can visit in a week; she can ask for up to 10. | The brief's own example is "Which 3 schools need my visit this week?". |
| A-30 | Teacher attendance is not part of the priority score, because a teacher's absence is often leave, training or official duty (for example BLO or election work). Below 85% it only shapes the action: how classes are covered. | Ranking a school on teacher absence would blame people for duties they cannot refuse. |
| A-31 | Suggested classroom activities use low-cost local materials (bundles and sticks, story cards, the village water source) and take 15–30 minutes a day, so a teacher can start them without new resources or training. | An action a school cannot start on the day of the visit is not an action. |
| A-32 | Every school has a working School Management Committee (SMC), as the RTE Act requires; follow-up with parents goes through the head teacher and the SMC, and the CRC does not contact families directly. | Matches how government schools reach parents; keeps children's details out of the assistant. |
| A-33 | Head teachers enter the data (the attendance app and monthly results). In a real deployment it would reach the assistant from VSK once a month; the prototype reads CSV files. | VSK Gujarat already collects attendance and assessment data (brief). |
| A-34 | The summary for the block officer is a short text message she forwards on WhatsApp, not a report or a dashboard. | The brief: she uses WhatsApp daily, and charts with many filters do not help her. |
| A-35 | Facility problems (toilets, drinking water, vacant teacher posts) explain results but never become the suggested action, because a CRC cannot fix them on a visit; the head teacher and the block office handle them. They are not in the score either (D-005). | Facilities change yearly and need budgets, not a visit. |
| A-36 | The AI can be slow, wrong or unavailable (quota, network), and is never trusted with numbers: it never sees the data files, never calculates, and every number it writes is checked against what the code computed. Every answer must be correct without it. | Accuracy over fluency (brief); D-001, D-009, D-013. |
| A-37 | With 12–15 hours, the must-haves (correct numbers, honest gaps, one action per school, Gujarati) come before extras such as WhatsApp integration, voice input, logins or dashboards. A web chat page stands in for WhatsApp; the same `/ask` endpoint is what a WhatsApp or SwiftChat webhook would call. | The brief caps the time and values thinking and shipping over polish. |
| A-38 | She is online when she asks (no offline mode), and replies are plain text, so the same answer would work as a WhatsApp message. | Patchy 4G is handled by one small request per question and short replies, not by offline storage. |
| A-39 | Sanctioned teacher posts follow the RTE Act's Schedule by enrolment (in a Std 1-8 school, 5 of every 8 children are taken to be in Std 1-5), and three schools have one vacant post. | Real posts are sanctioned by these norms; it gives a median of 30 children per teacher, as the RTE norm of 30-35 expects. |
| A-40 | A CRC fits about 2 school visits a week around meetings, training and data work, so each school is visited about once every two months. | No Gujarat norm was found; Samagra Shiksha circulars elsewhere ask for once a month (Andhra Pradesh) to once in two months (Delhi). |
| A-41 | The data follows the real 2026-27 Gujarat school calendar (reopening 8 June after a 35-day summer vacation; Diwali vacation 5-25 November), and no CRC visit falls on a Sunday or a school holiday (Muharram 26 June, Independence Day 15 August, Gandhi Jayanti 2 October, Dussehra 20 October). | Reviewers know this calendar; a visit on a holiday would look wrong. |
