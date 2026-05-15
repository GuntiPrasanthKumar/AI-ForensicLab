import React from 'react';
import { motion } from "framer-motion";

const TextInput = ({ text, setText, onAnalyze, loading, disabled }) => {
  return (
    <div className="w-full space-y-4">
      <div className="relative rounded-2xl overflow-hidden group">
        <textarea
          className={`w-full h-48 p-4 bg-white/5 border border-white/10 rounded-2xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all resize-none relative z-10 ${loading ? 'opacity-50 blur-[1px]' : ''}`}
          placeholder="Paste your text here (minimum 5 words)..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          disabled={loading || disabled}
        />
        {loading && (
          <div className="absolute inset-0 z-20 pointer-events-none rounded-2xl overflow-hidden">
            <motion.div 
              animate={{ top: ["-5%", "105%"] }}
              transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
              className="absolute left-0 right-0 h-1 bg-purple-500 shadow-[0_0_20px_rgba(168,85,247,1)]"
            />
            <div className="absolute inset-0 bg-purple-500/10 animate-pulse mix-blend-overlay" />
          </div>
        )}
      </div>
      <button
        onClick={onAnalyze}
        disabled={loading || !text.trim() || disabled}
        className="w-full py-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold rounded-2xl shadow-lg shadow-blue-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? "Analyzing Patterns..." : "Analyze Text"}
      </button>
    </div>
  );
};

export default TextInput;
