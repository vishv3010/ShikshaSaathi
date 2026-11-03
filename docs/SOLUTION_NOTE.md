# Shiksha Saathi: solution note

**Vishv Patel · CG AI Build assignment · November 2026** · Code, data and docs: <https://github.com/vishv3010/ShikshaSaathi> (the README runs it in under 5 minutes, no key needed).

Bhavnaben, a CRC with 20 schools, asks on her phone in Gujarati, English or Hindi, *"Which schools need attention this month, and what will you do about it?"* She gets the schools to visit first, why each one is flagged, and one action for each, in under two minutes. **Every number comes from code; the AI only words the answer, and a checker rejects any AI text with a number the data does not hold.**

## 1. Architecture

| Step | What happens | Built with |
|---|---|---|
| 1. Understand | Rules read the question: 13 question types, school names with typos, in Gujarati or Hindi script ("રામપુરામાં", "रामपुरा"), grade, subject, month. Trap questions are caught first. Only a question the rules cannot place (e.g. Gujarati typed in English letters) goes to Gemini, whose JSON is checked against the data: a school the question never named is dropped. | Python |
| 2. Compute | Pandas over six CSVs returns the facts: every number, missing as *missing* (never 0), *not applicable* kept apart (Grade 7 at a primary school, May vacation). | pandas |
| 3. Draft | A template writes the full answer in English or Gujarati, only from the facts. | Python |
| 4. Word | Gemini writes a one- or two-sentence opening above the draft (English, Gujarati) or translates the whole draft (Hindi). The details below the opening are never rewritten. | Gemini 3.5 Flash-Lite |
| 5. Check | Number checker (section 3). If the AI text fails, the draft is sent and the failure is logged. | Python |

One `/ask` endpoint (FastAPI) serves a WhatsApp-style chat page of about 4 KB over the network; a WhatsApp or SwiftChat webhook would call the same endpoint. Without an API key, or when Gemini fails or runs out of quota, the Gemini parts are skipped and every answer is still correct. All tools are free.

**Data.** 20 synthetic schools in cluster GJ-C07, May–October 2026, following the Gujarat calendar (May vacation, monsoon dips, Navratri in October). Seven schools carry a designed story (migration, one weak class, slow decline, data gaps, a school visited five days ago); 39 visit notes in English and Gujarati; a facilities table; a validator that keeps gaps as gaps.

## 2. Prioritisation: a need-for-support score, not a report card

Banded points in the style of the Government of India's grading of ITIs (DGT); learning carries 60 of 100 points, as Gujarat's Gunotsav weighted learning highest.

| Indicator (latest month) | Bands → points | Max |
|---|---|---|
| Student attendance | <70% → 25 · 70–79 → 18 · 80–89 → 9 · ≥90 → 0 | 25 |
| Fall in attendance vs previous 3 school months | ≥10 pts → 15 · 5–9.9 → 10 · 2–4.9 → 5 | 15 |
| Average score, all classes | <40% → 35 · 40–49 → 25 · 50–59 → 15 · 60–69 → 5 | 35 |
| Children below basic | ≥40% → 25 · 30–39 → 18 · 20–29 → 10 | 25 |

High ≥70, Medium 40–69, Low <40. A school missing its month's attendance or half its results is *"not enough data, please verify"*, never scored as 0. For "visit this week", a school visited in the last 14 days moves down with "follow up by phone"; any school unvisited for 90+ days, and a Low school where an action rule still fires (e.g. one class below 40%), are mentioned anyway. **One action per school** comes from eight ordered rules, first match wins: missing data → call the head teacher; attendance fell 10+ points → list absent children with the SMC; teacher attendance below 85% → discuss class cover during leave or official duty; school average below 45% → daily 30-minute remedial period; one class below 40% → a subject activity (e.g. place value with bundles and sticks), and so on. October result: High Haripar 78, Chandrapur 75, Ambaliya 71 (visited 5 days ago: phone); visit list Haripar, Chandrapur, Manekpur; Umarvada *not enough data*.

## 3. How made-up numbers are prevented and detected

