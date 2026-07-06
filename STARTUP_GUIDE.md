# AFK — How to Start the App (No Engineering Knowledge Needed)

**Read this once, top to bottom. Total time: ~5 minutes.**

The one rule that prevents every sync problem we just had:
**Delete your old AFK folder completely and use only the new one from `afk-platform-m1-verified.zip`. Never mix old and new files.**

---

## 1. Open the project

1. Download `afk-platform-m1-verified.zip` from this chat.
2. Unzip it. You'll get a folder called `afk-platform`.
3. Move it somewhere easy, e.g. your Desktop.
4. Open a terminal **inside that folder**:
   - **Windows:** open the `afk-platform` folder in File Explorer → click the address bar → type `cmd` → press Enter.
   - **Mac:** right-click the `afk-platform` folder → Services → "New Terminal at Folder". (Or open Terminal and type `cd ` (with a space), drag the folder into the window, press Enter.)

You'll know you're in the right place if typing `dir` (Windows) or `ls` (Mac) shows `run.py`, `backend`, and `frontend`.

## 2, 3 & 4. Install everything and start AFK — one command

You don't need to create a virtual environment or install anything by hand. The project has a launcher that does all of it:

```
python run.py
```

(If that says "python is not recognized", try `python3 run.py` on Mac, or `py run.py` on Windows.)

The **first run takes 1–2 minutes** — it's building a private Python environment and downloading dependencies. Every run after that takes ~5 seconds.

> If you prefer doing it manually, the equivalent steps are: `python -m venv venv`, then activate it (`venv\Scripts\activate` on Windows / `source venv/bin/activate` on Mac), then `pip install -r backend/requirements.txt`, then `python -m uvicorn backend.app.main:app --reload --port 8000`. But `python run.py` does all four for you.

## 5. How to know it started successfully

Watch the terminal. Success looks exactly like this:

```
[*] Seeding database with premium demo data...
[+] Seeding database completed successfully.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

The line **"Application startup complete"** is your green light. The terminal will then sit there doing nothing — that's normal. It's the engine running. Don't close it.

## 6. Open AFK

In your browser, go to: **http://127.0.0.1:8000**

You'll see the AFK landing page (dark theme, "Scale Your Business At The Speed of AI").

## 7. Login credentials (pre-loaded demo accounts)

| Role | Email | Password |
|---|---|---|
| Admin (use this one) | `admin@afk.agency` | `password123` |
| Team member | `team@afk.agency` | `password123` |
| Client | `client@acme.com` | `password123` |

You can also register a brand-new account. New passwords must be **8+ characters with an uppercase letter, a lowercase letter, and a number** (e.g. `MyLaunch2026`).

## 8. How to stop the server

Click on the terminal window and press **Ctrl + C** (that's Ctrl on Mac too, not Cmd). Wait a second, and it prints "Server stopped". Closing the terminal window also works.

## 9. Common errors and fixes

| What you see | What it means | Fix |
|---|---|---|
| `python is not recognized` | Python isn't installed or not on PATH | Install from python.org — on Windows, **tick "Add Python to PATH"** during install. Then reopen the terminal. |
| `Address already in use` / `port 8000` | An old AFK is still running | You already have it running in another terminal — just use the browser. Or restart your computer, then `python run.py` again. |
| `No module named ...` | Dependencies half-installed | Delete the `venv` folder inside `afk-platform`, then run `python run.py` again — it rebuilds everything. |
| `password cannot be longer than 72 bytes` | **You're running the OLD code.** | You mixed old files with new. Delete the whole folder, re-unzip `afk-platform-m1-verified.zip`, start over. |
| `cannot import name 'create_all'` | Same — old code. | Same fix: delete folder, re-unzip the verified zip. |
| Page loads but looks broken / login fails weirdly | Stale database from an old version | Stop the server, delete the file `database.db` inside `afk-platform`, start again. It rebuilds with fresh demo data. |
| Anything else | — | Copy the last ~20 lines from the terminal and paste them to me. |

## One more thing (important, quick)

Every time you log in, the app checks passwords against fresh security keys. In this dev setup, **restarting the server logs everyone out** — that's intentional and fine for now. Just log in again.
