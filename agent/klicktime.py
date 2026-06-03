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
# Locate config/token next to the actual program: the install folder when frozen
# (so the installer's settings and the saved login persist), else the source folder.
if getattr(sys, "frozen", False):
    HERE = os.path.dirname(sys.executable)
else:
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

    def forget(self):
        self.access = None
        self.refresh = None
        try:
            if os.path.exists(TOKEN_PATH):
                os.remove(TOKEN_PATH)
        except Exception:
            pass

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


# ---------------- Login window (first run) ----------------
def _logo_photo(tk, size=76):
    """A sized PhotoImage of the embedded KE logo, no ImageTk needed."""
    from PIL import Image
    im = Image.open(io.BytesIO(base64.b64decode(LOGO_B64))).convert("RGBA").resize((size, size), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, format="PNG")
    return tk.PhotoImage(data=base64.b64encode(buf.getvalue()))


def interactive_login(session):
    """A branded sign-in window. Returns True on success, False if cancelled."""
    import tkinter as tk
    result = {"ok": False}

    win = tk.Tk()
    win.title("KlickTime")
    win.configure(bg="#ffffff")
    win.resizable(False, False)
    W, H = 400, 540
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry(f"{W}x{H}+{(sw - W)//2}+{max(0,(sh - H)//3)}")

    # Dark branded header
    head = tk.Frame(win, bg="#14181b", height=196)
    head.pack(fill="x"); head.pack_propagate(False)
    try:
        photo = _logo_photo(tk, 76)
        lg = tk.Label(head, image=photo, bg="#14181b"); lg.image = photo
        lg.pack(pady=(34, 8))
    except Exception:
        tk.Label(head, text="K", bg="#14181b", fg="#1bbf9a",
                 font=("Segoe UI", 34, "bold")).pack(pady=(42, 4))
    tk.Label(head, text="KlickTime", bg="#14181b", fg="#ffffff",
             font=("Segoe UI Semibold", 18)).pack()
    tk.Label(head, text="Time tracking by Klickevents", bg="#14181b", fg="#8aa0a8",
             font=("Segoe UI", 9)).pack(pady=(2, 0))

    body = tk.Frame(win, bg="#ffffff")
    body.pack(fill="both", expand=True, padx=36, pady=(24, 8))
    tk.Label(body, text="Sign in to continue", bg="#ffffff", fg="#14181b",
             font=("Segoe UI Semibold", 13)).pack(anchor="w")

    def make_field(label, show=None):
        tk.Label(body, text=label, bg="#ffffff", fg="#5c6b73",
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(16, 4))
        e = tk.Entry(body, font=("Segoe UI", 11), relief="solid", bd=1,
                     highlightthickness=1, highlightcolor="#0e7c66",
                     highlightbackground="#d4dce0")
        if show:
            e.config(show=show)
        e.pack(fill="x", ipady=6)
        return e

    email = make_field("Work email")
    pwd = make_field("Password", show="\u2022")

    err = tk.Label(body, text="", bg="#ffffff", fg="#c0392b", font=("Segoe UI", 9),
                   wraplength=320, justify="left")
    err.pack(anchor="w", pady=(10, 0))

    def submit(*_):
        e, p = email.get().strip(), pwd.get()
        if not e or not p:
            err.config(text="Please enter your email and password.")
            return
        btn.config(state="disabled", text="Signing in\u2026"); win.update()
        try:
            session.login(e, p)
            result["ok"] = True
            win.destroy()
        except Exception as ex:
            msg = "Invalid email or password."
            try:
                if isinstance(ex, requests.exceptions.ConnectionError):
                    msg = "Can't reach the server. Check your connection."
            except Exception:
                pass
            err.config(text=msg)
            btn.config(state="normal", text="Sign in")

    btn = tk.Button(body, text="Sign in", command=submit, bg="#0e7c66", fg="#ffffff",
                    activebackground="#0b6353", activeforeground="#ffffff", relief="flat",
                    font=("Segoe UI Semibold", 11), cursor="hand2")
    btn.pack(fill="x", ipady=9, pady=(22, 0))

    host = session.base.replace("https://", "").replace("http://", "")
    tk.Label(win, text=f"Server: {host}", bg="#ffffff", fg="#9aa7ad",
             font=("Segoe UI", 8)).pack(side="bottom", pady=10)

    win.bind("<Return>", submit)
    email.focus_set()
    win.mainloop()
    return result["ok"]


