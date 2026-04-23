import { NavLink } from "react-router-dom";

function Navbar({ onOpenAuthModal }) {
  return (
    <nav className="absolute top-0 left-0 w-full h-20 z-50 flex justify-between items-center px-10 py-6 text-[#f4f4f9] bg-transparent backdrop-blur-md">
      <h1 className="text-3xl font-extrabold text-[#d2d7df]">FitGuard AI</h1>

      <div className="flex gap-12  text-xl rounded-full font-semibold">
        <NavLink className="px-4 py-2 rounded-full transition duration-300 ease-in-out
             hover:text-white hover:bg-white/10 hover:shadow-md hover:shadow-white/10" to="/">Home</NavLink>
        <NavLink className="px-4 py-2 rounded-full transition duration-300 ease-in-out
             hover:text-white hover:bg-white/10 hover:shadow-md hover:shadow-white/10" to="/about">About</NavLink>
        <NavLink className="px-4 py-2 rounded-full transition duration-300 ease-in-out
             hover:text-white hover:bg-white/10 hover:shadow-md hover:shadow-white/10" to="/health-fitness">Health & Fitness</NavLink>
        <NavLink className="px-4 py-2 rounded-full transition duration-300 ease-in-out
             hover:text-white hover:bg-white/10 hover:shadow-md hover:shadow-white/10" to="/contact">Contact</NavLink>
                    <button
                         type="button"
                         onClick={onOpenAuthModal}
                         className="px-4 py-2 rounded-full transition duration-300 ease-in-out hover:text-white hover:bg-white/10 hover:shadow-md hover:shadow-white/10"
                    >
                         LogIn/Register
                    </button>
      </div>
    </nav>
  );
}

export default Navbar;
