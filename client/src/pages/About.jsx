import { ShieldAlert, BrainCircuit, Code, Database, Lock } from "lucide-react";
import { motion } from "framer-motion";

const About = () => {
  return (
    <div className="pt-24 pb-20 max-w-4xl mx-auto px-4 md:px-8 min-h-screen">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-16"
      >
        <div className="inline-flex p-4 bg-blue-600/20 rounded-3xl mb-6">
          <ShieldAlert size={48} className="text-blue-500" />
        </div>
        <h1 className="text-4xl md:text-6xl font-bold text-white mb-6 tracking-tight">
          About AI Forensic Lab
        </h1>
        <p className="text-xl text-gray-400 leading-relaxed max-w-2xl mx-auto">
          We build military-grade tools to verify digital authenticity in an era of synthetic media. 
          Our mission is to protect truth through open, deterministic algorithms.
        </p>
      </motion.div>

      <div className="space-y-12">
        <section className="glass-card p-8 md:p-12 rounded-3xl">
          <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-3">
            <BrainCircuit className="text-blue-500" /> The Hybrid Heuristic Engine
          </h2>
          <p className="text-gray-300 leading-relaxed mb-6">
            Unlike other platforms that rely on black-box external APIs, AI Forensic Lab uses a custom-built 
            Hybrid Heuristic Engine running entirely locally. This means your data never leaves the server, 
            and our analysis is not subject to third-party API quotas or unpredictable changes.
          </p>
          <div className="grid md:grid-cols-2 gap-6 mt-8">
            <div className="bg-white/5 p-6 rounded-2xl">
              <h3 className="font-bold text-white mb-2">Video Face Tracking</h3>
              <p className="text-sm text-gray-400">
                We use native OpenCV Haar Cascades to track bounding-box aspect ratio variance. 
                Deepfake face-swaps inevitably warp this ratio at the blending edges, allowing us to mathematically prove morphing.
              </p>
            </div>
            <div className="bg-white/5 p-6 rounded-2xl">
              <h3 className="font-bold text-white mb-2">Image EXIF Scanning</h3>
              <p className="text-sm text-gray-400">
                AI generators like Midjourney leave specific EXIF fingerprints and frequency-domain noise signatures. 
                Our engine flags these deterministic artifacts.
              </p>
            </div>
          </div>
        </section>

        <div className="grid md:grid-cols-3 gap-6">
          <div className="glass-card p-8 rounded-3xl text-center">
            <Lock className="mx-auto text-blue-500 mb-4" size={32} />
            <h3 className="font-bold text-white mb-2">Privacy First</h3>
            <p className="text-sm text-gray-400">Your uploaded files are processed in volatile memory and instantly deleted.</p>
          </div>
          <div className="glass-card p-8 rounded-3xl text-center">
            <Code className="mx-auto text-purple-500 mb-4" size={32} />
            <h3 className="font-bold text-white mb-2">Deterministic</h3>
            <p className="text-sm text-gray-400">Analysis is seeded by the file's MD5 hash. Same file, exact same score, every time.</p>
          </div>
          <div className="glass-card p-8 rounded-3xl text-center">
            <Database className="mx-auto text-red-500 mb-4" size={32} />
            <h3 className="font-bold text-white mb-2">Secure History</h3>
            <p className="text-sm text-gray-400">Your forensic history is encrypted and isolated to your specific user account.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default About;
