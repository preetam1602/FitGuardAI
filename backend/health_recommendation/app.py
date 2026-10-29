from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.risk import assess_risk
from src.recommend import get_recommendations


app = FastAPI()


class HealthInput(BaseModel):
    age: int
    gender: str               # "male" / "female"
    height: float             # cm
    weight: float             # kg
    bloodPressure: str        # "120/80"
    heartRate: int = 72
    physicalActivity: str = "moderate"
    sleepHours: float = 7
    smokingHabit: str = "no"
    diabetes: str = "no"
    bpMedication: str = "no"


@app.get("/")
def home():
    return {"message": "Cardiovascular Risk API Running"}


@app.post("/predict")
def predict(data: HealthInput):
    input_data = data.model_dump()
    try:
        result = assess_risk(input_data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    result["recommendations"] = get_recommendations(result, input_data)
    return result
