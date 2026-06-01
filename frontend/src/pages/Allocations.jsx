import { useEffect, useState } from "react";
import Layout from "../components/Layout";
import Modal from "../components/Modal";
import api from "../api/client";
import { useCollection, extractError } from "../api/hooks";
import { useAuth, isManager } from "../auth/AuthContext";

const EMPTY = { user: "", project: "", allocation_type: "SHARED", allocation_percentage: 100, bill_rate: "", cost_rate: "", is_active: true };

export default function Allocations() {
  const { user } = useAuth();
  const manager = isManager(user);
  const { items: allocations, loading, reload } = useCollection("/allocations/");
  const { items: users } = useCollection("/users/");
  const { items: projects } = useCollection("/projects/");
  const [matrix, setMatrix] = useState(null);
  const [modal, setModal] = useState(null);
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function loadMatrix() {
    try { const r = await api.get("/allocations/matrix/"); setMatrix(r.data); }
    catch { setMatrix(null); }
  }
  useEffect(() => { if (manager) loadMatrix(); }, [manager, allocations.length]);

  function openCreate() { setForm(EMPTY); setError(""); setModal({ mode: "create" }); }
  function openEdit(a) {
    setForm({ user: a.user, project: a.project, allocation_type: a.allocation_type,
      allocation_percentage: a.allocation_percentage, bill_rate: a.bill_rate ?? "", cost_rate: a.cost_rate ?? "", is_active: a.is_active });
    setError(""); setModal({ mode: "edit", id: a.id });
  }

  async function save(e) {
    e.preventDefault(); setBusy(true); setError("");
    const payload = { ...form, bill_rate: form.bill_rate || null, cost_rate: form.cost_rate || null };
    try {
      if (modal.mode === "create") await api.post("/allocations/", payload);
      else await api.patch(`/allocations/${modal.id}/`, payload);
      setModal(null); reload();
    } catch (err) { setError(extractError(err)); }
    finally { setBusy(false); }
  }

  async function remove(a) {
    if (!window.confirm(`Remove ${a.user_name}'s allocation to ${a.project_name}?`)) return;
    try { await api.delete(`/allocations/${a.id}/`); reload(); }
    catch (err) { alert(extractError(err)); }
  }

  if (!manager) {
    return <Layout><div className="page-head"><div className="eyebrow">Staffing</div><h1>Allocations</h1></div>
      <div className="panel"><div className="empty">Allocations are managed by managers and firm owners.</div></div></Layout>;
  }

  const activeUsers = users.filter((u) => u.is_active);
  const activeProjects = projects.filter((p) => p.status === "ACTIVE");

  return (
    <Layout>
      <div className="page-head">
        <div className="eyebrow">Staffing</div>
        <h1>Allocations</h1>
        <p>Who works for which client — dedicated or shared.</p>
      </div>

      {matrix && matrix.rows.length > 0 && (
        <div className="panel">
          <h3>Allocation matrix</h3>
          <div className="sub">Each person's time split across clients. A total over 100% means over-allocated.</div>
          <div className="matrix-wrap">
            <table className="matrix">
              <thead>
                <tr>
                  <th className="emp">Employee</th>
                  {matrix.clients.map((c) => <th key={c.id}>{c.name}</th>)}
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                {matrix.rows.map((row) => (
                  <tr key={row.user_id}>
                    <td className="emp">{row.user_name}</td>
                    {matrix.clients.map((c) => {
                      const cell = row.cells[c.id];
                      return (
                        <td key={c.id}>
                          {cell ? (
                            <span className="cell-pct">{cell.percentage}%{cell.type === "DEDICATED" && <span className="ded-tag">DED</span>}</span>
                          ) : <span className="cell-empty">–</span>}
                        </td>
                      );
                    })}
                    <td className={"cell-pct " + (row.total_percentage > 100 ? "tot-over" : "tot-ok")}>{row.total_percentage}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="toolbar" style={{ marginTop: 22 }}>
        <div className="page-head" style={{ margin: 0 }}><h3 style={{ fontFamily: "var(--font-display)", fontWeight: 500, fontSize: 19 }}>All allocations</h3></div>
        <button className="btn btn-sm" onClick={openCreate} disabled={activeUsers.length === 0 || activeProjects.length === 0}>+ New allocation</button>
      </div>

      <div className="table-card">
        <table className="data">
          <thead><tr><th>Employee</th><th>Project</th><th>Client</th><th>Type</th><th style={{ textAlign: "right" }}>Share</th><th style={{ textAlign: "right" }}>Bill rate</th><th></th></tr></thead>
          <tbody>
            {loading ? <tr><td className="empty-row" colSpan={7}>Loading…</td></tr>
              : allocations.length === 0 ? <tr><td className="empty-row" colSpan={7}>No allocations yet.</td></tr>
              : allocations.map((a) => (
                <tr key={a.id}>
                  <td>{a.user_name}</td>
                  <td>{a.project_name}</td>
                  <td>{a.client_name}</td>
                  <td><span className={"badge " + (a.allocation_type === "DEDICATED" ? "active" : "completed")}>{a.allocation_type === "DEDICATED" ? "Dedicated" : "Shared"}</span></td>
                  <td className="amount">{a.allocation_percentage}%</td>
                  <td className="amount">{a.bill_rate ?? "—"}</td>
                  <td><div className="row-actions">
                    <button className="link-btn" onClick={() => openEdit(a)}>Edit</button>
                    <button className="link-btn danger" onClick={() => remove(a)}>Delete</button>
                  </div></td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {modal && (
        <Modal title={modal.mode === "create" ? "New allocation" : "Edit allocation"} onClose={() => setModal(null)}>
          <form onSubmit={save}>
            {error && <div className="error">{error}</div>}
            <div className="field"><label>Employee</label>
              <select value={form.user} onChange={(e) => setForm({ ...form, user: e.target.value })} required>
                <option value="">Select an employee…</option>
                {activeUsers.map((u) => <option key={u.id} value={u.id}>{u.full_name || u.email}</option>)}
              </select></div>
            <div className="field"><label>Project</label>
              <select value={form.project} onChange={(e) => setForm({ ...form, project: e.target.value })} required>
                <option value="">Select a project…</option>
                {activeProjects.map((p) => <option key={p.id} value={p.id}>{p.name} — {p.client_name}</option>)}
              </select></div>
            <div className="form-row">
              <div className="field"><label>Type</label>
                <select value={form.allocation_type} onChange={(e) => setForm({ ...form, allocation_type: e.target.value })}>
                  <option value="SHARED">Shared</option>
                  <option value="DEDICATED">Dedicated</option>
                </select></div>
              <div className="field"><label>Share %</label>
                <input type="number" min="0" max="100" value={form.allocation_percentage}
                  onChange={(e) => setForm({ ...form, allocation_percentage: Number(e.target.value) })} required /></div>
            </div>
            <div className="form-row">
              <div className="field"><label>Bill rate / hr</label>
                <input type="number" min="0" step="0.01" value={form.bill_rate}
                  onChange={(e) => setForm({ ...form, bill_rate: e.target.value })} placeholder="optional" /></div>
              <div className="field"><label>Cost rate / hr</label>
                <input type="number" min="0" step="0.01" value={form.cost_rate}
                  onChange={(e) => setForm({ ...form, cost_rate: e.target.value })} placeholder="optional" /></div>
            </div>
            <label className="check">
              <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
              Active allocation
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
