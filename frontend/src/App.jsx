import { useState, useEffect } from "react";
import { authService } from "./services/auth";
import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import About from "./pages/About";
import HealthFitness from "./pages/HealthFitness";
import Contact from "./pages/Contact";
import AuthModal from "./components/AuthModal";

function App(){
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  // Pick up a session from a previous visit via the httpOnly refresh cookie
  useEffect(() => {
    authService.restoreSession();
  }, []);

  const handleOpenAuthModal = () => {
    setIsAuthModalOpen(true);
  };

  const handleCloseAuthModal = () => {
    setIsAuthModalOpen(false);
  };

  const handleAuthSubmit = () => {
    // Token is already stored by AuthModal; Navbar updates via the auth-changed event
    setIsAuthModalOpen(false);
  };

  return (
    <>
      <Navbar onOpenAuthModal={handleOpenAuthModal} />
      <Routes>
         <Route path="/" element={<Home/>}/>
         <Route path="/about" element={<About/>}/>
         <Route path="/health-fitness" element={<HealthFitness/>}/>
        <Route path="/contact" element={<Contact/>}/>
      </Routes>
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={handleCloseAuthModal}
        onSubmit={handleAuthSubmit}
      />
    </>
  );
}

export default App;
