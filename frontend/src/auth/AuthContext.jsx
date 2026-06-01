import { createContext, useContext, useEffect, useState } from "react";
import api from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access");
    if (!token) { setLoading(false); return; }
    api.get("/auth/me/")
      .then((r) => setUser(r.data))
      .catch(() => localStorage.removeItem("access"))
      .finally(() => setLoading(false));
  }, []);

  async function login(email, password) {
    const r = await api.post("/auth/login/", { email, password });
    localStorage.setItem("access", r.data.access);
    localStorage.setItem("refresh", r.data.refresh);
    const me = await api.get("/auth/me/");
    setUser(me.data);
  }

  function logout() {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);

const MANAGER_ROLES = ["OWNER", "ADMIN", "PROJECT_HEAD", "PROJECT_MANAGER", "TEAM_LEADER"];
export const isManager = (user) => user && MANAGER_ROLES.includes(user.role);
