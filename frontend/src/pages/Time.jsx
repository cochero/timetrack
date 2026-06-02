import { useEffect, useMemo, useState } from "react";
import Layout from "../components/Layout";
import Modal from "../components/Modal";
import api from "../api/client";
import { useCollection, extractError } from "../api/hooks";
import { useAuth } from "../auth/AuthContext";

const DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

function mondayOf(d) {
  const x = new Date(d);
  const off = (x.getDay() + 6) % 7;     // days since Monday
  x.setDate(x.getDate() - off);
  x.setHours(0, 0, 0, 0);
  return x;
}
function addDays(d, n) { const x = new Date(d); x.setDate(x.getDate() + n); return x; }
function iso(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
function prettyRange(start) {
  const end = addDays(start, 6);
  const o = { month: "short", day: "numeric" };
  return `${start.toLocaleDateString(undefined, o)} – ${end.toLocaleDateString(undefined, o)}, ${end.getFullYear()}`;
}
const hrs = (m) => Math.round((m / 60) * 100) / 100;

export default function Time() {
  const { user } = useAuth();
  const { items: projects } = useCollection("/projects/");
  const { items: clients } = useCollection("/clients/");
  const projectsById = useMemo(() => Object.fromEntries(projects.map((p) => [p.id, p])), [projects]);

  const [weekStart, setWeekStart] = useState(() => mondayOf(new Date()));
  const [rowIds, setRowIds] = useState([]);
  const [entryMap, setEntryMap] = useState({});   // "projectId|date" -> {id, minutes}
  const [inputs, setInputs] = useState({});        // "projectId|date" -> "1.5"
  const [loading, setLoading] = useState(true);
  const [meetings, setMeetings] = useState([]);    // non-project entries this week
  const [refresh, setRefresh] = useState(0);
  const [mtgModal, setMtgModal] = useState(false);
  const [mtg, setMtg] = useState({ type: "INTERNAL_MEETING", entry_date: iso(new Date()), hours: "", description: "" });
  const [mtgErr, setMtgErr] = useState("");

  const days = useMemo(() => DOW.map((_, i) => addDays(weekStart, i)), [weekStart]);
  const key = (pid, d) => `${pid}|${iso(d)}`;

  useEffect(() => {
    let active = true;
    async function load() {
      if (!user) return;
      setLoading(true);
      const from = iso(weekStart), to = iso(addDays(weekStart, 6));
      try {
        const r = await api.get(`/time-entries/?user=${user.id}&date_from=${from}&date_to=${to}&page_size=200`);
        const list = r.data.results ?? r.data;
        if (!active) return;
        const map = {}, inp = {}, ids = new Set(), mtgs = [];
        for (const e of list) {
          const type = e.activity_type || "WORK";
          if (type === "WORK" && e.project) {
            const k = `${e.project}|${e.entry_date}`;
            map[k] = { id: e.id, minutes: e.minutes };
            inp[k] = String(hrs(e.minutes));
            ids.add(e.project);
          } else if (type !== "WORK") {
            mtgs.push(e);
          }
        }
        setEntryMap(map);
        setInputs(inp);
        setMeetings(mtgs);
        setRowIds((prev) => Array.from(new Set([...prev, ...ids])));
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => { active = false; };
  }, [weekStart, user, refresh]);

  const minutesOf = (k) => {
    const h = parseFloat(inputs[k]);
    return isNaN(h) || h < 0 ? 0 : Math.round(h * 60);
  };
  const rowMinutes = (pid) => days.reduce((s, d) => s + minutesOf(key(pid, d)), 0);
  const dayMinutes = (d) => rowIds.reduce((s, pid) => s + minutesOf(key(pid, d)), 0);
  const grand = rowIds.reduce((s, pid) => s + rowMinutes(pid), 0);
  const hasSaved = (pid) => days.some((d) => entryMap[key(pid, d)]);

  async function persist(pid, d) {
    const k = key(pid, d);
    const minutes = minutesOf(k);
    const existing = entryMap[k];
    try {
      if (existing && minutes > 0) {
        await api.patch(`/time-entries/${existing.id}/`, { minutes });
        setEntryMap((m) => ({ ...m, [k]: { ...existing, minutes } }));
      } else if (existing && minutes === 0) {
        await api.delete(`/time-entries/${existing.id}/`);
        setEntryMap((m) => { const c = { ...m }; delete c[k]; return c; });
        setInputs((i) => ({ ...i, [k]: "" }));
      } else if (!existing && minutes > 0) {
        const proj = projectsById[pid];
        const r = await api.post(`/time-entries/`, {
          project: pid, entry_date: iso(d), minutes,
          is_billable: proj ? proj.is_billable : true,
        });
        setEntryMap((m) => ({ ...m, [k]: { id: r.data.id, minutes } }));
      }
    } catch (err) {
      alert(extractError(err));
    }
  }

  const available = projects.filter((p) => !rowIds.includes(p.id) && p.status === "ACTIVE");

  async function saveMeeting(e) {
    e.preventDefault(); setMtgErr("");
    const minutes = Math.round(parseFloat(mtg.hours || "0") * 60);
    if (!minutes || minutes <= 0) { setMtgErr("Enter how long the meeting lasted."); return; }
    if (!mtg.description.trim()) { setMtgErr("Add a short description."); return; }
    if (mtg.type === "CLIENT_MEETING" && !mtg.client) { setMtgErr("Choose the client for this meeting."); return; }
    try {
      const payload = {
        activity_type: mtg.type, entry_date: mtg.entry_date, minutes, description: mtg.description,
      };
      if (mtg.type === "CLIENT_MEETING") payload.client = Number(mtg.client);
      await api.post("/time-entries/", payload);
      setMtgModal(false);
      setMtg({ type: "INTERNAL_MEETING", entry_date: iso(new Date()), hours: "", description: "" });
      setRefresh((x) => x + 1);
    } catch (err) { setMtgErr(extractError(err)); }
  }

  async function delMeeting(id) {
    if (!window.confirm("Delete this entry?")) return;
    try { await api.delete(`/time-entries/${id}/`); setRefresh((x) => x + 1); }
    catch (err) { alert(extractError(err)); }
  }

  return (
    <Layout>
      <div className="page-head">
        <div className="eyebrow">My week</div>
        <h1>Timesheet</h1>
        <p>Log the hours you spent on each client this week.</p>
      </div>

      <div className="week-bar">
        <div className="week-nav">
          <button className="nav-btn" onClick={() => setWeekStart(addDays(weekStart, -7))} aria-label="Previous week">‹</button>
          <div className="week-range">{prettyRange(weekStart)}</div>
          <button className="nav-btn" onClick={() => setWeekStart(addDays(weekStart, 7))} aria-label="Next week">›</button>
        </div>
        <button className="btn btn-ghost btn-sm" onClick={() => setWeekStart(mondayOf(new Date()))}>This week</button>
        <div className="week-total">Week total <span className="mono">{hrs(grand)}</span> h</div>
      </div>

      <div className="table-card">
        <table className="grid">
          <thead>
            <tr>
              <th className="proj">Project</th>
              {days.map((d, i) => (
                <th key={i} className={i >= 5 ? "cell-weekend" : ""}>
                  {DOW[i]}<br /><span className="dnum">{d.getDate()}</span>
                </th>
              ))}
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td className="empty-row" colSpan={9}>Loading your week…</td></tr>
            ) : rowIds.length === 0 ? (
              <tr><td className="empty-row" colSpan={9}>Add a project below to start logging time.</td></tr>
            ) : rowIds.map((pid) => {
              const proj = projectsById[pid];
              return (
                <tr key={pid}>
                  <td className="proj">
                    <span className="proj-name">{proj ? proj.name : `Project ${pid}`}</span>
                    {proj && <div className="proj-client">{proj.client_name}</div>}
                    {!hasSaved(pid) && (
                      <button className="row-remove" title="Remove row"
                        onClick={() => setRowIds((r) => r.filter((x) => x !== pid))}>×</button>
                    )}
                  </td>
                  {days.map((d, i) => {
                    const k = key(pid, d);
                    return (
                      <td key={i} className={i >= 5 ? "cell-weekend" : ""}>
                        <input className="cell-input" type="number" min="0" step="0.25"
                          value={inputs[k] ?? ""}
                          onChange={(e) => setInputs((s) => ({ ...s, [k]: e.target.value }))}
                          onBlur={() => persist(pid, d)} />
                      </td>
                    );
                  })}
                  <td className="rowtotal">{hrs(rowMinutes(pid))}</td>
                </tr>
              );
            })}
          </tbody>
          {rowIds.length > 0 && (
            <tfoot>
              <tr className="totals">
                <td className="proj">Daily total</td>
                {days.map((d, i) => <td key={i}>{hrs(dayMinutes(d))}</td>)}
                <td>{hrs(grand)}</td>
              </tr>
            </tfoot>
          )}
        </table>
      </div>

      {available.length > 0 && (
        <div className="addrow">
          <select value="" onChange={(e) => e.target.value && setRowIds((r) => [...r, Number(e.target.value)])}>
            <option value="">+ Add a project row…</option>
            {available.map((p) => <option key={p.id} value={p.id}>{p.name} — {p.client_name}</option>)}
          </select>
        </div>
      )}

      <div className="meeting-section">
        <div className="meeting-head">
          <h3>Meetings this week</h3>
          <button className="btn btn-sm" onClick={() => {
            setMtg({ type: "INTERNAL_MEETING", entry_date: iso(new Date()), hours: "", description: "" });
            setMtgErr(""); setMtgModal(true);
          }}>+ Log a meeting</button>
        </div>
        {meetings.length === 0 ? (
          <div className="empty-row">No meetings logged this week.</div>
        ) : (
          <div className="meeting-list">
            {meetings.map((m) => (
              <div key={m.id} className="meeting-item">
                <span className={"badge " + (m.activity_type === "CLIENT_MEETING" ? "yes" : "no")}>{m.activity_label}</span>
                <span className="meeting-desc">{m.description || "—"}{m.client_name ? ` · ${m.client_name}` : ""}</span>
                <span className="meeting-date mono">{m.entry_date}</span>
                <span className="meeting-hrs mono">{hrs(m.minutes)} h</span>
                <button className="link-btn danger" onClick={() => delMeeting(m.id)}>Delete</button>
              </div>
            ))}
          </div>
        )}
      </div>

      {mtgModal && (
        <Modal title="Log a meeting" onClose={() => setMtgModal(false)}>
          <form onSubmit={saveMeeting}>
            {mtgErr && <div className="error">{mtgErr}</div>}
            <div className="field">
              <label>Type</label>
              <select value={mtg.type} onChange={(e) => setMtg({ ...mtg, type: e.target.value })}>
                <option value="INTERNAL_MEETING">Internal meeting (non-billable)</option>
                <option value="CLIENT_MEETING">Client meeting (billable)</option>
              </select>
            </div>
            {mtg.type === "CLIENT_MEETING" && (
              <div className="field">
                <label>Client</label>
                <select value={mtg.client || ""} onChange={(e) => setMtg({ ...mtg, client: e.target.value })}>
                  <option value="">Select a client…</option>
                  {clients.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
            )}
            <div className="form-row">
              <div className="field">
                <label>Date</label>
                <input type="date" value={mtg.entry_date} onChange={(e) => setMtg({ ...mtg, entry_date: e.target.value })} />
              </div>
              <div className="field">
                <label>Hours</label>
                <input type="number" min="0" step="0.25" value={mtg.hours}
                  onChange={(e) => setMtg({ ...mtg, hours: e.target.value })} placeholder="e.g. 1.5" />
              </div>
            </div>
            <div className="field">
              <label>Description</label>
              <input value={mtg.description} onChange={(e) => setMtg({ ...mtg, description: e.target.value })}
                placeholder="What was the meeting about?" />
            </div>
            <div className="modal-actions">
              <button type="button" className="btn btn-ghost" onClick={() => setMtgModal(false)}>Cancel</button>
              <button className="btn">Save</button>
            </div>
          </form>
        </Modal>
      )}
    </Layout>
  );
}
