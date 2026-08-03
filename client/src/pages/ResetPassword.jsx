import { useState, useEffect, useRef } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { Lock, ShieldCheck, ArrowLeft, RefreshCw, Mail } from "lucide-react";
import axios from "axios";

const API_BASE = `${import.meta.env.VITE_API_URL || "http://localhost:5000"}/api/auth`;

const ResetPassword = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const email = location.state?.email || "";
  const [step, setStep] = useState("otp"); // "otp" or "password"
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [verifiedOtp, setVerifiedOtp] = useState("");
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [cooldown, setCooldown] = useState(60);

  const inputRefs = useRef([]);

  useEffect(() => {
    if (!email) {
      navigate("/forgot-password");
    }
  }, [email, navigate]);

  useEffect(() => {
    if (cooldown > 0) {
      const timer = setTimeout(() => setCooldown(cooldown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [cooldown]);

  // ─── OTP input handlers ────────────────────────────────────────────────────

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

  // ─── Verify OTP ────────────────────────────────────────────────────────────

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    const code = otp.join("");
    if (code.length !== 6) {
      setError("Please enter the complete 6-digit code.");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");

    try {
      await axios.post(`${API_BASE}/verify-reset-otp`, { email, otp: code });
      setVerifiedOtp(code);
      setStep("password");
      setMessage("Code verified! Set your new password below.");
    } catch (err) {
      setError(err.response?.data?.message || "Invalid or expired code. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // ─── Reset Password ───────────────────────────────────────────────────────

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");

    if (password.length < 6) {
      return setError("Password must be at least 6 characters.");
    }
    if (password !== confirmPassword) {
      return setError("Passwords do not match.");
    }

    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/reset-password`, {
        email,
        otp: verifiedOtp,
        password,
      });
      setMessage(res.data.message);
      setTimeout(() => navigate("/login"), 3000);
    } catch (err) {
      setError(err.response?.data?.message || "Error resetting password. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // ─── Resend OTP ────────────────────────────────────────────────────────────

  const handleResend = async () => {
    if (cooldown > 0 || resending) return;
    setResending(true);
    setError("");
    setMessage("");

    try {
      const res = await axios.post(`${API_BASE}/resend-reset-otp`, { email });
      setMessage(res.data.message || "A new reset code has been sent to your email.");
      setCooldown(60);
      setOtp(["", "", "", "", "", ""]);
      setStep("otp");
      setVerifiedOtp("");
    } catch (err) {
      setError(err.response?.data?.message || "Failed to resend code. Please try again.");
    } finally {
      setResending(false);
    }
  };

  // ─── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen flex items-center justify-center pt-20 px-4">
      <div className="w-full max-w-md relative z-10 glass-card p-8 rounded-3xl animate-glow">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-amber-500/10 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-amber-500/20 shadow-[0_0_20px_rgba(245,158,11,0.2)]">
            <ShieldCheck className="text-amber-400" size={32} />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            {step === "otp" ? "Verify Reset Code" : "Create New Password"}
          </h1>
          <p className="text-sm text-gray-400 mt-2 flex items-center justify-center gap-1">
            <Mail size={14} className="text-gray-500" />
            Code sent to <span className="text-white font-medium">{email}</span>
          </p>
        </div>

        {/* Step 1: OTP verification */}
        {step === "otp" && (
          <form onSubmit={handleVerifyOtp} className="space-y-6">
            <div className="flex justify-between gap-2" onPaste={handlePaste}>
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
                  className="w-12 h-14 text-center text-xl font-bold bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500 transition-all"
                  autoFocus={i === 0}
                />
              ))}
            </div>

            {error && <div className="text-sm text-red-400 bg-red-500/10 p-3 rounded-lg border border-red-500/20 text-center">{error}</div>}
            {message && <div className="text-sm text-green-400 bg-green-500/10 p-3 rounded-lg border border-green-500/20 text-center">{message}</div>}

            <button
              type="submit"
              disabled={loading || otp.join("").length !== 6}
              className="w-full py-3.5 bg-amber-600 hover:bg-amber-700 text-white font-bold rounded-xl transition-all shadow-[0_0_20px_rgba(245,158,11,0.3)] disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed"
            >
              {loading ? "Verifying..." : "Verify Code"}
            </button>
          </form>
        )}

        {/* Step 2: New password */}
        {step === "password" && (
          <form onSubmit={handleResetPassword} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">New Password</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Lock size={18} className="text-gray-500" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-11 pr-4 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                  placeholder="••••••••"
                  minLength={6}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Confirm Password</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Lock size={18} className="text-gray-500" />
                </div>
                <input
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-11 pr-4 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                  placeholder="••••••••"
                  minLength={6}
                />
              </div>
            </div>

            {error && <div className="text-sm text-red-400 bg-red-500/10 p-3 rounded-lg border border-red-500/20">{error}</div>}
            {message && <div className="text-sm text-green-400 bg-green-500/10 p-3 rounded-lg border border-green-500/20">{message}</div>}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-amber-600 hover:bg-amber-700 text-white font-bold rounded-xl transition-all shadow-[0_0_20px_rgba(245,158,11,0.3)] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Resetting..." : "Reset Password"}
            </button>
          </form>
        )}

        {/* Footer */}
        <div className="mt-6 pt-6 border-t border-white/10 flex items-center justify-between text-sm">
          <Link to="/forgot-password" className="text-gray-400 hover:text-white flex items-center gap-1 transition-colors">
            <ArrowLeft size={16} /> Try different email
          </Link>

          {step === "otp" && (
            <button
              onClick={handleResend}
              disabled={cooldown > 0 || resending}
              className="text-amber-400 hover:text-amber-300 disabled:text-gray-500 font-medium flex items-center gap-1 transition-colors cursor-pointer disabled:cursor-not-allowed"
            >
              <RefreshCw size={14} className={resending ? "animate-spin" : ""} />
              {cooldown > 0 ? `Resend in ${cooldown}s` : "Resend Code"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResetPassword;
