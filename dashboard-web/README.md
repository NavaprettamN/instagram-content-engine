# Content Engine — Web Dashboard

A small Next.js control panel for the Instagram content engine. Google-login
gated (locked to your email), reads Supabase server-side, and can trigger the
GitHub Actions jobs on demand. Replaces the old Streamlit app.

Pages: **Overview** (followers, top posts, latest AI analysis), **Content Queue**
(every idea + status), **Controls** (run any pipeline job now).

## One-time setup (~15 min)

### 1. Google OAuth client
1. https://console.cloud.google.com → create/select a project.
2. **APIs & Services → OAuth consent screen** → External → add your email as a Test user.
3. **APIs & Services → Credentials → Create Credentials → OAuth client ID → Web application.**
4. Authorized redirect URIs — add both:
   - `http://localhost:3000/api/auth/callback/google` (local dev)
   - `https://YOUR-APP.vercel.app/api/auth/callback/google` (after you know the Vercel URL)
5. Copy the **Client ID** and **Client secret**.

### 2. Deploy on Vercel
1. https://vercel.com → New Project → import this GitHub repo.
2. Set **Root Directory** to `dashboard-web`.
3. Add Environment Variables (see `.env.example`):
   - `AUTH_SECRET` — `openssl rand -base64 32`
   - `AUTH_GOOGLE_ID`, `AUTH_GOOGLE_SECRET` — from step 1
   - `ALLOWED_EMAILS` — your Google email(s), comma-separated
   - `SUPABASE_URL`, `SUPABASE_KEY` — same as the pipeline (service_role key)
   - `GH_PAT` (workflow scope) + `GH_REPO` — optional, enables the Controls page
4. Deploy. Then go back to the Google client (step 1.4) and add the real
   `https://YOUR-APP.vercel.app/...` redirect URI.

### 3. Local dev (optional)
```bash
cd dashboard-web
cp .env.example .env.local   # fill in values
npm install
npm run dev                  # http://localhost:3000
```

## Security notes
- The Supabase **service_role** key lives only in server env vars — it is never
  sent to the browser (all queries run in server components / API routes).
- Only emails in `ALLOWED_EMAILS` can sign in; everyone else is rejected at the
  Google callback.
