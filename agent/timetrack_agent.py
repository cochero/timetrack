"""
TimeTrack desktop agent (Windows).

A transparent, employer-deployed time tracker. While running it:
  - detects whether you are active (keyboard/mouse) or idle,
  - reads the title of the window you're working in,
  - sends that, plus active minutes, to YOUR firm's TimeTrack server,
  - which adds the active minutes to the project you've selected.

It does NOT capture keystrokes, passwords, or screenshots. It prints what it
is doing so it is never hidden. Employees must be told it is running.

Run:  python timetrack_agent.py
Config lives in config.json (copy config.example.json). On first run it asks
for your login once and stores only a refresh token afterwards.
"""
import ctypes
import json
import os
import platform
import sys
import threading
import time
from getpass import getpass

try:
    import requests
except ImportError:
    print("This agent needs the 'requests' library. Install it with:  pip install requests")
    sys.exit(1)

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "config.json")
TOKEN_PATH = os.path.join(HERE, "token.json")
IS_WINDOWS = platform.system() == "Windows"


# ---------- Activity detection (Windows) ----------
def idle_seconds():
    if not IS_WINDOWS:
        return 0.0
    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
    info = LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(LASTINPUTINFO)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info))
    millis = ctypes.windll.kernel32.GetTickCount() - info.dwTime
    return millis / 1000.0


def active_window():
    """Return (app_exe, window_title). Best effort; titles only, no contents."""
    if not IS_WINDOWS:
        return ("(non-Windows build)", "(active-window detection is Windows only)")
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    hwnd = user32.GetForegroundWindow()
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    title = buf.value or ""
    exe = ""
    pid = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if handle:
        size = ctypes.c_ulong(260)
        name_buf = ctypes.create_unicode_buffer(260)
        if kernel32.QueryFullProcessImageNameW(handle, 0, name_buf, ctypes.byref(size)):
            exe = name_buf.value.split("\\")[-1]
        kernel32.CloseHandle(handle)
    return (exe, title)


# ---------- Server session ----------
class Session:
    def __init__(self, base):
        self.base = base.rstrip("/")
        self.access = None
        self.refresh = None

    def _save_refresh(self):
        with open(TOKEN_PATH, "w") as f:
            json.dump({"refresh": self.refresh}, f)

    def login_interactive(self):
        print("\nSign in to TimeTrack (asked only once).")
        email = input("  Email: ").strip()
        password = getpass("  Password: ")
        r = requests.post(f"{self.base}/api/auth/login/", json={"email": email, "password": password}, timeout=20)
        r.raise_for_status()
        data = r.json()
        self.access, self.refresh = data["access"], data["refresh"]
        self._save_refresh()

    def try_stored_login(self):
        if not os.path.exists(TOKEN_PATH):
            return False
        try:
            self.refresh = json.load(open(TOKEN_PATH)).get("refresh")
            return self._refresh_access()
        except Exception:
            return False

    def _refresh_access(self):
        if not self.refresh:
            return False
        r = requests.post(f"{self.base}/api/auth/token/refresh/", json={"refresh": self.refresh}, timeout=20)
        if r.status_code != 200:
            return False
        self.access = r.json()["access"]
        return True

    def _headers(self):
        return {"Authorization": f"Bearer {self.access}"}

    def get(self, path):
        r = requests.get(f"{self.base}{path}", headers=self._headers(), timeout=20)
        if r.status_code == 401 and self._refresh_access():
            r = requests.get(f"{self.base}{path}", headers=self._headers(), timeout=20)
        r.raise_for_status()
        return r.json()

    def post(self, path, body):
        r = requests.post(f"{self.base}{path}", json=body, headers=self._headers(), timeout=20)
        if r.status_code == 401 and self._refresh_access():
            r = requests.post(f"{self.base}{path}", json=body, headers=self._headers(), timeout=20)
        r.raise_for_status()
        return r.json()


# ---------- Agent ----------
class Agent:
    def __init__(self, cfg):
        self.cfg = cfg
        self.session = Session(cfg["server_url"])
        self.interval = int(cfg.get("interval_seconds", 60))
        self.idle_limit = int(cfg.get("idle_seconds", 300))
        self.current_project = None
        self.projects = []
        self.stop = threading.Event()

    def setup(self):
        if not self.session.try_stored_login():
            self.session.login_interactive()
        self.projects = self.session.get("/api/projects/").get("results", [])
        if not self.projects:
            print("No projects found for your account. Ask your manager to set up a project first.")
            sys.exit(0)

    def choose_project(self):
        print("\nYour projects:")
        for i, p in enumerate(self.projects, 1):
            print(f"  {i}. {p['name']} — {p.get('client_name', '')}")
        while True:
            choice = input("Pick the project number you're working on now: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(self.projects):
                self.current_project = self.projects[int(choice) - 1]
                print(f"  → Tracking '{self.current_project['name']}'. (type a number to switch, 'q' to quit)\n")
                return

    def sample_loop(self):
        minutes_per = max(1, round(self.interval / 60))
        while not self.stop.wait(self.interval):
            idle = idle_seconds()
            active = idle < self.idle_limit
            exe, title = active_window()
            proj = self.current_project
            try:
                res = self.session.post("/api/agent/heartbeat/", {
                    "project": proj["id"] if proj else None,
                    "minutes": minutes_per,
                    "active": active,
                    "app": exe,
                    "window_title": title,
                })
                state = f"active · +{res.get('logged_minutes', 0)}m" if active else "idle · nothing logged"
                print(f"  [{time.strftime('%H:%M')}] {state} | {exe} — {title[:50]}")
            except Exception as e:
                print(f"  [warn] could not reach server: {e}")

    def command_loop(self):
        while not self.stop.is_set():
            cmd = input().strip().lower()
            if cmd == "q":
                self.stop.set()
                print("Stopping agent. Goodbye.")
                break
            if cmd.isdigit() and 1 <= int(cmd) <= len(self.projects):
                self.current_project = self.projects[int(cmd) - 1]
                print(f"  → Switched to '{self.current_project['name']}'.")

    def run(self):
        self.setup()
        self.choose_project()
        if not IS_WINDOWS:
            print("NOTE: full activity detection only works on Windows; this run will report as active.")
        t = threading.Thread(target=self.sample_loop, daemon=True)
        t.start()
        self.command_loop()


def main():
    if not os.path.exists(CONFIG_PATH):
        print(f"Missing config.json. Copy config.example.json to config.json and edit it.")
        sys.exit(1)
    cfg = json.load(open(CONFIG_PATH))
    print("TimeTrack agent — this records your active app/window titles and time, and reports to your firm's server.")
    Agent(cfg).run()


if __name__ == "__main__":
    main()
