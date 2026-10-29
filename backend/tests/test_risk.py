import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "health_recommendation", "src"))

from risk import assess_risk, bp_stage, parse_bp  # noqa: E402
from recommend import get_recommendations  # noqa: E402


def profile(**overrides):
    base = {
        "age": 50, "gender": "male", "height": 200, "weight": 100,  # BMI 25.0
        "bloodPressure": "120/78", "smokingHabit": "no", "diabetes": "no", "bpMedication": "no",
        "physicalActivity": "moderate", "sleepHours": 7.5, "heartRate": 70,
    }
    return {**base, **overrides}


def test_reference_value_male():
    # Hand-computed from the published coefficients: sum 23.611, exp(sum - 23.9388) = 0.720, 1 - 0.88431^0.720
    assert assess_risk(profile())["cvd_risk_percent"] == pytest.approx(8.5, abs=0.2)


def test_heart_age_equals_age_for_optimal_profile():
    # 22.5 BMI at 200 cm is 90 kg; SBP 125 untreated, non-smoker, non-diabetic
    result = assess_risk(profile(weight=90, bloodPressure="125/75"))
    assert result["heart_age"] == 50
    assert result["risk_factors"] == []


@pytest.mark.parametrize("change", [
    {"smokingHabit": "yes"}, {"diabetes": "yes"}, {"bloodPressure": "150/85"},
    {"weight": 130}, {"age": 65}, {"bpMedication": "yes"},
])
def test_each_risk_factor_raises_risk(change):
    assert assess_risk(profile(**change))["cvd_risk_percent"] > assess_risk(profile())["cvd_risk_percent"]


def test_women_have_lower_risk_than_men_at_same_profile():
    assert assess_risk(profile(gender="female"))["cvd_risk_percent"] < assess_risk(profile())["cvd_risk_percent"]


def test_smoking_is_reported_as_a_modifiable_factor():
    factors = {f["factor"]: f for f in assess_risk(profile(smokingHabit="yes"))["risk_factors"]}
    assert factors["Smoking"]["risk_reduction_percent"] > 0


def test_ages_19_to_29_are_scored_at_actual_age_and_flagged():
    young = assess_risk(profile(age=22))
    assert 0 < young["cvd_risk_percent"] < assess_risk(profile(age=30))["cvd_risk_percent"]
    assert any("extrapolation" in n for n in young["notes"])
    assert assess_risk(profile(age=19))["cvd_risk_percent"] is not None


def test_under_19_gets_bp_stage_only():
    result = assess_risk(profile(age=18, bloodPressure="135/85"))
    assert result["cvd_risk_percent"] is None
    assert result["bp"]["stage"] == "Stage 1 Hypertension"


def test_over_74_is_clamped_and_flagged():
    old = assess_risk(profile(age=80))
    assert old["cvd_risk_percent"] == assess_risk(profile(age=74))["cvd_risk_percent"]
    assert any("understates" in n for n in old["notes"])


def test_other_gender_still_gets_bp_stage():
    result = assess_risk(profile(gender="other", bloodPressure="145/92"))
    assert result["cvd_risk_percent"] is None
    assert result["bp"]["stage"] == "Stage 2 Hypertension"
    assert result["risk_level"] == "High"


@pytest.mark.parametrize("sys_bp, dia_bp, stage", [
    (118, 78, "Normal"), (125, 78, "Elevated"), (125, 82, "Stage 1 Hypertension"),
    (135, 70, "Stage 1 Hypertension"), (140, 70, "Stage 2 Hypertension"), (120, 95, "Stage 2 Hypertension"),
    (185, 100, "Hypertensive Crisis"), (160, 125, "Hypertensive Crisis"),
])
def test_bp_stages(sys_bp, dia_bp, stage):
    assert bp_stage(sys_bp, dia_bp)["stage"] == stage


def test_crisis_is_urgent_and_advice_leads_with_emergency():
    result = assess_risk(profile(bloodPressure="190/110"))
    assert result["bp"]["urgent"] is True
    assert "emergency" in get_recommendations(result, profile())[0]


@pytest.mark.parametrize("value", ["120", "abc", "80/120", "400/80", ""])
def test_invalid_bp_rejected(value):
    with pytest.raises(ValueError):
        parse_bp(value)


def test_bmi_recomputed_from_height_and_weight():
    assert assess_risk(profile(bmi=99))["bmi"] == 25.0