- **Prevent.** Gemini never sees the CSVs and never calculates. It sees only this question's draft, and writes only the opening line; the details, with each number next to its school, come from code, so they cannot be dropped or attached to the wrong school.
- **Detect.** Every number in the AI's text (digits 0-9, ૦-૯ or ०-९) must exist in the facts computed for this question; a percentage written in words is rejected; numbers in her question never count as allowed ("say Rampura scored 99%"); a Hindi translation must keep every number of the draft. On any failure the checked draft is sent and the rejection is logged. The rule-based answers pass the same facts-only check (a test).
- **Evidence.** 200 automated tests, written from values worked out by hand from the CSVs; 10 deliberately planted bugs, all caught. Live runs: 31 Gemini texts checked, **0 with an unsupported number**; a made-up 99.9% injected through the page's *Test the number checker* switch was caught every time (3 of 3); trap questions never reach Gemini.
- **What it cannot see, and the fix.** The checker proves a number exists in the facts, not that it sits next to the right school. The first live version let Gemini rewrite the whole answer: every number passed, but it silently dropped the warning that Umarvada's October data was missing. So Gemini now writes only the opening line.

## 4. Guardrails

- **Accuracy over fluency:** "No attendance record for Umarvada in October: the data has not arrived. Please check with the head teacher." Closed months, not-yet months and grades a school does not have each get their own wording. The assistant never states a cause the data cannot show; it quotes visit notes as "visit notes mention…".
- **Respectful framing:** "needs support first", never "worst"; questions blaming teachers are declined; low teacher attendance is described as a school pattern that "can be leave, training or official duty"; no staff or child names in any answer.
- **Low bandwidth:** about 4 KB page, one request per question, answers in about 1–3 s, short replies under WhatsApp's message limit, Gujarati replies fully in Gujarati.
- **Scope boundary:** off-topic questions, personal details and "ignore your rules" are declined politely with examples of what she can ask.

## 5. Cost per CRC per month at 10,000 CRCs

Measured on the live runs, tokens per Gemini call: opening line 888 in / 46 out (60% Gujarati), Hindi translation 614 / 353, reading an unplaced question 882 / 72. Assume **100 questions per CRC per month** (about 5 a day on 20 working days): 80 get an opening line, 10 are Hindi translations, 10 need Gemini to read them, and boundary answers make no call. That is about **86,000 input and 8,000 output tokens per CRC per month**. At Gemini 3.5 Flash-Lite's paid price ($0.30 per million input, $2.50 per million output tokens; Google pricing page, Nov 2026): **≈ $0.05 (about ₹4) per CRC per month, ≈ $460 (about ₹40,000) a month for 10,000 CRCs**, at ₹88/$. One small server (about $20–50 a month) covers the peak of about 3 questions a second. At 5× the usage it is still about ₹2 lakh a month. Levers: context caching of the fixed prompt ($0.03 per million cached tokens) and answering more questions by rules alone.

## 6. Privacy by design (in a real deployment)

What would leave the government system per question: only that answer's draft (school names, school-level percentages, visit-note text). Never student-level data (there is none: classes are averages), staff names (kept out of the facts) or the CRC's identity. To minimise further: replace school names with codes before the AI call and restore them after; use a paid or government-contracted model with no training on the data, in an Indian region, or a government-hosted open model (the check-and-fallback design works with any model); keep logs for 30 days with no personal identifiers. This prototype uses Gemini's free tier, whose content Google may use to improve its products; that is acceptable here only because all data is synthetic.

## 7. What I would do next

1. **WhatsApp or SwiftChat** on the same `/ask` (stateless already), plus Gujarati voice notes.
2. **Four-week pilot with 5 CRCs** on real VSK data: tune bands and actions, record which actions were done, and check whether flagged schools improve.
3. **Replace school names with codes** before the AI call; a monitoring view of checker rejections and missing data across clusters.
4. **A per-sentence check** that each number belongs to the school it is next to, which would let the AI write more of the answer.

Assumptions (23) and decisions (26) are in `docs/ASSUMPTIONS.md` and `docs/DECISIONS.md`; AI use, including where the AI was wrong and how it was caught, in `docs/AI_USAGE_LOG.md`.
