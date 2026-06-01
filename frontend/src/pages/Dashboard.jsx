import { useEffect, useState } from "react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell,
} from "recharts";
import api from "../api/client";
import { useAuth, isManager } from "../auth/AuthContext";
import Layout from "../components/Layout";

const BAR_COLORS = ["#0e7c66", "#1c9b80", "#39b89b", "#c4762a", "#7aa295", "#b3402f"];

export default function Dashboard() {
  const { user } = useAuth();
  const manager = isManager(user);
  const [loading, setLoading] = useState(true);
  const [byClient, setByClient] = useState([]);
  const [myHours, setMyHours] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        if (manager) {
          const r = await api.get("/reports/hours-by-client/");
          setByClient(r.data.results || []);
        } else {
          const r = await api.get("/time-entries/");
          const mins = (r.data.results || []).reduce((s, e) => s + (e.minutes || 0), 0);
          setMyHours(Math.round((mins / 60) * 10) / 10);
        }
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [manager]);

  const totalHours = byClient.reduce((s, c) => s + (c.total_hours || 0), 0);
  const billableHours = byClient.reduce((s, c) => s + (c.billable_hours || 0), 0);
  const billablePct = totalHours ? Math.round((billableHours / totalHours) * 100) : 0;

  return (
    <Layout>
      <div className="page-head">
        <div className="eyebrow">This month</div>
        <h1>Good to see you, {(user?.full_name || user?.email || "").split(" ")[0] || "there"}.</h1>
        <p>{manager
          ? "Here's how your firm's hours are landing across clients."
          : "Here's a snapshot of the time you've logged."}</p>
      </div>

      {loading ? (
        <div className="loading">Loading your dashboard…</div>
      ) : manager ? (
        <>
          <div className="stat-grid">
            <div className="stat">
              <div className="label">Total hours</div>
              <div className="value mono">{totalHours.toFixed(1)}<small> h</small></div>
              <div className="foot">across {byClient.length} client{byClient.length === 1 ? "" : "s"}</div>
            </div>
            <div className="stat">
              <div className="label">Billable hours</div>
              <div className="value mono">{billableHours.toFixed(1)}<small> h</small></div>
              <div className="foot">{billablePct}% of total</div>
            </div>
            <div className="stat amber">
              <div className="label">Non-billable</div>
              <div className="value mono">{(totalHours - billableHours).toFixed(1)}<small> h</small></div>
              <div className="foot">watch this gap</div>
            </div>
            <div className="stat">
              <div className="label">Active clients</div>
              <div className="value mono">{byClient.length}</div>
              <div className="foot">with logged time</div>
            </div>
          </div>

          <div className="panel">
            <h3>Hours by client</h3>
            <div className="sub">Where this month's time is going.</div>
            {byClient.length === 0 ? (
              <div className="empty">No time logged yet this month.</div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={byClient} margin={{ top: 6, right: 8, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ece7de" vertical={false} />
                  <XAxis dataKey="client" tick={{ fontSize: 12, fill: "#6b7177" }} tickLine={false} axisLine={{ stroke: "#e6e1d8" }} />
                  <YAxis tick={{ fontSize: 12, fill: "#6b7177" }} tickLine={false} axisLine={false} />
                  <Tooltip cursor={{ fill: "rgba(14,124,102,.06)" }}
                    contentStyle={{ borderRadius: 10, border: "1px solid #e6e1d8", fontSize: 13 }} />
                  <Bar dataKey="total_hours" name="Hours" radius={[6, 6, 0, 0]}>
                    {byClient.map((_, i) => <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </>
      ) : (
        <div className="stat-grid">
          <div className="stat">
            <div className="label">Your hours logged</div>
            <div className="value mono">{(myHours ?? 0).toFixed(1)}<small> h</small></div>
            <div className="foot">recent entries</div>
          </div>
        </div>
      )}
    </Layout>
  );
}
