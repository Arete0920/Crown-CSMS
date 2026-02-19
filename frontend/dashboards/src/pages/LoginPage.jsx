import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { jwtLogin, setSelectedSchoolId } from "../utils/authClient.js";

/**
 * LoginPage
 * Simple manual login form (fallback for when auto-login disabled/fails)
 */
export function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("demo");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const apiBase = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
      
      // Use the existing jwtLogin helper (hits /api/v1/auth/token/)
      await jwtLogin({ username, password, apiBase });
      
      // Set default school ID
      const schoolId = import.meta.env.VITE_DEMO_SCHOOL_ID || "19801b59-8c05-4c84-9312-5d792e4e839d";
      setSelectedSchoolId(schoolId);

      // Navigate to home
      navigate("/");
    } catch (err) {
      setError(err.message);
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
      backgroundColor: "#f5f5f5",
      fontFamily: "system-ui, sans-serif"
    }}>
      <div style={{ 
        backgroundColor: "white", 
        padding: "2rem", 
        borderRadius: "8px",
        boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
        width: "100%",
        maxWidth: "400px"
      }}>
        <h1 style={{ marginTop: 0 }}>Crown Login</h1>
        
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: "1rem" }}>
            <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: 500 }}>
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              style={{ 
                width: "100%", 
                padding: "0.5rem", 
                border: "1px solid #ccc",
                borderRadius: "4px",
                fontSize: "1rem"
              }}
            />
          </div>

          <div style={{ marginBottom: "1rem" }}>
            <label style={{ display: "block", marginBottom: "0.5rem", fontWeight: 500 }}>
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{ 
                width: "100%", 
                padding: "0.5rem", 
                border: "1px solid #ccc",
                borderRadius: "4px",
                fontSize: "1rem"
              }}
            />
          </div>

          {error && (
            <div style={{ 
              padding: "0.75rem", 
              marginBottom: "1rem",
              backgroundColor: "#fee",
              color: "#c00",
              borderRadius: "4px",
              fontSize: "0.9rem"
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "0.75rem",
              backgroundColor: loading ? "#ccc" : "#007bff",
              color: "white",
              border: "none",
              borderRadius: "4px",
              fontSize: "1rem",
              fontWeight: 500,
              cursor: loading ? "not-allowed" : "pointer"
            }}
          >
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>

        <div style={{ marginTop: "1rem", fontSize: "0.9rem", color: "#666" }}>
          <strong>Demo credentials:</strong><br />
          Username: demo<br />
          Password: DemoPass!232
        </div>
      </div>
    </div>
  );
}
