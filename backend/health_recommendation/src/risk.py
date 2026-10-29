"""
Cardiovascular risk engine.

10-year general CVD risk uses the office-based (BMI, non-laboratory) Framingham equation:
    D'Agostino RB Sr et al. "General Cardiovascular Risk Profile for Use in Primary Care:
    The Framingham Heart Study." Circulation. 2008;117:743-753.
Blood pressure is staged from the user's own reading using the 2017 ACC/AHA guideline.

Nothing here is trained or random: the same inputs always give the same, citable result.
"""

import math
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class _Coefficients:
    ln_age: float
    ln_bmi: float
    ln_sbp_untreated: float
    ln_sbp_treated: float
    smoker: float
    diabetes: float
    baseline_survival: float  # S0(10)
    mean_sum: float           # sum of beta * mean(x) in the derivation cohort


# Table 3 of D'Agostino 2008 (BMI-based model)
_FRAMINGHAM_BMI = {
    "female": _Coefficients(2.72107, 0.51125, 2.81291, 2.88267, 0.61868, 0.77763, 0.94833, 26.0145),
    "male": _Coefficients(3.11296, 0.79277, 1.85508, 1.92672, 0.70953, 0.53160, 0.88431, 23.9388),
}

VALIDATED_AGE_RANGE = (30, 74)  # ages in the Framingham derivation cohort
SCORED_AGE_RANGE = (19, 74)     # ages we score; 19-29 is an extrapolation of the equation

# Risk factor values the paper uses to define "heart age" (an otherwise optimal person)
_OPTIMAL = {"bmi": 22.5, "sbp": 125.0, "treated": False, "smoker": False, "diabetic": False}

MODEL_INFO = {
    "name": "Framingham 10-year general CVD risk (office-based, BMI)",
    "reference": "D'Agostino RB Sr et al. Circulation. 2008;117:743-753",
    "bp_reference": "2017 ACC/AHA Guideline for High Blood Pressure in Adults",
}


# =========================
# INPUT PARSING
# =========================
def _truthy(value) -> bool:
    return str(value).strip().lower() in ("yes", "true", "1", "y")


def parse_bp(value) -> Tuple[int, int]:
    """Parse "120/80" into (systolic, diastolic). Raises ValueError on anything else."""
    try:
        systolic, diastolic = (int(round(float(p))) for p in str(value).split("/"))
    except (ValueError, TypeError):
        raise ValueError(f"Blood pressure must look like '120/80', got {value!r}")
    if not (70 <= systolic <= 260 and 40 <= diastolic <= 160) or diastolic >= systolic:
        raise ValueError(f"Blood pressure {value!r} is outside a plausible range")
    return systolic, diastolic


def _bmi(data: Dict) -> float:
    # Recompute from height/weight rather than trusting a client-supplied BMI
    height, weight = data.get("height"), data.get("weight")
    if height and weight:
        return float(weight) / ((float(height) / 100) ** 2)
    if data.get("bmi"):
        return float(data["bmi"])
    raise ValueError("Height and weight are required to compute BMI")


def _sex(data: Dict) -> Optional[str]:
    gender = str(data.get("gender") or "").strip().lower()
    if gender in ("male", "m"):
        return "male"
    if gender in ("female", "f"):
        return "female"
    return None


# =========================
# FRAMINGHAM
# =========================
def _framingham_sum(c: _Coefficients, age: float, bmi: float, sbp: float,
                    treated: bool, smoker: bool, diabetic: bool) -> float:
    sbp_beta = c.ln_sbp_treated if treated else c.ln_sbp_untreated
    return (
        c.ln_age * math.log(age)
        + c.ln_bmi * math.log(bmi)
        + sbp_beta * math.log(sbp)
        + c.smoker * smoker
        + c.diabetes * diabetic
    )


def _risk_from_sum(c: _Coefficients, total: float) -> float:
    return 1 - c.baseline_survival ** math.exp(total - c.mean_sum)


def _framingham_risk(c: _Coefficients, **factors) -> float:
    return _risk_from_sum(c, _framingham_sum(c, **factors))


def _heart_age(c: _Coefficients, total: float) -> float:
    """Age at which a person with optimal risk factors has the same risk."""
    o = _OPTIMAL
    rest = _framingham_sum(c, 1.0, o["bmi"], o["sbp"], o["treated"], o["smoker"], o["diabetic"])
    return math.exp((total - rest) / c.ln_age)


def _cvd_category(risk: float) -> str:
    # Framingham / ATP III bands
    if risk < 0.10:
        return "Low"
    if risk < 0.20:
        return "Intermediate"
    return "High"


