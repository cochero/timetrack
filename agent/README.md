# TimeTrack Desktop Agents (Windows)

## KlickTime — system-tray work timer
`klicktime.py` builds into **KlickTime.exe**: a tray app showing each employee's
assigned projects with hotkeys (Ctrl+Alt+1..9). Click or press a project to
start; switch in one tap; the KE logo is colour while tracking, grey when idle
or stopped. Active minutes go to the server and into that day's hours.

Modes (set in config.json or chosen during install):
- **dedicated** — one employee per PC; signs in once and stays signed in.
- **shared** — multiple employees per PC; a "Sign out / switch user" option in
  the tray lets the next person sign in at shift change.

### A. Build KlickTime.exe (on a Windows PC with Python)
1. Open a terminal in this `agent` folder.
2. Run `build_KlickTime.bat`.
3. Result: `dist\KlickTime.exe` (with the KE icon).

### B. Build the installer KlickTimeSetup.exe (with Inno Setup)
1. Install **Inno Setup** (free) from jrsoftware.org.
2. Make sure step A is done (so `dist\KlickTime.exe` exists).
3. Open `KlickTime.iss` in Inno Setup and click **Build > Compile**
   (or run `ISCC.exe KlickTime.iss` from a terminal).
4. Result: **KlickTimeSetup.exe** in this folder.

The installer:
- installs to the user's folder (no admin rights needed),
- offers "start automatically when I sign in to Windows" (auto-start),
- offers a "shared by multiple employees (shift mode)" checkbox that writes the
  correct mode into config.json,
- creates Start Menu (and optional desktop) shortcuts,
- includes an uninstaller.

### C. Distribute
Give employees **KlickTimeSetup.exe**. They run it, accept the options, and
KlickTime installs and starts. On first launch they sign in once.

## Privacy
KlickTime sends app/window titles and active minutes only — no keystrokes,
screenshots, or passwords. It is visible (tray icon) and announces itself.
Inform employees and follow local consent rules.

## timetrack_agent.py
A simple console tracker (no tray/hotkeys) — handy for testing the server.
