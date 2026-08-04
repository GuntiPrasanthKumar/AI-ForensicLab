import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AuthProvider, AuthContext } from "./context/AuthContext";
import { useContext, useEffect } from "react";
import Navbar from "./components/Navbar";
import Footer from "./components/Footer";
import Landing from "./pages/Landing";
import Auth from "./pages/Auth";
import Dashboard from "./pages/Dashboard";
import ImageLab from "./pages/ImageLab";
import VideoLab from "./pages/VideoLab";
import TextLab from "./pages/TextLab";
import About from "./pages/About";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import VerifyEmailOtp from "./pages/VerifyEmailOtp";

const ScrollToTop = () => {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
};

const PrivateRoute = ({ children }) => {
  const { user, loading } = useContext(AuthContext);
  if (loading) return <div className="min-h-screen bg-black flex items-center justify-center text-white">Loading...</div>;
  return user ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <ScrollToTop />
        <div className="min-h-screen w-full max-w-full overflow-x-hidden relative bg-black text-white flex flex-col font-sans">
          <Navbar />
          <div className="flex-grow w-full max-w-full overflow-x-hidden">
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/login" element={<Auth />} />
              <Route path="/register" element={<Auth />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/reset-password" element={<ResetPassword />} />
              <Route path="/verify-email-otp" element={<VerifyEmailOtp />} />
              <Route path="/about" element={<About />} />
              <Route 
                path="/app" 
                element={
                  <PrivateRoute>
                    <Dashboard />
                  </PrivateRoute>
                } 
              />
              <Route path="/app/image" element={
                <PrivateRoute>
                  <ImageLab />
                </PrivateRoute>
              } />
              <Route path="/app/video" element={
                <PrivateRoute>
                  <VideoLab />
                </PrivateRoute>
              } />
              <Route path="/app/text" element={
                <PrivateRoute>
                  <TextLab />
                </PrivateRoute>
              } />
              <Route path="*" element={<Navigate to="/" />} />
            </Routes>
          </div>
          <Footer />
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;