def fmt(sec):
    sec = int(sec); h = sec // 3600; m = (sec % 3600) // 60; s = sec % 60
    return f"{h}:{m:02d}:{s:02d}"


def _branded_window(meeting_type, height=300):
    """Create a styled KlickTime window. Header shows the meeting type. Returns (win, body)."""
    import tkinter as tk
    win = tk.Tk()
    win.title("KlickTime")
    win.configure(bg="#ffffff")
    win.resizable(False, False)
    W, H = 440, height
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry(f"{W}x{H}+{(sw - W)//2}+{max(0,(sh - H)//3)}")
    try:
        ic = _logo_photo(tk, 32)
        win.iconphoto(True, ic)
        win._icon_ref = ic
    except Exception:
        pass

    head = tk.Frame(win, bg="#14181b", height=96)
    head.pack(fill="x"); head.pack_propagate(False)
    row = tk.Frame(head, bg="#14181b"); row.pack(expand=True, fill="both", padx=28)
    try:
        photo = _logo_photo(tk, 42)
        lg = tk.Label(row, image=photo, bg="#14181b"); lg.image = photo
        lg.pack(side="left", pady=26, padx=(0, 14))
    except Exception:
        pass
    txt = tk.Frame(row, bg="#14181b"); txt.pack(side="left", anchor="center")
    tk.Label(txt, text="KLICKTIME", bg="#14181b", fg="#7fd8c0",
             font=("Segoe UI", 8, "bold")).pack(anchor="w")
    tk.Label(txt, text=meeting_type, bg="#14181b", fg="#ffffff",
             font=("Segoe UI Semibold", 16)).pack(anchor="w")

    body = tk.Frame(win, bg="#ffffff")
    body.pack(fill="both", expand=True, padx=32, pady=(24, 26))
    return win, body


def _force_foreground_win(win):
    """On Windows, claim the foreground so a tray-launched window can take input."""
    try:
        import ctypes
        win.update_idletasks()
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        hwnd = win.winfo_id()
        parent = user32.GetParent(hwnd) or hwnd
        fg = user32.GetForegroundWindow()
        cur = kernel32.GetCurrentThreadId()
        tgt = user32.GetWindowThreadProcessId(fg, 0)
        user32.AttachThreadInput(cur, tgt, True)
        user32.BringWindowToTop(parent)
        user32.SetForegroundWindow(parent)
        user32.SetActiveWindow(parent)
        user32.SetFocus(parent)
        user32.AttachThreadInput(cur, tgt, False)
    except Exception:
        pass


def _focus_window(win, first_widget=None):
    """Force the window to the front and give it keyboard focus (fixes no-typing).

    Must run AFTER the event loop has started, so it is scheduled with after().
    """
    def grab():
        try:
            win.attributes("-topmost", True)
            win.lift()
            win.focus_force()
            _force_foreground_win(win)          # Windows: actually claim foreground
            if first_widget is not None:
                first_widget.focus_set()
            win.after(600, lambda: win.attributes("-topmost", False))
        except Exception:
            pass
    win.after(120, grab)


def _field_label(body, text):
    import tkinter as tk
    tk.Label(body, text=text, bg="#ffffff", fg="#5c6b73",
             font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(2, 6))


def _styled_entry(body):
    import tkinter as tk
    wrap = tk.Frame(body, bg="#e0ddd4", padx=1, pady=1)   # 1px border
    wrap.pack(fill="x")
    e = tk.Entry(wrap, font=("Segoe UI", 11), relief="flat", bd=0, bg="#ffffff")
    e.pack(fill="x", ipady=8, ipadx=8)
    return e


def _accent_button(body, text, command):
    import tkinter as tk
    return tk.Button(body, text=text, command=command, bg="#0e7c66", fg="#ffffff",
                     activebackground="#0b6353", activeforeground="#ffffff", relief="flat",
                     font=("Segoe UI Semibold", 11), cursor="hand2", bd=0)


def ask_text(title, prompt):
    """Branded popup to capture a meeting description. Returns trimmed text or ''."""
    try:
        import tkinter as tk
        result = {"val": ""}
        win, body = _branded_window("Internal meeting", height=300)
        _field_label(body, prompt)
        entry = _styled_entry(body)

        def ok(*_):
            result["val"] = entry.get().strip()
            win.destroy()

        btn = _accent_button(body, "Start meeting", ok)
        btn.pack(fill="x", ipady=11, side="bottom")
        win.bind("<Return>", ok)
        _focus_window(win, entry)
        win.mainloop()
        return result["val"]
    except Exception:
        return ""


