# Demo video script (5 minutes at most)

The brief asks for three real conversations, one with missing data. This script shows four short ones plus the number checker. Record with Loom (free, up to 5 minutes) or OBS.

**Before recording**
- Gemini on: the page footer says **AI: on**. (On the live link, open it once a minute before, to wake the free server.)
- Phone view: on a laptop, Chrome → right-click → **Inspect** → phone icon (device toolbar) → a phone such as *Pixel 7*. Or record your real phone screen.
- Keep this script open on another screen. Speak slowly; short sentences.

---

**0:00–0:30 · The problem**
> "This is Shiksha Saathi, for Bhavnaben, a cluster coordinator with 20 schools. Her block officer asks: which schools need attention this month, and what will you do about it? She has 10 minutes and a basic phone. She can ask in Gujarati, English or Hindi."

**0:30–1:30 · Conversation 1: the main question, in Gujarati**
Tap *આ અઠવાડિયે કઈ 3 શાળાઓની મુલાકાત લેવી?*
> "She gets the three schools to visit first: Haripar, Chandrapur and Manekpur. For each one: why it is flagged, a score out of 100 she can explain, and one action. The first line is written by Gemini; everything below it, every number, comes from code."

Point at:
- the green line **"AI wording · every number checked"**;
- *Ambaliya … visited 5 days ago, so it is lower on this list: follow up by phone*;
- *Umarvada: not enough October data*.

**1:30–2:20 · Conversation 2: "why"**
Tap *Why is Grade 5 Maths low in Rampura?*
> "36%, falling every month since June, 12.6 points below the cluster average. It quotes her own visit notes, and it says honestly that the data cannot show the exact cause. The action is a 20-minute place value activity she can start on the visit."

**2:20–3:00 · Conversation 3: missing data**
Tap *What was Umarvada's attendance in October?*
> "Umarvada's October attendance never arrived. The assistant says so and tells her to check with the head teacher. It never guesses a number. May shows as school closed for vacation, which is different from missing."

**3:00–3:50 · The number checker at work**
Tick **Test the number checker** (bottom left). Ask *Why is Grade 5 Maths low in Rampura?* again.
> "This test switch slips a made-up figure, 99.9%, into Gemini's text. The checker compares every number with the computed facts, finds 99.9 is not there, throws the AI text away, and sends the checked answer instead. Prevention: the AI never sees the data and never calculates. Detection: this checker, in English, Gujarati and Hindi digits."

Untick the switch.

**3:50–4:30 · Conversation 4: Hindi and boundaries**
Tap the Hindi question *पाँचवीं कक्षा गणित रामपुरा में कम क्यों है?* (Hindi answer, same numbers). Then type *Which teacher is lazy?*
> "Hindi works through Gemini, with the same checks. And it never blames people: it describes school patterns, and low teacher attendance can be leave or official duty."

**4:30–5:00 · Close**
> "It works without the AI too: every answer stays correct if Gemini is down. It costs about 4 rupees per coordinator per month at 10,000 coordinators. The code, the 2-page note, the data and my AI usage log are in the repository. Thank you."

---

**If something goes wrong while recording:** an answer marked "Checked answer from the records" (no AI wording) is still correct: say "Gemini's free quota is busy, so the checked answer is shown", which is the fallback working as designed.
