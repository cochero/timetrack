import { NavLink } from "react-router-dom";
import { useAuth, isManager } from "../auth/AuthContext";
import TimerBar from "./TimerBar";

const NAV = [
  { to: "/", label: "Dashboard", live: true },
  { to: "/clients", label: "Clients", live: true },
  { to: "/projects", label: "Projects", live: true },
  { to: "/people", label: "People", live: true },
  { to: "/allocations", label: "Allocations", live: true },
  { to: "/time", label: "Time", live: true },
  { to: "/reports", label: "Reports", live: true },
  { to: "/activity", label: "Activity", live: true, managerOnly: true },
];

export default function Layout({ children }) {
  const { user, logout } = useAuth();
  const manager = isManager(user);
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand-mark">Time<b>Track</b></div>
        <nav>
          {NAV.filter((n) => !n.managerOnly || manager).map((n) => (
            <NavLink key={n.to} to={n.to} end={n.to === "/"}
              className={({ isActive }) => "nav-item" + (isActive ? " active" : "")}>
              <span className="dot" />
              {n.label}
              {!n.live && <span className="nav-soon">soon</span>}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot">
          <div className="who">{user?.full_name || user?.email}</div>
          <div className="role">{(user?.role || "").toLowerCase().replace("_", " ")}</div>
          <button className="logout" onClick={logout}>Sign out</button>
        </div>
      </aside>
      <main className="content">
        <TimerBar />
        {children}
        <footer className="app-footer">
          Developed by <a href="https://klickevents.in" target="_blank" rel="noreferrer">Klickevents Infosolutions Pvt Ltd</a>
        </footer>
      </main>
    </div>
  );
}