# =========================
# BLOOD PRESSURE STAGING
# =========================
def bp_stage(systolic: int, diastolic: int) -> Dict:
    if systolic > 180 or diastolic > 120:
        stage, urgent = "Hypertensive Crisis", True
    elif systolic >= 140 or diastolic >= 90:
        stage, urgent = "Stage 2 Hypertension", False
    elif systolic >= 130 or diastolic >= 80:
        stage, urgent = "Stage 1 Hypertension", False
    elif systolic >= 120:
        stage, urgent = "Elevated", False
    else:
        stage, urgent = "Normal", False
    return {"systolic": systolic, "diastolic": diastolic, "stage": stage, "urgent": urgent}


# =========================
# PUBLIC API
# =========================
def assess_risk(data: Dict) -> Dict:
    systolic, diastolic = parse_bp(data.get("bloodPressure"))
    bmi = _bmi(data)
    age = int(data["age"])
    smoker = _truthy(data.get("smokingHabit"))
    diabetic = _truthy(data.get("diabetes"))
    treated = _truthy(data.get("bpMedication"))
    sex = _sex(data)

    result = {
        "bp": bp_stage(systolic, diastolic),
        "bmi": round(bmi, 1),
        "cvd_risk_percent": None,
        "cvd_category": None,
        "heart_age": None,
        "risk_factors": [],
        "notes": [],
        "model": MODEL_INFO,
    }

    if sex is None:
        result["notes"].append(
            "The Framingham equation is sex-specific, so a 10-year risk can't be estimated "
            "for this gender selection. Blood pressure staging still applies."
        )
    elif age < SCORED_AGE_RANGE[0]:
        result["notes"].append(
            f"A 10-year heart risk is only estimated from age {SCORED_AGE_RANGE[0]}. Blood pressure staging still applies."
        )
    else:
        c = _FRAMINGHAM_BMI[sex]
        validated_lo, _ = VALIDATED_AGE_RANGE
        _, hi = SCORED_AGE_RANGE
        model_age = min(age, hi)
        if age < validated_lo:
            result["notes"].append(
                f"The Framingham equation was developed on adults aged {validated_lo}-{hi}. At your age the "
                "estimate is an extrapolation, so treat it as a rough guide; your risk factors matter more than the number."
            )
        elif age > hi:
            result["notes"].append(
                f"The equation is validated up to age {hi}; your estimate is calculated at age {hi} "
                "and likely understates your actual risk."
            )

        factors = dict(age=model_age, bmi=bmi, sbp=systolic, treated=treated, smoker=smoker, diabetic=diabetic)
        total = _framingham_sum(c, **factors)
        risk = _risk_from_sum(c, total)

        result["cvd_risk_percent"] = round(risk * 100, 1)
        result["cvd_category"] = _cvd_category(risk)
        result["heart_age"] = round(_heart_age(c, total))

        # How much each modifiable factor adds: risk now minus risk with that factor at its optimal value
        improvements = {
            "Smoking": (smoker, {"smoker": False}, "Quit smoking"),
            "Systolic blood pressure": (systolic > _OPTIMAL["sbp"], {"sbp": _OPTIMAL["sbp"]},
                                        f"Bring systolic BP to {int(_OPTIMAL['sbp'])} mmHg"),
            "BMI": (bmi > _OPTIMAL["bmi"], {"bmi": _OPTIMAL["bmi"]}, f"Reach a BMI of {_OPTIMAL['bmi']}"),
        }
        for name, (applies, change, action) in improvements.items():
            if not applies:
                continue
            reduced = _framingham_risk(c, **{**factors, **change})
            delta = round((risk - reduced) * 100, 1)
            if delta > 0:
                result["risk_factors"].append({"factor": name, "action": action, "risk_reduction_percent": delta})
        result["risk_factors"].sort(key=lambda f: f["risk_reduction_percent"], reverse=True)

        if diabetic:
            result["notes"].append("Diabetes substantially raises cardiovascular risk; keep it well controlled with your doctor.")

    result["risk_level"] = _overall_level(result)
    return result


def _overall_level(result: Dict) -> str:
    """Single headline level, taking whichever of CVD risk and BP stage is worse."""
    stage = result["bp"]["stage"]
    bp_level = {
        "Normal": "Low",
        "Elevated": "Intermediate",
        "Stage 1 Hypertension": "Intermediate",
        "Stage 2 Hypertension": "High",
        "Hypertensive Crisis": "High",
    }[stage]
    order = ["Low", "Intermediate", "High"]
    levels = [bp_level] + ([result["cvd_category"]] if result["cvd_category"] else [])
    return max(levels, key=order.index)
