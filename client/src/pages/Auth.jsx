import { useState, useContext, useEffect } from "react";
import { AuthContext } from "../context/AuthContext";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { UserPlus, LogIn, Mail, Lock, User as UserIcon } from "lucide-react";
import { Turnstile } from "@marsidev/react-turnstile";
import axios from "axios";

const Auth = () => {
  const location = useLocation();
  const [isLogin, setIsLogin] = useState(location.pathname === "/login");
  const [formData, setFormData] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [loading, setLoading] = useState(false);
  const [turnstileToken, setTurnstileToken] = useState("");
  
  const { fetchUser, user } = useContext(AuthContext);
  const navigate = useNavigate();

  useEffect(() => {
    setIsLogin(location.pathname === "/login");
    setError("");
    setSuccessMsg("");
    setTurnstileToken("");
  }, [location.pathname]);

  useEffect(() => {
    if (user) navigate("/app");
  }, [user, navigate]);

  const API_BASE = import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL}/api/auth` : "http://localhost:5000/api/auth";

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccessMsg("");
    setLoading(true);

    if (!turnstileToken && import.meta.env.PROD) {
      setError("Please complete the CAPTCHA");
      setLoading(false);
      return;
    }

    try {
      const endpoint = isLogin ? "/login" : "/register";
      const payload = isLogin 
        ? { email: formData.email, password: formData.password, turnstileToken } 
        : { ...formData, turnstileToken };
        
      const res = await axios.post(`${API_BASE}${endpoint}`, payload, {
        withCredentials: true,
      });
      
      if (!isLogin) {
        if (res.data?.requiresEmailVerification) {
          navigate("/verify-email-otp", { state: { email: res.data.email || formData.email } });
          return;
        }
      }
      await fetchUser();
      navigate("/app");
    } catch (err) {
      const data = err.response?.data;
      if (data?.requiresEmailVerification) {
        navigate("/verify-email-otp", { state: { email: data.email || formData.email } });
        return;
      }
      if (!err.response) {
        setError(
          "Cannot reach the server. Check your connection, or wait a moment if the API is waking up (Render free tier), then try again."
        );
        return;
      }
      setError(data?.message || "Authentication failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full max-w-full overflow-x-hidden flex items-center justify-center pt-24 pb-12 px-4 relative">
      <div className="absolute inset-0 overflow-hidden pointer-events-none flex items-center justify-center z-0">
        <div className="w-[300px] h-[300px] sm:w-[500px] sm:h-[500px] md:w-[700px] md:h-[700px] bg-blue-600/20 blur-[100px] sm:blur-[120px] rounded-full" />
      </div>

      <div className="w-full max-w-md relative z-10 mx-auto">
        <div className="text-center mb-8 sm:mb-10">
          <div className="mx-auto w-14 h-14 sm:w-16 sm:h-16 bg-blue-600 rounded-2xl shadow-[0_0_40px_rgba(37,99,235,0.5)] flex items-center justify-center mb-4 sm:mb-6">
            {isLogin ? <LogIn size={28} className="text-white" /> : <UserPlus size={28} className="text-white" />}
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">{isLogin ? "Welcome Back" : "Create Account"}</h1>
          <p className="text-xs sm:text-sm text-gray-400">
            {isLogin ? "Enter your credentials to access the Forensic Lab." : "Join the fight against synthetic media."}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="glass-card p-5 sm:p-8 rounded-3xl space-y-5 sm:space-y-6 w-full">
          {!isLogin && (
            <div>
              <label className="block text-xs sm:text-sm font-medium text-gray-300 mb-1.5 sm:mb-2">Full Name</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 sm:pl-4 flex items-center pointer-events-none">
                  <UserIcon size={18} className="text-gray-500" />
                </div>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 sm:py-3 pl-10 sm:pl-11 pr-4 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
                  placeholder="John Doe"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs sm:text-sm font-medium text-gray-300 mb-1.5 sm:mb-2">Email Address</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 sm:pl-4 flex items-center pointer-events-none">
                <Mail size={18} className="text-gray-500" />
              </div>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 sm:py-3 pl-10 sm:pl-11 pr-4 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
                placeholder="you@example.com"
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between items-center mb-1.5 sm:mb-2">
              <label className="block text-xs sm:text-sm font-medium text-gray-300">Password</label>
              {isLogin && (
                <Link to="/forgot-password" className="text-xs sm:text-sm text-blue-400 hover:text-blue-300">
                  Forgot Password?
                </Link>
              )}
            </div>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 sm:pl-4 flex items-center pointer-events-none">
                <Lock size={18} className="text-gray-500" />
              </div>
              <input
                type="password"
                required
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 sm:py-3 pl-10 sm:pl-11 pr-4 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all"
                placeholder="••••••••"
              />
            </div>
          </div>

          <div className="flex justify-center w-full overflow-x-auto">
            <Turnstile
              key={isLogin ? 'login' : 'register'}
              siteKey={import.meta.env.VITE_TURNSTILE_SITE_KEY || "1x00000000000000000000AA"}
              onSuccess={(token) => setTurnstileToken(token)}
              onError={() => setError("CAPTCHA Error. Please try again.")}
              options={{ theme: 'dark' }}
            />
          </div>

          {error && <div className="text-xs sm:text-sm text-red-400 bg-red-500/10 p-3 rounded-lg">{error}</div>}
          {successMsg && <div className="text-xs sm:text-sm text-green-400 bg-green-500/10 p-3 rounded-lg">{successMsg}</div>}

          <button
            type="submit"
            disabled={loading || !turnstileToken}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm sm:text-base rounded-xl transition-all shadow-[0_0_20px_rgba(37,99,235,0.3)] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Processing..." : !turnstileToken ? "Waiting for CAPTCHA..." : isLogin ? "Sign In" : "Create Account"}
          </button>

          <p className="text-center text-xs sm:text-sm text-gray-400">
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <Link to={isLogin ? "/register" : "/login"} className="text-blue-400 hover:text-blue-300 font-medium">
              {isLogin ? "Sign Up" : "Sign In"}
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
};

export default Auth;
