import { useState } from "react";
import Modal from "./Modal";
import api from "../api/client";
import { useCollection } from "../api/hooks";

const iso = (d) => d.toISOString().slice(0, 10);

// A small, self-contained "log a meeting" dialog used by the quick bar.
// type is fixed by how it is opened ("INTERNAL_MEETING" or "CLIENT_MEETING").
export default function MeetingModal({ type, onClose, onSaved }) {
  const { items: clients } = useCollection("/clients/");
  const [form, setForm] = useState({ entry_date: iso(new Date()), hours: "", description: "", client: "" });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const isClient = type === "CLIENT_MEETING";

  async function save(e) {
    e.preventDefault(); setErr("");
    const minutes = Math.round(parseFloat(form.hours || "0") * 60);
    if (!minutes || minutes <= 0) { setErr("Enter how long the meeting lasted."); return; }
    if (!form.description.trim()) { setErr("Add a short description."); return; }
    if (isClient && !form.client) { setErr("Choose the client for this meeting."); return; }
    setBusy(true);
    try {
      const payload = { activity_type: type, entry_date: form.entry_date, minutes, description: form.description };
      if (isClient) payload.client = Number(form.client);
      await api.post("/time-entries/", payload);
      onSaved && onSaved();
      onClose();
    } catch (e2) {
      setErr(e2?.response?.data?.detail || "Could not save. Please check the form.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title={isClient ? "Log a client meeting" : "Log an internal meeting"} onClose={onClose}>
      <form onSubmit={save}>
        {err && <div className="error">{err}</div>}
        {isClient && (
          <div className="field">
            <label>Client</label>
            <select value={form.client} onChange={(e) => setForm({ ...form, client: e.target.value })}>
              <option value="">Select a client…</option>
              {clients.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
        )}
        <div className="form-row">
          <div className="field">
            <label>Date</label>
            <input type="date" value={form.entry_date} max={iso(new Date())}
              onChange={(e) => setForm({ ...form, entry_date: e.target.value })} />
          </div>
          <div className="field">
            <label>Hours</label>
            <input type="number" min="0" step="0.25" value={form.hours}
              onChange={(e) => setForm({ ...form, hours: e.target.value })} placeholder="e.g. 1.5" />
          </div>
        </div>
        <div className="field">
          <label>{isClient ? "Meeting topic" : "Description"}</label>
          <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder="What was the meeting about?" />
        </div>
        <div className="modal-actions">
          <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn" disabled={busy}>{busy ? "Saving…" : "Save"}</button>
        </div>
      </form>
    </Modal>
  );
}
