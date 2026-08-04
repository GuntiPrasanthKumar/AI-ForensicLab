import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Mail, ArrowLeft } from "lucide-react";
import axios from "axios";

const ForgotPassword = () => {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");

    try {
      const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:5000";
      const res = await axios.post(`${API_BASE}/api/auth/forgot-password`, { email });
      
      if (res.data.sent) {
        // Navigate to the reset password page with OTP input
        navigate("/reset-password", { state: { email } });
      } else {
        setMessage(res.data.message);
      }
    } catch (err) {
      if (!err.response) {
        setError("Cannot reach the server. Please check your connection and try again.");
      } else {
        setError(err.response?.data?.message || "An error occurred. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full max-w-full overflow-x-hidden flex items-center justify-center pt-24 pb-12 px-4 relative">
      <div className="w-full max-w-md relative z-10 glass-card p-5 sm:p-8 rounded-3xl">
        <Link to="/login" className="flex items-center text-xs sm:text-sm text-blue-400 hover:text-blue-300 mb-6 transition-colors">
          <ArrowLeft size={16} className="mr-2" /> Back to Login
        </Link>
        <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">Reset Password</h1>
        <p className="text-xs sm:text-sm text-gray-400 mb-6">Enter your email and we'll send you a 6-digit code to reset your password.</p>

        <form onSubmit={handleSubmit} className="space-y-5 sm:space-y-6">
          <div>
            <label className="block text-xs sm:text-sm font-medium text-gray-300 mb-2">Email Address</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 sm:pl-4 flex items-center pointer-events-none">
                <Mail size={18} className="text-gray-500" />
              </div>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 sm:py-3 pl-10 sm:pl-11 pr-4 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                placeholder="you@example.com"
              />
            </div>
          </div>

          {error && <div className="text-xs sm:text-sm text-red-400 bg-red-500/10 p-3 rounded-lg border border-red-500/20">{error}</div>}
          {message && <div className="text-xs sm:text-sm text-blue-400 bg-blue-500/10 p-3 rounded-lg border border-blue-500/20">{message}</div>}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm sm:text-base rounded-xl transition-all shadow-[0_0_20px_rgba(37,99,235,0.3)] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Sending..." : "Send Reset Code"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ForgotPassword;
