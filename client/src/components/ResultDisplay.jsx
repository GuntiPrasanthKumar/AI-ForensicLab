import { motion } from "framer-motion";
import { TrendingUp, BrainCircuit, CheckCircle2 } from "lucide-react";
import Charts from "./Charts";

const ResultDisplay = ({ result }) => {
  if (!result) return null;

  return (
    <motion.div 
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className="space-y-6 w-full"
    >
      {/* Main Probability Card */}
      <div className="glass-card p-8 rounded-3xl relative overflow-hidden">
        <div className={`absolute top-0 right-0 w-24 h-24 blur-3xl opacity-20 ${result.aiProbability > 50 || result.morphProbability > 50 ? 'bg-red-500' : 'bg-green-500'}`} />
        
        <div className="flex justify-between items-start mb-8">
          <div>
            <h2 className="text-3xl font-bold text-white">
              {result.inputType === 'image' || result.inputType === 'video' ? (
                result.morphProbability > result.aiProbability ? `${result.morphProbability}% Morph Likely` : `${result.aiProbability}% AI Likely`
              ) : (
                `${result.aiProbability}% AI Likely`
              )}
            </h2>
            <div className={`mt-2 inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${result.confidence === 'High' ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
              {result.confidence} Confidence
            </div>
          </div>
          <TrendingUp className="text-blue-500" size={32} />
        </div>

        <div className="h-4 bg-white/5 rounded-full overflow-hidden mb-8">
          <motion.div 
            initial={{ width: 0 }}
            animate={{ width: `${Math.max(result.aiProbability, result.morphProbability)}%` }}
            transition={{ duration: 1 }}
            className={`h-full ${Math.max(result.aiProbability, result.morphProbability) > 70 ? 'bg-red-500' : 'bg-green-500 shadow-[0_0_15px_rgba(34,197,94,0.4)]'}`}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white/5 p-4 rounded-2xl border border-white/5">
            <p className="text-gray-500 text-xs uppercase mb-1">Human Score</p>
            <p className="text-xl font-semibold text-green-400">{result.humanProbability}%</p>
          </div>
          <div className="bg-white/5 p-4 rounded-2xl border border-white/5">
            <p className="text-gray-500 text-xs uppercase mb-1">{(result.inputType === 'image' || result.inputType === 'video') && result.morphProbability > 0 ? 'Morph Score' : 'AI Score'}</p>
            <p className="text-xl font-semibold text-red-400">{Math.max(result.aiProbability, result.morphProbability)}%</p>
          </div>
        </div>
      </div>

      {/* AI Explanation */}
      <div className="glass-card p-6 rounded-3xl border-l-4 border-blue-500">
        <h3 className="text-sm font-bold text-blue-400 uppercase tracking-widest mb-3 flex items-center gap-2">
          <BrainCircuit size={16} /> Forensic Reasoning
        </h3>
        <p className="text-gray-300 leading-relaxed italic">
          "{result.explanation}"
        </p>
      </div>

      {/* Charts & Metrics (Only for Text/File) */}
      {(result.inputType !== 'image' && result.inputType !== 'video') && result.metrics && (
        <Charts metrics={result.metrics} />
      )}

      {/* Reasons / Artifacts List */}
      <div className="glass-card p-6 rounded-3xl">
        <h3 className="text-sm font-medium text-gray-400 mb-4 uppercase">
          {result.inputType === 'image' ? 'Detected Artifacts' : 'Key Observations'}
        </h3>
        <ul className="space-y-3">
          {(result.detectedArtifacts || result.reasons || []).map((item, i) => (
            <li key={i} className="flex items-center gap-3 text-gray-300 text-sm">
              <CheckCircle2 size={16} className="text-blue-500" />
              {item}
            </li>
          ))}
        </ul>
      </div>
    </motion.div>
  );
};

export default ResultDisplay;
