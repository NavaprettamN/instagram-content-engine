# AGENTS.md — durable facts for agents working in this repo

- Architecture, pipeline, and env-var docs live in CLAUDE.md; operating guide
  in FLOW.md; roadmap in tasks.md (MANDATORY to update after every work session).
- **Vercel CLI must run from `dashboard-web/`** — that's the linked directory
  (`.vercel/project.json`). From the repo root, env/deploy commands fail with
  "not linked". Project: meme-engine-dashboard, team navaprettamns-projects,
  rootDirectory=dashboard-web, git auto-deploy on push to main.
- The local `gh` CLI token has repo+workflow scopes and is used as the
  dashboard's GH_PAT env var on Vercel (workflow_dispatch triggers).
- Google OAuth for the dashboard lives in Google Cloud project **finance-app**
  → Google Auth Platform → Clients → "Web client 1" (id …bceqan). Publishing
  status "In production", External. The console UI has no "External" wording
  anymore — it's under Audience.
- Reddit access (2026): unauth JSON 403s everywhere; the Atom RSS feed and
  v.redd.it HLS/DASH playlists work (details in CLAUDE.md "Reddit access").
- Local ffmpeg (homebrew) lacks the drawtext filter — burn text via PIL
  overlay PNG + overlay filter instead (meme_agent does this).
- v.redd.it video memes are frequently SILENT (no audio stream); `-map 0:a?`
  used to ship them soundless. `build_video` now detects this via
  `MemeAgent.has_audio()` and adds a CC music bed (`add_music_bed`) so a video
  reel never posts silent. ffmpeg calls go through `_run_ffmpeg` (300s timeout).
- Background Bash tasks may start in a different cwd than the last foreground
  `cd`; use absolute paths in `run_in_background` commands.
