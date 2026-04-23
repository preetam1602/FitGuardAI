import { useNavigate } from "react-router-dom";

function Home() {
    const navigate = useNavigate();

    return (
        <div className="w-full min-h-screen bg-[#0a0908]">
            <section className="w-full h-screen flex flex-col justify-center items-center px-6">
                <h1 className="text-6xl md:text-7xl font-extrabold text-[#ffea00] text-center mb-6 tracking-tight">
                    "Predict Today. Prevent Tomorrow."
                </h1>
                <p className="text-xl md:text-2xl text-[#d2d7df] text-center max-w-3xl mb-10">
                    Harness the power of AI to predict health risks, optimize your fitness, and take control of your wellness journey.
                </p>
                <button
                    onClick={() => navigate("/health-fitness")}
                    className="px-8 py-4 bg-[#ffea00] text-[#0a0908] text-lg font-bold rounded-full hover:bg-[#ffd700] transition duration-300 shadow-lg hover:shadow-xl hover:shadow-[#ffea00]/30"
                >
                    Get Started
                </button>
            </section>

            <section className="w-full py-20 px-6 bg-[#00253e]/30">
                <h2 className="text-4xl md:text-5xl font-bold text-[#ffea00] text-center mb-16">
                    Why Choose FitGuard AI?
                </h2>
                <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-10">
                    <div className="bg-[#00253e]/50 p-8 rounded-2xl backdrop-blur-sm border border-white/10 hover:border-[#ffea00]/50 transition duration-300">
                        <div className="text-5xl mb-4">🔮</div>
                        <h3 className="text-2xl font-bold text-[#d2d7df] mb-4">
                            Predictive Health Insights
                        </h3>
                        <p className="text-[#d2d7df]/80">
                            AI-powered analysis predicts potential health risks before they become issues, keeping you ahead of the curve.
                        </p>
                    </div>
                    <div className="bg-[#00253e]/50 p-8 rounded-2xl backdrop-blur-sm border border-white/10 hover:border-[#ffea00]/50 transition duration-300">
                        <div className="text-5xl mb-4">💪</div>
                        <h3 className="text-2xl font-bold text-[#d2d7df] mb-4">
                            Personalized Fitness Plans
                        </h3>
                        <p className="text-[#d2d7df]/80">
                            Custom workout and nutrition plans tailored to your body, goals, and lifestyle using advanced machine learning.
                        </p>
                    </div>
                    <div className="bg-[#00253e]/50 p-8 rounded-2xl backdrop-blur-sm border border-white/10 hover:border-[#ffea00]/50 transition duration-300">
                        <div className="text-5xl mb-4">📊</div>
                        <h3 className="text-2xl font-bold text-[#d2d7df] mb-4">
                            Real-Time Monitoring
                        </h3>
                        <p className="text-[#d2d7df]/80">
                            Track your vitals, activities, and progress with intelligent monitoring that adapts to your changing needs.
                        </p>
                    </div>
                </div>
            </section>

            <section className="w-full py-20 px-6">
                <h2 className="text-4xl md:text-5xl font-bold text-[#ffea00] text-center mb-16">
                    How It Works
                </h2>
                <div className="max-w-5xl mx-auto space-y-12">
                    <div className="flex flex-col md:flex-row items-center gap-8">
                        <div className="flex-shrink-0 w-16 h-16 bg-[#ffea00] text-[#0a0908] rounded-full flex items-center justify-center text-2xl font-bold">
                            1
                        </div>
                        <div>
                            <h3 className="text-2xl font-bold text-[#d2d7df] mb-3">
                                Input Your Health Data
                            </h3>
                            <p className="text-[#d2d7df]/80 text-lg">
                                Share your medical history, lifestyle habits, and fitness goals through our secure platform.
                            </p>
                        </div>
                    </div>
                    <div className="flex flex-col md:flex-row items-center gap-8">
                        <div className="flex-shrink-0 w-16 h-16 bg-[#ffea00] text-[#0a0908] rounded-full flex items-center justify-center text-2xl font-bold">
                            2
                        </div>
                        <div>
                            <h3 className="text-2xl font-bold text-[#d2d7df] mb-3">
                                AI Analysis & Prediction
                            </h3>
                            <p className="text-[#d2d7df]/80 text-lg">
                                Our advanced AI algorithms analyze your data to identify patterns and predict potential health risks.
                            </p>
                        </div>
                    </div>
                    <div className="flex flex-col md:flex-row items-center gap-8">
                        <div className="flex-shrink-0 w-16 h-16 bg-[#ffea00] text-[#0a0908] rounded-full flex items-center justify-center text-2xl font-bold">
                            3
                        </div>
                        <div>
                            <h3 className="text-2xl font-bold text-[#d2d7df] mb-3">
                                Get Personalized Recommendations
                            </h3>
                            <p className="text-[#d2d7df]/80 text-lg">
                                Receive custom fitness plans, nutrition advice, and preventive care strategies designed just for you.
                            </p>
                        </div>
                    </div>
                    <div className="flex flex-col md:flex-row items-center gap-8">
                        <div className="flex-shrink-0 w-16 h-16 bg-[#ffea00] text-[#0a0908] rounded-full flex items-center justify-center text-2xl font-bold">
                            4
                        </div>
                        <div>
                            <h3 className="text-2xl font-bold text-[#d2d7df] mb-3">
                                Track & Improve
                            </h3>
                            <p className="text-[#d2d7df]/80 text-lg">
                                Monitor your progress with real-time updates and continuous AI optimization of your health journey.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="w-full py-20 px-6 bg-gradient-to-b from-[#00253e]/30 to-[#0a0908]">
                <div className="max-w-4xl mx-auto text-center">
                    <h2 className="text-4xl md:text-5xl font-bold text-[#ffea00] mb-6">
                        Ready to Transform Your Health?
                    </h2>
                    <p className="text-xl text-[#d2d7df] mb-10">
                        Join thousands who are already using FitGuard AI to predict, prevent, and achieve their wellness goals.
                    </p>
                    <button className="px-10 py-5 bg-[#ffea00] text-[#0a0908] text-xl font-bold rounded-full hover:bg-[#ffd700] transition duration-300 shadow-lg hover:shadow-2xl hover:shadow-[#ffea00]/40">
                        Start Your Journey
                    </button>
                </div>
            </section>

            {/* Footer */}
            <footer className="w-full py-8 px-6 border-t border-white/10">
                <div className="max-w-6xl mx-auto text-center text-[#d2d7df]/60">
                    <p>&copy; 2026 FitGuard AI. All rights reserved.</p>
                </div>
            </footer>
        </div>
    )
}

export default Home;