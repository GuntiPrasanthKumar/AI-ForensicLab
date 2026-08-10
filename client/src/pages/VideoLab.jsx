/**
 * VideoLab Page Component
 * Provides video deepfake detection and frame analysis interface.
 */
import { useState, useRef, useEffect } from "react";
import axios from "axios";
import { Video, AlertCircle, RefreshCw } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import ResultDisplay from "../components/ResultDisplay";

const API_BASE = `${import.meta.env.VITE_API_URL}/api`;

const VideoLab = () => {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
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

  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && selectedFile.type.startsWith("video/")) {
      setFile(selectedFile);
      const videoUrl = URL.createObjectURL(selectedFile);
      setPreview(videoUrl);
      setResult(null);
      setError("");
    }
  };

  const handleAnalyze = async () => {
    if (!file || loading) return;

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await axios.post(
        `${API_BASE}/detect`, 
        formData,
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
        console.log("[VideoLab] Request aborted.");
        return;
      }
      console.error("[VideoLab] Error:", err);
      setError(err.response?.data?.message || "Deepfake video scan failed. Please try another file.");
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (loading) return;
    const droppedFile = e.dataTransfer?.files?.[0];
    if (droppedFile && droppedFile.type.startsWith("video/")) {
      setFile(droppedFile);
      setPreview(URL.createObjectURL(droppedFile));
      setResult(null);
      setError("");
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  return (
    <div className="pt-24 pb-12 max-w-6xl mx-auto px-4 md:px-8 min-h-screen w-full max-w-full overflow-x-hidden">
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight flex items-center gap-3">
          <Video className="text-red-500 shrink-0" /> Deepfake Video Lab
        </h1>
        <p className="text-xs sm:text-sm text-gray-400 mt-2">Upload footage to analyze facial morphing and edge-blending aspect ratios.</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        <section className="space-y-6">
          <div className="glass-card p-4 sm:p-6 rounded-3xl animate-glow">
            <div 
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              className="border-2 border-dashed border-white/10 rounded-2xl p-4 sm:p-8 text-center hover:border-red-500/50 transition-all cursor-pointer relative min-h-[250px] sm:min-h-[300px] flex flex-col items-center justify-center overflow-hidden group"
            >
              {preview ? (
                <>
                  <video src={preview} controls={!loading} className={`absolute inset-0 w-full h-full object-contain p-2 ${loading ? 'opacity-50 blur-[2px]' : 'opacity-100'} transition-all`} />
                  {loading && (
                    <div className="absolute inset-0 z-20 pointer-events-none overflow-hidden rounded-2xl">
                      <motion.div 
                        animate={{ top: ["-5%", "105%"] }}
                        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                        className="absolute left-0 right-0 h-1 bg-red-500 shadow-[0_0_20px_rgba(239,68,68,1)]"
                      />
                      <div className="absolute inset-0 bg-red-500/10 animate-pulse mix-blend-overlay" />
                    </div>
                  )}
                </>
              ) : (
                <>
                  <Video className="mx-auto mb-4 text-gray-500 shrink-0" size={40} />
                  <p className="text-gray-300 font-medium text-base sm:text-lg">Drop a video here</p>
                  <p className="text-gray-500 text-xs sm:text-sm mt-2">MP4, MOV supported. (Max 50MB)</p>
                </>
              )}
              <input 
                type="file" 
                accept="video/*"
                disabled={loading}
                onChange={handleFileChange}
                aria-label="Upload Video File"
                className="absolute inset-0 opacity-0 cursor-pointer disabled:cursor-not-allowed"
                title=""
              />
            </div>
            
            {file && <p className="text-xs text-gray-500 text-center truncate px-4 mt-4">{file.name}</p>}
            
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 mt-6">
              <button 
                disabled={loading}
                onClick={() => {
                  if (abortControllerRef.current) abortControllerRef.current.abort();
                  setFile(null);
                  setPreview(null);
                  setResult(null);
                  setError("");
                }}
                className="flex-1 py-4 bg-white/5 text-gray-400 font-medium rounded-2xl hover:bg-white/10 transition-all disabled:opacity-50 cursor-pointer"
              >
                Clear
              </button>
              <button 
                onClick={handleAnalyze}
                disabled={loading || !file}
                className="flex-[2] py-4 bg-gradient-to-r from-red-600 to-rose-600 text-white font-bold rounded-2xl disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-red-500/20 flex items-center justify-center gap-2 cursor-pointer transition-all"
              >
                {loading ? (
                  <>
                    <RefreshCw className="animate-spin" size={18} />
                    Extracting Frames...
                  </>
                ) : (
                  "Run Deepfake Scan"
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
                <Video size={64} className="mb-4 opacity-20" />
                <p className="text-center text-lg">Upload a video to see the facial morphing breakdown.</p>
              </div>
            )}
          </AnimatePresence>
        </section>
      </div>
    </div>
  );
};

export default VideoLab;