def ask_client_meeting(clients):
    """Branded popup to pick a client and topic. Returns (client_dict, topic) or (None, '')."""
    try:
        import tkinter as tk
        from tkinter import ttk
        result = {"client": None, "topic": ""}
        win, body = _branded_window("Client meeting", height=400)

        style = ttk.Style(win)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("KT.TCombobox", fieldbackground="#ffffff", background="#ffffff",
                        bordercolor="#e0ddd4", arrowcolor="#14181b", padding=8, relief="flat")
        style.map("KT.TCombobox", fieldbackground=[("readonly", "#ffffff")])

        # Button pinned to the bottom first, so it is always visible.
        def ok(*_):
            sel = var.get()
            result["client"] = next((c for c in clients if c["name"] == sel), None)
            result["topic"] = topic.get().strip()
            win.destroy()

        btn = _accent_button(body, "Start meeting", ok)
        btn.pack(fill="x", ipady=11, side="bottom")

        _field_label(body, "Client")
        names = [c["name"] for c in clients]
        var = tk.StringVar(value=names[0] if names else "")
        cb = ttk.Combobox(body, textvariable=var, values=names, state="readonly",
                          style="KT.TCombobox", font=("Segoe UI", 11))
        cb.pack(fill="x", ipady=4)
        if names:
            cb.current(0)

        tk.Frame(body, bg="#ffffff", height=14).pack()
        _field_label(body, "Meeting topic")
        topic = _styled_entry(body)

        win.bind("<Return>", ok)
        _focus_window(win, topic)
        win.mainloop()
        return result["client"], result["topic"]
    except Exception:
        return None, ""


