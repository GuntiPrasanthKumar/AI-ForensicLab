import { Canvas, useFrame } from "@react-three/fiber";
import { Points, PointMaterial, OrbitControls, Float } from "@react-three/drei";
import * as random from "maath/random/dist/maath-random.esm";
import { useState, useRef } from "react";
import { ShieldAlert, ArrowRight, BrainCircuit, Activity, Video } from "lucide-react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";

const ParticleMesh = (props) => {
  const ref = useRef();
  const [sphere] = useState(() => random.inSphere(new Float32Array(5000 * 3), { radius: 1.5 }));

  useFrame((state, delta) => {
    ref.current.rotation.x -= delta / 10;
    ref.current.rotation.y -= delta / 15;
  });

  return (
    <group rotation={[0, 0, Math.PI / 4]}>
      <Points ref={ref} positions={sphere} stride={3} frustumCulled={false} {...props}>
        <PointMaterial transparent color="#3b82f6" size={0.005} sizeAttenuation={true} depthWrite={false} />
      </Points>
    </group>
  );
};

const Landing = () => {
  return (
    <div className="bg-black">
      {/* Hero Section - Full Screen */}
      <div className="relative h-screen w-full flex flex-col items-center justify-center overflow-hidden">
        {/* 3D Background */}
        <div className="absolute inset-0 z-0">
          <Canvas camera={{ position: [0, 0, 1] }}>
            <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.5} />
            <Float speed={1.5} rotationIntensity={1} floatIntensity={2}>
              <ParticleMesh />
            </Float>
          </Canvas>
        </div>

        {/* Content Overlay */}
        <div className="relative z-10 w-full px-4 pt-16">
        <motion.div 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1 }}
          className="max-w-4xl mx-auto text-center"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 mb-8">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500"></span>
            </span>
            Local Heuristic Engine v2.0 Live
          </div>

          <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 tracking-tight leading-tight">
            Uncover the <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-500">Synthetic</span> Truth
          </h1>
          
          <p className="text-lg md:text-xl text-gray-400 mb-10 max-w-2xl mx-auto leading-relaxed">
            Military-grade AI forensics deployed entirely locally. Detect deepfakes, AI-generated text, and synthetic face morphs without compromising privacy.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link 
              to="/login"
              className="px-8 py-4 bg-white text-black font-bold rounded-full hover:bg-gray-200 transition-all flex items-center gap-2 group w-full sm:w-auto justify-center"
            >
              Start Analyzing <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
            </Link>
            <a 
              href="#features"
              className="px-8 py-4 bg-white/5 border border-white/10 text-white font-medium rounded-full hover:bg-white/10 transition-all w-full sm:w-auto text-center"
            >
              How it works
            </a>
          </div>
        </motion.div>
      </div>
    </div>

      {/* Features Section */}
      <div id="features" className="relative z-10 bg-black/80 backdrop-blur-xl border-t border-white/5 py-24">
        <div className="max-w-6xl mx-auto px-4 md:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-white mb-4">Multi-Modal Forensics</h2>
            <p className="text-gray-400">Everything you need to combat digital deception.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              { icon: Video, title: "Deepfake Video Morphing", desc: "Native OpenCV bounding-box aspect ratio variance tracking to catch edge-blended face swaps." },
              { icon: ShieldAlert, title: "Image EXIF Scanning", desc: "Detect hardware signatures and synthetic pixel noise from Midjourney, DALL-E, and Stable Diffusion." },
              { icon: BrainCircuit, title: "Text Linguistic Analysis", desc: "Identify robotic LLM phrasing, low perplexity, and predictable burstiness in documents." }
            ].map((feat, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.2 }}
                className="glass-card p-8 rounded-3xl border border-white/5 hover:border-blue-500/30 transition-colors group"
              >
                <div className="w-14 h-14 bg-blue-500/10 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <feat.icon size={28} className="text-blue-400" />
                </div>
                <h3 className="text-xl font-bold text-white mb-3">{feat.title}</h3>
                <p className="text-gray-400 leading-relaxed text-sm">{feat.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Landing;
