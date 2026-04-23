function Contact() {
	return (
		<div className="w-full min-h-screen bg-[#0a0908] pt-28 pb-16 px-6">
			<section className="max-w-4xl mx-auto">
				<h1 className="text-5xl md:text-6xl font-extrabold text-[#ffea00] mb-6 text-center tracking-tight">
					Contact Us
				</h1>
				<p className="text-xl text-[#d2d7df] text-center mb-12">
					Have a question or feedback? Send us a message and we’ll get back to you.
				</p>

				<form className="bg-[#00253e]/30 border border-white/10 rounded-2xl p-8 md:p-10 space-y-6">
					<div>
						<label className="block text-[#d2d7df] font-semibold mb-2">Full Name</label>
						<input
							type="text"
							placeholder="Enter your full name"
							className="w-full px-4 py-3 bg-[#0a0908] border border-white/10 rounded-lg text-[#d2d7df] focus:outline-none focus:border-[#ffea00]"
						/>
					</div>

					<div>
						<label className="block text-[#d2d7df] font-semibold mb-2">Email</label>
						<input
							type="email"
							placeholder="Enter your email"
							className="w-full px-4 py-3 bg-[#0a0908] border border-white/10 rounded-lg text-[#d2d7df] focus:outline-none focus:border-[#ffea00]"
						/>
					</div>

					<div>
						<label className="block text-[#d2d7df] font-semibold mb-2">Message</label>
						<textarea
							rows="5"
							placeholder="Write your message"
							className="w-full px-4 py-3 bg-[#0a0908] border border-white/10 rounded-lg text-[#d2d7df] focus:outline-none focus:border-[#ffea00] resize-none"
						/>
					</div>

					<button
						type="submit"
						className="w-full md:w-auto px-10 py-4 bg-[#ffea00] text-[#0a0908] text-lg font-bold rounded-full hover:bg-[#ffd700] transition duration-300"
					>
						Send Message
					</button>
				</form>
			</section>
		</div>
	);
}

export default Contact;
