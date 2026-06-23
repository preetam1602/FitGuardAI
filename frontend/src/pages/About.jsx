import { useNavigate } from "react-router-dom";

function About() {
    const navigate = useNavigate();

    return (
        <div className="w-full min-h-screen bg-[var(--bg)] scanline pt-28 pb-16 relative">
            <div className="fixed inset-0 bg-grid pointer-events-none opacity-30 z-0"></div>
            
            {/* Hero Section */}
            <section className="w-full px-6 py-16 relative z-10">
                <div className="max-w-4xl mx-auto text-center">
                    <div className="inline-flex items-center gap-2 px-4 py-[6px] border border-[var(--border)] bg-[rgba(0,255,200,0.04)] text-[var(--pulse)] text-[9px] uppercase tracking-[4px] w-fit mx-auto mb-8 font-mono">
                        <div className="w-[6px] h-[6px] rounded-full bg-[var(--pulse)] animate-blink"></div>
                        Mission Parameters
                    </div>
                    <h1 className="font-orbitron font-black text-5xl md:text-6xl text-[var(--white)] mb-6 tracking-tight">
                        About <span className="text-[var(--pulse)]">FitGuard AI</span>
                    </h1>
                    <p className="font-mono text-sm md:text-lg text-[var(--dim)] leading-relaxed max-w-2xl mx-auto italic">
                        Revolutionizing preventive healthcare through distributed intelligence and biometric predictive modeling.
                    </p>
                </div>
            </section>

            {/* Story Section */}
            <section className="w-full px-6 py-16 relative z-10 border-y border-[var(--border)] bg-[rgba(7,18,24,0.5)] backdrop-blur-sm">
                <div className="max-w-5xl mx-auto">
                    <h2 className="font-orbitron font-bold text-3xl text-[var(--pulse)] mb-10 tracking-widest uppercase">
                        // Origin_Story
                    </h2>
                    <div className="space-y-6 font-mono text-sm text-[var(--text)]/80 leading-relaxed">
                        <p>
                            FitGuard AI was born from a simple yet powerful idea: what if we could predict health issues before they happen? In a world where reactive healthcare has been the norm, we envisioned a future where neural intelligence empowers individuals to take preventive action.
                        </p>
                        <p>
                            Founded by a team of healthcare professionals, clinical analysts, and fitness experts, we recognized that the convergence of predictive models, wearable systems, and physiological data could transform how we approach wellness. Every day, millions of people struggle with preventable health conditions that could have been avoided with early intervention.
                        </p>
                        <p>
                            Today, FitGuard AI serves thousands of users worldwide, helping them make informed decisions about their health through predictive analytics, personalized health protocols, and real-time biometric monitoring.
                        </p>
                    </div>
                </div>
            </section>

            {/* Mission & Vision Section */}
            <section className="w-full px-6 py-16 relative z-10">
                <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="bg-[var(--surface)] p-10 border border-[var(--border)] hover:border-[rgba(0,255,200,0.3)] transition-colors">
                        <h2 className="font-orbitron font-bold text-2xl text-[var(--white)] mb-6 uppercase tracking-wider">
                            Our Mission
                        </h2>
                        <p className="font-mono text-xs md:text-sm text-[var(--dim)] leading-relaxed">
                            To democratize predictive healthcare by providing cutting-edge AI technology that helps individuals predict health risks, optimize fitness routines, and achieve their wellness goals with confidence and precision.
                        </p>
                    </div>
                    <div className="bg-[var(--surface)] p-10 border border-[var(--border)] hover:border-[rgba(0,255,200,0.3)] transition-colors">
                        <h2 className="font-orbitron font-bold text-2xl text-[var(--white)] mb-6 uppercase tracking-wider">
                            Our Vision
                        </h2>
                        <p className="font-mono text-xs md:text-sm text-[var(--dim)] leading-relaxed">
                            A world where preventive healthcare is the standard, not the exception—where every person has the tools and insights to live their healthiest, longest, and most fulfilling life.
                        </p>
                    </div>
                </div>
            </section>

            {/* Core Values Section */}
            <section className="w-full px-6 py-16 relative z-10 border-t border-[var(--border)]">
                <div className="max-w-5xl mx-auto">
                    <h2 className="font-orbitron font-bold text-3xl text-[var(--white)] mb-16 text-center tracking-widest uppercase">
                        Core <span className="text-[var(--pulse)]">Protocols</span>
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
                        {[
                            { icon: "🔒", title: "Privacy First", desc: "Your health data is yours. We use high-level encryption and never share your information without explicit consent." },
                            { icon: "🎯", title: "Accuracy & Trust", desc: "We build our diagnostic protocols on peer-reviewed research and validate them with medical professionals to ensure reliability." },
                            { icon: "💡", title: "Innovation", desc: "We continuously improve our predictive protocols and features to stay at the forefront of health intelligence." },
                        ].map((v, i) => (
                            <div key={i} className="text-center group">
                                <div className="text-5xl mb-6 grayscale group-hover:grayscale-0 transition-all">{v.icon}</div>
                                <h3 className="font-orbitron font-bold text-lg text-[var(--white)] mb-4 tracking-wider uppercase">
                                    {v.title}
                                </h3>
                                <p className="font-mono text-[10px] text-[var(--dim)] leading-relaxed group-hover:text-[var(--text)] transition-colors">
                                    {v.desc}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="w-full px-6 py-24 relative z-10 border-t border-[var(--border)]">
                <div className="max-w-4xl mx-auto text-center">
                    <h2 className="font-orbitron font-black text-4xl md:text-5xl text-[var(--white)] mb-10 tracking-tighter">
                        JOIN THE <span className="text-[var(--pulse)]">PROTOCOL</span>
                    </h2>
                    <p className="font-mono text-sm text-[var(--dim)] mb-12 italic">
                        Be part of the future of preventive healthcare. Initialize your health diagnostic today.
                    </p>
                    <button onClick={() => navigate("/health-fitness")} className="btn-primary">
                        Initialize Diagnostic Mode
                    </button>
                </div>
            </section>
        </div>
    )
}

export default About;