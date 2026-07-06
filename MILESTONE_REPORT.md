# MILESTONE REPORT — M1: Security & Correctness Hardening
**Date:** 2026-07-03 · **Status:** ✅ Complete · **Tests:** 10/10 passing · **App:** boots clean, all endpoints verified live

---

## Founder summary (read this part)

Before this milestone, AFK had a demo-grade auth system: the signing key for every login token was hardcoded in the source code (anyone with the code could forge admin sessions), users could register with a 1-character password, and a browser security misconfiguration would have broken logins the moment the frontend was hosted on a real domain. All of that is fixed. AFK's login, registration, and permission system is now built the way a real SaaS builds it, and there's a test suite that will catch regressions automatically.

**What you can now do:** register real users with enforced strong passwords, log in, and every business area (CRM, projects, automations, invoices, analytics, AI) is properly locked behind authentication — verified live, not assumed.

---

## What was built / changed

| Area | Before | After |
|---|---|---|
| JWT secret | Hardcoded string in source | Environment variable (`AFK_SECRET_KEY`); random per-boot key in dev; **refuses to start in production without one** |
| Password policy | None — "a" was a valid password | Min 8 chars, mixed case, at least one digit, enforced at API level |
| CORS | `*` origins + credentials (invalid & unsafe) | Explicit origin allowlist via `AFK_CORS_ORIGINS` |
| Registration | Two commits — crash mid-way orphaned an Organization row | Single atomic transaction with rollback |
| Unknown `/api/*` routes | Returned HTTP 200 with `null` body (bug) | Proper 404 with JSON error |
| Auth cookie | `secure=False` always | `secure=True` automatically in production |
| Startup events | Deprecated `@app.on_event` | Modern FastAPI `lifespan` |
| Datetimes | Deprecated `datetime.utcnow()` | Timezone-aware `datetime.now(timezone.utc)` |
| Config | Scattered constants in code | Central `settings.py`, fully env-driven |

## Files changed
- `backend/app/core/settings.py` — **new**: central env-driven configuration
- `backend/app/core/security.py` — rewritten: no hardcoded secrets, single token decode path
- `backend/app/api/auth.py` — password policy, atomic registration, env-aware cookies, modern Pydantic
- `backend/app/api/deps.py` — uses central decode path instead of importing raw secret
- `backend/app/main.py` — lifespan, explicit CORS, SPA 404 fix
- `backend/tests/test_api.py` — fixed broken in-memory-DB fixture (StaticPool); **+8 new regression tests**

## Bugs fixed
1. Test suite in-memory SQLite fixture created a fresh empty DB per connection (missing `StaticPool`) — the auth test could never pass
2. `/api/*` unknown routes returned `200 null` instead of `404`
3. Orphaned-Organization risk on failed registration
4. (Carried from last session: `create_all` import, missing `email-validator`, bcrypt/passlib pin)

## Verified live (fresh DB boot)
- Clean seed + startup ✅ · Landing 200 ✅ · Weak password → 422 ✅ · Register → login → `/me` round trip ✅ · Garbage token → 401 ✅ · Unknown API route → 404 ✅ · All 6 business endpoint groups: 200 with auth / 401 without ✅

## Remaining issues / technical debt
- `forgot-password` is a stub (returns success without sending email) — needs an email provider decision (**founder input required eventually**)
- Passlib emits deprecation warnings on Python 3.12+; long-term should migrate to `bcrypt` direct or `argon2` (not urgent, works fine pinned)
- No rate limiting on login (brute-force protection) — good candidate within a later milestone
- Frontend `landing.js` builds UI via giant template strings with inline styles — works, but hurts maintainability; candidate for M3 (frontend quality pass)
- No token refresh flow — 7-day tokens only

## Next milestone — M2: Data integrity & API robustness
Org-level data isolation audit (can org A read org B's clients? must verify), input validation on all business models, pagination on list endpoints, consistent error response shape, login rate limiting.

