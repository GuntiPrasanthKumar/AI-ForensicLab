import { useState, useEffect } from "react";
import axios from "axios";
import { Upload, FileText, Video, ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import HistoryTable from "../components/HistoryTable";

const API_BASE = "http://localhost:5000/api";

const Dashboard = () => {
  const [history, setHistory] = useState([]);
  const [serverStatus, setServerStatus] = useState("checking");

  const fetchHistory = async () => {
    try {
      const res = await axios.get(`${API_BASE}/history`);
      setHistory(res.data);
      setServerStatus("online");
    } catch (err) {
      if (err.response?.status === 401) {
        // Handled globally or token expired
      } else {
        setServerStatus("offline");
      }
    }
  };

  useEffect(() => {
    fetchHistory();
    const interval = setInterval(fetchHistory, 10000);
    return () => clearInterval(interval);
  }, []);

  const deleteHistoryItem = async (id) => {
    try {
      await axios.delete(`${API_BASE}/history/${id}`);
      setHistory(history.filter(item => item._id !== id));
    } catch (err) {
      console.error("Delete failed");
    }
  };

  return (
    <div className="pt-24 pb-12 max-w-6xl mx-auto px-4 md:px-8 min-h-screen">
      <div className="mb-12">
        <h1 className="text-3xl font-bold text-white tracking-tight">Forensic Control Hub</h1>
        <div className="flex items-center gap-2 mt-2">
          <div className={`w-2 h-2 rounded-full ${serverStatus === 'online' ? 'bg-green-500 animate-pulse' : serverStatus === 'offline' ? 'bg-red-500' : 'bg-yellow-500'}`} />
          <span className="text-xs text-gray-500 uppercase tracking-widest">{serverStatus} Engine</span>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-6 mb-12">
        <Link to="/app/image" className="glass-card p-8 rounded-3xl hover:border-blue-500/50 transition-all group relative overflow-hidden block">
          <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 blur-3xl rounded-full" />
          <Upload className="text-blue-500 mb-6 group-hover:scale-110 transition-transform" size={40} />
          <h2 className="text-xl font-bold text-white mb-2">Image Lab</h2>
          <p className="text-sm text-gray-400 mb-6">Scan EXIF data and structural noise for diffusion artifacts.</p>
          <div className="flex items-center text-blue-400 text-sm font-medium">
            Enter Lab <ArrowRight size={16} className="ml-2 group-hover:translate-x-1 transition-transform" />
          </div>
        </Link>

        <Link to="/app/video" className="glass-card p-8 rounded-3xl hover:border-red-500/50 transition-all group relative overflow-hidden block">
          <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/10 blur-3xl rounded-full" />
          <Video className="text-red-500 mb-6 group-hover:scale-110 transition-transform" size={40} />
          <h2 className="text-xl font-bold text-white mb-2">Video Lab</h2>
          <p className="text-sm text-gray-400 mb-6">Analyze deepfake bounding-box aspect ratio distortions.</p>
          <div className="flex items-center text-red-400 text-sm font-medium">
            Enter Lab <ArrowRight size={16} className="ml-2 group-hover:translate-x-1 transition-transform" />
          </div>
        </Link>

        <Link to="/app/text" className="glass-card p-8 rounded-3xl hover:border-purple-500/50 transition-all group relative overflow-hidden block">
          <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/10 blur-3xl rounded-full" />
          <FileText className="text-purple-500 mb-6 group-hover:scale-110 transition-transform" size={40} />
          <h2 className="text-xl font-bold text-white mb-2">Text Lab</h2>
          <p className="text-sm text-gray-400 mb-6">Detect LLM linguistics, perplexity, and burstiness.</p>
          <div className="flex items-center text-purple-400 text-sm font-medium">
            Enter Lab <ArrowRight size={16} className="ml-2 group-hover:translate-x-1 transition-transform" />
          </div>
        </Link>
      </div>

      <HistoryTable history={history} deleteHistoryItem={deleteHistoryItem} />
    </div>
  );
};

export default Dashboard;
