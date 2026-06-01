import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError(""); setBusy(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError("Wrong email or password. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-wrap">
      <div className="login-brand">
        <div className="brand-mark">Time<b>Track</b></div>
        <div className="login-pitch">
          <h1>Every hour, every client, accounted for.</h1>
          <p>Track dedicated and shared resources across all your clients —
             and see exactly where the billable hours go.</p>
        </div>
        <div className="login-foot">Operations Console · v0.1</div>
      </div>
      <div className="login-form-side">
        <form className="login-card" onSubmit={submit}>
          <h2>Welcome back</h2>
          <p className="sub">Sign in to your firm's console.</p>
          {error && <div className="error">{error}</div>}
          <div className="field">
            <label>Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                   placeholder="you@firm.com" required />
          </div>
          <div className="field">
            <label>Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                   placeholder="••••••••" required />
          </div>
          <button className="btn" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
        </form>
      </div>
    </div>
  );
}
