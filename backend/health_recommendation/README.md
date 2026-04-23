# Health Recommendation API

A FastAPI-based machine learning project that predicts blood pressure (`trestbps`) from health inputs and returns risk-based lifestyle recommendations.

## Project Structure

```
model/
├── app.py
├── requirements.txt
├── data/
│   └── heart.csv
├── models/
├── notebooks/
│   └── training.ipynb
└── src/
    ├── preprocess.py
    ├── train.py
    ├── predict.py
    └── recommend.py
```

## Features

- Trains a `LinearRegression` model on transformed heart-disease dataset features.
- Saves trained artifacts:
  - `models/model.pkl`
  - `models/scaler.pkl`
- Exposes REST API endpoints using FastAPI.
- Returns BP risk category with practical recommendations:
  - Normal
  - Elevated
  - High

## Tech Stack

- Python 3.9+
- FastAPI
- Uvicorn
- Pandas
- NumPy
- Scikit-learn
- Joblib

## Setup

1. Open terminal in the `model` folder.
2. (Optional but recommended) Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install fastapi uvicorn pandas numpy scikit-learn joblib
```

> Note: `requirements.txt` is currently empty. You can populate it later with `pip freeze > requirements.txt`.

## Train the Model

Before running predictions, train and save the model/scaler:

```bash
python -m src.train
```

Expected output includes MAE, R2 score, and a confirmation that the model was saved.

## Run the API

```bash
uvicorn app:app --reload
```

Server starts at:

- API root: `http://127.0.0.1:8000/`
- Swagger docs: `http://127.0.0.1:8000/docs`

## API Endpoints

### `GET /`
Health check endpoint.

**Response**
```json
{
  "message": "Health Risk Prediction API Running"
}
```

### `POST /predict`
Predicts blood pressure and returns risk + recommendations.

**Request Body**
```json
{
  "age": 45,
  "gender": 1,
  "height": 172.5,
  "weight": 78.0,
  "bmi": 26.2,
  "bloodPressure": 1,
  "heartRate": 82,
  "physicalActivity": 1,
  "sleepHours": 7.0,
  "smokingHabit": 0
}
```

**Response (example)**
```json
{
  "predicted_bp": 132.4,
  "risk_level": "Elevated",
  "recommendations": [
    "Reduce salt intake",
    "Increase physical activity",
    "Monitor blood pressure regularly"
  ]
}
```

## Input Field Notes

- `gender`: `0 = Female`, `1 = Male`
- `bloodPressure` category: `0 = Normal`, `1 = Elevated`, `2 = High`
- `physicalActivity`: `0 = Low`, `1 = High`
- `smokingHabit`: `0 = No`, `1 = Yes`

## Common Issues

- `FileNotFoundError` for model/scaler: run training first (`python -m src.train`).
- Import errors: ensure dependencies are installed in the active Python environment.

## Future Improvements

- Add proper `requirements.txt` with pinned versions.
- Add model evaluation report and validation metrics logging.
- Add unit tests for preprocessing, prediction, and recommendation logic.
