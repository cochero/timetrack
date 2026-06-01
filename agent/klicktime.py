"""
KlickTime — system-tray work timer for TimeTrack (Windows).

What it does:
  - Lives in the Windows system tray.
  - Shows the employee's assigned projects, each with a hotkey (Ctrl+Alt+1..9).
  - Click a project (or press its hotkey) to start timing it.
  - Click/press a DIFFERENT project to switch: the time already worked is sent
    to the server continuously, and counting moves to the new project.
  - Auto-pauses after the firm's idle timeout (set by the admin, fetched live).
  - Sends active minutes to YOUR TimeTrack server, which adds them to that day's
    hours for the project (same data as the web app — no double entry).

It records app/window titles + active minutes only. No keystrokes, no
screenshots, no passwords. Sign in once; only a refresh token is stored.

First run asks for login in a small window, then it just lives in the tray.
Build into KlickTime.exe with build_KlickTime.bat (PyInstaller).
"""
import base64
import ctypes
import io
import json
import os
import platform
import sys
import threading
import time

import requests

try:
    import pystray
    from PIL import Image, ImageDraw, ImageOps
    import keyboard
    HAVE_GUI = True
except Exception:
    HAVE_GUI = False  # lets the file import for syntax/CI checks on non-Windows

# Klickevents "KE" logo, embedded so KlickTime.exe is fully self-contained.
LOGO_B64 = "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"

IS_WINDOWS = platform.system() == "Windows"
HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "config.json")
TOKEN_PATH = os.path.join(HERE, "klicktime_token.json")
HEARTBEAT_PATH = "/api/agent/heartbeat/"


# ---------------- Windows activity detection ----------------
def idle_seconds():
    if not IS_WINDOWS:
        return 0.0
    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
    info = LASTINPUTINFO(); info.cbSize = ctypes.sizeof(LASTINPUTINFO)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info))
    return (ctypes.windll.kernel32.GetTickCount() - info.dwTime) / 1000.0


def active_window():
    if not IS_WINDOWS:
        return ("", "")
    user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
    hwnd = user32.GetForegroundWindow()
    n = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(hwnd, buf, n + 1)
    title, exe = buf.value or "", ""
    pid = ctypes.c_ulong(); user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    h = kernel32.OpenProcess(0x1000, False, pid.value)
    if h:
        size = ctypes.c_ulong(260); nb = ctypes.create_unicode_buffer(260)
        if kernel32.QueryFullProcessImageNameW(h, 0, nb, ctypes.byref(size)):
            exe = nb.value.split("\\")[-1]
        kernel32.CloseHandle(h)
    return (exe, title)


# ---------------- Server session ----------------
class Session:
    def __init__(self, base):
        self.base = base.rstrip("/"); self.access = None; self.refresh = None

    def _save(self):
        with open(TOKEN_PATH, "w") as f:
            json.dump({"refresh": self.refresh}, f)

    def login(self, email, password):
        r = requests.post(f"{self.base}/api/auth/login/", json={"email": email, "password": password}, timeout=20)
        r.raise_for_status()
        d = r.json(); self.access, self.refresh = d["access"], d["refresh"]; self._save()

    def try_token(self):
        if not os.path.exists(TOKEN_PATH):
            return False
        try:
            self.refresh = json.load(open(TOKEN_PATH)).get("refresh")
            return self._refresh()
        except Exception:
            return False

    def _refresh(self):
        if not self.refresh:
            return False
        r = requests.post(f"{self.base}/api/auth/token/refresh/", json={"refresh": self.refresh}, timeout=20)
        if r.status_code != 200:
            return False
        self.access = r.json()["access"]; return True

    def _h(self):
        return {"Authorization": f"Bearer {self.access}"}

    def get(self, path):
        r = requests.get(f"{self.base}{path}", headers=self._h(), timeout=20)
        if r.status_code == 401 and self._refresh():
            r = requests.get(f"{self.base}{path}", headers=self._h(), timeout=20)
        r.raise_for_status(); return r.json()

    def post(self, path, body):
        r = requests.post(f"{self.base}{path}", json=body, headers=self._h(), timeout=20)
        if r.status_code == 401 and self._refresh():
            r = requests.post(f"{self.base}{path}", json=body, headers=self._h(), timeout=20)
        r.raise_for_status(); return r.json()


# ---------------- Login dialog (first run) ----------------
def ask_login():
    import tkinter as tk
    from tkinter import simpledialog
    root = tk.Tk(); root.withdraw()
    email = simpledialog.askstring("KlickTime", "Your work email:")
    pwd = simpledialog.askstring("KlickTime", "Your password:", show="*")
    root.destroy()
    return email, pwd


def fmt(sec):
    sec = int(sec); h = sec // 3600; m = (sec % 3600) // 60; s = sec % 60
    return f"{h}:{m:02d}:{s:02d}"


