# Deploying the live link

The app is one small Python web service. Two free ways to put it online, straight from the GitHub repository; either way every push to `main` redeploys it. **Vercel** (about 5 minutes, recommended: the app stays awake) or **Render** (about 10 minutes, sleeps when idle).

## Before you start: use a fresh Gemini key

The first key was pasted into a chat, so make a new one for the public link:

1. <https://aistudio.google.com> → **Get API key** → open the old key → **Delete key**.
2. **Create API key** → copy it. (Also put it in your local `.env` with `nano .env`.)

## Deploy on Vercel (free Hobby plan)

The repository already has what Vercel needs: `vercel.json` and `api/index.py` (the same app as the local run).

1. Go to <https://vercel.com> and log in **with GitHub**.
2. **Add New** → **Project** → find `ShikshaSaathi` → **Import**. (If it is not listed: **Adjust GitHub App Permissions** and allow the repository.)
3. Leave every setting as it is and click **Deploy**. Wait 1-2 minutes. The link looks like `https://shiksha-saathi.vercel.app`.
4. Add the key: the project → **Settings** → **Environment Variables** → key `GEMINI_API_KEY`, value the new key, environments **Production** and **Preview** → **Save**.
5. Apply it: **Deployments** → the latest one → **⋯** → **Redeploy**. Without the key the app still works, on rules only ("AI: off").
6. Make sure reviewers can open it: **Settings** → **Deployment Protection** → **Vercel Authentication** must not cover the production link (the default protects only preview links, which is fine).

## Or deploy on Render (free)

1. Go to <https://render.com> → **Get Started** → sign up **with GitHub**.
2. When GitHub asks, allow Render to see the `ShikshaSaathi` repository (a private repo is fine).
3. In the Render dashboard: **New** → **Blueprint** → choose `vishv3010/ShikshaSaathi`. Render reads `render.yaml` and shows one web service, `shiksha-saathi`, on the free plan.
4. It asks for **GEMINI_API_KEY**: paste the new key. Click **Apply** / **Deploy**.
5. Wait for the build (2–3 minutes). The link looks like `https://shiksha-saathi.onrender.com` (Render may add a suffix if the name is taken).

## Check it (2 minutes)

- `https://<your-link>/health` should show `"llm": true` and `"latest_month": "2026-10"`.
- Open the link on your phone and tap: *Which 3 schools need my visit this week?*, *What was Umarvada's attendance in October?*, the Hindi question, and once with **Test the number checker** ticked (the red "AI text rejected" line should appear above the answer).

## Good to know

- **Render's free plan sleeps** after about 15 minutes without visitors; the next visit takes up to a minute to wake it. Open the link yourself a minute before recording the video or sending it. Vercel does not sleep this way; its first answer after a quiet spell takes a few extra seconds.
- **If Gemini's free quota runs out**, or several people use it at once, answers continue without AI wording ("Checked answer from the records"); they stay correct. Each visitor is limited to 20 questions a minute.
- **After it works:** add the link to the top of `README.md` and to the first line of `docs/SOLUTION_NOTE.md`, rebuild the PDF (`.venv/bin/python scripts/build_note.py`), commit and push.

## If neither is available

Any host that runs a Python web app works: install with `pip install -r requirements.txt`, start with `uvicorn saathi.web:app --host 0.0.0.0 --port $PORT`, and set `GEMINI_API_KEY` as a secret. (For example a Hugging Face Space or Koyeb.) The repository with the README's 5-minute local run is also an accepted deliverable on its own.
