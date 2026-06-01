# TimeTrack Desktop Agents (Windows)

Two ways for employees to track time without the browser:

## KlickTime (recommended) — system-tray app with hotkeys
`klicktime.py` → builds into **KlickTime.exe**. Lives in the system tray, shows
the employee's assigned projects with hotkeys (Ctrl+Alt+1..9). Click or press a
project to start; switch projects in one tap; auto-pauses after the firm's idle
timeout (set by the admin). Sends active minutes to the server, which adds them
to that day's hours — same data as the web app.

**Build KlickTime.exe (on a Windows PC with Python installed):**
1. Open a terminal in this `agent` folder.
2. Double-click `build_KlickTime.bat` (or run it).
3. The result is `dist\KlickTime.exe`.
4. Put `KlickTime.exe` and a `config.json` (copy `config.example.json`, set your
   server URL) together on each employee PC. Double-click to run.

First run asks for the employee's login once (stores only a token after).

## timetrack_agent.py — simple console version
A no-frills console tracker (same server, no tray/hotkeys). Useful for testing.

## Privacy
Both send app/window titles + active minutes only — no keystrokes, screenshots,
or passwords. They announce themselves and are not hidden. Inform employees and
follow local consent rules. Idle timeout is configured by the admin per firm.
