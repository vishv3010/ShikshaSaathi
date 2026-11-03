# Decisions

One entry per non-obvious choice: what we chose, what else we considered, and why. Status is **Accepted** or **Proposed** (not yet confirmed).

---

### D-001 · Code computes every number; the LLM only understands and phrases — Accepted (2 Nov)

- **Problem:** a confident wrong number can send the CRC to the wrong school.
- **Options:** (a) give the LLM the CSVs and let it answer; (b) let the LLM write SQL; (c) the LLM picks from a fixed set of Python tools that return exact numbers, then phrases the reply.
- **Choice:** (c), plus an automatic checker that rejects any reply containing a number that is not in the tool output.
- **Why:** (a) lets the model do arithmetic and invent figures; (b) is flexible but hard to guarantee correct on a deadline. (c) makes made-up numbers both unlikely (prevention) and catchable (detection), which is exactly what the brief asks to show.

### D-002 · Priority score uses weighted bands, with learning weighted highest — Accepted in principle (2 Nov)

- **Choice:** each indicator is mapped to a band 0–5 and multiplied by a weight; the total gives a support-priority score. Learning outcomes carry the largest weight. A month-over-month trend component is included.
- **Why:** the banded method is the one the Government of India uses for ITIs (DGT DDGM 2025-26), so it is familiar to officials and easy to explain ("attendance is in band 2 of 5"). Gujarat's Gunotsav 2.0 gave 80% weight to learning outcomes. DDGM averages two years, so it misses sudden drops; a CRC needs this month's change. See `RESEARCH.md` §1–2.
- **Open:** exact indicators, band cut-offs and weights get fixed when the scoring code is written.

### D-003 · "Not enough data" instead of a guessed score — Accepted (2 Nov)

- **Choice:** if a school lacks the data needed for a fair score, it is marked "not enough data" and the assistant says so.
- **Why:** mirrors DDGM's Non-Graded rule and the brief's "when data is missing, the assistant must say so".

### D-004 · Only score on indicators that differ between schools — Accepted (2 Nov)

- **Why:** in the DDGM annexure, two of eight parameters were identical for every ITI listed, so they added nothing to the ranking.

### D-005 · Add a fifth table, `facilities`, used for "why" and actions only — Accepted (2 Nov, Vishv)

- **Problem:** low attendance or scores can come from many causes (facilities, teacher vacancies, multigrade classes) that attendance and scores alone cannot show.
- **Options:** (a) stay with the four required tables; (b) add facilities to the priority score; (c) add a small facilities table used only to explain and to pick the action.
- **Choice:** (c). A yearly snapshot with about five fields: teacher posts sanctioned vs filled, multigrade classes, drinking water, functional girls' toilet, electricity.
- **Why:** the brief says "at least" these tables, so extra context is allowed. Facilities change yearly and a CRC visit cannot fix them, so they should not move a monthly ranking, but they make "why" answers and actions (e.g. escalate to the block officer) much better.

### D-006 · Never state a cause the data cannot show — Accepted (2 Nov)

- **Choice:** the assistant reports what the data shows and suggests what to check on the visit. It cites visit notes and facilities data as evidence when they exist.
- **Why:** an invented cause ("attendance fell because of migration") is the same failure as an invented number.

### D-007 · A support score, not a report card — Accepted (2 Nov)

- **Choice:** language is "needs support first", never "worst school". Teacher attendance is never framed as blame (it may be official duty).
- **Why:** the brief asks to flag patterns, not people. DDGM is a judgement with consequences; this tool is for helping.

---

### D-008 · Gemini free tier, and free tools only — Accepted (2 Nov, Vishv)

- **Context:** Vishv's Claude subscription covers building with Claude Code until 5 Nov, but cannot power a deployed app, and reviewers may test after 5 Nov.
- **Choice:** Google Gemini API on the free tier for the demo. Every other tool is free too.
- **Trade-off:** free-tier requests may be used by Google to improve its products. Acceptable for synthetic data; a real deployment would use a paid tier or a government-hosted model (solution note, privacy section).

### D-009 · The app works without the LLM — Accepted (2 Nov)

- **Choice:** if Gemini is unavailable (no key, quota hit, error), keyword matching picks the intent and fixed templates write the reply, in Gujarati and English.
- **Why:** free-tier limits could break a reviewer's test. It also proves D-001: the numbers never depended on the LLM.

### D-010 · FastAPI + one small HTML page, not Streamlit — Accepted (2 Nov)

- **Options:** Streamlit (suggested by the ChatGPT plan) or FastAPI with a hand-written chat page.
- **Choice:** FastAPI + one small HTML page.
- **Why:** the brief asks for low bandwidth and light pages. Streamlit loads a large JavaScript bundle and keeps a live websocket that struggles on patchy 4G; a plain page with one HTTP request per question is light and survives a dropped connection. The `/ask` endpoint is also exactly what a WhatsApp or SwiftChat webhook would call. Cost: roughly one extra hour of UI work.

### D-011 · Starting score: four banded indicators, visits as a separate rule — Accepted in principle (2 Nov)

