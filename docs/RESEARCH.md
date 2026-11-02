# Research notes

Done before designing anything, to understand the user, the data and the local system.

## 1. Government grading method (DGT DDGM circular, July 2025)

Source: Directorate General of Training, MSDE — "Data Driven Grading Methodology (DDGM) for grading of ITIs, AY 2025-26" (circular dated 17 July 2025). It grades vocational institutes (ITIs), not schools, but the method transfers.

- 8 parameters, each with a weight (weights sum to 100), e.g. Admission % (30), Pass % (30), CBT participation (10).
- Each raw value is mapped to a band 0–5 (e.g. Pass % ≥80 → 5, <40 → 0).
- Formula: `(Σ weight × band / 100) × 2` → score out of 10.
- Checked by hand against Annexure-I row 1: 2.4 + 0.5 + 0.3 + 3 + 1 + 0.8 + 0 + 0 = 8.0, which matches the published final grade. Max contribution of a parameter = weight / 10.
- **Non-Graded (NG):** 90 of 14,580 ITIs got no grade because data was insufficient. Missing data → no score, not a guessed score.
- **Grievance + appeal:** institutes can contest a grade with evidence.
- Observation from the annexure: parameter 5 is at max (1) and parameter 7 is 0 for all 29 listed ITIs, so those two parameters separate no one.

**What we take:** banded weighted scoring, a published formula, a "not enough data" status, a way for the human to contest a flag, and only scoring on indicators that vary.
**What we don't take:** it is a judgement with consequences (score < 4 blocks affiliation) and averages two years. Ours is a support-priority signal and must react to month-to-month change.

## 2. Gujarat's own school grading — Gunotsav 2.0 / GSQAC

- Gunotsav 2.0 (launched 2019-20) gave **80% weight to learning outcomes**; co-curricular activities 12%, resources and their use 8%. Grades: A+ (85–100), A (75–85), B (50–75), C (25–50), D (0–25). — Indian Express, 28 Jul 2021: https://indianexpress.com/article/cities/ahmedabad/gunotsav-evaluation-only-14-of-gujarats-30681-govt-schools-show-improved-learning-outcomes-7425785/
- Now run as GSQAC on the VSK platform: https://gsqac-frontend.gujaratvsk.org/
- **Takeaway:** learning should carry the largest weight in our priority score.

## 3. VSK Gujarat and ConveGenius

- VSK monitors about 1.15 crore students across about 54,000 schools: attendance, assessments, infrastructure and teacher data. — NITI Frontier Tech: https://frontiertech.niti.gov.in/story/data-driven-classrooms-gujarats-vidya-samiksha-kendra-ushers-in-smart-governance-in-education/
- ConveGenius frames VSK as a "6A" framework: Attendance, Assessments, Adaptive Learning, Administration, Accreditation, AI nudges. VSK bots run on **SwiftChat**, ConveGenius's chat platform. — https://convegenius.com/VSK-CaseStudy.html
- **Takeaway:** Shiksha Saathi fits as a CRC-facing bot on SwiftChat / WhatsApp.

## 4. The CRC role

- CRCs give on-site academic support: regular school visits, classroom observation, teacher support and training, monitoring of programmes. — https://educationforallinindia.com/overview-of-cluster-resource-center/
- **Takeaway:** actions must be things a CRC can do on one visit: observe a class, run a short remedial activity, talk to the head teacher, or escalate to the block officer.

## 5. Why schools struggle (beyond attendance and scores)

| Area | Examples |
|---|---|
| Children / families | Seasonal migration (sugarcane harvest migration from south Gujarat for about half the year), farm work, monsoon illness, home language other than Gujarati |
| Facilities | No drinking water, non-functional girls' toilet, no electricity, too few classrooms |
| Teachers | Vacant posts, multigrade classes, teachers on non-teaching duty (elections, surveys) |
| Calendar | Monsoon, Navratri, Diwali break, June reopening |

Sources: seasonal sugarcane migration in Gujarat — https://pmc.ncbi.nlm.nih.gov/articles/PMC7874564/ ; NITI Aayog, School Education System in India (2026) — https://www.niti.gov.in/sites/default/files/2026-05/School-Education-System-in-India.pdf

**Key insight:** monthly attendance and scores show *where* there is a problem, rarely *why*. The why is found on the visit. The assistant points to the school and suggests what to check; it does not invent causes.

## 6. Gujarat school calendar

- 2025-26: term 1 from 9 June to 15 October, Diwali break 16 October to 5 November, summer vacation 4 May to 7 June 2026. — Times of India: https://timesofindia.indiatimes.com/city/ahmedabad/gujarat-board-releases-academic-calendar-with-exam-dates-holidays-for-2025-26/articleshow/120137529.cms
- **Takeaway:** synthetic data should show a June reopening ramp-up, monsoon dips (July–August), a festival dip (Navratri, October) and no regular classes during vacations.
