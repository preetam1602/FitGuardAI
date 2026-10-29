import { useState, useEffect, useRef } from 'react';
import AuthModal from '../components/AuthModal';
import { healthService } from '../services/health';
import { authService } from '../services/auth';

const RISK_COLORS = {
    Low: 'text-[var(--pulse)]',
    Intermediate: 'text-[var(--info)]',
    High: 'text-[var(--warn)]',
};

const DIET_STAGES = [
    { key: 'retrieving', label: 'Retrieving dietary guidelines' },
    { key: 'generating', label: 'Drafting your diet blueprint' },
    { key: 'verifying', label: 'Verifying against guidelines' },
    { key: 'revising', label: 'Revising flagged recommendations' },
];

const BP_STAGE_COLORS = {
    'Normal': 'text-[var(--pulse)]',
    'Elevated': 'text-[var(--info)]',
    'Stage 1 Hypertension': 'text-[var(--info)]',
    'Stage 2 Hypertension': 'text-[var(--warn)]',
    'Hypertensive Crisis': 'text-[#ff4d6d]',
};

function HealthFitness() {
    const [formData, setFormData] = useState({
        age: '',
        gender: '',
        height: '',
        weight: '',
        bloodPressure: '',
        heartRate: '72',
        physicalActivity: '',
        sleepHours: '',
        smokingHabit: '',
        diabetes: '',
        bpMedication: ''
    });

    const [bmi, setBmi] = useState('');
    const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
    const [pendingHealthData, setPendingHealthData] = useState(null);
    const [prediction, setPrediction] = useState(null);
    const [dietBlueprint, setDietBlueprint] = useState(null);
    const [activeTab, setActiveTab] = useState('bp');
    const [loading, setLoading] = useState(false);
    const [submitError, setSubmitError] = useState(null);
    // Diet generation progress: retrieving / generating / verifying / revising, null when idle
    const [dietStage, setDietStage] = useState(null);
    const [dietError, setDietError] = useState(null);
    const [dietRecordId, setDietRecordId] = useState(null);
    const dietRecordRef = useRef(null);

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

    const getBmiCategory = (bmiValue) => {
        if (!bmiValue) return null;
        const val = parseFloat(bmiValue);
        if (val < 18.5) return { label: 'Underweight', color: 'text-[var(--info)]' };
        if (val < 25) return { label: 'Normal', color: 'text-[var(--pulse)]' };
        if (val < 30) return { label: 'Overweight', color: 'text-[var(--warn)]' };
        return { label: 'Obese', color: 'text-[#ff4d6d]' };
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        const healthDataWithBMI = { ...formData, bmi };
        await authService.restoreSession(); // a returning user may still be logged in via the refresh cookie
        if (authService.isAuthenticated()) {
            submitAssessment(healthDataWithBMI);
        } else {
            // Ask the user to log in first; the assessment is submitted once they do
            setPendingHealthData(healthDataWithBMI);
            setIsAuthModalOpen(true);
        }
    };

    const handleAuthSubmit = () => {
        // AuthModal has already stored the token, which the API service sends as a Bearer header
        setIsAuthModalOpen(false);
        if (pendingHealthData) submitAssessment(pendingHealthData);
    };

    const submitAssessment = async (healthData) => {
        const payload = {
            age: Number(healthData.age),
            gender: healthData.gender,
            height: parseFloat(healthData.height),
            weight: parseFloat(healthData.weight),
            bmi: healthData.bmi ? parseFloat(healthData.bmi) : 0,
            bloodPressure: healthData.bloodPressure,
            heartRate: parseInt(healthData.heartRate, 10),
            physicalActivity: healthData.physicalActivity,
            sleepHours: parseFloat(healthData.sleepHours),
            smokingHabit: healthData.smokingHabit,
            diabetes: healthData.diabetes,
            bpMedication: healthData.bpMedication,
        };

        setLoading(true);
        setSubmitError(null);
        setActiveTab('bp'); // reset to bp tab before fetching

        try {
            // Risk assessment + save returns in milliseconds; the diet blueprint is streamed afterwards
            const result = await healthService.submitHealthAssessment(payload);
            setPrediction(result.prediction);
            generateDiet(result.record_id);

            // Reset form after successful submission
            setFormData({
                age: '',
                gender: '',
                height: '',
                weight: '',
                bloodPressure: '',
                heartRate: '72',
                physicalActivity: '',
                sleepHours: '',
                smokingHabit: '',
                diabetes: '',
                bpMedication: '',
            });
            setBmi('');
            setPendingHealthData(null);
        } catch (error) {
            if (error.status === 401) {
                // Session ended (the API client already tried a refresh): log in again, keeping the inputs
                authService.clearSession();
                setPendingHealthData(healthData);
                setIsAuthModalOpen(true);
                return;
            }
            console.error('Error submitting data:', error);
            setSubmitError(error.message || 'An error occurred connecting to the server. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const generateDiet = async (recordId) => {
        dietRecordRef.current = recordId;
        // A newer submission replaces this one; ignore events from the older stream
        const isCurrent = () => dietRecordRef.current === recordId;
        setDietRecordId(recordId);
        setDietBlueprint(null);
        setDietError(null);
        setDietStage('retrieving');

        try {
            await healthService.streamDietForRecord(recordId, (event, data) => {
                if (!isCurrent()) return;
                if (event === 'status') setDietStage(data.stage);
                else if (event === 'draft') setDietBlueprint({ ...data, isDraft: true });
                else if (event === 'final') setDietBlueprint(data);
                else if (event === 'error') setDietError(data.detail);
            });
        } catch (error) {
            if (isCurrent()) setDietError(error.message || 'Diet generation failed. Please try again.');
        } finally {
            if (isCurrent()) setDietStage(null);
        }
    };

    const handleAuthClose = () => {
        setIsAuthModalOpen(false);
    };

    return (
        <div className="w-full min-h-screen bg-[var(--bg)] scanline pt-28 pb-16 relative overflow-hidden">
            {/* Background Effects */}
            <div className="fixed inset-0 bg-grid pointer-events-none opacity-30 z-0"></div>
            
            {/* Hero Section */}
            <section className="w-full px-6 py-12 relative z-10">
                <div className="max-w-4xl mx-auto text-center">
                    <div className="inline-flex items-center gap-2 px-4 py-[6px] border border-[var(--border)] bg-[rgba(0,255,200,0.04)] text-[var(--pulse)] text-[9px] uppercase tracking-[4px] w-fit mx-auto mb-8">
                        <div className="w-[6px] h-[6px] rounded-full bg-[var(--pulse)] animate-blink"></div>
                        Diagnostic Interface Mode
                    </div>
                    <h1 className="font-orbitron font-black text-4xl md:text-6xl text-[var(--white)] mb-6 tracking-tight">
                        Health & <span className="text-[var(--pulse)]">Fitness</span> Assessment
                    </h1>
                    <p className="font-mono text-sm md:text-base text-[var(--dim)] leading-relaxed max-w-2xl mx-auto">
                        Initialize diagnostic protocol. Input biometric data for neural analysis and preventive risk assessment.
                    </p>
                </div>
            </section>

            {/* Results Display (Prediction & Diet Blueprint) */}
            {prediction && (
                <section className="w-full px-6 py-8 relative z-10">
                    <div className="max-w-4xl mx-auto">
                        <div className="bg-[var(--surface)] p-8 border border-[var(--pulse)] shadow-[0_0_20px_rgba(0,255,200,0.15)] relative overflow-hidden">
                            <div className="absolute top-0 right-0 p-2 font-mono text-[8px] text-[var(--pulse)] opacity-50">FRAMINGHAM 2008 · ACC/AHA 2017</div>
                            <h2 className="font-orbitron font-bold text-2xl text-[var(--pulse)] mb-6 tracking-wider">DIAGNOSTIC CORE ANALYSIS</h2>
                            
                            {/* Tabs */}
                            <div className="flex gap-4 border-b border-[var(--border)] mb-8">
                                <button 
                                    className={`pb-3 px-4 font-orbitron text-xs md:text-sm uppercase tracking-widest transition-colors ${activeTab === 'bp' ? 'border-b-2 border-[var(--pulse)] text-[var(--pulse)]' : 'text-[var(--dim)] hover:text-[var(--white)]'}`}
                                    onClick={() => setActiveTab('bp')}
                                >
                                    Risk Assessment
                                </button>
                                {(dietBlueprint || dietStage || dietError) && (
                                    <button
                                        className={`pb-3 px-4 font-orbitron text-xs md:text-sm uppercase tracking-widest transition-colors flex items-center gap-2 ${activeTab === 'diet' ? 'border-b-2 border-[var(--pulse)] text-[var(--pulse)]' : 'text-[var(--dim)] hover:text-[var(--white)]'}`}
                                        onClick={() => setActiveTab('diet')}
                                    >
                                        AI Diet Blueprint
                                        {dietStage && <span className="w-[6px] h-[6px] rounded-full bg-[var(--pulse)] animate-blink" aria-label="Generating"></span>}
                                    </button>
                                )}
                            </div>

                            {activeTab === 'bp' && (
                                <div className="animate-fade-in">
                                    {/* Urgent BP warning */}
                                    {prediction.bp?.urgent && (
                                        <div className="mb-8 p-5 border-2 border-[#ff4d6d] bg-[rgba(255,77,109,0.1)] font-mono text-sm text-[var(--white)] flex items-start gap-3">
                                            <span className="animate-blink text-[#ff4d6d] text-lg">⚠</span>
                                            <span>{prediction.recommendations?.[0]}</span>
                                        </div>
                                    )}

                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
                                        {/* 10-year CVD Risk */}
                                        <div className="bg-[var(--panel)] p-6 border border-[var(--border)] relative group hover:border-[var(--pulse)] transition-colors">
                                            <p className="text-[var(--dim)] text-[10px] uppercase tracking-[2px] mb-3">10-Year Heart Risk</p>
                                            <div className="flex items-baseline gap-2">
                                                <p className={`text-4xl font-bold font-orbitron ${RISK_COLORS[prediction.cvd_category] || 'text-[var(--white)]'}`}>
                                                    {prediction.cvd_risk_percent != null ? prediction.cvd_risk_percent.toFixed(1) : '—'}
                                                </p>
                                                {prediction.cvd_risk_percent != null && <p className="text-[var(--dim)] text-xs">%</p>}
                                            </div>
                                            <p className="text-[var(--dim)] text-[10px] uppercase tracking-[2px] mt-2">{prediction.cvd_category ? `${prediction.cvd_category} risk` : 'Not estimated'}</p>
                                        </div>

                                        {/* Blood Pressure Stage */}
                                        <div className="bg-[var(--panel)] p-6 border border-[var(--border)] relative group hover:border-[var(--pulse)] transition-colors">
                                            <p className="text-[var(--dim)] text-[10px] uppercase tracking-[2px] mb-3">Blood Pressure</p>
                                            <div className="flex items-baseline gap-2">
                                                <p className="text-4xl font-bold font-orbitron text-[var(--white)]">{prediction.bp?.systolic}/{prediction.bp?.diastolic}</p>
                                                <p className="text-[var(--dim)] text-xs">mmHg</p>
                                            </div>
                                            <p className={`text-[10px] uppercase tracking-[2px] mt-2 ${BP_STAGE_COLORS[prediction.bp?.stage] || 'text-[var(--dim)]'}`}>{prediction.bp?.stage}</p>
                                        </div>

                                        {/* Heart Age */}
                                        <div className="bg-[var(--panel)] p-6 border border-[var(--border)] relative group hover:border-[var(--pulse)] transition-colors">
                                            <p className="text-[var(--dim)] text-[10px] uppercase tracking-[2px] mb-3">Heart Age</p>
                                            <div className="flex items-baseline gap-2">
                                                <p className="text-4xl font-bold font-orbitron text-[var(--white)] group-hover:text-[var(--pulse)] transition-colors">{prediction.heart_age ?? '—'}</p>
                                                {prediction.heart_age != null && <p className="text-[var(--dim)] text-xs">years</p>}
                                            </div>
                                            <p className="text-[var(--dim)] text-[10px] uppercase tracking-[2px] mt-2">Overall: {prediction.risk_level}</p>
                                        </div>
                                    </div>

                                    {/* What drives the risk */}
                                    {prediction.risk_factors?.length > 0 && (
                                        <div className="mb-10 bg-[var(--panel)] p-6 border border-[var(--border)]">
                                            <h3 className="font-orbitron text-[10px] uppercase tracking-[4px] text-[var(--dim)] mb-5">Biggest Levers On Your Risk</h3>
                                            <div className="space-y-4">
                                                {prediction.risk_factors.map((f) => (
                                                    <div key={f.factor} className="font-mono text-xs md:text-sm">
                                                        <div className="flex justify-between gap-4 mb-2 text-[var(--text)]">
                                                            <span>{f.action}</span>
                                                            <span className="text-[var(--pulse)] whitespace-nowrap">−{f.risk_reduction_percent.toFixed(1)} pts</span>
                                                        </div>
                                                        <div className="h-[6px] bg-[var(--surface)]">
                                                            <div className="h-full bg-[var(--pulse)]" style={{ width: `${Math.min(100, (f.risk_reduction_percent / prediction.cvd_risk_percent) * 100)}%` }}></div>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Model limits */}
                                    {prediction.notes?.length > 0 && (
                                        <ul className="mb-10 space-y-2 font-mono text-[11px] text-[var(--dim)]">
                                            {prediction.notes.map((note, idx) => <li key={idx}>ⓘ {note}</li>)}
                                        </ul>
                                    )}

                                    {/* Recommendations */}
                                    {prediction.recommendations && prediction.recommendations.length > 0 && (
                                        <div className="bg-[rgba(0,255,200,0.03)] p-6 border border-[var(--border)]">
                                            <div className="flex items-center gap-3 mb-6">
                                                <div className="h-[1px] flex-1 bg-[var(--border)]"></div>
                                                <h3 className="font-orbitron text-[10px] uppercase tracking-[4px] text-[var(--dim)] whitespace-nowrap">Neural Recommendations</h3>
                                                <div className="h-[1px] flex-1 bg-[var(--border)]"></div>
                                            </div>
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                {prediction.recommendations.map((rec, idx) => (
                                                    <div key={idx} className="flex items-center gap-4 text-[var(--text)] text-xs md:text-sm p-3 bg-[var(--panel)] border-l-2 border-[var(--pulse)]">
                                                        <span className="text-[var(--pulse)] font-mono">[{idx + 1}]</span>
                                                        <span className="font-mono italic">{rec}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    <p className="mt-8 font-mono text-[10px] text-[var(--dim)] leading-relaxed">
                                        Screening estimate from the {prediction.model?.name} ({prediction.model?.reference}) and the {prediction.model?.bp_reference}.
                                        It is not a diagnosis. Talk to a doctor about your results.
                                    </p>
                                </div>
                            )}

                            {activeTab === 'diet' && !dietBlueprint && dietStage && (
                                <div className="bg-[var(--panel)] p-6 border border-[var(--border)] animate-fade-in" aria-live="polite">
                                    <p className="font-orbitron text-[12px] uppercase tracking-[4px] text-[var(--pulse)] mb-4">Generating AI Diet Blueprint</p>
                                    <ul className="space-y-3 font-mono text-sm">
                                        {DIET_STAGES.filter(s => s.key !== 'revising' || dietStage === 'revising').map((s, idx) => {
                                            const current = DIET_STAGES.findIndex(d => d.key === dietStage);
                                            const state = idx < current ? 'done' : idx === current ? 'active' : 'pending';
                                            return (
                                                <li key={s.key} className={`flex items-center gap-3 ${state === 'pending' ? 'text-[var(--dim)]' : 'text-[var(--white)]'}`}>
                                                    <span className={state === 'active' ? 'text-[var(--pulse)] animate-blink' : 'text-[var(--pulse)]'}>
                                                        {state === 'done' ? '✓' : state === 'active' ? '▸' : '·'}
                                                    </span>
                                                    {s.label}
                                                </li>
                                            );
                                        })}
                                    </ul>
                                </div>
                            )}

                            {activeTab === 'diet' && dietError && (
                                <div className="mb-8 p-5 border border-[var(--warn)] bg-[rgba(255,77,109,0.05)] font-mono text-sm text-[var(--warn)] flex flex-wrap items-center justify-between gap-4">
                                    <span><span className="animate-blink">⚠</span> {dietError}</span>
                                    {!dietStage && dietRecordId && (
                                        <button
                                            onClick={() => generateDiet(dietRecordId)}
                                            className="px-4 py-2 border border-[var(--pulse)] text-[var(--pulse)] font-orbitron text-[10px] uppercase tracking-widest hover:bg-[rgba(0,255,200,0.1)] transition-colors"
                                        >
                                            Retry
                                        </button>
                                    )}
                                </div>
                            )}

                            {activeTab === 'diet' && dietBlueprint && (
                                <div className="space-y-8 animate-fade-in">
                                    {dietBlueprint.isDraft && (
                                        <div className="p-4 border border-[var(--border)] bg-[rgba(0,255,200,0.04)] font-mono text-xs text-[var(--dim)] flex items-center gap-3" aria-live="polite">
                                            <span className="w-[6px] h-[6px] rounded-full bg-[var(--pulse)] animate-blink"></span>
                                            {dietStage === 'revising'
                                                ? 'Draft — the reviewer flagged some recommendations; a revised plan is being generated…'
                                                : 'Draft — checking recommendations against the dietary guidelines…'}
                                        </div>
                                    )}
                                    {/* Diet Type Badge & Reason */}
                                    <div className="bg-[var(--panel)] p-6 border border-[var(--border)] flex flex-col md:flex-row items-center gap-6">
                                        <div className="px-4 py-2 bg-[rgba(0,255,200,0.1)] border border-[var(--pulse)] text-[var(--pulse)] font-orbitron font-bold uppercase tracking-widest whitespace-nowrap">
                                            {dietBlueprint.diet_type || "Custom AI Diet"}
                                        </div>
                                        <p className="text-[var(--text)] font-mono text-sm leading-relaxed">
                                            {dietBlueprint.reason || dietBlueprint.diet_reason || "Optimized based on your biometric profile, activity level, and health assessment to regulate blood pressure and promote cardiovascular health."}
                                        </p>
                                    </div>

                                    {/* Macro Cards */}
                                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                                        {[
                                            { label: 'Calories', value: dietBlueprint.macros?.calories || 'N/A' },
                                            { label: 'Protein', value: dietBlueprint.macros?.protein || 'N/A' },
                                            { label: 'Carbs', value: dietBlueprint.macros?.carbs || 'N/A' },
                                            { label: 'Fat', value: dietBlueprint.macros?.fat || 'N/A' },
                                            { label: 'Fiber', value: dietBlueprint.macros?.fiber || '30g' }
                                        ].map((macro, idx) => (
                                            <div key={idx} className="bg-[var(--surface)] border border-[var(--border)] p-4 flex flex-col items-center justify-center relative overflow-hidden group hover:border-[var(--pulse)] transition-colors">
                                                <span className="text-[10px] uppercase tracking-[2px] text-[var(--dim)] mb-2">{macro.label}</span>
                                                <span className="font-orbitron font-bold text-xl text-[var(--white)] group-hover:text-[var(--pulse)] transition-colors">{macro.value}</span>
                                            </div>
                                        ))}
                                    </div>

                                    {/* Meal Plan Grid */}
                                    <div>
                                        <h3 className="font-orbitron text-[12px] uppercase tracking-[4px] text-[var(--pulse)] mb-4 border-b border-[var(--border)] pb-2">Daily Meal Protocol</h3>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            {(dietBlueprint.meal_plan || []).map((meal, idx) => (
                                                <div key={idx} className="bg-[var(--panel)] border border-[var(--border)] p-4 flex flex-col gap-2">
                                                    <span className="font-orbitron text-[10px] text-[var(--dim)] uppercase tracking-widest">{meal.meal}</span>
                                                    <p className="font-mono text-sm text-[var(--white)]">{meal.description || meal.food || JSON.stringify(meal)}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Foods to Avoid (Red) & Supplements (Blue) */}
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div className="bg-[rgba(255,77,109,0.05)] border border-[var(--warn)] p-6 relative">
                                            <h3 className="font-orbitron text-[12px] uppercase tracking-[4px] text-[var(--warn)] mb-4 flex items-center gap-2">
                                                <span className="animate-blink">⚠</span> Restricted Items
                                            </h3>
                                            <ul className="space-y-2">
                                                {(dietBlueprint.foods_to_avoid || []).map((food, idx) => (
                                                    <li key={idx} className="font-mono text-xs text-[var(--text)] flex items-start gap-2">
                                                        <span className="text-[var(--warn)] mt-[2px]">×</span> {food}
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                        
                                        <div className="bg-[rgba(0,150,255,0.05)] border border-[#0096ff] p-6 relative">
                                            <h3 className="font-orbitron text-[12px] uppercase tracking-[4px] text-[#0096ff] mb-4 flex items-center gap-2">
                                                <span className="text-[#0096ff]">+</span> Recommended Supplements
                                            </h3>
                                            <ul className="space-y-3">
                                                {(dietBlueprint.supplements || []).map((supp, idx) => (
                                                    <li key={idx} className="font-mono text-xs text-[var(--text)] flex flex-col gap-1">
                                                        <div className="flex items-start gap-2">
                                                            <span className="text-[#0096ff] mt-[2px]">•</span> 
                                                            <span className="font-bold text-[var(--white)]">{typeof supp === 'string' ? supp : supp.name}</span>
                                                        </div>
                                                        {typeof supp === 'object' && supp.dose && <span className="text-[var(--dim)] ml-4 text-[10px]">Dose: {supp.dose}</span>}
                                                        {typeof supp === 'object' && supp.reason && <span className="text-[var(--dim)] ml-4 text-[10px] italic">Reason: {supp.reason}</span>}
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    </div>

                                    {/* Weekly Habit Tip */}
                                    <div className="bg-[var(--surface)] border-l-4 border-[var(--pulse)] p-6">
                                        <h3 className="font-orbitron text-[10px] uppercase tracking-[3px] text-[var(--dim)] mb-2">Weekly Actionable Habit</h3>
                                        <p className="font-mono text-sm text-[var(--white)]">
                                            {dietBlueprint.weekly_habit_tip || "Stay consistent with hydration. Aim to drink at least 2.5 liters of water daily to support metabolic function and blood pressure regulation."}
                                        </p>
                                    </div>
                                </div>
                            )}

                        </div>
                    </div>
                </section>
            )}

            {/* Error Display */}
            {submitError && (
                <section className="w-full px-6 py-8 relative z-10">
                    <div className="max-w-4xl mx-auto">
                        <div className="bg-[rgba(255,77,109,0.05)] p-6 border border-[var(--warn)]">
                            <p className="text-[var(--warn)] text-sm font-mono flex items-center gap-3">
                                <span className="animate-blink">⚠</span> SYSTEM_ERROR: {submitError}
                            </p>
                        </div>
                    </div>
                </section>
            )}

            {/* Form Section */}
            <section className="w-full px-6 py-12 relative z-10">
                <div className="max-w-4xl mx-auto">
                    <form onSubmit={handleSubmit} className="bg-[var(--surface)] p-8 md:p-12 border border-[var(--border)] relative overflow-hidden">
                        <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-[var(--pulse)] to-transparent opacity-20"></div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-8">
                            {[
                                { name: "age", label: "Age", type: "number", placeholder: "YEARS" },
                                { name: "gender", label: "Gender", type: "select", options: ["Male", "Female", "Other"] },
                                { name: "height", label: "Height", type: "number", placeholder: "CM" },
                                { name: "weight", label: "Weight", type: "number", placeholder: "KG" },
                                { name: "bmi", label: "Body Mass Index", type: "number", value: bmi, readOnly: true, placeholder: "AUTO" },
                                { name: "bloodPressure", label: "Blood Pressure", type: "text", placeholder: "120/80" },
                                { name: "physicalActivity", label: "Activity Level", type: "select", options: ["Sedentary", "Light", "Moderate", "Active", "Very Active"] },
                                { name: "sleepHours", label: "Sleep Duration", type: "number", step: "0.5", placeholder: "HOURS" },
                                { name: "smokingHabit", label: "Smoking Habit", type: "select", options: ["No", "Yes"] },
                                { name: "diabetes", label: "Diagnosed Diabetes", type: "select", options: ["No", "Yes"] },
                                { name: "bpMedication", label: "Taking BP Medication", type: "select", options: ["No", "Yes"] },
                            ].map((field) => (
                                <div key={field.name} className="flex flex-col gap-2">
                                    <label className="text-[8px] uppercase tracking-[3px] text-[var(--dim)] font-orbitron">
                                        {field.label}
                                    </label>
                                    {field.type === "select" ? (
                                        <select
                                            name={field.name}
                                            value={formData[field.name]}
                                            onChange={handleChange}
                                            className="w-full px-4 py-3 bg-[var(--panel)] border border-[var(--border)] text-[var(--text)] text-xs font-mono focus:outline-none focus:border-[var(--pulse)] transition-colors appearance-none"
                                            required
                                        >
                                            <option value="">SELECT_{field.name.toUpperCase()}</option>
                                            {field.options.map(opt => <option key={opt} value={opt.toLowerCase()}>{opt}</option>)}
                                        </select>
                                    ) : (
                                        <div className="relative w-full">
                                            <input
                                                type={field.type}
                                                name={field.name}
                                                value={field.value !== undefined ? field.value : formData[field.name]}
                                                onChange={handleChange}
                                                step={field.step}
                                                readOnly={field.readOnly}
                                                className={`w-full px-4 py-3 bg-[var(--panel)] border border-[var(--border)] text-[var(--text)] text-xs font-mono focus:outline-none focus:border-[var(--pulse)] transition-colors ${field.readOnly ? 'opacity-50 cursor-not-allowed text-[var(--pulse)] font-bold' : ''}`}
                                                placeholder={field.placeholder}
                                                required={!field.readOnly}
                                            />
                                            {field.name === "bmi" && field.value && (
                                                <span className={`absolute right-3 top-1/2 -translate-y-1/2 font-orbitron text-[10px] tracking-widest font-bold ${getBmiCategory(field.value)?.color}`}>
                                                    {getBmiCategory(field.value)?.label}
                                                </span>
                                            )}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>

                        {/* Submit Button */}
                        <div className="mt-16 flex flex-col items-center gap-4">
                            <button
                                type="submit"
                                disabled={loading}
                                className="btn-primary min-w-[240px]"
                            >
                                {loading ? 'ANALYZING BIOMETRICS...' : 'EXECUTE DIAGNOSTIC'}
                            </button>
                            <div className="text-[8px] uppercase tracking-[2px] text-[var(--dim)]">
                                Encrypted biometric data transmission enabled
                            </div>
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