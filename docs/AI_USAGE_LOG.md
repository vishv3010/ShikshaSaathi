# AI usage log

**Shiksha Saathi · CG AI Build assignment · Vishv Patel · November 2026**

I used AI throughout the build as a fast collaborator whose work was always checked. I set the direction and made the decisions: what to build first, every design choice that changes an answer, the Gujarati wording, and the assumptions. The AI did much of the research, coding, testing and writing, and nothing it produced was accepted without a check.

## Tools and what they were used for

| Tool | Used for |
|---|---|
| **Claude Code** and the **Claude app** (Claude Opus 5.5) | The main build partner: reading the brief, research, design options, the code, tests and docs, deployment, and the demo video. |
| **Claude Code skills** | An independent code review, a design critique, an accessibility audit (WCAG 2.1 AA), plain-language interface text, the page's visual design, and chart colours that work for colour-blind readers. |
| **Firecrawl** (web search, from Claude Code) | Research: VSK Gujarat, Gunotsav, the CRC role, the 2026-27 Gujarat school calendar, RTE teacher norms, Gemini's price. |
| **ChatGPT** | A second, independent development plan, compared with Claude Code's; the better parts of each were kept. |
| **Gemini 3.5 Flash-Lite** (inside the product, free tier) | A one-line opening for answers, Hindi translations, and reading questions typed in Gujarati or Hindi with English letters. It never computes a number. |
| **Remotion** and **Kokoro** (open source) | The demo video: motion graphics around real recordings of the live app, and the narration voice. |

## How the AI's work was checked

- **Tests from hand-worked values:** 284 automated tests whose expected values were worked out from the CSVs by hand, not copied from the code's output.
- **Planted bugs:** 13 known bugs are planted one at a time in a copy of the code, and the tests must catch every one. They do.
- **Independent review:** an AI code review found 10 bugs the tests had missed; each was reproduced before it was fixed, and each now has a test.
- **Unseen questions:** 68 questions written after the rules were built, in four language forms, measure understanding honestly (on the held-out set, 87% with rules alone and 91% with Gemini, before fixes).
- **Live checks:** every Gemini reply passes the number checker (97 live texts checked), and the app was driven at phone size in all four language settings (123 of 123 browser checks).

## Where the AI was wrong, and how it was caught

57 AI mistakes were logged during the build, each with how it was caught. Six that shaped the design:

| What went wrong | How it was caught |
|---|---|
| Gemini, allowed to rewrite a whole answer, silently dropped the warning that Umarvada's October data was missing. Every number passed the checker. | Read in the first live run. Gemini now writes only the opening line; the details always come from code. |
| Gemini, translating into Hindi, wrote an attendance figure (80%) that is not in the data. | The number checker rejected it, and the checked answer was shown instead. |
| Gemini sometimes left a "Hindi" answer mostly in English. | A new check that a Hindi reply is really in Hindi, with one retry and an honest fallback. |
| ChatGPT's plan treated May as a normal school month; in Gujarat, May is the summer vacation. | Checked against the official school calendar while comparing the two plans. |
| Claude Code's own code had 10 bugs its tests missed, such as reading "2nd week" as Grade 2. | The independent code review; each bug was reproduced, fixed and covered by a test. |
| Claude Code reported that every colour pair on the page met WCAG AA after checking only the text colours. | An accessibility audit that measured the rendered page; the failing pairs were fixed and measured again. |
