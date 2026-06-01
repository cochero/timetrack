import { useEffect, useMemo, useRef, useState } from "react";
import api from "../api/client";
import { useCollection } from "../api/hooks";
import { useAuth } from "../auth/AuthContext";

function fmt(totalSec) {
  const s = Math.max(0, Math.floor(totalSec));
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;
  const pad = (n) => String(n).padStart(2, "0");
  return `${h}:${pad(m)}:${pad(sec)}`;
}

export default function TimerBar() {
  const { user } = useAuth();
  const { items: projects } = useCollection("/projects/");
  const { items: allocations } = useCollection("/allocations/");
  const [active, setActive] = useState(null);
  const [elapsed, setElapsed] = useState(0);
  const [busy, setBusy] = useState(false);
  const [flash, setFlash] = useState("");
  const tick = useRef(null);

  useEffect(() => {
    api.get("/timer/active/").then((r) => setActive(r.data.active)).catch(() => {});
  }, []);

  useEffect(() => {
    clearInterval(tick.current);
    if (active) {
      const start = new Date(active.started_at).getTime();
      const upd = () => setElapsed((Date.now() - start) / 1000);
      upd(); tick.current = setInterval(upd, 1000);
    }
    return () => clearInterval(tick.current);
  }, [active]);

  const projectsById = useMemo(() => Object.fromEntries(projects.map((p) => [p.id, p])), [projects]);
  const activeProjects = projects.filter((p) => p.status === "ACTIVE");

  // The employee's own projects (from their active allocations); fall back to all active.
  const myProjects = useMemo(() => {
    const mine = allocations
      .filter((a) => a.user === user?.id && a.is_active)
      .map((a) => projectsById[a.project])
      .filter((p) => p && p.status === "ACTIVE");
    const seen = new Set(); const list = [];
    for (const p of mine) if (!seen.has(p.id)) { seen.add(p.id); list.push(p); }
    return list.length ? list : activeProjects.slice(0, 8);
  }, [allocations, projectsById, user, activeProjects]);

  // ensure the running project always appears as a chip even if not allocated
  const chips = useMemo(() => {
    if (active && !myProjects.some((p) => p.id === active.project)) {
      const p = projectsById[active.project];
      return [p || { id: active.project, name: active.project_name, client_name: active.client_name }, ...myProjects];
    }
    return myProjects;
  }, [active, myProjects, projectsById]);

  async function startOn(pid) {
    if (busy) return;
    setBusy(true); setFlash("");
    try { const r = await api.post("/timer/start/", { project: pid }); setActive(r.data); }
    catch { /* ignore */ } finally { setBusy(false); }
  }
  async function stop() {
    if (busy) return;
    setBusy(true);
    try {
      const r = await api.post("/timer/stop/");
      const m = r.data.minutes || 0, h = Math.floor(m / 60), mm = m % 60;
      setFlash(m > 0 ? `Logged ${h ? h + "h " : ""}${mm}m to ${r.data.project_name}.` : "Too short to log.");
      setActive(null); setTimeout(() => setFlash(""), 6000);
    } catch { /* ignore */ } finally { setBusy(false); }
  }
  function onChipClick(p) {
    if (active && active.project === p.id) stop();
    else startOn(p.id);
  }

  const otherProjects = activeProjects.filter((p) => !chips.some((c) => c.id === p.id));

  return (
    <div className="quickbar">
      <span className="quick-label">Quick start</span>
      {chips.map((p) => {
        const running = active && active.project === p.id;
        return (
          <button key={p.id} className={"chip" + (running ? " running" : "")} onClick={() => onChipClick(p)} disabled={busy}>
            {running && <span className="chip-dot" />}
            {p.name}{p.client_name && <span className="chip-sub">· {p.client_name}</span>}
            {running && <span className="chip-clock">{fmt(elapsed)}</span>}
            {running && <span className="chip-stop">✕</span>}
          </button>
        );
      })}
      {otherProjects.length > 0 && (
        <select className="quick-other" value="" onChange={(e) => e.target.value && startOn(Number(e.target.value))}>
          <option value="">Other project…</option>
          {otherProjects.map((p) => <option key={p.id} value={p.id}>{p.name} — {p.client_name}</option>)}
        </select>
      )}
      {flash && <span className="quick-flash">{flash}</span>}
    </div>
  );
}
