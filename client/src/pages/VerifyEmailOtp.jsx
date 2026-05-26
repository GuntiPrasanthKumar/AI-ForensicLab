import { useState, useContext } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { AuthContext } from "../context/AuthContext";
import { Mail, ArrowLeft } from "lucide-react";
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api/auth`
  : "http://localhost:5000/api/auth";

const VerifyEmailOtp = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { fetchUser } = useContext(AuthContext);
  const [email, setEmail] = useState(location.state?.email || "");
  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);

  const handleVerify = async (e) => {
    e.preventDefault();
    setError("");
    setSuccessMsg("");
    setLoading(true);

    try {
      await axios.post(
        `${API_BASE}/verify-otp`,
        { email, otp },
        { withCredentials: true }
      );
      await fetchUser();
      setSuccessMsg("Email verified! Redirecting...");
      setTimeout(() => navigate("/app"), 800);
    } catch (err) {
      setError(err.response?.data?.message || "Verification failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (!email) {
      setError("Enter your email address first.");
      return;
    }
    setError("");
    setSuccessMsg("");
    setResending(true);

    try {
      const res = await axios.post(`${API_BASE}/resend-otp`, { email });
      setSuccessMsg(res.data.message || "A new code has been sent.");
    } catch (err) {
      setError(err.response?.data?.message || "Could not resend code.");
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center pt-20 px-4">
      <div className="w-full max-w-md relative z-10 glass-card p-8 rounded-3xl">
        <div className="text-center mb-8">
          <div className="mx-auto w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center mb-6">
            <Mail size={32} className="text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Verify Your Email</h1>
          <p className="text-gray-400">Enter the 6-digit code sent to your inbox.</p>
        </div>

        <form onSubmit={handleVerify} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-4 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Verification Code</label>
            <input
              type="text"
              required
              maxLength={6}
              inputMode="numeric"
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
              className="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-4 text-white text-center text-2xl tracking-[0.5em] focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              placeholder="000000"
            />
          </div>

          {error && <div className="text-sm text-red-400 bg-red-500/10 p-3 rounded-lg">{error}</div>}
          {successMsg && <div className="text-sm text-green-400 bg-green-500/10 p-3 rounded-lg">{successMsg}</div>}

          <button
            type="submit"
            disabled={loading || otp.length !== 6}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl disabled:opacity-50"
          >
            {loading ? "Verifying..." : "Verify Email"}
          </button>
        </form>

        <button
          type="button"
          onClick={handleResend}
          disabled={resending}
          className="w-full mt-4 py-2 text-sm text-blue-400 hover:text-blue-300 disabled:opacity-50"
        >
          {resending ? "Sending..." : "Resend code"}
        </button>

        <Link to="/login" className="flex items-center justify-center gap-2 mt-6 text-sm text-gray-400 hover:text-white">
          <ArrowLeft size={16} /> Back to sign in
        </Link>
      </div>
    </div>
  );
};

export default VerifyEmailOtp;
