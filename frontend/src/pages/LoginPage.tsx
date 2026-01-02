import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      minHeight: "100vh",
      backgroundColor: "var(--bg-main)",
    }}>
      <div style={{
        width: "100%",
        maxWidth: "400px",
        padding: "2rem",
      }}>
        <div style={{
          textAlign: "center",
          marginBottom: "2rem",
        }}>
          <h1 style={{ marginBottom: "0.5rem" }}>EventSec Enterprise</h1>
          <p style={{ color: "var(--text-muted)" }}>Sign in to continue</p>
        </div>

        <form onSubmit={handleSubmit} className="stack-vertical">
          {error && (
            <div style={{
              padding: "0.75rem",
              backgroundColor: "var(--alpha-239-68-68-0_1)",
              border: "1px solid var(--danger)",
              borderRadius: "4px",
              color: "var(--danger)",
              marginBottom: "1rem",
            }}>
              {error}
            </div>
          )}

          <div className="field-group">
            <label htmlFor="email" className="field-label">
              Email
            </label>
            <input
              id="email"
              type="email"
              className="field-control"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>

          <div className="field-group">
            <label htmlFor="password" className="field-label">
              Password
            </label>
            <input
              id="password"
              type="password"
              className="field-control"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            className="btn"
            disabled={loading}
            style={{ width: "100%" }}
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>

          <div style={{
            marginTop: "1rem",
            padding: "1rem",
            backgroundColor: "var(--bg-elevated-soft)",
            borderRadius: "4px",
            fontSize: "var(--text-sm)",
            color: "var(--text-muted)",
          }}>
            <strong>Demo credentials:</strong><br />
            Admin: admin@example.com / Admin123!<br />
            Analyst: analyst@example.com / Analyst123!
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;

