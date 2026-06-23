from fastapi import FastAPI
from pydantic import BaseModel

from src.predict import predict_bp
from src.recommend import get_recommendations


app = FastAPI()


# Input schema (numeric health data)
class HealthInput(BaseModel):
    age: int
    gender: int            # 0 = Female, 1 = Male
    height: float
    weight: float
    bmi: float
    bloodPressure: int     # 0 = Normal, 1 = Elevated, 2 = High
    heartRate: int
    physicalActivity: int  # 0 = Low, 1 = High
    sleepHours: float
    smokingHabit: int      # 0 = No, 1 = Yes


@app.get("/")
def home():
    return {"message": "Health Risk Prediction API Running"}


@app.post("/predict")
def predict(data: HealthInput):
    try:
        # Convert input to dictionary
        input_data = data.model_dump()

        # Predict BP
        predicted_bp = predict_bp(input_data)

        # Get recommendations (personalized using the original inputs)
        result = get_recommendations(predicted_bp, health_data=input_data)

        return result

    except Exception as e:
        return {"error": str(e)}