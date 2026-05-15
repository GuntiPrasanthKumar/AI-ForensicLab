import { useContext } from "react";
import { AuthContext } from "../context/AuthContext";
import { ShieldAlert, LogOut, LayoutDashboard } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

const Navbar = () => {
  const { user, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <nav className="fixed w-full z-50 bg-black/50 backdrop-blur-md border-b border-white/5">
      <div className="max-w-6xl mx-auto px-4 md:px-8 h-20 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center group-hover:scale-105 transition-transform shadow-[0_0_20px_rgba(37,99,235,0.4)]">
            <ShieldAlert className="text-white" size={24} />
          </div>
          <span className="text-white font-bold text-xl tracking-tight hidden sm:block">AI Forensic Lab</span>
        </Link>

        <div className="flex items-center gap-6">
          <Link to="/about" className="text-gray-300 hover:text-white transition-colors font-medium text-sm">
            About
          </Link>
          <Link to="/tools" className="text-gray-300 hover:text-white transition-colors font-medium text-sm">
            Tools
          </Link>
          
          {user ? (
            <>
              <Link to="/app" className="text-gray-300 hover:text-white transition-colors font-medium text-sm">
                Hub
              </Link>
              <div className="flex items-center gap-4 border-l border-white/10 pl-6">
                <span className="text-sm font-medium text-blue-400">Hi, {user.name}</span>
                <button 
                  onClick={handleLogout}
                  className="p-2 hover:bg-white/5 rounded-full transition-colors text-gray-400 hover:text-white"
                  title="Logout"
                >
                  <LogOut size={20} />
                </button>
              </div>
            </>
          ) : (
            <>
              <Link to="/login" className="text-sm font-medium text-gray-300 hover:text-white transition-colors">
                Login
              </Link>
              <Link to="/register" className="text-sm font-medium bg-white text-black px-4 py-2 rounded-lg hover:bg-gray-200 transition-colors">
                Get Started
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
