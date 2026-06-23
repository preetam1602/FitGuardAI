function Contact() {
	return (
		<div className="w-full min-h-screen bg-[var(--bg)] scanline pt-28 pb-16 px-6 relative">
            <div className="fixed inset-0 bg-grid pointer-events-none opacity-30 z-0"></div>
            
			<section className="max-w-4xl mx-auto relative z-10">
                <div className="inline-flex items-center gap-2 px-4 py-[6px] border border-[var(--border)] bg-[rgba(0,255,200,0.04)] text-[var(--pulse)] text-[9px] uppercase tracking-[4px] w-fit mx-auto mb-8 font-mono flex justify-center">
                    <div className="w-[6px] h-[6px] rounded-full bg-[var(--pulse)] animate-blink"></div>
                    Communication Channel
                </div>
				<h1 className="font-orbitron font-black text-5xl md:text-6xl text-[var(--white)] mb-6 text-center tracking-tight uppercase">
					Contact <span className="text-[var(--pulse)]">Us</span>
				</h1>
				<p className="font-mono text-sm md:text-base text-[var(--dim)] text-center mb-12 max-w-2xl mx-auto">
					Establish a secure communication link. Our diagnostics team will respond to your query within 24 standard cycles.
				</p>

				<form className="bg-[var(--surface)] border border-[var(--border)] p-8 md:p-10 space-y-6 relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-[var(--pulse)] to-transparent opacity-20"></div>
					
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label className="text-[8px] uppercase tracking-[3px] text-[var(--dim)] font-orbitron mb-2 block">Full Name</label>
                            <input
                                type="text"
                                placeholder="IDENT_NAME"
                                className="w-full px-4 py-3 bg-[var(--panel)] border border-[var(--border)] text-[var(--text)] text-xs font-mono focus:outline-none focus:border-[var(--pulse)] transition-colors"
                            />
                        </div>

                        <div>
                            <label className="text-[8px] uppercase tracking-[3px] text-[var(--dim)] font-orbitron mb-2 block">Email Address</label>
                            <input
                                type="email"
                                placeholder="IDENT_EMAIL"
                                className="w-full px-4 py-3 bg-[var(--panel)] border border-[var(--border)] text-[var(--text)] text-xs font-mono focus:outline-none focus:border-[var(--pulse)] transition-colors"
                            />
                        </div>
                    </div>

					<div>
						<label className="text-[8px] uppercase tracking-[3px] text-[var(--dim)] font-orbitron mb-2 block">Message Protocol</label>
						<textarea
							rows="5"
							placeholder="ENTER_MESSAGE_DATA..."
							className="w-full px-4 py-3 bg-[var(--panel)] border border-[var(--border)] text-[var(--text)] text-xs font-mono focus:outline-none focus:border-[var(--pulse)] transition-colors resize-none"
						/>
					</div>

					<div className="flex justify-center">
                        <button
                            type="submit"
                            className="btn-primary min-w-[200px]"
                        >
                            Send Transmission
                        </button>
                    </div>
				</form>
			</section>
		</div>
	);
}

export default Contact;
