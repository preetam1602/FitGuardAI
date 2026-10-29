from typing import Dict, List


def _truthy(value) -> bool:
    return str(value).strip().lower() in ("yes", "true", "1", "y")


def get_recommendations(assessment: Dict, health_data: Dict) -> List[str]:
    """Guideline-based advice driven by the risk assessment and the user's own inputs."""
    advice: List[str] = []
    stage = assessment["bp"]["stage"]

    if assessment["bp"]["urgent"]:
        advice.append(
            "Your reading is in the hypertensive crisis range. Re-measure after 5 minutes of rest; "
            "if it is still above 180/120, or you have chest pain, breathlessness, weakness or vision changes, "
            "seek emergency care now."
        )
    elif stage == "Stage 2 Hypertension":
        advice.append("See a doctor soon: stage 2 readings usually need medication alongside lifestyle changes.")
    elif stage == "Stage 1 Hypertension":
        advice.append("Discuss this reading with a doctor and re-check your BP at home over the next few weeks.")

    if stage != "Normal":
        advice.append("Keep salt under 5 g a day and eat more potassium-rich vegetables, fruits and pulses (DASH-style).")

    if assessment.get("cvd_category") == "High":
        advice.append("Your 10-year cardiovascular risk is high; ask a doctor about a lipid profile and blood sugar test.")

    if _truthy(health_data.get("smokingHabit")):
        advice.append("Quitting smoking is the single biggest change you can make to your heart risk.")

    bmi = assessment.get("bmi") or 0
    if bmi >= 25:
        advice.append("Losing 5-10% of your body weight lowers blood pressure and cardiovascular risk.")
    elif 0 < bmi < 18.5:
        advice.append("Your BMI is below the healthy range; focus on nutrient-dense meals to regain weight.")

    activity = str(health_data.get("physicalActivity") or "").lower()
    if activity in ("sedentary", "light"):
        advice.append("Build up to at least 150 minutes of moderate activity a week, such as brisk walking.")

    sleep = health_data.get("sleepHours")
    if sleep is not None and float(sleep) < 7:
        advice.append("Aim for 7-9 hours of sleep; short sleep is linked to higher blood pressure.")

    heart_rate = health_data.get("heartRate")
    if heart_rate is not None and int(heart_rate) > 100:
        advice.append("A resting heart rate above 100 bpm is worth checking with a doctor.")

    if not advice:
        advice.append("Your numbers look healthy. Keep up a balanced diet, regular activity and yearly check-ups.")
    return advice
