import { useState } from "react";
import {Routes, Route} from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import About from "./pages/About";
import HealthFitness from "./pages/HealthFitness";
import Contact from "./pages/Contact";
import AuthModal from "./components/AuthModal";

function App(){
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  const handleOpenAuthModal = () => {
    setIsAuthModalOpen(true);
  };

  const handleCloseAuthModal = () => {
    setIsAuthModalOpen(false);
  };

  const handleAuthSubmit = (authData) => {
    console.log("Navbar Authentication Data:", authData);
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