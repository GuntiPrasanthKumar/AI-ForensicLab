import { useState, useContext } from "react";
import { AuthContext } from "../context/AuthContext";
import { Shield } from "lucide-react";
import axios from "axios";

const MfaSetup = () => {
  const [qrCode, setQrCode] = useState("");
  const [secret, setSecret] = useState("");
  const [token, setToken] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const { user } = useContext(AuthContext);

  const startSetup = async () => {
    try {
      const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:5000";
      const res = await axios.post(`${API_BASE}/api/auth/mfa/setup`);
      setQrCode(res.data.qrCodeUrl);
      setSecret(res.data.secret);
    } catch (err) {
      setError("Failed to generate MFA token");
    }
  };

  const verifySetup = async (e) => {
    e.preventDefault();
    try {
      const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:5000";
      await axios.post(`${API_BASE}/api/auth/mfa/verify`, {
        token,
        isSetup: true
      });
      setMessage("MFA enabled successfully!");
      setQrCode("");
    } catch (err) {
      setError(err.response?.data?.message || "Invalid token");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center pt-20 px-4">
      <div className="w-full max-w-md relative z-10 glass-card p-8 rounded-3xl">
        <div className="mx-auto w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center mb-6">
          <Shield size={32} className="text-white" />
        </div>
        <h1 className="text-3xl font-bold text-white text-center mb-6">Setup 2FA</h1>
        
        {!qrCode && !message && (
          <button onClick={startSetup} className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl transition-all">
            Enable Authenticator App
          </button>
        )}

        {qrCode && (
          <div className="text-center space-y-4">
            <p className="text-gray-300">Scan this QR code in Google Authenticator or Authy:</p>
            <img src={qrCode} alt="MFA QR Code" className="mx-auto border-4 border-white rounded-lg" />
            <p className="text-xs text-gray-400">Secret: {secret}</p>

            <form onSubmit={verifySetup} className="mt-6">
              <input
                type="text"
                required
                maxLength="6"
                value={token}
                onChange={(e) => setToken(e.target.value.replace(/\D/g, ''))}
                className="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-4 text-white text-center tracking-[0.5em] mb-4"
                placeholder="000000"
              />
              <button type="submit" className="w-full py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded-xl transition-all">
                Verify & Enable
              </button>
            </form>
          </div>
        )}

        {message && <div className="mt-4 text-green-400 bg-green-500/10 p-4 rounded-xl text-center">{message}</div>}
        {error && <div className="mt-4 text-red-400 bg-red-500/10 p-4 rounded-xl text-center">{error}</div>}
      </div>
    </div>
  );
};

export default MfaSetup;
