import { useEffect, useMemo, useState } from "react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend, Cell,
} from "recharts";
import Layout from "../components/Layout";
import api from "../api/client";
import { useAuth, isManager } from "../auth/AuthContext";

const TABS = [
  { id: "clients", label: "By client" },
  { id: "employees", label: "By employee" },
  { id: "projects", label: "By project" },
  { id: "utilization", label: "Utilization" },
  { id: "billing", label: "Billing" },
];
const ENDPOINT = {
  clients: "/reports/hours-by-client/",
  employees: "/reports/hours-by-employee/",
  projects: "/reports/hours-by-project/",
  utilization: "/reports/utilization/",
  billing: "/reports/billing-export/",
};

const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
const num = (n) => Number(n || 0).toLocaleString(undefined, { maximumFractionDigits: 2 });

function presets() {
  const now = new Date();
  const firstThis = new Date(now.getFullYear(), now.getMonth(), 1);
  const firstLast = new Date(now.getFullYear(), now.getMonth() - 1, 1);
  const lastLast = new Date(now.getFullYear(), now.getMonth(), 0);
  const monday = new Date(now); monday.setDate(now.getDate() - ((now.getDay() + 6) % 7));
  return {
    month: { from: iso(firstThis), to: iso(now), label: "This month" },
    lastmonth: { from: iso(firstLast), to: iso(lastLast), label: "Last month" },
    week: { from: iso(monday), to: iso(now), label: "This week" },
  };
}

export default function Reports() {
  const { user } = useAuth();
  const manager = isManager(user);
  const P = useMemo(presets, []);
  const [from, setFrom] = useState(P.month.from);
  const [to, setTo] = useState(P.month.to);
  const [activePreset, setActivePreset] = useState("month");
  const [tab, setTab] = useState("clients");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!manager) return;
    let active = true;
    setLoading(true);
    api.get(ENDPOINT[tab], { params: { date_from: from, date_to: to } })
      .then((r) => active && setData(r.data))
      .catch(() => active && setData(null))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [tab, from, to, manager]);

  function applyPreset(key) {
    setActivePreset(key); setFrom(P[key].from); setTo(P[key].to);
  }
  function onDate(setter) {
    return (e) => { setter(e.target.value); setActivePreset(""); };
  }

  if (!manager) {
    return (
      <Layout>
        <div className="page-head"><div className="eyebrow">Reports</div><h1>Reports</h1></div>
        <div className="panel"><div className="empty">Reports are available to managers and firm owners.</div></div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="page-head">
        <div className="eyebrow">Reports</div>
        <h1>Where the hours went</h1>
        <p>Hours, utilization, and billing across your firm.</p>
      </div>

      <div className="filters">
        <div className="preset-row">
          {Object.keys(P).map((k) => (
            <button key={k} className={"preset" + (activePreset === k ? " active" : "")}
              onClick={() => applyPreset(k)}>{P[k].label}</button>
          ))}
        </div>
        <div className="field"><label>From</label><input type="date" value={from} onChange={onDate(setFrom)} /></div>
        <div className="field"><label>To</label><input type="date" value={to} onChange={onDate(setTo)} /></div>
      </div>

      <div className="tabs">
        {TABS.map((t) => (
          <button key={t.id} className={"tab" + (tab === t.id ? " active" : "")} onClick={() => setTab(t.id)}>{t.label}</button>
        ))}
      </div>

      {loading ? <div className="loading">Crunching the numbers…</div> : <ReportBody tab={tab} data={data} />}
    </Layout>
  );
}

const BAR_COLORS = ["#0e7c66", "#1c9b80", "#39b89b", "#c4762a", "#7aa295", "#b3402f"];

