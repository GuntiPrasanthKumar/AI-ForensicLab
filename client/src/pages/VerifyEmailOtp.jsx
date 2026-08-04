import { useState, useContext, useEffect, useRef } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import axios from "axios";
import { AuthContext } from "../context/AuthContext";
import { ShieldCheck, ArrowLeft, RefreshCw, Mail } from "lucide-react";

const API_BASE = `${import.meta.env.VITE_API_URL}/api`;

const VerifyEmailOtp = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { fetchUser } = useContext(AuthContext);

  const email = location.state?.email || "";
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [cooldown, setCooldown] = useState(60);

  const inputRefs = useRef([]);

  useEffect(() => {
    if (!email) {
      navigate("/register");
    }
  }, [email, navigate]);

  useEffect(() => {
    if (cooldown > 0) {
      const timer = setTimeout(() => setCooldown(cooldown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [cooldown]);

  const handleChange = (index, value) => {
    if (!/^\d*$/.test(value)) return;
    const newOtp = [...otp];
    newOtp[index] = value.slice(-1);
    setOtp(newOtp);

    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData("text").trim();
    if (!/^\d{6}$/.test(pastedData)) return;
    const digits = pastedData.split("");
    setOtp(digits);
    inputRefs.current[5]?.focus();
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    const code = otp.join("");
    if (code.length !== 6) {
      setError("Please enter the complete 6-digit verification code.");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");

    try {
      await axios.post(
        `${API_BASE}/auth/verify-otp`,
        { email, otp: code },
        { withCredentials: true }
      );
      await fetchUser();
      navigate("/app");
    } catch (err) {
      setError(err.response?.data?.message || "Verification failed. Please check your code.");
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (cooldown > 0 || resending) return;
    setResending(true);
    setError("");
    setMessage("");

    try {
      const res = await axios.post(`${API_BASE}/auth/resend-otp`, { email });
      setMessage(res.data.message || "A new 6-digit code has been sent to your email.");
      setCooldown(60);
    } catch (err) {
      setError(err.response?.data?.message || "Failed to resend code. Please try again.");
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="pt-24 pb-12 min-h-screen w-full max-w-full overflow-x-hidden flex items-center justify-center px-4 relative">
      <div className="w-full max-w-md glass-card p-5 sm:p-8 rounded-3xl animate-glow">
        <div className="text-center mb-6 sm:mb-8">
          <div className="w-14 h-14 sm:w-16 sm:h-16 bg-blue-500/10 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-blue-500/20 shadow-[0_0_20px_rgba(59,130,246,0.2)]">
            <ShieldCheck className="text-blue-400" size={28} />
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">Verify Your Email</h1>
          <p className="text-xs sm:text-sm text-gray-400 mt-2 flex items-center justify-center gap-1 flex-wrap">
            <Mail size={14} className="text-gray-500 shrink-0" />
            Code sent to <span className="text-white font-medium truncate max-w-[200px] inline-block">{email}</span>
          </p>
        </div>

        <form onSubmit={handleVerify} className="space-y-5 sm:space-y-6">
          <div className="flex justify-between gap-1.5 sm:gap-2 w-full" onPaste={handlePaste}>
            {otp.map((digit, i) => (
              <input
                key={i}
                ref={(el) => (inputRefs.current[i] = el)}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleChange(i, e.target.value)}
                onKeyDown={(e) => handleKeyDown(i, e)}
                className="w-9 sm:w-12 h-11 sm:h-14 text-center text-lg sm:text-xl font-bold bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all min-w-0 shrink"
                autoFocus={i === 0}
              />
            ))}
          </div>

          {error && <div className="text-xs sm:text-sm text-red-400 bg-red-500/10 p-3 rounded-lg border border-red-500/20 text-center">{error}</div>}
          {message && <div className="text-xs sm:text-sm text-green-400 bg-green-500/10 p-3 rounded-lg border border-green-500/20 text-center">{message}</div>}

          <button
            type="submit"
            disabled={loading || otp.join("").length !== 6}
            className="w-full py-3 sm:py-3.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm sm:text-base rounded-xl transition-all shadow-[0_0_20px_rgba(37,99,235,0.3)] disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed"
          >
            {loading ? "Verifying..." : "Verify & Continue"}
          </button>
        </form>

        <div className="mt-6 pt-6 border-t border-white/10 flex items-center justify-between text-xs sm:text-sm">
          <Link to="/register" className="text-gray-400 hover:text-white flex items-center gap-1 transition-colors">
            <ArrowLeft size={16} /> Back to Register
          </Link>

          <button
            onClick={handleResend}
            disabled={cooldown > 0 || resending}
            className="text-blue-400 hover:text-blue-300 disabled:text-gray-500 font-medium flex items-center gap-1 transition-colors cursor-pointer disabled:cursor-not-allowed"
          >
            <RefreshCw size={14} className={resending ? "animate-spin" : ""} />
            {cooldown > 0 ? `Resend code in ${cooldown}s` : "Resend Code"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default VerifyEmailOtp;
