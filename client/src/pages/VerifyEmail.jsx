import { useEffect, useState, useContext } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { AuthContext } from "../context/AuthContext";
import axios from "axios";

const VerifyEmail = () => {
  const { token } = useParams();
  const [status, setStatus] = useState("Verifying your email...");
  const navigate = useNavigate();
  const { fetchUser } = useContext(AuthContext);

  useEffect(() => {
    const verify = async () => {
      try {
        const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:5000";
        await axios.post(`${API_BASE}/api/auth/verify-email/${token}`);
        setStatus("Email verified successfully! Redirecting...");
        await fetchUser();
        setTimeout(() => navigate("/app"), 2000);
      } catch (err) {
        setStatus(err.response?.data?.message || "Verification failed. Link may be invalid or expired.");
      }
    };
    verify();
  }, [token, navigate, fetchUser]);

  return (
    <div className="min-h-screen flex items-center justify-center pt-20 px-4">
      <div className="glass-card p-8 rounded-3xl text-center max-w-md w-full">
        <h2 className="text-2xl font-bold text-white mb-4">Email Verification</h2>
        <p className="text-gray-300">{status}</p>
      </div>
    </div>
  );
};

export default VerifyEmail;
