# Demo video script (5 minutes at most)

The brief asks for three real conversations, one with missing data. This script shows four short ones plus the number checker. Record with Loom (free, up to 5 minutes) or OBS. Every step below was walked through in the browser on 3 Nov.

**Before recording**
- Use the live link: <https://shiksha-saathi-ruddy.vercel.app>. Tap **For reviewers** at the bottom: it should say **AI: on**. Open the link once before recording, so the first answer is quick.
- Phone view: on a laptop, Chrome → right-click → **Inspect** → phone icon (device toolbar) → a phone such as *Pixel 7*. Or record your real phone screen.
- The page answers one question at a time: wait for an answer to finish before tapping the next question.
- Keep this script open on another screen. Speak slowly; short sentences.

---

**0:00–0:30 · The problem, and the first screen**
> "This is Shiksha Saathi, for a cluster coordinator like Bhavnaben with 20 schools. Her block officer asks: which schools need attention this month, and what will you do about it? She has 10 minutes and a basic phone. Before she types anything, the first screen answers it: the three schools to visit first, each with its reason, and the month in three numbers: 3 need help first, 4 to keep an eye on, 1 still waiting for data."

**0:30–1:30 · Conversation 1: the main question, in Gujarati**
Tap the language picker (🌐 **Auto**, top right) and choose **ગુજરાતી**: the whole screen switches to Gujarati. Tap the white button at the bottom of the green "board", *મુલાકાતની યોજના જુઓ*.
> "She gets the three schools to visit first as cards: Haripar, Chandrapur and Manekpur. Each card shows the priority, a score out of 100, why it is flagged, and one thing to do on the visit. The first line is written by Gemini; the cards, and every number on them, come from code."

Point at:
- the line under the answer, *✓ AIની મદદથી લખ્યું, દરેક આંકડો રેકોર્ડ સાથે ચકાસ્યો* ("written with AI, every number checked against the records");
- the box *આ પણ ધ્યાનમાં રાખો* ("also keep in mind"): Ambaliya was visited 5 days ago, so it is lower on the list (follow up by phone); Umarvada does not have enough October data to score.

Then set the picker back to **Auto** and scroll up to **Try asking**.

**1:30–2:20 · Conversation 2: "why"**
Tap *Why is Grade 5 Maths low in Rampura?*
> "36%, falling every month since June, 12.6 points below the cluster average. It quotes her own visit notes, and it says honestly that the data cannot show the exact cause. The action is a 20-minute place value activity she can start on the visit."

**2:20–3:00 · Conversation 3: missing data**
Tap *What was Umarvada's attendance in October?* (under **Try asking**).
> "Umarvada's October attendance never arrived. The assistant says so and tells her to check with the head teacher. It never guesses a number. May shows as school closed for vacation, which is different from missing."

**3:00–3:50 · The number checker at work**
Open **For reviewers** at the bottom and tick **Test the number checker**. Tap *Why is Grade 5 Maths low in Rampura?* again.
> "This test switch slips a made-up figure, 99.9%, into Gemini's text. The checker compares every number with the computed facts, finds 99.9 is not there, throws the AI text away, and says so at the top of the answer; the checked answer is shown instead. Prevention: the AI never sees the data and never calculates. Detection: this checker, in English, Gujarati and Hindi digits."

Untick the switch.

**3:50–4:30 · Conversation 4: Hindi and boundaries**
Set the picker to **हिन्दी** and tap the first question in the list, *पाँचवीं कक्षा गणित रामपुरा में कम क्यों है?* (Hindi answer, same numbers). Set the picker back to **Auto**, then type *Which teacher is lazy?*
> "Hindi works through Gemini, with the same checks. And it never blames people: it describes school patterns, and low teacher attendance can be leave or official duty."

**4:30–5:00 · Close**
> "It works without the AI too: every answer stays correct if Gemini is down. It costs about 4 rupees per coordinator per month at 10,000 coordinators. The code, the 2-page note, the data and my AI usage log are in the repository. Thank you."

---

**If something goes wrong while recording:** if the line under an answer says *AI is unavailable right now, so this answer comes straight from the records* (or *Lots of questions right now…*), the answer is still correct. Say "Gemini is slow right now, so the checked answer is shown", which is the fallback working as designed. It happened once in rehearsal (Gemini took over 10 seconds); the next question was back to normal.
