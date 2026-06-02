import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/client";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

export default function Download() {
  const [name, setName] = useState("");
  const [answer, setAnswer] = useState("");
  const [question, setQuestion] = useState("");
  const [token, setToken] = useState("");
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  async function loadChallenge() {
    setError(""); setAnswer("");
    try {
      const { data } = await api.get("/download/challenge/");
      setQuestion(data.question);
      setToken(data.token);
    } catch {
      setError("Could not load the verification. Please refresh the page.");
    }
  }

  useEffect(() => { loadChallenge(); }, []);

  async function submit(e) {
    e.preventDefault();
    setError(""); setBusy(true);
    try {
      const { data } = await api.post("/download/request/", { name, token, answer });
      // Start the download via the one-time token.
      window.location.href = `${API_BASE}/download/file/?t=${encodeURIComponent(data.download_token)}`;
      setDone(true);
    } catch (err) {
      const d = err?.response?.data || {};
      setError(d.captcha || d.name || "Something went wrong. Please try again.");
      loadChallenge();          // refresh the challenge after a failed attempt
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-wrap">
      <div className="login-brand">
        <div className="brand-mark">Time<b>Track</b></div>
        <div className="login-pitch">
          <h1>Download KlickTime</h1>
          <p>The desktop time tracker for your projects. Enter your name and
             confirm you're human to download the installer for Windows.</p>
        </div>
        <div className="login-foot">
          Operations Console · v0.1<br />
          Developed by <a href="https://klickevents.in" target="_blank" rel="noreferrer">Klickevents Infosolutions Pvt Ltd</a>
        </div>
      </div>
      <div className="login-form-side">
        <form className="login-card" onSubmit={submit}>
          <h2>Get KlickTime for Windows</h2>
          <p className="sub">No account needed — just your name.</p>
          {error && <div className="error">{error}</div>}
          {done && <div className="ok-note">Your download should begin shortly. If it doesn't,
                     <button type="button" className="linklike" onClick={submit}> click here</button>.</div>}
          <div className="field">
            <label>Your name</label>
            <input value={name} onChange={(e) => setName(e.target.value)}
                   placeholder="e.g. Asha Menon" required />
          </div>
          <div className="field">
            <label>Verification — {question || "loading…"}</label>
            <input value={answer} onChange={(e) => setAnswer(e.target.value)}
                   placeholder="Type the answer" inputMode="numeric" required />
          </div>
          <button className="btn" disabled={busy || !token}>{busy ? "Preparing…" : "Download installer"}</button>
          <p className="sub" style={{ marginTop: 16 }}>
            <Link to="/login">← Back to sign in</Link>
          </p>
        </form>
      </div>
    </div>
  );
}
