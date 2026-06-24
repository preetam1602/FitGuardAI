import { useState, useEffect } from 'react';
import { NavLink } from "react-router-dom";
import { authService } from '../services/auth';

function Navbar({ onOpenAuthModal }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    setIsAuthenticated(authService.isAuthenticated());
  }, []);

  const handleLogout = () => {
    authService.logout();
    setIsAuthenticated(false);
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-[1000] flex items-center justify-between px-6 md:px-12 py-[18px] border-b border-[var(--border)] bg-[rgba(3,11,15,0.85)] backdrop-blur-md">
      {/* Logo */}
      <div className="flex items-center gap-[10px] font-orbitron font-black text-base tracking-[3px] text-[var(--white)] select-none cursor-pointer">
        <div className="w-2 h-2 rounded-full bg-[var(--pulse)] shadow-[0_0_10px_var(--pulse)] animate-heartbeat"></div>
        FITGUARD<span className="text-[var(--pulse)]">_AI</span>
      </div>

      {/* Nav Links */}
      <div className="hidden lg:flex items-center gap-9">
        {[
          { name: "Home", path: "/" },
          { name: "About", path: "/about" },
          { name: "Health & Fitness", path: "/health-fitness" },
          { name: "Contact", path: "/contact" },
        ].map((link) => (
          <NavLink
            key={link.path}
            to={link.path}
            className={({ isActive }) =>
              `text-[10px] uppercase tracking-[3px] font-mono transition-colors duration-300 ${
                isActive ? "text-[var(--pulse)]" : "text-[var(--dim)] hover:text-[var(--pulse)]"
              }`
            }
          >
            {link.name}
          </NavLink>
        ))}
      </div>

      {/* Right Actions / Status */}
      <div className="flex items-center gap-6">
        {isAuthenticated ? (
          <button
            onClick={handleLogout}
            className="hidden sm:block text-[10px] uppercase tracking-[3px] font-mono text-[var(--warn)] hover:text-[#ff4d6d] transition-colors duration-300"
          >
            LOGOUT
          </button>
        ) : (
          <button
            onClick={onOpenAuthModal}
            className="hidden sm:block text-[10px] uppercase tracking-[3px] font-mono text-[var(--dim)] hover:text-[var(--pulse)] transition-colors duration-300"
          >
            USER_ACCESS
          </button>
        )}
        
        <div className="flex items-center gap-2 text-[10px] uppercase tracking-[2px] text-[var(--pulse)] font-mono">
          <div className="w-[6px] h-[6px] rounded-full bg-[var(--pulse)] shadow-[0_0_6px_var(--pulse)] animate-blink"></div>
          System Online
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
