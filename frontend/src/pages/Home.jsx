import { useNavigate } from "react-router-dom";

function Home() {
    const navigate = useNavigate();

    return (
        <div className="w-full min-h-screen bg-[var(--bg)] scanline">
            <div className="fixed inset-0 bg-grid pointer-events-none opacity-50 z-0"></div>
            <div className="fixed top-[-100px] left-[-100px] w-[400px] h-[400px] bg-[rgba(0,255,200,0.04)] blur-[80px] rounded-full pointer-events-none z-0"></div>
            <div className="fixed bottom-0 right-0 w-[300px] h-[300px] bg-[rgba(61,159,255,0.04)] blur-[80px] rounded-full pointer-events-none z-0"></div>

            <section className="relative z-10 w-full min-h-screen flex flex-col justify-center pt-20 px-6 md:px-12 py-20 max-w-[1600px] mx-auto">
                <div className="inline-flex items-center gap-2 px-4 py-[6px] border border-[var(--border)] bg-[rgba(0,255,200,0.04)] text-[var(--pulse)] text-[9px] uppercase tracking-[4px] w-fit mb-10">
                    <div className="w-[6px] h-[6px] rounded-full bg-[var(--pulse)] shadow-[0_0_6px_var(--pulse)] animate-blink"></div>
                    Health Intelligence Platform · v1.0
                </div>

                <div className="grid grid-cols-1 gap-16">
                    <div className="max-w-[1200px]">
                        <h1 className="font-orbitron font-black text-[clamp(48px,8vw,88px)] leading-[0.9] tracking-[-2px] text-[var(--white)] mb-6">
                            <span className="block opacity-30 [text-stroke:1px_var(--text)] text-transparent">PROTECT</span>
                            <span className="block text-[var(--pulse)] drop-shadow-[0_0_30px_rgba(0,255,200,0.4)]">HEALTH.</span>
                            <span className="block text-[var(--text)]">POWERED<br />BY AI.</span>
                        </h1>

                        <p className="font-mono text-xs md:text-sm leading-relaxed text-[var(--dim)] max-w-2xl italic mb-10">
                            Personalized health insights, fitness guidance, and preventive analysis in one clean dashboard built for everyday wellness decisions.
                        </p>

                        <div className="flex flex-wrap gap-4 mb-14">
                            <button onClick={() => navigate("/health-fitness")} className="btn-primary">
                                Start Assessment
                            </button>
                            <button className="btn-outline" onClick={() => navigate("/about")}>
                                Learn More →
                            </button>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-[1400px]">
                            {[
                                {
                                    label: "Health Insights",
                                    value: "Track progress",
                                    desc: "Turn daily inputs into practical guidance for better recovery and routine planning.",
                                },
                                {
                                    label: "Fitness Planning",
                                    value: "Stay consistent",
                                    desc: "Build smarter workout and activity habits with recommendations that fit your pace.",
                                },
                                {
                                    label: "Preventive Care",
                                    value: "Act early",
                                    desc: "Stay ahead of issues with early checks, awareness, and healthier decisions.",
                                },
                            ].map((card) => (
                                <div key={card.label} className="bg-[var(--surface)] border border-[var(--border)] p-6 rounded-[24px]">
                                    <div className="text-[8px] uppercase tracking-[4px] text-[var(--dim)] font-mono mb-3">{card.label}</div>
                                    <div className="font-orbitron font-black text-2xl text-[var(--white)] mb-3">{card.value}</div>
                                    <p className="font-mono text-[11px] leading-relaxed text-[var(--dim)]">{card.desc}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </section>

            <div className="bg-[var(--pulse)] text-[var(--bg)] py-3 overflow-hidden whitespace-nowrap font-orbitron text-[11px] font-bold tracking-[4px] relative z-20">
                <div className="inline-flex animate-march">
                    {[1, 2].map((m) => (
                        <div key={m} className="inline-flex items-center">
                            <span>PERSONALIZED HEALTH INSIGHTS</span><span className="mx-7 opacity-40">◆</span>
                            <span>FITNESS GOALS TRACKED</span><span className="mx-7 opacity-40">◆</span>
                            <span>PREVENTIVE CARE RECOMMENDATIONS</span><span className="mx-7 opacity-40">◆</span>
                            <span>WELLNESS PLANS GENERATED</span><span className="mx-7 opacity-40">◆</span>
                            <span>REAL-TIME PROGRESS MONITORING</span><span className="mx-7 opacity-40">◆</span>
                        </div>
                    ))}
                </div>
            </div>

            <section id="core" className="relative z-10 py-28 px-6 md:px-12 max-w-[1600px] mx-auto">
                <div className="flex items-center gap-4 mb-16 opacity-50">
                    <div className="flex-1 h-[1px] bg-[var(--border)]"></div>
                    <div className="text-[9px] uppercase tracking-[4px] text-[var(--dim)] whitespace-nowrap">// 01 — Platform Highlights</div>
                    <div className="flex-1 h-[1px] bg-[var(--border)]"></div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-[1px] bg-[var(--border)]">
                    {[
                        {
                            icon: "◈",
                            title: "Health Insights",
                            desc: "Turn daily inputs into practical guidance for better recovery, consistency, and routine planning.",
                            tags: ["Health", "Insights", "Guidance"],
                        },
                        {
                            icon: "🧬",
                            title: "Fitness Planning",
                            desc: "Build smarter workout and activity habits with recommendations that fit your pace and goals.",
                            tags: ["Fitness", "Routine", "Goals"],
                        },
                        {
                            icon: "🧪",
                            title: "Preventive Care",
                            desc: "Stay ahead of issues with early checks, risk awareness, and a simple path to healthier decisions.",
                            tags: ["Care", "Prevention", "Support"],
                        },
                    ].map((card, i) => (
                        <div key={i} className="group bg-[var(--surface)] p-12 relative overflow-hidden transition-colors duration-500 hover:bg-[var(--panel)]">
                            <div className="absolute -bottom-2 -right-4 font-orbitron text-[100px] font-black text-[var(--panel)] leading-none select-none group-hover:text-[var(--bg)] transition-colors duration-500">0{i + 1}</div>
                            <div className="relative z-10">
                                <div className="text-4xl mb-6 grayscale group-hover:grayscale-0 transition-all duration-300">{card.icon}</div>
                                <h3 className="font-orbitron font-bold text-xl text-[var(--white)] mb-4 tracking-wider uppercase">{card.title}</h3>
                                <p className="font-mono text-[11px] leading-relaxed text-[var(--dim)] mb-8">{card.desc}</p>
                                <div className="flex flex-wrap gap-2">
                                    {card.tags.map((tag) => (
                                        <span key={tag} className="text-[8px] uppercase tracking-[2px] px-3 py-1 border border-[var(--border)] text-[var(--dim)] group-hover:border-[rgba(0,255,200,0.3)] group-hover:text-[var(--pulse)] transition-all duration-300">
                                            {tag}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            <section className="relative z-10 py-28 px-6 md:px-12 border-t border-[var(--border)] max-w-[1600px] mx-auto">
                <div className="max-w-4xl mx-auto text-center">
                    <h2 className="font-orbitron font-black text-4xl md:text-5xl text-[var(--white)] mb-8 tracking-tighter">
                        READY TO <span className="text-[var(--pulse)]">START?</span>
                    </h2>
                    <p className="text-sm md:text-base text-[var(--dim)] mb-12 max-w-2xl mx-auto font-mono">
                        Start using a cleaner way to plan your health, fitness, and daily wellness decisions with AI.
                    </p>
                    <button onClick={() => navigate("/health-fitness")} className="btn-primary">
                        Begin Assessment
                    </button>
                </div>
            </section>

            <footer className="relative z-10 py-8 px-6 md:px-12 border-t border-[var(--border)] flex flex-col md:flex-row justify-between items-center gap-6 max-w-[1600px] mx-auto">
                <div className="font-orbitron font-black text-sm tracking-[3px] text-[var(--white)]">
                    FIT<span className="text-[var(--pulse)]">GUARD</span>_AI
                </div>
                <div className="text-[10px] uppercase tracking-[2px] text-[var(--dim)]">
                    © 2026 · FitGuard AI Wellness Platform
                </div>
                <div className="flex gap-6">
                    <a href="#" className="text-[9px] uppercase tracking-[3px] text-[var(--dim)] hover:text-[var(--pulse)] transition-colors">Privacy Protocol</a>
                    <a href="#" className="text-[9px] uppercase tracking-[3px] text-[var(--dim)] hover:text-[var(--pulse)] transition-colors">Medical Disclosure</a>
                </div>
            </footer>
        </div>
    );
}

export default Home;