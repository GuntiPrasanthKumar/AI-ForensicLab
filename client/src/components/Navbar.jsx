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
    <nav className="fixed top-0 left-0 right-0 w-full z-50 bg-black/50 backdrop-blur-md border-b border-white/5">
      <div className="max-w-6xl mx-auto px-3 sm:px-8 h-16 sm:h-20 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 sm:gap-3 group shrink-0">
          <div className="w-9 h-9 sm:w-10 sm:h-10 bg-blue-600 rounded-xl flex items-center justify-center group-hover:scale-105 transition-transform shadow-[0_0_20px_rgba(37,99,235,0.4)]">
            <ShieldAlert className="text-white shrink-0" size={20} />
          </div>
          <span className="text-white font-bold text-lg sm:text-xl tracking-tight hidden xs:inline-block sm:block">AI Forensic Lab</span>
        </Link>

        <div className="flex items-center gap-3 sm:gap-6">
          <Link to="/about" className="text-gray-300 hover:text-white transition-colors font-medium text-xs sm:text-sm">
            About
          </Link>
          <Link to={user ? "/app" : "/about"} className="text-gray-300 hover:text-white transition-colors font-medium text-xs sm:text-sm">
            Tools
          </Link>
          
          {user ? (
            <>
              <Link to="/app" className="text-gray-300 hover:text-white transition-colors font-medium text-xs sm:text-sm">
                Hub
              </Link>
              <div className="flex items-center gap-2 sm:gap-4 border-l border-white/10 pl-3 sm:pl-6">
                <span className="text-xs sm:text-sm font-medium text-blue-400 max-w-[80px] sm:max-w-[150px] truncate">Hi, {user.name}</span>
                <button 
                  onClick={handleLogout}
                  className="p-1.5 sm:p-2 hover:bg-white/5 rounded-full transition-colors text-gray-400 hover:text-white shrink-0"
                  title="Logout"
                >
                  <LogOut size={18} />
                </button>
              </div>
            </>
          ) : (
            <>
              <Link to="/login" className="text-xs sm:text-sm font-medium text-gray-300 hover:text-white transition-colors">
                Login
              </Link>
              <Link to="/register" className="text-xs sm:text-sm font-medium bg-white text-black px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg hover:bg-gray-200 transition-colors">
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
