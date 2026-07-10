import { useState } from "react";

// Demo config comes from Vite env (see .env.example). These are inlined into the
// client bundle at build time — this is a demo gate, not real authentication.
const STREAMLIT_URL = import.meta.env.VITE_STREAMLIT_URL || "http://localhost:8501";
const APP_USERNAME = import.meta.env.VITE_APP_USERNAME || "admin";
const APP_PASSWORD = import.meta.env.VITE_APP_PASSWORD || "insurclaim2026";
const APP_LOGIN_TOKEN = import.meta.env.VITE_APP_LOGIN_TOKEN || "insurclaim-demo-2026";

export default function LoginCard() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setError("");
    if (username.trim() === APP_USERNAME && password === APP_PASSWORD) {
      setLoading(true);
      // Hand off to the Streamlit dashboard with a shared token so the user is
      // not asked to sign in a second time.
      const url = `${STREAMLIT_URL.replace(/\/$/, "")}/?token=${encodeURIComponent(APP_LOGIN_TOKEN)}`;
      window.location.href = url;
    } else {
      setError("Invalid username or password.");
    }
  };

  return (
    <div className="glass login" id="signin">
      <h3>🔐 Sign in</h3>
      <p className="sub">Open the investigator dashboard.</p>
      <form onSubmit={handleSubmit} noValidate>
        <div className="field">
          <label htmlFor="username">Username</label>
          <input
            id="username"
            type="text"
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="admin"
          />
        </div>
        <div className="field">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
          />
        </div>
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? "Opening dashboard…" : "Sign in →"}
        </button>
        {error && <p className="error">⚠️ {error}</p>}
      </form>
      <p className="hint">
        Demo access — synthetic &amp; public data only, no real customer information.
        Try <code>admin</code> / <code>insurclaim2026</code>.
      </p>
    </div>
  );
}