# ---------------- The app ----------------
class KlickTime:
    def __init__(self, cfg):
        self.s = Session(cfg["server_url"])
        self.projects = []
        self.idle_limit = 5 * 60          # seconds; refreshed from server
        self.current = None               # index into self.projects, or None
        self.session_seconds = 0          # active seconds on current project (display)
        self.unsent_seconds = 0           # active seconds not yet sent
        self.stop_flag = threading.Event()
        self.icon = None
        self.img_color = None
        self.img_gray = None
        self._icon_is_color = None

    # --- setup ---
    def authenticate(self):
        if self.s.try_token():
            return True
        email, pwd = ask_login()
        if not email or not pwd:
            return False
        self.s.login(email, pwd)
        return True

    def load_data(self):
        org = self.s.get("/api/org/")
        self.idle_limit = max(1, int(org.get("idle_timeout_minutes", 5))) * 60
        all_projects = self.s.get("/api/projects/").get("results", [])
        by_id = {p["id"]: p for p in all_projects}
        allocs = self.s.get("/api/allocations/").get("results", [])
        mine, seen = [], set()
        for a in allocs:
            p = by_id.get(a.get("project"))
            if p and p.get("status") == "ACTIVE" and p["id"] not in seen:
                seen.add(p["id"]); mine.append(p)
        self.projects = (mine or [p for p in all_projects if p.get("status") == "ACTIVE"])[:9]

    # --- timing ---
    def send(self, minutes, active):
        if minutes <= 0 and active:
            return
        proj = self.projects[self.current] if self.current is not None else None
        exe, title = active_window()
        try:
            self.s.post(HEARTBEAT_PATH, {
                "project": proj["id"] if proj else None,
                "minutes": minutes, "active": active, "app": exe, "window_title": title,
            })
        except Exception:
            pass  # offline tick; try again next minute

    def flush(self):
        if self.unsent_seconds > 0:
            m = round(self.unsent_seconds / 60)
            if m > 0:
                self.send(m, True)
            self.unsent_seconds = 0

    def select(self, idx):
        if idx >= len(self.projects):
            return
        if self.current == idx:
            return
        self.flush()                       # append previous project's pending time
        self.current = idx
        self.session_seconds = 0
        self.unsent_seconds = 0
        self._apply_icon(True)
        self._refresh_tray()

    def stop(self, *_):
        self.flush()
        self.current = None
        self.session_seconds = 0
        self._apply_icon(False)
        self._refresh_tray()

    def worker(self):
        while not self.stop_flag.wait(1):
            active = self.current is not None and idle_seconds() < self.idle_limit
            self._apply_icon(active)              # color when working, gray otherwise
            if self.current is None:
                self._set_title("KlickTime — not tracking")
                continue
            if not active:
                self._set_title("KlickTime — paused (idle)")
                continue
            self.session_seconds += 1
            self.unsent_seconds += 1
            if self.unsent_seconds >= 60:
                self.send(self.unsent_seconds // 60, True)
                self.unsent_seconds = self.unsent_seconds % 60
            p = self.projects[self.current]
            self._set_title(f"KlickTime — {p['name']}  {fmt(self.session_seconds)}")

    # --- tray ---
    def _set_title(self, text):
        if self.icon:
            self.icon.title = text[:127]

    def _refresh_tray(self):
        if self.icon:
            self.icon.menu = self._menu()
            self.icon.update_menu()
            if self.current is None:
                self._set_title("KlickTime — not tracking")

    def _menu(self):
        items = []
        for i, p in enumerate(self.projects):
            label = f"{p['name']} · {p.get('client_name','')}   [Ctrl+Alt+{i+1}]"
            items.append(pystray.MenuItem(
                label,
                (lambda _icon, _item, idx=i: self.select(idx)),
                checked=(lambda _item, idx=i: self.current == idx),
                radio=True,
            ))
        items.append(pystray.Menu.SEPARATOR)
        items.append(pystray.MenuItem("Stop tracking", self.stop, enabled=lambda _i: self.current is not None))
        items.append(pystray.MenuItem("Quit", self._quit))
        return pystray.Menu(*items)

    def _build_icons(self):
        raw = base64.b64decode(LOGO_B64)
        base = Image.open(io.BytesIO(raw)).convert("RGBA").resize((64, 64), Image.LANCZOS)
        self.img_color = base
        gray = ImageOps.grayscale(base.convert("RGB")).convert("RGBA")
        gray.putalpha(base.split()[-1])     # keep the logo's transparency
        self.img_gray = gray

    def _apply_icon(self, active):
        if not self.icon:
            return
        if active and self._icon_is_color is not True:
            self.icon.icon = self.img_color
            self._icon_is_color = True
        elif not active and self._icon_is_color is not False:
            self.icon.icon = self.img_gray
            self._icon_is_color = False

    def _quit(self, *_):
        self.flush()
        self.stop_flag.set()
        if self.icon:
            self.icon.stop()

    def _bind_hotkeys(self):
        for i in range(len(self.projects)):
            try:
                keyboard.add_hotkey(f"ctrl+alt+{i+1}", lambda idx=i: self.select(idx))
            except Exception:
                pass

    def run(self):
        if not self.authenticate():
            return
        self.load_data()
        if not self.projects:
            import tkinter as tk
            from tkinter import messagebox
            r = tk.Tk(); r.withdraw()
            messagebox.showinfo("KlickTime", "No projects are assigned to you yet. Ask your manager to allocate you to a project.")
            r.destroy(); return
        self._build_icons()
        threading.Thread(target=self.worker, daemon=True).start()
        self._bind_hotkeys()
        self.icon = pystray.Icon("KlickTime", self.img_gray, "KlickTime — not tracking", menu=self._menu())
        self._icon_is_color = False
        self.icon.run()


def main():
    cfg = {"server_url": "https://tt.klickevents.in"}
    if os.path.exists(CONFIG_PATH):
        try:
            cfg.update(json.load(open(CONFIG_PATH)))
        except Exception:
            pass
    if not HAVE_GUI:
        print("KlickTime needs pystray, Pillow and keyboard. Install: pip install -r requirements.txt")
        return
    KlickTime(cfg).run()


if __name__ == "__main__":
    main()
