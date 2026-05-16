import { useState } from "react";
import axios from "axios";
import { FileText, AlertCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import ResultDisplay from "../components/ResultDisplay";
import TextInput from "../components/TextInput";

const API_BASE = import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL}/api` : "http://localhost:5000/api";

const TextLab = () => {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleAnalyze = async () => {
    if (!text || text.split(" ").length < 5) {
      setError("Please enter at least 5 words.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const res = await axios.post(`${API_BASE}/detect-text`, { text });
      setResult({
        aiProbability: 0,
        humanProbability: 0,
        morphProbability: 0,
        confidence: "Low",
        explanation: "Analysis complete.",
        ...res.data
      });
    } catch (err) {
      setError(err.response?.data?.message || "Analysis failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="pt-24 pb-12 max-w-6xl mx-auto px-4 md:px-8 min-h-screen">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
          <FileText className="text-purple-500" /> Linguistics Lab
        </h1>
        <p className="text-gray-400 mt-2">Paste text or essays to identify LLM burstiness and predictable perplexity.</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        <section className="space-y-6">
          <div className="glass-card p-6 rounded-3xl animate-glow">
            <TextInput text={text} setText={setText} onAnalyze={handleAnalyze} loading={loading} />
            
            <div className="flex gap-4 mt-6">
              <button 
                onClick={() => { setText(""); setResult(null); }}
                className="flex-1 py-4 bg-white/5 text-gray-400 font-medium rounded-2xl hover:bg-white/10 transition-all"
              >
                Clear
              </button>
              <button 
                onClick={handleAnalyze}
                disabled={loading || !text}
                className="flex-[2] py-4 bg-gradient-to-r from-purple-600 to-fuchsia-600 text-white font-bold rounded-2xl disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-purple-500/20"
              >
                {loading ? `Analyzing Linguistics...` : `Analyze Text`}
              </button>
            </div>

            {error && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3 text-red-400"
              >
                <AlertCircle size={20} />
                <p className="text-sm">{error}</p>
              </motion.div>
            )}
          </div>
        </section>

        <section>
          <AnimatePresence mode="wait">
            {result ? (
              <ResultDisplay key="result" result={result} />
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-gray-500 border-2 border-dashed border-white/5 rounded-3xl p-12 min-h-[400px]">
                <FileText size={64} className="mb-4 opacity-20" />
                <p className="text-center text-lg">Paste some text to see the linguistic breakdown.</p>
              </div>
            )}
          </AnimatePresence>
        </section>
      </div>
    </div>
  );
};

export default TextLab;
