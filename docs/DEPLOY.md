# Deploy AFK to production (Render + afk.agency)

## What gets deployed

Single Python web service: FastAPI serves `/api/*` and the SPA (`/#offer`, `#login`, Try demo, etc.).

## 1. Push code

```powershell
cd C:\Users\INTEL\afk
git push origin feature/diagnostic-v3-phase1-honesty
```

Merge to `main` on GitHub when ready; point Render at `main` for production.

## 2. Create Render service

1. [render.com](https://render.com) → **New** → **Blueprint**
2. Connect repo `akhiwesh/afk`
3. Render reads `render.yaml` and creates `afk-platform`
4. First deploy takes ~3–5 minutes

### Env vars (set in Render dashboard if not from blueprint)

| Variable | Value |
|----------|--------|
| `PYTHONPATH` | `.` |
| `AFK_ENV` | `production` |
| `AFK_SECRET_KEY` | auto-generated |
| `AFK_CORS_ORIGINS` | `https://afk.agency,https://www.afk.agency` |
| `AFK_DEMO_MODE` | `true` (enables one-click demo on login/offer) |

Optional: `ANTHROPIC_API_KEY` or `GEMINI_API_KEY` for Analyst LLM mode.

## 3. Custom domain

1. Render → `afk-platform` → **Settings** → **Custom Domains**
2. Add `afk.agency` and `www.afk.agency`
3. At your registrar, replace the parking-page DNS with Render’s records:
   - **Root** `afk.agency` → A/ALIAS records Render provides, **or** ANAME if supported
   - **www** → CNAME to `afk-platform.onrender.com` (or Render’s target)
4. Wait for TLS (usually &lt;30 min)

Remove any redirect to `/lander` at the registrar — that was the old parking config.

## 4. Smoke test (before outreach)

```text
https://afk.agency/api/health          → {"status":"ok",...}
https://afk.agency/#offer                → offer page loads
https://afk.agency/#offer → Try demo     → lands on #diagnosis with sample audit
https://afk.agency/#offer → Apply        → inquiry POST succeeds
```

## 5. Known limits (free tier)

- **Cold start:** ~30–60s after sleep
- **SQLite:** `database.db` resets on redeploy unless you add a persistent disk or `DATABASE_URL` (Postgres). Fine for demos; use Postgres before multiple paying clients.
- **Secrets:** `AFK_SECRET_KEY` must stay stable across restarts or users get logged out

## 6. Local parity

```powershell
cd C:\Users\INTEL\afk
$env:PYTHONPATH='C:\Users\INTEL\afk'
.\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```