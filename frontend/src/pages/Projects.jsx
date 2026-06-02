import { useState } from "react";
import Layout from "../components/Layout";
import Modal from "../components/Modal";
import api from "../api/client";
import { useCollection, extractError } from "../api/hooks";
import { useAuth, isManager } from "../auth/AuthContext";

const EMPTY = { client: "", name: "", code: "", status: "ACTIVE", is_billable: true, start_date: "", end_date: "" };
const STATUS_LABEL = { ACTIVE: "Active", ON_HOLD: "On hold", COMPLETED: "Completed" };

export default function Projects() {
  const { user } = useAuth();
  const manager = isManager(user);
  const { items, loading, reload } = useCollection("/projects/");
  const { items: clients } = useCollection("/clients/");
  const [search, setSearch] = useState("");
  const [modal, setModal] = useState(null);
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const filtered = items.filter((p) => p.name.toLowerCase().includes(search.toLowerCase()));

  function openCreate() { setForm(EMPTY); setError(""); setModal({ mode: "create" }); }
  function openEdit(p) {
    setForm({
      client: p.client, name: p.name, code: p.code || "", status: p.status,
      is_billable: p.is_billable, start_date: p.start_date || "", end_date: p.end_date || "",
    });
    setError(""); setModal({ mode: "edit", id: p.id });
  }

  async function save(e) {
    e.preventDefault(); setBusy(true); setError("");
    const payload = {
      ...form,
      start_date: form.start_date || null,
      end_date: form.end_date || null,
    };
    try {
      if (modal.mode === "create") await api.post("/projects/", payload);
      else await api.patch(`/projects/${modal.id}/`, payload);
      setModal(null); reload();
    } catch (err) { setError(extractError(err)); }
    finally { setBusy(false); }
  }

  async function remove(p) {
    if (!window.confirm(`Delete project "${p.name}"? This cannot be undone.`)) return;
    try { await api.delete(`/projects/${p.id}/`); reload(); }
    catch (err) { alert(extractError(err)); }
  }

  return (
    <Layout>
      <div className="page-head">
        <div className="eyebrow">Setup</div>
        <h1>Projects</h1>
        <p>The work you deliver — each one belongs to a client.</p>
      </div>

      <div className="toolbar">
        <input className="search-input" placeholder="Search projects…"
          value={search} onChange={(e) => setSearch(e.target.value)} />
        {manager && (
          <button className="btn btn-sm" onClick={openCreate} disabled={clients.length === 0}
            title={clients.length === 0 ? "Add a client first" : ""}>+ New project</button>
        )}
      </div>

      <div className="project-list">
        {loading ? (
          <div className="empty-row">Loading…</div>
        ) : filtered.length === 0 ? (
          <div className="empty-row">No projects yet.</div>
        ) : filtered.map((p) => (
          <div key={p.id} className={"project-row" + (p.status === "ACTIVE" ? " is-active" : "")}>
            <div className="project-main">
              <div className="project-name">
                {p.name}
                {p.code ? <span className="project-code"> · {p.code}</span> : null}
              </div>
              <div className="project-sub">{p.client_name}</div>
            </div>
            <div className="project-tags">
              <span className={"badge " + p.status.toLowerCase()}>{STATUS_LABEL[p.status]}</span>
              <span className={"badge " + (p.is_billable ? "yes" : "no")}>{p.is_billable ? "Billable" : "Internal"}</span>
            </div>
            {manager && (
              <div className="row-actions">
                <button className="link-btn" onClick={() => openEdit(p)}>Edit</button>
                <button className="link-btn danger" onClick={() => remove(p)}>Delete</button>
              </div>
            )}
          </div>
        ))}
      </div>

      {modal && (
        <Modal title={modal.mode === "create" ? "New project" : "Edit project"} onClose={() => setModal(null)}>
          <form onSubmit={save}>
            {error && <div className="error">{error}</div>}
            <div className="field">
              <label>Client</label>
              <select value={form.client} onChange={(e) => setForm({ ...form, client: e.target.value })} required>
                <option value="">Select a client…</option>
                {clients.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div className="field">
              <label>Project name</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            </div>
            <div className="form-row">
              <div className="field">
                <label>Code</label>
                <input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} placeholder="optional" />
              </div>
              <div className="field">
                <label>Status</label>
                <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
                  <option value="ACTIVE">Active</option>
                  <option value="ON_HOLD">On hold</option>
                  <option value="COMPLETED">Completed</option>
                </select>
              </div>
            </div>
            <div className="form-row">
              <div className="field">
                <label>Start date</label>
                <input type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} />
              </div>
              <div className="field">
                <label>End date</label>
                <input type="date" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} />
              </div>
            </div>
            <label className="check">
              <input type="checkbox" checked={form.is_billable}
                onChange={(e) => setForm({ ...form, is_billable: e.target.checked })} />
              Billable to the client
            </label>
            <div className="modal-actions">
              <button type="button" className="btn btn-ghost" onClick={() => setModal(null)}>Cancel</button>
              <button className="btn" disabled={busy}>{busy ? "Saving…" : "Save"}</button>
            </div>
          </form>
        </Modal>
      )}
    </Layout>
  );
}
