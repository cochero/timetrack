import { useEffect, useMemo, useState } from "react";
import Layout from "../components/Layout";
import api from "../api/client";
import { useAuth, isManager } from "../auth/AuthContext";
import { useCollection } from "../api/hooks";

const iso = (d) => d.toISOString().slice(0, 10);
const hrs = (m) => (m / 60).toFixed(1);

// Window titles / apps that are worth a gentle highlight for a manager's eye.
const WATCH = ["youtube", "netflix", "facebook", "instagram", "tiktok", "twitch", "primevideo", "hotstar"];
const looksLeisure = (b) => {
  const hay = `${b.app} ${b.window_title}`.toLowerCase();
  return WATCH.some((w) => hay.includes(w));
};

export default function Activity() {
  const { user } = useAuth();
  const manager = isManager(user);
  const { items: people } = useCollection("/users/");
  const [empId, setEmpId] = useState("");
  const [date, setDate] = useState(iso(new Date()));
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const employees = useMemo(
    () => people.filter((p) => p.is_active).sort((a, b) => (a.full_name || a.email).localeCompare(b.full_name || b.email)),
    [people]
  );

  useEffect(() => {
    if (!empId || !date) { setData(null); return; }
    let active = true;
    (async () => {
      setLoading(true); setErr("");
      try {
        const r = await api.get(`/activity/feed/?user=${empId}&date=${date}`);
        if (active) setData(r.data);
      } catch {
        if (active) { setData(null); setErr("Could not load activity for that day."); }
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, [empId, date]);

  if (!manager) {
    return <Layout><div className="page-head"><h1>Activity</h1></div>
      <div className="panel"><div className="empty">Activity is available to managers and firm owners.</div></div></Layout>;
  }

  return (
    <Layout>
      <div className="page-head">
        <h1>Activity</h1>
        <p>Review an employee's day: the applications and windows in focus during tracked time.</p>
      </div>

      <div className="filter-bar">
        <select value={empId} onChange={(e) => setEmpId(e.target.value)}>
          <option value="">Choose an employee…</option>
          {employees.map((p) => <option key={p.id} value={p.id}>{p.full_name || p.email}</option>)}
        </select>
        <input type="date" value={date} max={iso(new Date())} onChange={(e) => setDate(e.target.value)} />
      </div>

      {!empId ? (
        <div className="panel"><div className="empty">Choose an employee and a day to see their activity.</div></div>
      ) : loading ? (
        <div className="panel"><div className="empty">Loading…</div></div>
      ) : err ? (
        <div className="panel"><div className="empty">{err}</div></div>
      ) : !data || data.blocks.length === 0 ? (
        <div className="panel"><div className="empty">No activity recorded for {data?.employee?.name || "this employee"} on this day.</div></div>
      ) : (
        <>
          <div className="activity-summary">
            <div className="sum-card">
              <div className="sum-num">{hrs(data.total_active_minutes)} h</div>
              <div className="sum-label">Active time</div>
            </div>
            <div className="sum-apps">
              <div className="sum-apps-title">Most used</div>
              {data.top_apps.map((a) => (
                <div key={a.app} className="sum-app-row">
                  <span className={looksLeisure(a) ? "leisure" : ""}>{a.app}</span>
                  <span className="mono">{hrs(a.active_minutes)} h</span>
                </div>
              ))}
            </div>
          </div>

          <div className="activity-timeline">
            {data.blocks.map((b, i) => (
              <div key={i} className={"timeline-row" + (looksLeisure(b) ? " leisure" : "")}>
                <span className="t-time mono">{b.start}–{b.end}</span>
                <span className="t-app">{b.app}</span>
                <span className="t-title">{b.window_title || "—"}</span>
                <span className="t-min mono">{b.active_minutes} min</span>
              </div>
            ))}
          </div>

          <p className="activity-note">
            This shows the foreground application and window title sampled during tracked time. It does not
            capture screen contents or keystrokes. Window titles in a different colour match common video or
            social sites and are highlighted only as a prompt to look, not as a judgement.
          </p>
        </>
      )}
    </Layout>
  );
}
