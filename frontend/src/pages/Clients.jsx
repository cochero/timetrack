import { useState } from "react";
import Layout from "../components/Layout";
import Modal from "../components/Modal";
import api from "../api/client";
import { useCollection, extractError } from "../api/hooks";
import { useAuth, isManager } from "../auth/AuthContext";

const EMPTY = { name: "", code: "", status: "ACTIVE", billing_currency: "INR" };

export default function Clients() {
  const { user } = useAuth();
  const manager = isManager(user);
  const { items, loading, reload } = useCollection("/clients/");
  const [search, setSearch] = useState("");
  const [modal, setModal] = useState(null);
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const filtered = items.filter((c) => c.name.toLowerCase().includes(search.toLowerCase()));

  function openCreate() { setForm(EMPTY); setError(""); setModal({ mode: "create" }); }
  function openEdit(c) {
    setForm({ name: c.name, code: c.code || "", status: c.status, billing_currency: c.billing_currency });
    setError(""); setModal({ mode: "edit", id: c.id });
  }

  async function save(e) {
    e.preventDefault(); setBusy(true); setError("");
    try {
      if (modal.mode === "create") await api.post("/clients/", form);
      else await api.patch(`/clients/${modal.id}/`, form);
      setModal(null); reload();
    } catch (err) { setError(extractError(err)); }
    finally { setBusy(false); }
  }

  async function remove(c) {
    if (!window.confirm(`Delete client "${c.name}"? This cannot be undone.`)) return;
    try { await api.delete(`/clients/${c.id}/`); reload(); }
    catch (err) { alert(extractError(err)); }
  }

  return (
    <Layout>
      <div className="page-head">
        <div className="eyebrow">Setup</div>
        <h1>Clients</h1>
        <p>The companies your firm provides services to.</p>
      </div>

      <div className="toolbar">
        <input className="search-input" placeholder="Search clients…"
          value={search} onChange={(e) => setSearch(e.target.value)} />
        {manager && <button className="btn btn-sm" onClick={openCreate}>+ New client</button>}
      </div>

      <div className="table-card">
        <table className="data">
          <thead>
            <tr><th>Name</th><th>Code</th><th>Status</th><th>Projects</th>{manager && <th></th>}</tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td className="empty-row" colSpan={5}>Loading…</td></tr>
            ) : filtered.length === 0 ? (
              <tr><td className="empty-row" colSpan={5}>No clients yet.</td></tr>
            ) : filtered.map((c) => (
              <tr key={c.id}>
                <td>{c.name}</td>
                <td className="num">{c.code || "—"}</td>
                <td><span className={"badge " + c.status.toLowerCase()}>{c.status === "ACTIVE" ? "Active" : "Inactive"}</span></td>
                <td className="num">{c.projects_count}</td>
                {manager && (
                  <td><div className="row-actions">
                    <button className="link-btn" onClick={() => openEdit(c)}>Edit</button>
                    <button className="link-btn danger" onClick={() => remove(c)}>Delete</button>
                  </div></td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {modal && (
        <Modal title={modal.mode === "create" ? "New client" : "Edit client"} onClose={() => setModal(null)}>
          <form onSubmit={save}>
            {error && <div className="error">{error}</div>}
            <div className="field">
              <label>Name</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            </div>
            <div className="form-row">
              <div className="field">
                <label>Code</label>
                <input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} placeholder="e.g. GBX" />
              </div>
              <div className="field">
                <label>Status</label>
                <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
                  <option value="ACTIVE">Active</option>
                  <option value="INACTIVE">Inactive</option>
                </select>
              </div>
            </div>
            <div className="field">
              <label>Billing currency</label>
              <input value={form.billing_currency} maxLength={3}
                onChange={(e) => setForm({ ...form, billing_currency: e.target.value.toUpperCase() })} />
            </div>
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
