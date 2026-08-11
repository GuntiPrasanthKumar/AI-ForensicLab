/**
 * TextLab Page Component
 * Evaluates text samples for AI generation and perplexity indicators.
 */
import { useState, useRef, useEffect } from "react";
import axios from "axios";
import { FileText, AlertCircle, RefreshCw } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import ResultDisplay from "../components/ResultDisplay";
import TextInput from "../components/TextInput";

const API_BASE = `${import.meta.env.VITE_API_URL}/api`;

const TextLab = () => {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const abortControllerRef = useRef(null);

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const handleAnalyze = async () => {
    if (!text || text.split(" ").filter(Boolean).length < 5) {
      setError("Please enter at least 5 words for accurate linguistic analysis.");
      return;
    }

    // Cancel any inflight request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const res = await axios.post(
        `${API_BASE}/detect-text`, 
        { text },
        { signal: abortControllerRef.current.signal }
      );

      setResult({
        aiProbability: 0,
        humanProbability: 0,
        morphProbability: 0,
        confidence: "Low",
        explanation: "Analysis complete.",
        ...res.data
      });
    } catch (err) {
      if (axios.isCancel(err) || err.name === "CanceledError") {
        console.log("[TextLab] Request aborted by user/new request.");
        return;
      }
      console.error("[TextLab] Analysis Error:", err);
      const userMsg = err.response?.data?.message || "Linguistic service temporarily busy. Please retry shortly.";
      setError(userMsg);
    } finally {
      setLoading(false);
    }
  };

  const sampleAiText = "In today's fast-paced digital era, artificial intelligence has emerged as a paramount paradigm shift. Furthermore, it is crucial to recognize that machine learning models leverage complex neural architectures to streamline human productivity.";
  const sampleHumanText = "I went to the store yesterday and ran into an old friend from high school. We ended up chatting for like an hour near the coffee section, totally forgetting what I originally came to buy!";

  return (
    <div className="pt-24 pb-12 max-w-6xl mx-auto px-4 md:px-8 min-h-screen w-full max-w-full overflow-x-hidden">
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight flex items-center gap-3">
          <FileText className="text-purple-500 shrink-0" /> Linguistics Lab
        </h1>
        <p className="text-xs sm:text-sm text-gray-400 mt-2">Paste text or essays to identify LLM burstiness and predictable perplexity.</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        <section className="space-y-6">
          <div className="glass-card p-4 sm:p-6 rounded-3xl animate-glow">
            <div className="flex flex-wrap items-center gap-2 mb-4">
              <span className="text-xs text-gray-400">Load sample:</span>
              <button 
                disabled={loading}
                onClick={() => { setText(sampleAiText); setError(""); }} 
                className="text-xs px-3 py-1 bg-purple-500/10 text-purple-300 rounded-full border border-purple-500/20 hover:bg-purple-500/20 transition-all cursor-pointer disabled:opacity-50"
              >
                AI Prompt Sample
              </button>
              <button 
                disabled={loading}
                onClick={() => { setText(sampleHumanText); setError(""); }} 
                className="text-xs px-3 py-1 bg-blue-500/10 text-blue-300 rounded-full border border-blue-500/20 hover:bg-blue-500/20 transition-all cursor-pointer disabled:opacity-50"
              >
                Human Sample
              </button>
            </div>
            
            <TextInput text={text} setText={setText} onAnalyze={handleAnalyze} loading={loading} />
            
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 mt-6">
              <button 
                disabled={loading}
                onClick={() => {
                  if (abortControllerRef.current) abortControllerRef.current.abort();
                  setText("");
                  setResult(null);
                  setError("");
                }}
                className="flex-1 py-4 bg-white/5 text-gray-400 font-medium rounded-2xl hover:bg-white/10 transition-all disabled:opacity-50 cursor-pointer"
              >
                Clear
              </button>
              <button 
                onClick={handleAnalyze}
                disabled={loading || !text.trim()}
                className="flex-[2] py-4 bg-gradient-to-r from-purple-600 to-fuchsia-600 text-white font-bold rounded-2xl disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-purple-500/20 flex items-center justify-center gap-2 cursor-pointer transition-all"
              >
                {loading ? (
                  <>
                    <RefreshCw className="animate-spin" size={18} />
                    Analyzing Linguistics...
                  </>
                ) : (
                  "Analyze Text"
                )}
              </button>
            </div>

            {error && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3 text-red-400"
              >
                <AlertCircle size={20} className="shrink-0" />
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
