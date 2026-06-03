import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./auth/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import Download from "./pages/Download";
import Dashboard from "./pages/Dashboard";
import Clients from "./pages/Clients";
import Projects from "./pages/Projects";
import Time from "./pages/Time";
import Reports from "./pages/Reports";
import People from "./pages/People";
import Allocations from "./pages/Allocations";
import Activity from "./pages/Activity";

const protect = (el) => <ProtectedRoute>{el}</ProtectedRoute>;

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/download" element={<Download />} />
          <Route path="/" element={protect(<Dashboard />)} />
          <Route path="/clients" element={protect(<Clients />)} />
          <Route path="/projects" element={protect(<Projects />)} />
          <Route path="/time" element={protect(<Time />)} />
          <Route path="/reports" element={protect(<Reports />)} />
          <Route path="/people" element={protect(<People />)} />
          <Route path="/allocations" element={protect(<Allocations />)} />
          <Route path="/activity" element={protect(<Activity />)} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
