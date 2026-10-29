# Cardiovascular Risk Engine

Estimates a user's 10-year cardiovascular disease risk and stages their blood pressure using
published, validated clinical methods. There is no trained model: the same inputs always give the
same, explainable result.

| Output | Method |
| --- | --- |
| 10-year CVD risk (%) and category | Framingham general CVD risk, office-based BMI model. D'Agostino RB Sr et al., *Circulation* 2008;117:743-753 |
| Heart age | Same paper: the age at which a person with optimal risk factors (SBP 125 untreated, BMI 22.5, non-smoker, non-diabetic) has the same risk |
| Blood pressure stage | 2017 ACC/AHA guideline (Normal / Elevated / Stage 1 / Stage 2 / Hypertensive Crisis) |
| Risk factor breakdown | Risk now minus risk with that factor at its optimal value (smoking, systolic BP, BMI) |

Risk categories: **Low** < 10%, **Intermediate** 10-20%, **High** ≥ 20%. The headline `risk_level`
is whichever is worse: the CVD category or the BP stage (Stage 2 or crisis counts as High).

## Limits

- Ages 19-74 are scored. The equation was derived on ages 30-74, so scores for 19-29 are an
  extrapolation and carry a note saying so. Users over 74 are scored at 74 (likely an underestimate)
  and flagged; under 19 gets BP staging only.
- It is sex-specific, so no percentage is produced for other gender selections; BP staging still applies.
- Heart rate, activity and sleep are not in the equation. They only shape the recommendations.
- It is a screening estimate, not a diagnosis.

## Layout

```
src/
├── risk.py        # Framingham equation, heart age, BP staging, factor breakdown
└── recommend.py   # Guideline-based advice from the assessment + raw inputs
app.py             # Optional standalone API (the main app uses these modules via backend/src/server.py)
```

## Standalone API

```bash
uvicorn app:app --reload
```

`POST /predict`

```json
{
  "age": 50, "gender": "male", "height": 175, "weight": 80,
  "bloodPressure": "135/85", "smokingHabit": "yes", "diabetes": "no", "bpMedication": "no",
  "physicalActivity": "light", "sleepHours": 6, "heartRate": 78
}
```

The response includes `risk_level`, `cvd_risk_percent`, `cvd_category`, `heart_age`, `bmi`,
`bp` (`systolic`, `diastolic`, `stage`, `urgent`), `risk_factors`, `recommendations`, `notes` and `model`.

## Tests

```bash
cd backend && python -m pytest tests
```
