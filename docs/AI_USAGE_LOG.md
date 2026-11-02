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
