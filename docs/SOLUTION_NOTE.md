<div class="masthead">
<div class="kicker">CG AI Build assignment · Solution note</div>
<h1>Shiksha Saathi</h1>
<div class="byline">Vishv Patel · 4 November 2026 · Live app: <a href="https://shiksha-saathi-ruddy.vercel.app">shiksha-saathi-ruddy.vercel.app</a> · Code, data and docs: <a href="https://github.com/vishv3010/ShikshaSaathi">github.com/vishv3010/ShikshaSaathi</a> (runs in under 5 minutes, no key needed)</div>
</div>

<div class="lead">A cluster coordinator asks, in Gujarati, English or Hindi, <em>"Which schools need attention this month, and what will you do about it?"</em> She gets the schools to visit first, why each one is flagged, and one action for each, in under two minutes. <strong>Every number comes from code. The AI only words the answer, and a checker rejects any AI text with a number the data does not hold.</strong></div>

<div class="stats">
<div><b>20</b>schools, May–October 2026, synthetic</div>
<div><b>3</b>languages: Gujarati, English, Hindi</div>
<div><b>284</b>automated tests; 13 of 13 planted bugs caught</div>
<div><b>≈ ₹4</b>per coordinator per month at 10,000</div>
</div>

## 1. Architecture

<div class="flow">
<div class="step"><b>1 · Understand</b>Rules read the question: 14 question types, misspelt school names, Gujarati and Hindi script. Gemini helps only when the rules cannot.</div>
<div class="arrow">→</div>
<div class="step"><b>2 · Compute</b>Python (pandas) computes every number from the CSVs. Missing stays missing, never 0.</div>
<div class="arrow">→</div>
<div class="step"><b>3 · Draft</b>A template writes the full answer in English or Gujarati, from those facts only.</div>
<div class="arrow">→</div>
<div class="step ai"><b>4 · Word (AI)</b>Gemini adds a one-line opening, or translates the answer into Hindi.</div>
<div class="arrow">→</div>
<div class="step check"><b>5 · Check</b>Every number in the AI text must be in the facts. If not, the checked draft is sent.</div>
</div>

- **One stateless `/ask` endpoint** (FastAPI) behind a phone-first chat page of about 13 KB; a WhatsApp or SwiftChat webhook could call the same endpoint.
- **Correct without the AI.** With no API key, or when Gemini fails or is slow, steps 1 and 4 are skipped and every answer is still right.
- **Plain language, measured.** On 23 questions written after the rules were built, the rules alone understood 87%, and 91% with Gemini; the misses were then fixed as general rules.
- **Free tools only:** Gemini 3.5 Flash-Lite (free tier), Vercel, open-source libraries.

## 2. Prioritisation logic

A *need-for-help* score from 0 to 100, built from published bands in the style of the Government of India's grading of ITIs (DGT). Learning carries 60 of the 100 points, as in Gujarat's Gunotsav.

| Indicator (latest month) | Bands → points | Max |
|---|---|---|
| Student attendance | below 70% → 25 · 70–79 → 18 · 80–89 → 9 · 90+ → 0 | 25 |
| Fall in attendance vs the previous 3 school months | 10+ points → 15 · 5–9.9 → 10 · 2–4.9 → 5 | 15 |
| Average score, all classes | below 40% → 35 · 40–49 → 25 · 50–59 → 15 · 60–69 → 5 | 35 |
| Children below basic level | 40%+ → 25 · 30–39 → 18 · 20–29 → 10 | 25 |

- **She sees why:** High is 70 and above, Medium 40–69, Low below 40. Each school shows *"need for help 78/100"* with its reasons, such as *"attendance fell from 80.8% to 64.9%"*.
- **The visit plan** moves a school visited in the last 14 days down to a phone follow-up, still mentions any school unvisited for 90+ days, and marks a school with missing data *"not enough data, please verify"*, never scoring it as 0.
- **One action per school**, from eight ordered rules (first match wins): missing data → call the head teacher; attendance fell 10+ points → list absent children with the SMC; school average below 45% → a daily 30-minute remedial period; one weak class → a subject activity, such as place value with bundles and sticks.
- **October result:** visit Haripar (78), Chandrapur (75) and Manekpur (66) first; Ambaliya (71) was visited 5 days ago, so a phone call; Umarvada does not have enough data.

