function About() {
    return (
        <div className="w-full min-h-screen bg-[#0a0908] pt-28 pb-16">
            {/* Hero Section */}
            <section className="w-full px-6 py-16">
                <div className="max-w-4xl mx-auto text-center">
                    <h1 className="text-5xl md:text-6xl font-extrabold text-[#ffea00] mb-6 tracking-tight">
                        About FitGuard AI
                    </h1>
                    <p className="text-xl md:text-2xl text-[#d2d7df] leading-relaxed">
                        We're on a mission to revolutionize preventive healthcare by making AI-powered health predictions accessible to everyone.
                    </p>
                </div>
            </section>

            {/* Story Section */}
            <section className="w-full px-6 py-16 bg-[#00253e]/20">
                <div className="max-w-5xl mx-auto">
                    <h2 className="text-4xl font-bold text-[#ffea00] mb-8">
                        Our Story
                    </h2>
                    <div className="space-y-6 text-lg text-[#d2d7df]/90 leading-relaxed">
                        <p>
                            FitGuard AI was born from a simple yet powerful idea: what if we could predict health issues before they happen? In a world where reactive healthcare has been the norm, we envisioned a future where artificial intelligence empowers individuals to take preventive action.
                        </p>
                        <p>
                            Founded by a team of healthcare professionals, data scientists, and fitness experts, we recognized that the convergence of AI, wearable technology, and big data could transform how we approach wellness. Every day, millions of people struggle with preventable health conditions that could have been avoided with early intervention.
                        </p>
                        <p>
                            Today, FitGuard AI serves thousands of users worldwide, helping them make informed decisions about their health through predictive analytics, personalized fitness plans, and real-time health monitoring.
                        </p>
                    </div>
                </div>
            </section>

            {/* Mission & Vision Section */}
            <section className="w-full px-6 py-16">
                <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-12">
                    <div className="bg-[#00253e]/30 p-10 rounded-2xl border border-white/10">
                        <h2 className="text-3xl font-bold text-[#ffea00] mb-6">
                            Our Mission
                        </h2>
                        <p className="text-lg text-[#d2d7df]/90 leading-relaxed">
                            To democratize predictive healthcare by providing cutting-edge AI technology that helps individuals predict health risks, optimize fitness routines, and achieve their wellness goals with confidence and precision.
                        </p>
                    </div>
                    <div className="bg-[#00253e]/30 p-10 rounded-2xl border border-white/10">
                        <h2 className="text-3xl font-bold text-[#ffea00] mb-6">
                            Our Vision
                        </h2>
                        <p className="text-lg text-[#d2d7df]/90 leading-relaxed">
                            A world where preventive healthcare is the standard, not the exception—where every person has the tools and insights to live their healthiest, longest, and most fulfilling life.
                        </p>
                    </div>
                </div>
            </section>

            {/* Core Values Section */}
            <section className="w-full px-6 py-16 bg-[#00253e]/20">
                <div className="max-w-5xl mx-auto">
                    <h2 className="text-4xl font-bold text-[#ffea00] mb-12 text-center">
                        Our Core Values
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        <div className="text-center">
                            <div className="text-5xl mb-4">🔒</div>
                            <h3 className="text-2xl font-bold text-[#d2d7df] mb-3">
                                Privacy First
                            </h3>
                            <p className="text-[#d2d7df]/80">
                                Your health data is yours. We use bank-level encryption and never share your information without explicit consent.
                            </p>
                        </div>
                        <div className="text-center">
                            <div className="text-5xl mb-4">🎯</div>
                            <h3 className="text-2xl font-bold text-[#d2d7df] mb-3">
                                Accuracy & Trust
                            </h3>
                            <p className="text-[#d2d7df]/80">
                                We build our AI models on peer-reviewed research and validate them with medical professionals to ensure reliability.
                            </p>
                        </div>
                        <div className="text-center">
                            <div className="text-5xl mb-4">💡</div>
                            <h3 className="text-2xl font-bold text-[#d2d7df] mb-3">
                                Innovation
                            </h3>
                            <p className="text-[#d2d7df]/80">
                                We continuously improve our algorithms and features to stay at the forefront of health technology.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="w-full px-6 py-16 bg-gradient-to-b from-[#00253e]/30 to-[#0a0908]">
                <div className="max-w-4xl mx-auto text-center">
                    <h2 className="text-4xl md:text-5xl font-bold text-[#ffea00] mb-6">
                        Join Us on This Journey
                    </h2>
                    <p className="text-xl text-[#d2d7df] mb-8">
                        Be part of the future of preventive healthcare.
                    </p>
                    <button className="px-10 py-5 bg-[#ffea00] text-[#0a0908] text-xl font-bold rounded-full hover:bg-[#ffd700] transition duration-300 shadow-lg hover:shadow-2xl hover:shadow-[#ffea00]/40">
                        Get Started Today
                    </button>
                </div>
            </section>
        </div>
    )
}

export default About;