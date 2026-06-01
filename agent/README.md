# TimeTrack Desktop Agent (Windows)

A transparent, employer-deployed time tracker. While running, it detects active
vs idle time and the title of the focused window, and reports active minutes to
your TimeTrack server for the project the employee selects.

**It does NOT record keystrokes, passwords, or screenshots.** It prints what it
is doing and is not hidden. Employees must be informed it is running, and you are
responsible for following local consent/monitoring laws.

## Run (on the employee's PC)
1. Install Python 3 and the requests library: `pip install requests`
2. Copy `config.example.json` to `config.json` and set `server_url` to your
   TimeTrack backend (e.g. your VPS address).
3. Run: `python timetrack_agent.py`
4. Sign in once (only a refresh token is stored afterwards — not the password),
   pick the current project, and leave it running. Type a number to switch
   projects, or `q` to quit.

## What gets sent each interval
`project, minutes, active (true/false), app (exe name), window_title`

## Notes & limits (first version)
- Windows only for activity detection (it will run elsewhere but report active).
- Console app for now; packaging as a tray app / auto-start service is a next step.
- Idle threshold and interval are set in config.json.