## 3. How made-up numbers are prevented and detected

<div class="two">
<div><b>Prevent</b>Gemini never sees the CSVs and never calculates. It sees only this answer's draft and writes only the opening line or the Hindi translation. The details, with each number next to its school, come from code.</div>
<div><b>Detect</b>Every number in the AI text (0–9, ૦–૯ or ०–९) must exist in the facts computed for this question; percentages in words are rejected; numbers typed in her question never count. A Hindi translation must keep every number and really be in Hindi. On any failure the checked draft is sent and the failure is logged.</div>
</div>

**Evidence:** 284 tests from values worked out by hand, and 13 planted bugs, all caught. Of 97 live Gemini texts, the one real made-up figure (80% in a Hindi translation) and 7 Hindi replies left in English were all caught; a planted 99.9% was caught 6 times out of 6. **Known limit:** the checker proves a number is in the facts, not that it sits next to the right school, so Gemini writes only the opening line.

## 4. Guardrails

| | How the build handles it |
|---|---|
| **Accuracy over fluency** | Missing data is said out loud: *"No attendance record for Umarvada in October: the data has not arrived. Please check with the head teacher."* A closed month (May vacation) and a grade a school does not have each get their own wording. No cause is stated that the data cannot show. |
| **Respectful framing** | "Needs support first", never "worst". Questions blaming teachers are declined; low teacher attendance is shown as a school pattern that "can be leave, training or official duty". No staff or child names appear in answers. |
| **Low bandwidth** | A page of about 13 KB, one request per question, and short replies that fit in a WhatsApp message. |
| **Scope boundary** | Off-topic questions, requests for personal details and "ignore your rules" are declined politely, with examples of what she can ask. |

## 5. Cost per coordinator per month, at 10,000 CRCs

- **Usage assumed:** 100 questions per CRC a month (5 a working day): 80 get an opening line, 10 are Hindi translations, 10 need Gemini to read them.
- **Tokens measured on live calls:** opening line 888 in / 46 out; Hindi 614 / 353; reading a question 882 / 72: about 86,000 in and 8,000 out per CRC a month.
- **Price:** Gemini 3.5 Flash-Lite, $0.30 / $2.50 per million input / output tokens (Google, November 2026), at ₹88 to the dollar.

<div class="callout"><b>≈ $0.05 (about ₹4) per CRC per month</b> · ≈ $460 (about ₹40,000) a month for 10,000 CRCs, plus one small server ($20–50 a month). At five times the usage: about ₹2 lakh a month.</div>

## 6. Privacy by design

- **What would leave the government system:** only each answer's draft (school names, school-level percentages, visit-note text). Never student-level data, staff names or the CRC's identity.
- **How to minimise it:** replace school names with codes before the AI call; use a contracted model that does not train on the data, hosted in India, or a government-hosted open model; keep logs for 30 days with no personal identifiers.
- **The prototype** runs on Gemini's free tier, which Google may use to improve its products: fine only for synthetic data.

## 7. What I would do next

1. **WhatsApp or SwiftChat** on the same `/ask` endpoint, with Gujarati voice notes.
2. **A four-week pilot with 5 CRCs** on real VSK data: tune the bands and actions, and track whether flagged schools improve.
3. **School names replaced by codes** before any AI call, and a view of checker rejections and missing data across clusters.
4. **A per-sentence check** that each number belongs to its school, so the AI could safely write more of the answer.

<div class="foot">Dataset: <code>data/</code> (7 CSVs) and <code>docs/DATASET.md</code> · AI usage: <code>docs/AI_USAGE_LOG.md</code> · 41 assumptions and 37 design decisions: <code>docs/ASSUMPTIONS.md</code>, <code>docs/DECISIONS.md</code></div>
