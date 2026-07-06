# AFK — Founder Test Script (15 minutes)
You are testing whether AFK feels like a Revenue Intelligence product. Don't test like an engineer — test like a skeptical founder seeing it for the first time. Note anywhere you feel bored, confused, or unconvinced: those notes ARE the next milestone.

## Setup (2 min)
Replace `C:\AFK\afk-platform` with this zip's folder → terminal → `python run.py` → wait for "Application startup complete" → browser `localhost:8000` → Ctrl+Shift+R → login `admin@afk.agency` / `password123`.

## Test 1 — The diagnosis (2 min)
You land on Executive Diagnosis. Check: score 75/100 · primary constraint Pricing & Monetization · every finding has evidence chips citing actual answers · "Where confidence comes from" shows Questionnaire capped + Invoices/Leads MISSING · "Questions AFK still has" reads intelligent, not generic.
**Pass = you could screenshot this page and a founder friend would ask "how do I get mine?"**

## Test 2 — Evidence changes the diagnosis (4 min)
Evidence page → upload any CSV with invoice-ish columns (or make one in Excel: Invoice No, Date, Customer, Amount, Discount — 5 rows, give big discounts). Watch column detection explain itself → Confirm.
Back on Diagnosis: confidence % went UP · "Founder belief vs business reality" appears if your data contradicts the audit answers (big discounts will trigger it) · "What's working" shows computed drivers.
**Pass = the contradiction card makes you feel slightly caught out. That feeling is the product.**

## Test 3 — The living memory (3 min)
Revenue Audit → change 2–3 answers → Save & Diagnose → watch the analysis sequence → "We've built the first version of your Business Twin."
Diagnosis now shows "Since your last diagnosis: +N" with which dimensions moved.
Business Twin page → scroll down → **Business Memory**: stat cards + a color-badged timeline of everything you just did, newest first.
**Pass = it feels like AFK has been paying attention.**

## Test 4 — The Analyst (2 min)
Analyst page → ask "Why is revenue stuck?" and "Is my pricing actually fine?"
Check: structured 5-part answers · cites your actual numbers · honestly labeled "Deterministic mode" (no AI key configured) · if evidence contradicts your answers, it says so.

## Test 5 — The never-invent rule (2 min)
Logout → Create organization → new account → Diagnosis shows **"Not enough evidence"** with exactly what's missing, refuses to guess.
**Pass = the empty state feels principled, not broken.**

## Phone testing (optional, +15 min, needs a GitHub account)
The zip now includes `render.yaml`. Push the folder to a GitHub repo → render.com → New → Blueprint → pick the repo → deploy (free tier). You get `https://afk-xxxx.onrender.com` — open it on your phone, test everything above from bed. After first deploy, set the env var `AFK_CORS_ORIGINS` to that exact URL. Note: free tier sleeps after inactivity (first load takes ~40s) and the database resets on redeploys — fine for testing, not for real customers yet.

## What to send back
Three lists, however rough:
1. Moments you felt "this is real"
2. Moments you felt bored/confused/unconvinced
3. The first thing a Vintech distributor would object to
