import { useState } from "react";
import Layout from "../components/Layout";
import Modal from "../components/Modal";
import api from "../api/client";
import { useCollection, extractError } from "../api/hooks";
import { useAuth, isManager } from "../auth/AuthContext";

const ROLE_LABEL = {
  OWNER: "Owner", ADMIN: "Admin", PROJECT_HEAD: "Project head",
  PROJECT_MANAGER: "Project manager", TEAM_LEADER: "Team leader", EMPLOYEE: "Employee",
};
const ASSIGNABLE = ["ADMIN", "PROJECT_HEAD", "PROJECT_MANAGER", "TEAM_LEADER", "EMPLOYEE"];
const EMPTY = { email: "", full_name: "", role: "EMPLOYEE", employee_code: "", password: "", is_active: true };

export default function People() {
  const { user } = useAuth();
  const manager = isManager(user);
  const { items, loading, reload } = useCollection("/users/");
  const [search, setSearch] = useState("");
  const [modal, setModal] = useState(null);
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const filtered = items.filter((u) =>
    (u.full_name || "").toLowerCase().includes(search.toLowerCase()) ||
    u.email.toLowerCase().includes(search.toLowerCase()));

  function openCreate() { setForm(EMPTY); setError(""); setModal({ mode: "create" }); }
  function openEdit(u) {
    setForm({ email: u.email, full_name: u.full_name || "", role: u.role, employee_code: u.employee_code || "", is_active: u.is_active });
    setError(""); setModal({ mode: "edit", id: u.id });
  }

  async function save(e) {
    e.preventDefault(); setBusy(true); setError("");
    try {
      if (modal.mode === "create") await api.post("/users/", form);
      else {
        const { password, ...rest } = form;
        await api.patch(`/users/${modal.id}/`, rest);
      }
      setModal(null); reload();
    } catch (err) { setError(extractError(err)); }
    finally { setBusy(false); }
  }

  async function deactivate(u) {
    if (!window.confirm(`Deactivate ${u.full_name || u.email}? They keep their logged time but can no longer sign in.`)) return;
    try { await api.delete(`/users/${u.id}/`); reload(); }
    catch (err) { alert(extractError(err)); }
  }

  if (!manager) {
    return <Layout><div className="page-head"><div className="eyebrow">Team</div><h1>People</h1></div>
      <div className="panel"><div className="empty">Managing people is available to managers and firm owners.</div></div></Layout>;
  }

  return (
    <Layout>
      <div className="page-head">
        <div className="eyebrow">Team</div>
        <h1>People</h1>
        <p>Your firm's employees and their roles.</p>
      </div>

      <div className="toolbar">
        <input className="search-input" placeholder="Search people…" value={search} onChange={(e) => setSearch(e.target.value)} />
        <button className="btn btn-sm" onClick={openCreate}>+ Add employee</button>
      </div>

      <div className="table-card">
        <table className="data">
          <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th></th></tr></thead>
          <tbody>
            {loading ? <tr><td className="empty-row" colSpan={5}>Loading…</td></tr>
              : filtered.length === 0 ? <tr><td className="empty-row" colSpan={5}>No people yet.</td></tr>
              : filtered.map((u) => (
                <tr key={u.id}>
                  <td>{u.full_name || "—"}</td>
                  <td className="num">{u.email}</td>
                  <td>{ROLE_LABEL[u.role]}</td>
                  <td><span className={"badge " + (u.is_active ? "active" : "inactive")}>{u.is_active ? "Active" : "Inactive"}</span></td>
                  <td><div className="row-actions">
                    <button className="link-btn" onClick={() => openEdit(u)}>Edit</button>
                    {u.is_active && u.id !== user.id && <button className="link-btn danger" onClick={() => deactivate(u)}>Deactivate</button>}
                  </div></td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {modal && (
        <Modal title={modal.mode === "create" ? "Add employee" : "Edit employee"} onClose={() => setModal(null)}>
          <form onSubmit={save}>
            {error && <div className="error">{error}</div>}
            <div className="field"><label>Full name</label>
              <input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required /></div>
            <div className="field"><label>Email</label>
              <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required /></div>
            <div className="form-row">
              <div className="field"><label>Role</label>
                <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
                  {ASSIGNABLE.map((r) => <option key={r} value={r}>{ROLE_LABEL[r]}</option>)}
                </select></div>
              <div className="field"><label>Employee code</label>
                <input value={form.employee_code} onChange={(e) => setForm({ ...form, employee_code: e.target.value })} placeholder="optional" /></div>
            </div>
            {modal.mode === "create" ? (
              <div className="field"><label>Starting password</label>
                <input type="text" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
                  placeholder="share this with them" required minLength={8} />
              </div>
            ) : (
              <label className="check">
                <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
                Active (can sign in)
              </label>
            )}
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