- **Choice:** student attendance (25), attendance drop vs previous 3 teaching months (15), learning level (35), students below basic (25), with High / Medium / Low bands. Visit recency is a separate rule for "visit this week" lists, not part of need. Details in `PLAN.md` §3.
- **From the ChatGPT plan:** the four indicators, thresholds and priority bands.
- **Added by us:** visit-recency rule (a school visited last week should not top "visit this week"), weakest grade-subject per school, no scoring on indicators that don't vary (D-004), learning weighted highest (D-002).

### D-012 · Validate the data before analysing it — Accepted (2 Nov)

- **From the ChatGPT plan.** A script checks columns, IDs, duplicates, ranges, dates and missing values, and prints a summary. Missing stays missing, never 0.

### D-013 · Prevent *and* detect made-up numbers — Accepted (2 Nov)

- **Prevent:** numbers on school cards are rendered straight from Python (from the ChatGPT plan), and the LLM only sees the facts for the current question.
- **Detect:** a checker compares every number in the LLM's text with the facts, including Gujarati and Devanagari digits, and falls back to the template when one does not match. The ChatGPT plan had prevention only; the brief asks for both.

### D-014 · Data window May–October 2026, with May as summer vacation — Accepted (2 Nov)

- **Context:** the ChatGPT plan used May–October as six normal months, but May is summer vacation in Gujarat (2025-26 calendar: 4 May – 7 June).
- **Choice:** keep the six calendar months ending October (the latest complete month on 2 Nov), with no school data in May by design. The assistant calls May "school closed", not "missing". November is the Diwali break, so "this month" answers use October and say so.
- **Why:** realism is graded, and the reviewers run VSK Gujarat; normal May attendance would look wrong to them. It also gives a natural example of "not applicable" vs "missing".

### D-015 · Designed data, not purely random data — Accepted (2 Nov)

- **Choice:** every school has a written profile, seven schools carry a specific story, and seeded noise sits on top. A `calendar.csv` table records which months school was open, so "school closed" comes from data rather than code. Gujarati names are stored alongside English ones. The brief's three sample rows are reproduced exactly.
- **Why:** purely random data has no patterns for the assistant to find and makes the demo meaningless. Designed stories (migration, a single weak class, data gaps, an improving school) test each part of the assistant on purpose. Details in `DATASET.md`.

### D-016 · Ties broken by learning level — Accepted (2 Nov)

- **Context:** on the generated data, banded points gave several schools identical scores (34, 24, 14).
- **Choice:** equal scores are ordered by lower average score, then higher share below basic, so the order is deterministic and still explainable.

### D-017 · Actions come from ordered rules, first match wins — Accepted (3 Nov)

- **Choice:** eight rules checked in a fixed order (table in `PLAN.md` §4). Sharp attendance drops come first because absent children cannot benefit from any classroom activity; teacher availability comes before learning because a remedial plan needs a teacher to run it.
- **Why not "biggest-scoring indicator decides"?** A fixed order is easier to explain in one sentence ("attendance fell 15.9 points, so the first step is finding the absent children") and gives the same answers on every story school.
- Action wording is stored in English and Gujarati in the code, so the no-LLM fallback can still give the action in Gujarati.

### D-018 · Facts are plain data; missing is None; head teacher names never leave the code — Accepted (3 Nov)

- **Choice:** every analysis function returns a plain JSON-ready dict. A missing value is `None`, never 0 or a guess. "Not applicable" (a grade the school does not have, a vacation month) has its own status. Head teacher names are not included in any facts.
- **Why:** the facts are exactly what the LLM will see and what the number checker compares against, so they must be complete, honest and minimal. Leaving names out means no personal name is ever sent to an external LLM (privacy by design).

### D-019 · The visit plan also mentions what the score alone would hide — Accepted (3 Nov)

- **Choice:** besides the top schools, the visit-plan facts include schools moved down because of a recent visit, Low-priority schools where an action rule fires (a single weak class), schools with not enough data, and schools not visited for over 90 days.
- **Why:** reviewing the first output showed Sonpura unvisited for 130 days and never mentioned, because its data looks fine. A CRC still needs to know that. The reply decides how much of this to show, so the message stays short.

### D-020 · School types follow the UDISE+ census categories — Accepted (3 Nov)

- **Context:** the brief gives `type` as "primary / upper primary" and assesses Grades 3–8, but does not define the types. Checked online on 3 Nov.
- **Findings:** the RTE Act 2009 defines elementary education as Class I–VIII and its rules split it into I–V (primary) and VI–VIII (upper primary). The national school census (UDISE+) has three categories: primary only (1–5), primary with upper primary (1–8), upper primary only (6–8). Gujarat's teacher eligibility test follows the same split (Std 1–5 and Std 6–8), and many Gujarat government schools run Std 1–8 under one roof and are still called "Prathmik Shala".
- **Choice:** `primary` = primary only (Std 1–5, assessed Grades 3–5). `upper primary` = primary with upper primary (Std 1–8, assessed Grades 3–8). Standalone Std 6–8 schools are not modelled.
- **Why:** it matches the census, covers the brief's Grade 3–8 range, and needs no change to the data or scoring. Only the wording in A-02 was imprecise: strictly, "upper primary" means Std 6–8, but the schools that offer it almost always also teach Std 1–5.
- **Sources:** UDISE+ Data Capture Format 2022-23 and guidelines (udiseplus.gov.in), RTE Act 2009 (indiacode.nic.in), Gujarat TET paper structure.