# ---------------- The app ----------------
class KlickTime:
    def __init__(self, cfg):
        self.s = Session(cfg["server_url"])
        self.mode = str(cfg.get("mode", "dedicated")).lower()   # "dedicated" or "shared"
        self.projects = []
        self.clients = []
        self.idle_limit = 5 * 60          # seconds; refreshed from server
        self.current = None               # index into self.projects, or None
        self.session_seconds = 0          # active seconds on current project (display)
        self.unsent_seconds = 0           # active seconds not yet sent
        self.stop_flag = threading.Event()
        self.icon = None
        self.img_color = None
        self.img_gray = None
        self._icon_is_color = None
        self.on_break = False
        self.break_resume_idx = None
        self.break_started_at = 0.0
        self.meeting = None      # None, or {"type","description","client_id","client_name","entry_id"}

    # --- setup ---
    def authenticate(self):
        if self.s.try_token():
            return True
        return interactive_login(self.s)

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
        try:
            self.clients = self.s.get("/api/clients/").get("results", [])
        except Exception:
            self.clients = []

    # --- timing ---
    def _tracking(self):
        return self.current is not None or self.meeting is not None

    def _current_label(self):
        if self.meeting:
            if self.meeting["type"] == "INTERNAL_MEETING":
                return "Internal meeting"
            return f"Client meeting · {self.meeting.get('client_name','')}"
        if self.current is not None:
            return self.projects[self.current]["name"]
        return ""

    def send(self, minutes, active):
        if minutes <= 0 and active:
            return
        exe, title = active_window()
        body = {"minutes": minutes, "active": active, "app": exe, "window_title": title}
        if self.meeting:
            body["activity_type"] = self.meeting["type"]
            body["description"] = self.meeting.get("description", "")
            if self.meeting.get("client_id"):
                body["client"] = self.meeting["client_id"]
            if self.meeting.get("entry_id"):
                body["entry_id"] = self.meeting["entry_id"]
        elif self.current is not None:
            body["activity_type"] = "WORK"
            body["project"] = self.projects[self.current]["id"]
        else:
            return
        try:
            resp = self.s.post(HEARTBEAT_PATH, body)
            if self.meeting and isinstance(resp, dict) and resp.get("entry_id"):
                self.meeting["entry_id"] = resp["entry_id"]   # keep adding to the same meeting
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
        self.on_break = False              # picking a project ends any break
        self.break_resume_idx = None
        self.meeting = None                # and ends any meeting
        if self.current == idx:
            return
        self.flush()                       # append previous project's pending time
        self.current = idx
        self.session_seconds = 0
        self.unsent_seconds = 0
        self._apply_icon(True)
        self._refresh_tray()

    def start_internal_meeting(self, description):
        self.on_break = False
        self.break_resume_idx = None
        self.flush()                       # bank whatever was running
        self.current = None
        self.meeting = {"type": "INTERNAL_MEETING", "description": description, "entry_id": None}
        self.session_seconds = 0
        self.unsent_seconds = 0
        self._apply_icon(True)
        self._refresh_tray()

    def _prompt_internal_meeting(self, *_):
        res = _run_dialog_subprocess("internal")
        if res and res.get("description"):
            self.start_internal_meeting(res["description"])

    def start_client_meeting(self, client, topic):
        self.on_break = False
        self.break_resume_idx = None
        self.flush()
        self.current = None
        self.meeting = {
            "type": "CLIENT_MEETING", "description": topic,
            "client_id": client["id"], "client_name": client.get("name", ""), "entry_id": None,
        }
        self.session_seconds = 0
        self.unsent_seconds = 0
        self._apply_icon(True)
        self._refresh_tray()

    def _prompt_client_meeting(self, *_):
        if not self.clients:
            return
        res = _run_dialog_subprocess("client", clients=self.clients)
        if res and res.get("client") and res.get("topic"):
            self.start_client_meeting(res["client"], res["topic"])

    def take_break(self, *_):
        """Pause tracking. Resumes the same project automatically on next activity."""
        if self.on_break or self.current is None:
            return
        self.flush()                       # bank the time worked so far
        self.break_resume_idx = self.current
        self.current = None
        self.on_break = True
        self.break_started_at = time.time()
        self.session_seconds = 0
        self.unsent_seconds = 0
        self._apply_icon(False)
        self._refresh_tray()

    def stop(self, *_):
        self.on_break = False
        self.break_resume_idx = None
        self.meeting = None
        self.flush()
        self.current = None
        self.session_seconds = 0
        self._apply_icon(False)
        self._refresh_tray()

    def worker(self):
        while not self.stop_flag.wait(1):
            # On break: stay paused until the employee touches keyboard/mouse again.
            if self.on_break:
                self._apply_icon(False)
                last_input = time.time() - idle_seconds()
                if self.break_resume_idx is not None and last_input > self.break_started_at + 1.0:
                    self.current = self.break_resume_idx     # resume same project
                    self.on_break = False
                    self.break_resume_idx = None
                    self.session_seconds = 0
                    self.unsent_seconds = 0
                    self._apply_icon(True)
                    self._refresh_tray()
                    continue
                self._set_title("KlickTime — on break (move mouse to resume)")
                continue
            active = self._tracking() and idle_seconds() < self.idle_limit
            self._apply_icon(active)              # color when working, gray otherwise
            if not self._tracking():
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
            self._set_title(f"KlickTime — {self._current_label()}  {fmt(self.session_seconds)}")

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

    def _make_select(self, idx):
        def handler(icon, item):
            self.select(idx)
        return handler

    def _make_checked(self, idx):
        def checker(item):
            return self.current == idx
        return checker

    def _menu(self):
        items = []
        for i, p in enumerate(self.projects):
            label = f"{p['name']} · {p.get('client_name','')}   [Ctrl+Alt+{i+1}]"
            items.append(pystray.MenuItem(
                label,
                self._make_select(i),
                checked=self._make_checked(i),
                radio=True,
            ))
        items.append(pystray.Menu.SEPARATOR)
        items.append(pystray.MenuItem(
            "Log internal meeting\u2026",
            (lambda icon, item: self._prompt_internal_meeting()),
        ))
        items.append(pystray.MenuItem(
            "Log client meeting\u2026",
            (lambda icon, item: self._prompt_client_meeting()),
            enabled=(lambda item: len(self.clients) > 0),
        ))
        items.append(pystray.MenuItem(
            "Break  [Ctrl+Alt+B]",
            (lambda icon, item: self.take_break()),
            enabled=(lambda item: self.current is not None and not self.on_break),
        ))
        items.append(pystray.MenuItem(
            "Stop tracking",
            (lambda icon, item: self.stop()),
            enabled=(lambda item: self._tracking() or self.on_break),
        ))
        if self.mode == "shared":
            items.append(pystray.MenuItem(
                "Sign out / switch user",
                (lambda icon, item: self._sign_out()),
            ))
        items.append(pystray.MenuItem("Quit", (lambda icon, item: self._quit())))
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

    def _sign_out(self, *_):
        """Shared mode: finalize current time, forget the user, return to login."""
        self.flush()
        self.current = None
        self.s.forget()
        self._signed_out = True      # tells run() to loop back to the login window
        self.stop_flag.set()
        if self.icon:
            self.icon.stop()

    def _bind_hotkeys(self):
        for i in range(len(self.projects)):
            try:
                keyboard.add_hotkey(f"ctrl+alt+{i+1}", lambda idx=i: self.select(idx))
            except Exception:
                pass
        try:
            keyboard.add_hotkey("ctrl+alt+b", lambda: self.take_break())
        except Exception:
            pass

    def run(self):
        while True:
            self._signed_out = False
            if not self.authenticate():
                return
            self.load_data()
            if not self.projects:
                import tkinter as tk
                from tkinter import messagebox
                r = tk.Tk(); r.withdraw()
                messagebox.showinfo("KlickTime", "No projects are assigned to you yet. Ask your manager to allocate you to a project.")
                r.destroy()
                # In shared mode, let the next person try; in dedicated, exit.
                if self.mode == "shared":
                    self.s.forget()
                    continue
                return

            # fresh per-session state
            self.current = None
            self.session_seconds = 0
            self.unsent_seconds = 0
            self.on_break = False
            self.break_resume_idx = None
            self.meeting = None
            self.stop_flag = threading.Event()
            self._icon_is_color = None

            self._build_icons()
            threading.Thread(target=self.worker, daemon=True).start()
            self._bind_hotkeys()
            self.icon = pystray.Icon("KlickTime", self.img_gray, "KlickTime — not tracking", menu=self._menu())
            self._icon_is_color = False
            self.icon.run()

            # tray has stopped: either a real quit, or a sign-out (loop back to login)
            try:
                keyboard.unhook_all()
            except Exception:
                pass
            if not self._signed_out:
                return


