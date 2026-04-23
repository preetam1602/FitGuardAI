from contextlib import asynccontextmanager
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr
import bcrypt
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import Optional

# =========================
# LOAD ENV
# =========================
load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

USERS_COLLECTION = "users"
HEALTH_COLLECTION = "health_records"

# =========================
# FIX ML PATH
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ML_PATH = os.path.join(BASE_DIR, "..", "health_recommendation", "src")
sys.path.insert(0, ML_PATH)

from predict import predict_bp
from recommend import get_recommendations

# =========================
# DATABASE LIFESPAN
# =========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncIOMotorClient(MONGO_URI)
    database = client["Health_System"]

    pong = await database.command("ping")
    if int(pong["ok"]) != 1:
        raise Exception("DB connection failed")

    app.db = database

    yield
    client.close()

# =========================
# APP INIT
# =========================
app = FastAPI(lifespan=lifespan, debug=DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# MODELS
# =========================
class HealthAssessmentRequest(BaseModel):
    name: str
    email: EmailStr
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
    smokingHabit: str

class HealthAssessmentResponse(BaseModel):
    message: str
    prediction: Optional[dict] = None

class PredictionResponse(BaseModel):
    predicted_bp: float
    risk_level: str
    recommendations: list

# =========================
# ROUTES
# =========================
@app.get("/")
def home():
    return {"status": "API running"}

@app.post("/api/predict", response_model=PredictionResponse)
async def get_prediction(payload: dict):
    try:
        predicted_bp = predict_bp(payload)
        prediction_result = get_recommendations(predicted_bp)
        return PredictionResponse(**prediction_result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Prediction error: {str(e)}"
        )

@app.post("/api/health-assessment", response_model=HealthAssessmentResponse)
async def submit_health_assessment(payload: HealthAssessmentRequest):
    try:
        input_data = payload.dict()
        predicted_bp = predict_bp(input_data)
        prediction_result = get_recommendations(predicted_bp)

        return HealthAssessmentResponse(
            message="Health assessment submitted",
            prediction=prediction_result,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

