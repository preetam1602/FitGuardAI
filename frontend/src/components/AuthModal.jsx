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
        onSubmit({ type: 'login', data: loginData });
        onClose();
    };

    const handleRegisterSubmit = (e) => {
        e.preventDefault();
        if (registerData.password !== registerData.confirmPassword) {
            alert('PROTOCOL_ERROR: Passwords do not match!');
            return;
        }
        onSubmit({ type: 'register', data: registerData });
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[2000] flex items-center justify-center bg-black/60 backdrop-blur-md px-4">
            <div className="relative w-full max-w-md animate-in fade-in zoom-in duration-300">
                {/* HUD Decoration - Corners */}
                <div className="absolute -top-2 -left-2 w-8 h-8 border-t-2 border-l-2 border-[var(--pulse)] z-10 pointer-events-none"></div>
                <div className="absolute -bottom-2 -right-2 w-8 h-8 border-b-2 border-r-2 border-[var(--pulse)] z-10 pointer-events-none"></div>
                
                {/* Close Button */}
                <button
                    onClick={onClose}
                    className="absolute -top-4 -right-4 w-10 h-10 bg-[var(--surface)] border border-[var(--border)] text-[var(--pulse)] hover:text-[var(--white)] hover:border-[var(--pulse)] transition-all duration-300 flex items-center justify-center font-bold text-xl z-20"
                >
                    ×
                </button>

                <div className="bg-[var(--surface)] border border-[var(--border)] overflow-hidden relative">
                    {/* Top Status Bar */}
                    <div className="bg-[var(--panel)] px-6 py-2 border-b border-[var(--border)] flex justify-between items-center">
                        <div className="flex items-center gap-2">
                            <div className="w-[6px] h-[6px] rounded-full bg-[var(--pulse)] animate-blink"></div>
                            <span className="font-orbitron text-[8px] uppercase tracking-[2px] text-[var(--dim)]">Security_Layer_Active</span>
                        </div>
                        <div className="font-mono text-[8px] text-[var(--dim)]">ID: {Math.random().toString(16).slice(2, 10).toUpperCase()}</div>
                    </div>

                    {/* Tab Headers */}
                    <div className="flex border-b border-[var(--border)]">
                        <button
                            onClick={() => setActiveTab('login')}
                            className={`flex-1 py-4 font-orbitron text-[10px] uppercase tracking-[4px] transition-all duration-300 relative ${
                                activeTab === 'login'
                                    ? 'bg-[rgba(0,255,200,0.05)] text-[var(--pulse)]'
                                    : 'text-[var(--dim)] hover:text-[var(--text)]'
                            }`}
                        >
                            [ Login ]
                            {activeTab === 'login' && <div className="absolute bottom-0 left-0 w-full h-[2px] bg-[var(--pulse)] shadow-[0_0_10px_var(--pulse)]"></div>}
                        </button>
                        <button
                            onClick={() => setActiveTab('register')}
                            className={`flex-1 py-4 font-orbitron text-[10px] uppercase tracking-[4px] transition-all duration-300 relative ${
                                activeTab === 'register'
                                    ? 'bg-[rgba(0,255,200,0.05)] text-[var(--pulse)]'
                                    : 'text-[var(--dim)] hover:text-[var(--text)]'
                            }`}
                        >
                            [ Register ]
                            {activeTab === 'register' && <div className="absolute bottom-0 left-0 w-full h-[2px] bg-[var(--pulse)] shadow-[0_0_10px_var(--pulse)]"></div>}
                        </button>
                    </div>

                    {/* Tab Content */}
                    <div className="p-10">
                        {activeTab === 'login' ? (
                            <form onSubmit={handleLoginSubmit} className="space-y-8">
                                <div className="space-y-2">
                                    <label className="block text-[8px] uppercase tracking-[3px] text-[var(--dim)] font-orbitron">
                                        Identity_Email
                                    </label>
                                    <input
                                        type="email"
                                        name="email"
                                        value={loginData.email}
                                        onChange={handleLoginChange}
                                        className="w-full px-4 py-3 bg-[var(--panel)] border border-[var(--border)] text-[var(--text)] text-xs font-mono focus:outline-none focus:border-[var(--pulse)] transition-colors"
                                        placeholder="USER@NETWORK.INT"
                                        required
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="block text-[8px] uppercase tracking-[3px] text-[var(--dim)] font-orbitron">
                                        Access_Key
                                    </label>
                                    <input
                                        type="password"
                                        name="password"
                                        value={loginData.password}
                                        onChange={handleLoginChange}
                                        className="w-full px-4 py-3 bg-[var(--panel)] border border-[var(--border)] text-[var(--text)] text-xs font-mono focus:outline-none focus:border-[var(--pulse)] transition-colors"
                                        placeholder="••••••••"
                                        required
                                    />
                                </div>
                                <div className="pt-4 flex flex-col gap-4">
                                    <button
                                        type="submit"
                                        className="btn-primary w-full"
                                    >
                                        INITIALIZE_SESSION
                                    </button>
                                    <div className="text-[8px] uppercase tracking-[2px] text-[var(--dim)] text-center">
                                        Neural link established — Encrypted
                                    </div>
                                </div>
                            </form>
                        ) : (
                            <form onSubmit={handleRegisterSubmit} className="space-y-6">
                                <div className="space-y-2">
                                    <label className="block text-[8px] uppercase tracking-[3px] text-[var(--dim)] font-orbitron">
                                        Biometric_Name
                                    </label>
                                    <input
                                        type="text"
                                        name="name"
                                        value={registerData.name}
                                        onChange={handleRegisterChange}
                                        className="w-full px-4 py-3 bg-[var(--panel)] border border-[var(--border)] text-[var(--text)] text-xs font-mono focus:outline-none focus:border-[var(--pulse)] transition-colors"
                                        placeholder="IDENT_STRING"
                                        required
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="block text-[8px] uppercase tracking-[3px] text-[var(--dim)] font-orbitron">
                                        Registry_Email
                                    </label>
                                    <input
                                        type="email"
                                        name="email"
                                        value={registerData.email}
                                        onChange={handleRegisterChange}
                                        className="w-full px-4 py-3 bg-[var(--panel)] border border-[var(--border)] text-[var(--text)] text-xs font-mono focus:outline-none focus:border-[var(--pulse)] transition-colors"
                                        placeholder="NEW_USER@NETWORK.INT"
                                        required
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <label className="block text-[8px] uppercase tracking-[3px] text-[var(--dim)] font-orbitron">
                                            New_Key
                                        </label>
                                        <input
                                            type="password"
                                            name="password"
                                            value={registerData.password}
                                            onChange={handleRegisterChange}
                                            className="w-full px-4 py-3 bg-[var(--panel)] border border-[var(--border)] text-[var(--text)] text-xs font-mono focus:outline-none focus:border-[var(--pulse)] transition-colors"
                                            placeholder="••••"
                                            required
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="block text-[8px] uppercase tracking-[3px] text-[var(--dim)] font-orbitron">
                                            Confirm
                                        </label>
                                        <input
                                            type="password"
                                            name="confirmPassword"
                                            value={registerData.confirmPassword}
                                            onChange={handleRegisterChange}
                                            className="w-full px-4 py-3 bg-[var(--panel)] border border-[var(--border)] text-[var(--text)] text-xs font-mono focus:outline-none focus:border-[var(--pulse)] transition-colors"
                                            placeholder="••••"
                                            required
                                        />
                                    </div>
                                </div>
                                <div className="pt-4 flex flex-col gap-4">
                                    <button
                                        type="submit"
                                        className="btn-primary w-full"
                                    >
                                        CREATE_PROTOCOL
                                    </button>
                                    <div className="text-[8px] uppercase tracking-[2px] text-[var(--dim)] text-center">
                                        Joining FitGuard Neural Network
                                    </div>
                                </div>
                            </form>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default AuthModal;
