# AI usage log

Which AI tools were used, for what, and who checked or decided what. Updated as the work happens, not at the end.

## Tools

- **Claude Code** (desktop app, Claude Opus 5.5): reading the brief, research, design discussion, writing code and docs, running checks.
- **Firecrawl** (web search and scraping, called from Claude Code): research on VSK, Gunotsav, CRC role, Gujarat school calendar, causes of low learning.
- **ChatGPT**: generated a second development plan from the brief, used as a comparison against the Claude Code plan.

## Log

| Date | Tool | What AI did (including its own checks) | What Vishv decided or did |
|---|---|---|---|
| 2 Nov | Claude Code | Cloned the repo; read the brief PDF and listed explicit and hidden requirements. | Shared the brief and the reviewer's email, which asks for all assumptions to be shared. |
| 2 Nov | Claude Code | Proposed a first plan and architecture. | Stopped it from jumping to a solution: asked for a plain explanation of the problem first, then research before design. |
| 2 Nov | Claude Code | Analysed the DGT DDGM grading circular and explained which parts transfer to schools; checked the grading formula against row 1 of the circular's results table (sums to 8.0). | Brought the circular (from his father) and asked whether it was useful. |
| 2 Nov | Claude Code + Firecrawl | Researched Gunotsav 2.0, VSK Gujarat, SwiftChat, the CRC role, migration and the Gujarat school calendar. Notes in `RESEARCH.md`. | Raised that low scores have many causes beyond attendance (facilities, teaching); chose to add a small facilities table (D-005). |
| 2 Nov | ChatGPT | Wrote a 7-page development plan (stack, data design, scoring table, tests, schedule). | Generated it and asked Claude Code to compare the two plans and keep the better parts. |
| 2 Nov | Claude Code | Compared both plans: kept ChatGPT's scoring table, validation step, intent list and cut list; rejected Streamlit and its May data month. Merged result in `PLAN.md`, reasons in D-008 to D-014. | Chose the Gemini free tier and free tools only (D-008). |
| 2 Nov | Claude Code | Wrote the data generator and validator. Inspected the output month by month, reproduced the brief's sample rows, tested the validator on deliberately corrupted data, confirmed identical output on re-runs, and previewed the planned score on the data. Notes in `DATASET.md`. | Approved starting the data step. |
| 3 Nov | Claude Code + web search | Checked school types against the RTE Act, UDISE+ census categories and the Gujarat TET structure; mapped the brief's two types to UDISE+ (D-020). | Noticed the school-type definition was an unchecked assumption and asked for it to be verified online. |
| 3 Nov | Claude Code | Wrote the no-LLM question layer (`understand.py`, `assistant.py`, `reply.py`) and two analysis additions (`class_overview`, `officer_summary`). Ran 56 realistic questions in English, Gujarati and Hindi and read every reply; re-derived the new expected figures from the raw CSVs with awk before writing tests; tapped every reply option to check it leads to an answer; added 4 guardrail bugs to the bug-planting script (8 of 8 caught). | Asked to be kept updated on what is being built and to be asked about anything unknown; left the "which school?" design to the recommendation. |
| 3 Nov | Claude Code | Wrote the scoring and analysis core (`saathi/`): priority score, visit plan, action rules in English and Gujarati, and facts for each question type. Checked two schools' scores by hand against the raw CSV rows, wrote 54 tests from those hand-checked values, then planted 4 bugs in a copy of the code to confirm the tests catch them (all 4 caught). Both bug-planting checks now live in the repo (`tests/test_validator.py`, `scripts/check_tests_catch_bugs.py`) so anyone can rerun them. | Approved starting the scoring step; asked for everything to be pushed so work can continue from a second laptop. |

## Where AI output was wrong or uncertain

| Date | What happened | How it was caught |
|---|---|---|
| 2 Nov | A scraped summary of the Gunotsav article split the 80% learning weight into sub-parts that did not add up clearly. | Claude Code flagged it as unclear and left it out; only unambiguous figures (80 / 12 / 8 and the grade bands) went into the notes. |
| 2 Nov | The ChatGPT plan treated May 2026 as a normal school month, but May is summer vacation in Gujarat. | Found while comparing plans, by checking against the Gujarat school calendar from the research (D-014). |
| 2 Nov | The ChatGPT plan only *prevented* made-up numbers; the brief asks to prevent *and detect* them. | Found while comparing plans; added a number checker (D-013). |
| 2 Nov | The ChatGPT plan's "which 3 schools to visit" ignored when each school was last visited. | Found while comparing plans; added a visit-recency rule (D-011). |
| 2 Nov | The AI-written validator crashed on duplicate rows instead of reporting them. | Caught by running it on a deliberately corrupted copy of the data; fixed, and it now reports all five planted errors. |
| 2 Nov | The generator picked random visit notes without checking school type, so two primary schools (Std 1–5) got notes about Grade 7 and Grade 8 classes. | Spotted while reading the generated `visits.csv`. Fixed the generator, and added a validator rule that fails on any note mentioning a grade the school does not have. |
| 2 Nov | The first version of the data put Ambaliya (the "just visited" school) fourth by need, so the visit rule would never visibly change the top 3. | Caught by previewing the score on the data; its learning level was lowered so the rule shows in the demo. |
| 3 Nov | A test written by Claude Code assumed only Ambaliya had a recent visit, but the visit dates had changed when the data was regenerated, so Talavdi (visited 20 Oct) was recent too. | The test failed; checking the data showed the code was right and the test's assumption was stale. Test fixed to match the data. |
| 3 Nov | The first visit plan never mentioned schools with fine data but no visit for months (Sonpura: 130 days). | Spotted while reading the first full output; added a "not visited for over 90 days" note (D-019). |
| 3 Nov | Assumption A-02 said "upper primary means Std 1–8", which is not the official definition (upper primary is Std 6–8). | Vishv asked for it to be checked online; corrected to the UDISE+ category "primary with upper primary" (D-020). Data unchanged. |
| 3 Nov | The first draft of the question rules would have refused "How can we increase attendance?" as a data-change attempt, treated "Which school should be visited this week?" as a past-visit question, answered "I need a loan" with the school list, and declined "worst teacher attendance" as blame. | Found by Claude Code reviewing its own draft against example questions before running it; rules narrowed and each case is now a test. |
| 3 Nov | First replies: "Science in Haripar" said "no Grade 6" (never asked); "Why is Gujarati low in Navli?" did not say it is above average; Chandrapur's attendance was mentioned twice; unknown names were echoed in lower case; "top 10" made a 2,700-character message. | Found by reading all 56 replies and by a test that caps reply length; each fixed and covered by a test. |
