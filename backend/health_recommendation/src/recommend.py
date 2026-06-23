def get_recommendations(predicted_bp: float):
    """
    Takes predicted blood pressure and returns
    risk level + suggestions
    """

    if predicted_bp < 120:
        risk = "Normal"
        advice = [
            "Maintain a balanced diet",
            "Exercise regularly",
            "Continue healthy lifestyle"
        ]

    elif 120 <= predicted_bp < 140:
        risk = "Elevated"
        advice = [
            "Reduce salt intake",
            "Increase physical activity",
            "Monitor blood pressure regularly"
        ]

    else:
        risk = "High"
        advice = [
            "Consult a doctor",
            "Follow low-sodium diet",
            "Exercise daily",
            "Manage stress levels"
        ]

    return {
        "predicted_bp": predicted_bp,
        "risk_level": risk,
        "recommendations": advice
    }