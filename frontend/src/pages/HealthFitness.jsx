import { useState, useEffect } from 'react';
import AuthModal from '../components/AuthModal';

function HealthFitness(){
    const [formData, setFormData] = useState({
        age: '',
        gender: '',
        height: '',
        weight: '',
        bloodPressure: '',
        heartRate: '',
        physicalActivity: '',
        sleepHours: '',
        smokingHabit: ''
    });

    const [bmi, setBmi] = useState('');
    const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
    const [pendingHealthData, setPendingHealthData] = useState(null);
    const [prediction, setPrediction] = useState(null);
    const [loading, setLoading] = useState(false);
    const [submitError, setSubmitError] = useState(null);

    // Calculate BMI whenever height or weight changes
    useEffect(() => {
        if (formData.height && formData.weight) {
            const heightInMeters = formData.height / 100;
            const calculatedBMI = (formData.weight / (heightInMeters * heightInMeters)).toFixed(2);
            setBmi(calculatedBMI);
        } else {
            setBmi('');
        }
    }, [formData.height, formData.weight]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        // Store health data and open auth modal
        const healthDataWithBMI = { ...formData, bmi };
        setPendingHealthData(healthDataWithBMI);
        setIsAuthModalOpen(true);
    };

    const handleAuthSubmit = async (authData) => {
        // Combine auth data with health data
        const payload = {
            name: authData.data.name || "Existing User",
            email: authData.data.email,
            password: authData.data.password,
            age: Number(pendingHealthData.age),
            gender: pendingHealthData.gender,
            height: parseFloat(pendingHealthData.height),
            weight: parseFloat(pendingHealthData.weight),
            bmi: pendingHealthData.bmi ? parseFloat(pendingHealthData.bmi) : 0,
            bloodPressure: pendingHealthData.bloodPressure,
            heartRate: parseInt(pendingHealthData.heartRate, 10),
            physicalActivity: pendingHealthData.physicalActivity,
            sleepHours: parseFloat(pendingHealthData.sleepHours),
            smokingHabit: pendingHealthData.smokingHabit
        };

        setLoading(true);
        setSubmitError(null);

        try {
            // Get predictions first
            const predictionPayload = {
                age: payload.age,
                gender: payload.gender,
                height: payload.height,
                weight: payload.weight,
                bmi: payload.bmi,
                bloodPressure: payload.bloodPressure,
                heartRate: payload.heartRate,
                physicalActivity: payload.physicalActivity,
                sleepHours: payload.sleepHours,
                smokingHabit: payload.smokingHabit,
            };

            const predictionResponse = await fetch('http://localhost:3001/api/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(predictionPayload)
            });

            let predictionData = null;
            if (predictionResponse.ok) {
                predictionData = await predictionResponse.json();
                setPrediction(predictionData);
            }

            // Submit health assessment
            const response = await fetch('http://localhost:3001/api/health-assessment', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                const result = await response.json();
                alert('Data submitted successfully! ' + (result.message || ''));
                // Reset form after successful submission
                setFormData({
                    age: '',
                    gender: '',
                    height: '',
                    weight: '',
                    bloodPressure: '',
                    heartRate: '',
                    physicalActivity: '',
                    sleepHours: '',
                    smokingHabit: ''
                });
                setBmi('');
                setPendingHealthData(null);
                setIsAuthModalOpen(false);
            } else {
                const errorData = await response.json();
                setSubmitError('Failed to submit data: ' + JSON.stringify(errorData.detail || errorData || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error submitting data:', error);
            setSubmitError('An error occurred connecting to the server. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleAuthClose = () => {
        setIsAuthModalOpen(false);
    };

    return (
        <div className="w-full min-h-screen bg-[#0a0908] pt-28 pb-16">
            {/* Hero Section */}
            <section className="w-full px-6 py-16">
                <div className="max-w-4xl mx-auto text-center">
                    <h1 className="text-5xl md:text-6xl font-extrabold text-[#ffea00] mb-6 tracking-tight">
                        Health & Fitness Assessment
                    </h1>
                    <p className="text-xl md:text-2xl text-[#d2d7df] leading-relaxed">
                        Enter your health information to get AI-powered insights and personalized recommendations.
                    </p>
                </div>
            </section>

            {/* Predictions Display */}
            {prediction && (
                <section className="w-full px-6 py-8">
                    <div className="max-w-4xl mx-auto">
                        <div className="bg-gradient-to-r from-[#00253e]/50 to-[#001a2e]/50 p-8 rounded-2xl border border-[#ffea00]/30 shadow-lg shadow-[#ffea00]/10">
                            <h2 className="text-3xl font-bold text-[#ffea00] mb-6">Your Health Analysis Results</h2>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                {/* Predicted Blood Pressure */}
                                <div className="bg-[#0a0908]/50 p-6 rounded-lg border border-white/10">
                                    <p className="text-[#d2d7df] text-sm font-semibold mb-2">Predicted Blood Pressure</p>
                                    <p className="text-4xl font-bold text-[#ffea00]">{prediction.predicted_bp.toFixed(1)}</p>
                                    <p className="text-[#d2d7df] text-sm mt-2">mmHg</p>
                                </div>

                                {/* Risk Level */}
                                <div className="bg-[#0a0908]/50 p-6 rounded-lg border border-white/10">
                                    <p className="text-[#d2d7df] text-sm font-semibold mb-2">Health Risk Level</p>
                                    <p className={`text-4xl font-bold ${
                                        prediction.risk_level === 'Normal' ? 'text-green-400' :
                                        prediction.risk_level === 'Elevated' ? 'text-yellow-400' :
                                        'text-red-400'
                                    }`}>
                                        {prediction.risk_level}
                                    </p>
                                </div>
                            </div>

                            {/* Recommendations */}
                            {prediction.recommendations && prediction.recommendations.length > 0 && (
                                <div className="mt-8">
                                    <h3 className="text-2xl font-bold text-[#ffea00] mb-4">Personalized Recommendations</h3>
                                    <ul className="space-y-3">
                                        {prediction.recommendations.map((rec, idx) => (
                                            <li key={idx} className="flex items-start gap-3 text-[#d2d7df]">
                                                <span className="text-[#ffea00] font-bold mt-1">✓</span>
                                                <span className="text-lg">{rec}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    </div>
                </section>
            )}

            {/* Error Display */}
            {submitError && (
                <section className="w-full px-6 py-8">
                    <div className="max-w-4xl mx-auto">
                        <div className="bg-red-900/30 p-6 rounded-2xl border border-red-500/50">
                            <p className="text-red-300 text-lg font-semibold">{submitError}</p>
                        </div>
                    </div>
                </section>
            )}

            {/* Form Section */}
            <section className="w-full px-6 py-16">
                <div className="max-w-4xl mx-auto">
                    <form onSubmit={handleSubmit} className="bg-[#00253e]/30 p-10 rounded-2xl border border-white/10">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Age */}
                            <div>
                                <label className="block text-[#d2d7df] text-lg font-semibold mb-2">
                                    Age
                                </label>
                                <input
                                    type="number"
                                    name="age"
                                    value={formData.age}
                                    onChange={handleChange}
                                    className="w-full px-4 py-3 bg-[#0a0908] border border-white/10 rounded-lg text-[#d2d7df] focus:outline-none focus:border-[#ffea00] transition duration-300"
                                    placeholder="Enter your age"
                                    required
                                />
                            </div>

                            {/* Gender */}
                            <div>
                                <label className="block text-[#d2d7df] text-lg font-semibold mb-2">
                                    Gender
                                </label>
                                <select
                                    name="gender"
                                    value={formData.gender}
                                    onChange={handleChange}
                                    className="w-full px-4 py-3 bg-[#0a0908] border border-white/10 rounded-lg text-[#d2d7df] focus:outline-none focus:border-[#ffea00] transition duration-300"
                                    required
                                >
                                    <option value="">Select Gender</option>
                                    <option value="male">Male</option>
                                    <option value="female">Female</option>
                                    <option value="other">Other</option>
                                </select>
                            </div>

                            {/* Height */}
                            <div>
                                <label className="block text-[#d2d7df] text-lg font-semibold mb-2">
                                    Height (cm)
                                </label>
                                <input
                                    type="number"
                                    name="height"
                                    value={formData.height}
                                    onChange={handleChange}
                                    className="w-full px-4 py-3 bg-[#0a0908] border border-white/10 rounded-lg text-[#d2d7df] focus:outline-none focus:border-[#ffea00] transition duration-300"
                                    placeholder="Enter height in cm"
                                    required
                                />
                            </div>

                            {/* Weight */}
                            <div>
                                <label className="block text-[#d2d7df] text-lg font-semibold mb-2">
                                    Weight (kg)
                                </label>
                                <input
                                    type="number"
                                    name="weight"
                                    value={formData.weight}
                                    onChange={handleChange}
                                    className="w-full px-4 py-3 bg-[#0a0908] border border-white/10 rounded-lg text-[#d2d7df] focus:outline-none focus:border-[#ffea00] transition duration-300"
                                    placeholder="Enter weight in kg"
                                    required
                                />
                            </div>

                            {/* BMI (Auto-calculated) */}
                            <div>
                                <label className="block text-[#d2d7df] text-lg font-semibold mb-2">
                                    BMI (Auto-calculated)
                                </label>
                                <input
                                    type="text"
                                    value={bmi}
                                    className="w-full px-4 py-3 bg-[#00253e]/50 border border-[#ffea00]/30 rounded-lg text-[#ffea00] font-bold focus:outline-none cursor-not-allowed"
                                    placeholder="BMI will be calculated"
                                    readOnly
                                />
                            </div>

                            {/* Blood Pressure */}
                            <div>
                                <label className="block text-[#d2d7df] text-lg font-semibold mb-2">
                                    Blood Pressure (mmHg)
                                </label>
                                <input
                                    type="text"
                                    name="bloodPressure"
                                    value={formData.bloodPressure}
                                    onChange={handleChange}
                                    className="w-full px-4 py-3 bg-[#0a0908] border border-white/10 rounded-lg text-[#d2d7df] focus:outline-none focus:border-[#ffea00] transition duration-300"
                                    placeholder="e.g., 120/80"
                                    required
                                />
                            </div>

                            {/* Heart Rate */}
                            <div>
                                <label className="block text-[#d2d7df] text-lg font-semibold mb-2">
                                    Heart Rate (BPM)
                                </label>
                                <input
                                    type="number"
                                    name="heartRate"
                                    value={formData.heartRate}
                                    onChange={handleChange}
                                    className="w-full px-4 py-3 bg-[#0a0908] border border-white/10 rounded-lg text-[#d2d7df] focus:outline-none focus:border-[#ffea00] transition duration-300"
                                    placeholder="Enter heart rate"
                                    required
                                />
                            </div>

                            {/* Physical Activity Level */}
                            <div>
                                <label className="block text-[#d2d7df] text-lg font-semibold mb-2">
                                    Physical Activity Level
                                </label>
                                <select
                                    name="physicalActivity"
                                    value={formData.physicalActivity}
                                    onChange={handleChange}
                                    className="w-full px-4 py-3 bg-[#0a0908] border border-white/10 rounded-lg text-[#d2d7df] focus:outline-none focus:border-[#ffea00] transition duration-300"
                                    required
                                >
                                    <option value="">Select Activity Level</option>
                                    <option value="sedentary">Sedentary</option>
                                    <option value="light">Light</option>
                                    <option value="moderate">Moderate</option>
                                    <option value="active">Active</option>
                                    <option value="very-active">Very Active</option>
                                </select>
                            </div>

                            {/* Sleep Hours */}
                            <div>
                                <label className="block text-[#d2d7df] text-lg font-semibold mb-2">
                                    Sleep Hours (per day)
                                </label>
                                <input
                                    type="number"
                                    name="sleepHours"
                                    value={formData.sleepHours}
                                    onChange={handleChange}
                                    step="0.5"
                                    className="w-full px-4 py-3 bg-[#0a0908] border border-white/10 rounded-lg text-[#d2d7df] focus:outline-none focus:border-[#ffea00] transition duration-300"
                                    placeholder="Enter hours of sleep"
                                    required
                                />
                            </div>

                            {/* Smoking Habit */}
                            <div>
                                <label className="block text-[#d2d7df] text-lg font-semibold mb-2">
                                    Smoking Habit
                                </label>
                                <select
                                    name="smokingHabit"
                                    value={formData.smokingHabit}
                                    onChange={handleChange}
                                    className="w-full px-4 py-3 bg-[#0a0908] border border-white/10 rounded-lg text-[#d2d7df] focus:outline-none focus:border-[#ffea00] transition duration-300"
                                    required
                                >
                                    <option value="">Select Option</option>
                                    <option value="no">No</option>
                                    <option value="yes">Yes</option>
                                </select>
                            </div>
                        </div>

                        {/* Submit Button */}
                        <div className="mt-10 text-center">
                            <button
                                type="submit"
                                disabled={loading}
                                className="px-12 py-4 bg-[#ffea00] text-[#0a0908] text-xl font-bold rounded-full hover:bg-[#ffd700] transition duration-300 shadow-lg hover:shadow-2xl hover:shadow-[#ffea00]/40 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {loading ? 'Analyzing...' : 'Analyze My Health'}
                            </button>
                        </div>
                    </form>
                </div>
            </section>

            {/* Auth Modal */}
            <AuthModal 
                isOpen={isAuthModalOpen} 
                onClose={handleAuthClose}
                onSubmit={handleAuthSubmit}
            />
        </div>
    )
}

export default HealthFitness;