def _run_dialog_subprocess(kind, clients=None):
    """Launch the meeting dialog as a SEPARATE process (a real foreground window),
    so the text field, dropdown, and buttons all work. Returns a dict or None."""
    import subprocess, tempfile, json as _json
    clients_path = out_path = None
    try:
        fd, out_path = tempfile.mkstemp(suffix=".json"); os.close(fd)
        cmd = [sys.executable] if getattr(sys, "frozen", False) \
            else [sys.executable, os.path.abspath(__file__)]
        cmd += ["--dialog", kind, "--out", out_path]
        if clients is not None:
            fd, clients_path = tempfile.mkstemp(suffix=".json"); os.close(fd)
            with open(clients_path, "w", encoding="utf-8") as f:
                _json.dump(clients, f)
            cmd += ["--clients", clients_path]
        flags = 0x08000000 if IS_WINDOWS else 0   # CREATE_NO_WINDOW
        subprocess.run(cmd, timeout=3600, creationflags=flags)
        with open(out_path, "r", encoding="utf-8") as f:
            return _json.load(f)
    except Exception:
        return None
    finally:
        for p in (clients_path, out_path):
            if p:
                try: os.remove(p)
                except Exception: pass


def _dialog_main():
    """Runs in the separate process: shows one dialog, writes the result, exits."""
    import json as _json
    a = sys.argv
    kind = clients_path = out_path = None
    for i, x in enumerate(a):
        if x == "--dialog" and i + 1 < len(a): kind = a[i + 1]
        elif x == "--clients" and i + 1 < len(a): clients_path = a[i + 1]
        elif x == "--out" and i + 1 < len(a): out_path = a[i + 1]
    res = {}
    if kind == "internal":
        res = {"description": ask_text("Internal meeting", "What is the meeting about?")}
    elif kind == "client":
        clients = []
        try:
            with open(clients_path, "r", encoding="utf-8") as f:
                clients = _json.load(f)
        except Exception:
            clients = []
        client, topic = ask_client_meeting(clients)
        res = {"client": client, "topic": topic}
    if out_path:
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                _json.dump(res, f)
        except Exception:
            pass


_INSTANCE_MUTEX = None


def _acquire_single_instance():
    """Return True if we are the only KlickTime tray instance; False if one already runs."""
    global _INSTANCE_MUTEX
    if not IS_WINDOWS:
        return True
    try:
        _INSTANCE_MUTEX = ctypes.windll.kernel32.CreateMutexW(None, False, "Global\\KlickTime_Tray")
        if ctypes.windll.kernel32.GetLastError() == 183:   # ERROR_ALREADY_EXISTS
            return False
    except Exception:
        pass
    return True


def main():
    if not _acquire_single_instance():
        return                      # another KlickTime tray is already running
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
    if "--dialog" in sys.argv:
        _dialog_main()        # separate-process dialog mode
    else:
        main()
