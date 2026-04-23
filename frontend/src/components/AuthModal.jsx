import { useState } from 'react';

function AuthModal({ isOpen, onClose, onSubmit }) {
    const [activeTab, setActiveTab] = useState('login');
    const [loginData, setLoginData] = useState({
        email: '',
        password: ''
    });
    const [registerData, setRegisterData] = useState({
        name: '',
        email: '',
        password: '',
        confirmPassword: ''
    });

    const handleLoginChange = (e) => {
        const { name, value } = e.target;
        setLoginData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleRegisterChange = (e) => {
        const { name, value } = e.target;
        setRegisterData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleLoginSubmit = (e) => {
        e.preventDefault();
        console.log('Login Data:', loginData);
        onSubmit({ type: 'login', data: loginData });
        onClose();
    };

    const handleRegisterSubmit = (e) => {
        e.preventDefault();
        if (registerData.password !== registerData.confirmPassword) {
            alert('Passwords do not match!');
            return;
        }
        console.log('Register Data:', registerData);
        onSubmit({ type: 'register', data: registerData });
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-sm">
            <div className="relative w-full max-w-md mx-4">
                {/* Close Button */}
                <button
                    onClick={onClose}
                    className="absolute -top-4 -right-4 w-10 h-10 bg-[#ffea00] text-[#0a0908] rounded-full hover:bg-[#ffd700] transition duration-300 flex items-center justify-center font-bold text-xl z-10"
                >
                    ×
                </button>

                <div className="bg-[#00253e] rounded-2xl border border-[#ffea00]/30 overflow-hidden">
                    {/* Tab Headers */}
                    <div className="flex border-b border-white/10">
                        <button
                            onClick={() => setActiveTab('login')}
                            className={`flex-1 py-4 text-lg font-semibold transition duration-300 ${
                                activeTab === 'login'
                                    ? 'bg-[#ffea00]/20 text-[#ffea00] border-b-2 border-[#ffea00]'
                                    : 'text-[#d2d7df]/70 hover:text-[#d2d7df]'
                            }`}
                        >
                            Login
                        </button>
                        <button
                            onClick={() => setActiveTab('register')}
                            className={`flex-1 py-4 text-lg font-semibold transition duration-300 ${
                                activeTab === 'register'
                                    ? 'bg-[#ffea00]/20 text-[#ffea00] border-b-2 border-[#ffea00]'
                                    : 'text-[#d2d7df]/70 hover:text-[#d2d7df]'
                            }`}
                        >
                            Register
                        </button>
                    </div>

                    {/* Tab Content */}
                    <div className="p-8">
                        {activeTab === 'login' ? (
                            <form onSubmit={handleLoginSubmit} className="space-y-6">
                                <div>
                                    <label className="block text-[#d2d7df] text-sm font-semibold mb-2">
                                        Email Address
                                    </label>
                                    <input
                                        type="email"
                                        name="email"
                                        value={loginData.email}
                                        onChange={handleLoginChange}
                                        className="w-full px-4 py-3 bg-[#0a0908] border border-white/10 rounded-lg text-[#d2d7df] focus:outline-none focus:border-[#ffea00] transition duration-300"
                                        placeholder="Enter your email"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-[#d2d7df] text-sm font-semibold mb-2">
                                        Password
                                    </label>
                                    <input
                                        type="password"
                                        name="password"
                                        value={loginData.password}
                                        onChange={handleLoginChange}
                                        className="w-full px-4 py-3 bg-[#0a0908] border border-white/10 rounded-lg text-[#d2d7df] focus:outline-none focus:border-[#ffea00] transition duration-300"
                                        placeholder="Enter your password"
                                        required
                                    />
                                </div>
                                <button
                                    type="submit"
                                    className="w-full py-3 bg-[#ffea00] text-[#0a0908] text-lg font-bold rounded-lg hover:bg-[#ffd700] transition duration-300 shadow-lg hover:shadow-xl hover:shadow-[#ffea00]/30"
                                >
                                    Login
                                </button>
                            </form>
                        ) : (
                            <form onSubmit={handleRegisterSubmit} className="space-y-6">
                                <div>
                                    <label className="block text-[#d2d7df] text-sm font-semibold mb-2">
                                        Full Name
                                    </label>
                                    <input
                                        type="text"
                                        name="name"
                                        value={registerData.name}
                                        onChange={handleRegisterChange}
                                        className="w-full px-4 py-3 bg-[#0a0908] border border-white/10 rounded-lg text-[#d2d7df] focus:outline-none focus:border-[#ffea00] transition duration-300"
                                        placeholder="Enter your full name"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-[#d2d7df] text-sm font-semibold mb-2">
                                        Email Address
                                    </label>
                                    <input
                                        type="email"
                                        name="email"
                                        value={registerData.email}
                                        onChange={handleRegisterChange}
                                        className="w-full px-4 py-3 bg-[#0a0908] border border-white/10 rounded-lg text-[#d2d7df] focus:outline-none focus:border-[#ffea00] transition duration-300"
                                        placeholder="Enter your email"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-[#d2d7df] text-sm font-semibold mb-2">
                                        Password
                                    </label>
                                    <input
                                        type="password"
                                        name="password"
                                        value={registerData.password}
                                        onChange={handleRegisterChange}
                                        className="w-full px-4 py-3 bg-[#0a0908] border border-white/10 rounded-lg text-[#d2d7df] focus:outline-none focus:border-[#ffea00] transition duration-300"
                                        placeholder="Create a password"
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-[#d2d7df] text-sm font-semibold mb-2">
                                        Confirm Password
                                    </label>
                                    <input
                                        type="password"
                                        name="confirmPassword"
                                        value={registerData.confirmPassword}
                                        onChange={handleRegisterChange}
                                        className="w-full px-4 py-3 bg-[#0a0908] border border-white/10 rounded-lg text-[#d2d7df] focus:outline-none focus:border-[#ffea00] transition duration-300"
                                        placeholder="Confirm your password"
                                        required
                                    />
                                </div>
                                <button
                                    type="submit"
                                    className="w-full py-3 bg-[#ffea00] text-[#0a0908] text-lg font-bold rounded-lg hover:bg-[#ffd700] transition duration-300 shadow-lg hover:shadow-xl hover:shadow-[#ffea00]/30"
                                >
                                    Register
                                </button>
                            </form>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default AuthModal;
