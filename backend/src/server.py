from contextlib import asynccontextmanager
import os
import sys
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
import bcrypt
from fastapi.middleware.cors import CORSMiddleware
from fastapi import status
import uvicorn
from dotenv import load_dotenv
from typing import Optional

# Add path to Health Recommendation module
ML_MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Health Recommendation/model"))
sys.path.insert(0, ML_MODEL_PATH)

from src.predict import predict_bp
from src.recommend import get_recommendations

load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI")
DEBUG=os.environ.get("DEBUG","false").lower()=="true"
PORT=int(os.environ.get("PORT",3001))

USERS_COLLECTION="users"
HEALTH_COLLECTION="health_records"


@asynccontextmanager
async def lifespan(app:FastAPI):
    client=AsyncIOMotorClient(MONGO_URI)
    database=client["Health_System"]

    pong=await database.command("ping")
    if int(pong["ok"])!=1:
        raise Exception("Cluster connection is not okay")
    
    app.dal = FitGuardDAL(
        users_collection=database.get_collection(USERS_COLLECTION),
        health_collection=database.get_collection(HEALTH_COLLECTION),
    )

    yield
    client.close()
app=FastAPI(lifespan=lifespan,debug=DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthAssessmentRequest(BaseModel):
    name: str
    email: EmailStr    # validates format — rejects "notanemail"
    password: str
    age: int
    gender: str
    height: float
    weight: float
    bmi: float
    bloodPressure: str
    heartRate: int
    physicalActivity: str
    sleepHours: float
    smokingHabit: str  # "yes" or "no"

class HealthAssessmentResponse(BaseModel):
    user_id: str
    record_id: str
    message: str
    prediction: Optional[dict] = None


class PredictionResponse(BaseModel):
    predicted_bp: float
    risk_level: str
    recommendations: list



@app.post(
    "/api/health-assessment",
    status_code=status.HTTP_201_CREATED,
    response_model=HealthAssessmentResponse,
)

async def submit_health_assessment(payload:HealthAssessmentRequest):
    existing=await app.dal.get_user_by_email(payload.email)

    if(existing):
        if not bcrypt.checkpw(payload.password.encode(),
                              existing["password"].encode()):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid crendtials",
            )
        user_id=str(existing["_id"])
    else:
        hashed=bcrypt.hashpw(
            payload.password.encode(),
            bcrypt.gensalt()
        ).decode()
        user_id = await app.dal.create_user(
            name=payload.name,
            email=payload.email,
            hashed_password=hashed,
        )

    record_id = await app.dal.create_health_record(
        user_id=user_id,
        age=payload.age,
        gender=payload.gender,
        height_cm=payload.height,
        weight_kg=payload.weight,
        bmi=payload.bmi,
        blood_pressure=payload.bloodPressure,
        heart_rate=payload.heartRate,
        physical_activity=payload.physicalActivity,
        sleep_hours=payload.sleepHours,
        smoking_habit=payload.smokingHabit == "yes",
    )

    # Get ML predictions
    try:
        input_data = {
            "age": payload.age,
            "gender": payload.gender,
            "height": payload.height,
            "weight": payload.weight,
            "bmi": payload.bmi,
            "bloodPressure": payload.bloodPressure,
            "heartRate": payload.heartRate,
            "physicalActivity": payload.physicalActivity,
            "sleepHours": payload.sleepHours,
            "smokingHabit": payload.smokingHabit,
        }
        predicted_bp = predict_bp(input_data)
        prediction_result = get_recommendations(predicted_bp)
    except Exception as e:
        print(f"ML Prediction error: {e}")
        prediction_result = None

    return HealthAssessmentResponse(
        user_id=user_id,
        record_id=record_id,
        message="Health assessment submitted successfully!",
        prediction=prediction_result,
    )

@app.get("/api/users/{user_id}/records", response_model=list[HealthRecord])
async def get_user_records(user_id: str):
    return await app.dal.get_health_records_by_user(user_id)


@app.get("/api/records/{record_id}", response_model=HealthRecord)
async def get_record(record_id: str):
    record = await app.dal.get_health_record(record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Record not found"
        )
    return record


@app.post("/api/predict", response_model=PredictionResponse)
async def get_prediction(payload: dict):
    """Get ML prediction for health data without saving to database"""
    try:
        predicted_bp = predict_bp(payload)
        prediction_result = get_recommendations(predicted_bp)
        return PredictionResponse(**prediction_result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Prediction error: {str(e)}"
        )

def main(argv=sys.argv[1:]):
    try:
        uvicorn.run(
            "server:app",
            host="0.0.0.0",
            port=PORT,
            workers=1,
            reload=DEBUG,  
        )
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
