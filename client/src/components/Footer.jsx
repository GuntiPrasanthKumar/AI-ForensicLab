import { ShieldAlert } from "lucide-react";

const Footer = () => {
  return (
    <footer className="border-t border-white/10 bg-black/50 mt-20 relative z-10">
      <div className="max-w-6xl mx-auto px-4 py-12 md:px-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-3">
            <ShieldAlert size={20} className="text-blue-500" />
            <span className="font-bold text-lg tracking-tight text-white">AI Forensic Lab</span>
          </div>
          <div className="flex gap-6 text-sm text-gray-400">
            <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
            <a href="#" className="hover:text-white transition-colors">Terms of Service</a>
            <a href="#" className="hover:text-white transition-colors">Contact Support</a>
          </div>
        </div>
        <div className="mt-8 text-center text-xs text-gray-600">
          &copy; {new Date().getFullYear()} AI Forensic Lab. All rights reserved. Powered by Hybrid Local Heuristics.
        </div>
      </div>
    </footer>
  );
};

export default Footer;
