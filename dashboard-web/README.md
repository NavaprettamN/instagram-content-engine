# Meme Engine — Web Dashboard

A Next.js control panel for the Instagram meme engine, hosted on Vercel at
https://meme-engine-dashboard.vercel.app (auto-deploys from `main`).
Google-login gated (owner's email is the built-in admin), reads Supabase and
the Instagram API server-side, and triggers the GitHub Actions jobs on demand.

Pages:
- **Overview** — followers + weekly delta, engagement KPIs, interactive
  follower-growth chart, recent-posts grid with live likes/comments, top
  performers, latest AI analysis.
- **Controls** — run any job now; the meme job has a format picker
  (Auto / Video / Images) that maps to `meme.yml`'s `format` dispatch input.

## One-time setup (~15 min)

### 1. Google OAuth client
1. https://console.cloud.google.com → create/select a project.
2. **APIs & Services → OAuth consent screen** → External → add your email as a Test user.
3. **APIs & Services → Credentials → Create Credentials → OAuth client ID → Web application.**
4. Authorized redirect URIs — add both:
   - `http://localhost:3000/api/auth/callback/google` (local dev)
   - `https://meme-engine-dashboard.vercel.app/api/auth/callback/google`
5. Copy the **Client ID** and **Client secret**.

### 2. Deploy on Vercel
1. https://vercel.com → New Project → import this GitHub repo.
2. Set **Root Directory** to `dashboard-web`.
3. Add Environment Variables (see `.env.example`):
   - `AUTH_SECRET` — `openssl rand -base64 32`
   - `AUTH_GOOGLE_ID`, `AUTH_GOOGLE_SECRET` — from step 1
   - `SUPABASE_URL`, `SUPABASE_KEY` — same as the pipeline (service_role key)
   - `META_ACCESS_TOKEN`, `INSTAGRAM_USER_ID` — enables the recent-posts grid
     (optional; the page degrades gracefully without them)
   - `GH_PAT` (workflow scope) + `GH_REPO` (`owner/repo`) — enables Controls
   - `ALLOWED_EMAILS` — optional; defaults to the owner's email in `auth.ts`
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
- The Supabase **service_role** key and the Instagram token live only in server
  env vars — never sent to the browser (all reads run in server components /
  API routes).
- Sign-in is allowlist-only: `ALLOWED_EMAILS`, defaulting to the owner's email.
  Everyone else is rejected at the Google callback.
- The trigger API only dispatches allowlisted workflows and allowlisted input
  values.
