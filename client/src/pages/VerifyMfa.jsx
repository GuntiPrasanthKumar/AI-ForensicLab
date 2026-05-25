import { useState, useContext } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AuthContext } from "../context/AuthContext";
import { Shield } from "lucide-react";
import axios from "axios";

const VerifyMfa = () => {
  const [token, setToken] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { fetchUser } = useContext(AuthContext);

  const tempToken = location.state?.tempToken;

  if (!tempToken) {
    navigate("/login");
    return null;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:5000";
      await axios.post(`${API_BASE}/api/auth/mfa/verify`, {
        token,
        isSetup: false,
        tempToken,
      });

      // Verification successful, cookie is set. Update context.
      await fetchUser();
      navigate("/app");
    } catch (err) {
      setError(err.response?.data?.message || "Invalid authentication code.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center pt-20 px-4">
      <div className="w-full max-w-md relative z-10 glass-card p-8 rounded-3xl text-center">
        <div className="mx-auto w-16 h-16 bg-blue-600 rounded-2xl shadow-[0_0_40px_rgba(37,99,235,0.5)] flex items-center justify-center mb-6">
          <Shield size={32} className="text-white" />
        </div>
        <h1 className="text-3xl font-bold text-white mb-2">Two-Factor Auth</h1>
        <p className="text-gray-400 mb-6">Enter the 6-digit code from your authenticator app.</p>

        <form onSubmit={handleSubmit} className="space-y-6">
          <input
            type="text"
            required
            maxLength="6"
            value={token}
            onChange={(e) => setToken(e.target.value.replace(/\D/g, ''))}
            className="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-4 text-white text-center text-2xl tracking-[0.5em] focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            placeholder="000000"
          />

          {error && <div className="text-sm text-red-400 bg-red-500/10 p-3 rounded-lg">{error}</div>}

          <button
            type="submit"
            disabled={loading || token.length !== 6}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl transition-all shadow-[0_0_20px_rgba(37,99,235,0.3)] disabled:opacity-50"
          >
            {loading ? "Verifying..." : "Verify"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default VerifyMfa;