function ReportBody({ tab, data }) {
  if (!data) return <div className="empty">No data for this range.</div>;

  if (tab === "clients") {
    const rows = data.results || [];
    return (
      <>
        <div className="panel">
          <h3>Hours by client</h3>
          <div className="sub">Total vs billable for the selected range.</div>
          {rows.length === 0 ? <div className="empty">Nothing logged in this range.</div> : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={rows} margin={{ top: 6, right: 8, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ece7de" vertical={false} />
                <XAxis dataKey="client" tick={{ fontSize: 12, fill: "#6b7177" }} tickLine={false} axisLine={{ stroke: "#e6e1d8" }} />
                <YAxis tick={{ fontSize: 12, fill: "#6b7177" }} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ borderRadius: 10, border: "1px solid #e6e1d8", fontSize: 13 }} />
                <Legend wrapperStyle={{ fontSize: 13 }} />
                <Bar dataKey="total_hours" name="Total" fill="#0e7c66" radius={[5, 5, 0, 0]} />
                <Bar dataKey="billable_hours" name="Billable" fill="#c4762a" radius={[5, 5, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
        <SimpleTable cols={["Client", "Total hours", "Billable hours"]}
          rows={rows.map((r) => [r.client, num(r.total_hours), num(r.billable_hours)])} numeric={[1, 2]} />
      </>
    );
  }

  if (tab === "employees") {
    const rows = data.results || [];
    return <SimpleTable cols={["Employee", "Total hours", "Billable hours"]}
      rows={rows.map((r) => [r.employee, num(r.total_hours), num(r.billable_hours)])} numeric={[1, 2]} />;
  }

  if (tab === "projects") {
    const rows = data.results || [];
    return <SimpleTable cols={["Project", "Client", "Total hours", "Billable hours"]}
      rows={rows.map((r) => [r.project, r.client, num(r.total_hours), num(r.billable_hours)])} numeric={[2, 3]} />;
  }

  if (tab === "utilization") {
    const rows = data.results || [];
    return (
      <>
        <div className="stat-grid" style={{ gridTemplateColumns: "repeat(2,1fr)" }}>
          <div className="stat"><div className="label">Working days</div><div className="value mono">{data.working_days}</div></div>
          <div className="stat"><div className="label">Capacity / person</div><div className="value mono">{num(data.capacity_hours)}<small> h</small></div></div>
        </div>
        <SimpleTable cols={["Employee", "Allocated", "Actual hours", "Capacity", "Utilization"]}
          rows={rows.map((r) => [
            r.employee, r.allocated_percentage + "%", num(r.actual_hours), num(r.capacity_hours),
            <UtilBadge key="u" pct={r.utilization_percentage} />,
          ])} numeric={[1, 2, 3]} />
      </>
    );
  }

  if (tab === "billing") {
    const rows = data.results || [];
    const t = data.totals || {};
    return (
      <>
        <div className="stat-grid">
          <div className="stat"><div className="label">Revenue (billable)</div><div className="value mono">{num(t.amount)}</div></div>
          <div className="stat amber"><div className="label">Cost</div><div className="value mono">{num(t.cost)}</div></div>
          <div className="stat"><div className="label">Margin</div><div className="value mono">{num(t.margin)}</div></div>
          <div className="stat"><div className="label">Unrated hours</div><div className="value mono">{num(t.unrated_hours)}</div><div className="foot">need a rate</div></div>
        </div>
        <SimpleTable cols={["Client", "Cur", "Billable h", "Amount", "Cost", "Margin", "Unrated h"]}
          rows={rows.map((r) => [r.client, r.currency, num(r.billable_hours), num(r.amount), num(r.cost), num(r.margin), num(r.unrated_hours)])}
          numeric={[2, 3, 4, 5, 6]} />
        <div className="note">Amounts are summary figures using each entry's snapshotted rate. Hours with no rate set appear under “unrated”.</div>
      </>
    );
  }
  return null;
}

function UtilBadge({ pct }) {
  let cls = "on_hold", text = pct + "%";
  if (pct > 100) cls = "no";        // overloaded -> red-ish
  else if (pct >= 70) cls = "active";
  return <span className={"badge " + cls}>{text}</span>;
}

function SimpleTable({ cols, rows, numeric = [] }) {
  return (
    <div className="table-card">
      <table className="data">
        <thead><tr>{cols.map((c, i) => <th key={i} style={numeric.includes(i) ? { textAlign: "right" } : null}>{c}</th>)}</tr></thead>
        <tbody>
          {rows.length === 0 ? (
            <tr><td className="empty-row" colSpan={cols.length}>Nothing to show for this range.</td></tr>
          ) : rows.map((r, ri) => (
            <tr key={ri}>{r.map((cell, ci) => (
              <td key={ci} className={numeric.includes(ci) ? "amount" : ""} style={numeric.includes(ci) ? { textAlign: "right" } : null}>{cell}</td>
            ))}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
