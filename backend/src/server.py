import os
import sys
import asyncio
import json
import logging
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from urllib.parse import urlparse, unquote

from fastapi import FastAPI, HTTPException, status, Request, Depends
from pydantic import BaseModel, EmailStr
import bcrypt
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import Optional, Any
import asyncpg
from groq import AsyncGroq
import jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from dal import FitGuardDAL
from rag import generate_rag_diet_blueprint, get_retriever

logger = logging.getLogger(__name__)

# =========================
# LOAD ENV
# =========================
load_dotenv()

db_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
if db_url.startswith("postgresql+psycopg://"):
    db_url = db_url.replace("postgresql+psycopg://", "postgresql://", 1)

# Parse the DB URL into components so we can pass them individually to asyncpg.
# This is necessary because asyncpg doesn't decode percent-encoded characters in
# DSN strings — e.g. a password containing '@' encoded as '%40' would break
# the hostname resolution. Decoding only the password field avoids this.
_parsed = urlparse(db_url)
PG_HOST = _parsed.hostname or "localhost"
PG_PORT = _parsed.port or 5432
PG_USER = unquote(_parsed.username or "postgres")
PG_PASS = unquote(_parsed.password or "")
PG_DB   = (_parsed.path or "/postgres").lstrip("/")

DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", FRONTEND_URL).split(",")
    if origin.strip()
]

SECRET_KEY = os.environ.get("SECRET_KEY", "fallback_secret_key")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# =========================
# FIX ML PATH
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ML_PATH = os.path.join(BASE_DIR, "..", "health_recommendation", "src")
sys.path.insert(0, ML_PATH)

from predict import predict_bp
from recommend import get_recommendations

# =========================
# JWT UTILS
# =========================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email: str = payload.get("sub")
        if user_email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    dal: FitGuardDAL = request.app.state.dal
    user = await dal.get_user_by_email(user_email)
    if user is None:
        raise credentials_exception
    return user

# =========================
# GROQ INTEGRATION
# =========================
_groq_client: Optional[AsyncGroq] = None

async def generate_diet_blueprint(health_data: dict, prediction_result: dict) -> dict:
    """Diet blueprint grounded in the dietary-guideline knowledge base (see src/rag)."""
    global _groq_client
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set in environment")

    # Reused across requests: building a client costs ~400 ms (SSL context) and drops warm connections
    if _groq_client is None:
        _groq_client = AsyncGroq(api_key=GROQ_API_KEY)
    client = _groq_client
    try:
        return await generate_rag_diet_blueprint(client, health_data, prediction_result)
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        raise e

# =========================
# DATABASE LIFESPAN
# =========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Use explicit kwargs instead of a DSN string to avoid percent-encoding issues.
    pool = await asyncpg.create_pool(
        host=PG_HOST,
        port=PG_PORT,
        user=PG_USER,
        password=PG_PASS,
        database=PG_DB,
    )
    dal = FitGuardDAL(pool)
    await dal.create_tables()
    app.state.dal = dal
    # Load/build the RAG index in the background so startup isn't blocked
    asyncio.create_task(asyncio.to_thread(get_retriever))
    yield
    await pool.close()

# =========================
# APP INIT
# =========================
app = FastAPI(lifespan=lifespan, debug=DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# MODELS
# =========================
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

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
    diet_blueprint: Optional[dict] = None
    access_token: Optional[str] = None

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

@app.post("/api/register")
async def register(payload: RegisterRequest, request: Request):
    dal: FitGuardDAL = request.app.state.dal
    user = await dal.get_user_by_email(payload.email)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_password = bcrypt.hashpw(payload.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user_id = await dal.create_user(payload.name, payload.email, hashed_password)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": payload.email, "user_id": user_id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/login")
async def login(payload: LoginRequest, request: Request):
    dal: FitGuardDAL = request.app.state.dal
    user = await dal.get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"], "user_id": user["id"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user["id"], "name": user["name"], "email": user["email"]}}

@app.post("/api/token")
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    dal: FitGuardDAL = request.app.state.dal
    user = await dal.get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"], "user_id": user["id"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/token/refresh")
async def refresh_access_token(current_user: dict = Depends(get_current_user)):
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user["email"], "user_id": current_user["id"]},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/users/me")
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "name": current_user["name"],
        "email": current_user["email"],
    }

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
async def submit_health_assessment(payload: HealthAssessmentRequest, request: Request):
    dal: FitGuardDAL = request.app.state.dal
    try:
        input_data = payload.dict()
        
        # 1. Get ML Prediction
        predicted_bp = predict_bp(input_data)
        prediction_result = get_recommendations(predicted_bp)
        
        # 2. Database save: ensure user exists and verify password
        user = await dal.get_user_by_email(payload.email)
        if not user:
            hashed_password = bcrypt.hashpw(payload.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user_id = await dal.create_user(payload.name, payload.email, hashed_password)
        else:
            if not verify_password(payload.password, user["password"]):
                raise HTTPException(status_code=401, detail="Incorrect password for existing user")
            user_id = user["id"]
            
        smoking_bool = True if str(payload.smokingHabit).lower() in ("yes", "true") else False
        
        record_id = await dal.create_health_record(
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
            smoking_habit=smoking_bool
        )

        # 3. Groq Diet Blueprint
        diet_blueprint = None
        try:
            diet_blueprint = await generate_diet_blueprint(input_data, prediction_result)
            await dal.save_diet_blueprint(
                user_id=user_id,
                record_id=record_id,
                macros=diet_blueprint.get("macros", {}),
                meal_plan=diet_blueprint.get("meal_plan", []),
                foods_to_avoid=diet_blueprint.get("foods_to_avoid", []),
                supplements=diet_blueprint.get("supplements", [])
            )
        except Exception as e:
            logger.error(f"Failed to generate or save diet blueprint: {e}")

        # 4. Generate JWT token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": payload.email, "user_id": user_id}, expires_delta=access_token_expires
        )

        return HealthAssessmentResponse(
            message="Health assessment submitted successfully",
            prediction=prediction_result,
            diet_blueprint=diet_blueprint,
            access_token=access_token
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

class DietRecommendationRequest(BaseModel):
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

@app.post("/api/diet/recommend")
async def recommend_diet(payload: DietRecommendationRequest):
    """ML prediction + RAG-grounded diet blueprint, without creating a user or saving records."""
    input_data = payload.dict()
    try:
        predicted_bp = predict_bp(input_data)
        prediction_result = get_recommendations(predicted_bp)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")
    try:
        diet_blueprint = await generate_diet_blueprint(input_data, prediction_result)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Diet generation failed: {str(e)}")
    return {"prediction": prediction_result, "diet_blueprint": diet_blueprint}

@app.get("/api/rag/status")
async def rag_status():
    retriever = await asyncio.to_thread(get_retriever, False)
    if retriever is None:
        return {"ready": False, "chunks": 0}
    sources = sorted({c["source"] for c in retriever.chunks})
    return {"ready": True, "chunks": len(retriever.chunks), "sources": sources}

@app.get("/api/records/{record_id}/diet")
async def get_diet_by_record(record_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    dal: FitGuardDAL = request.app.state.dal
    blueprint = await dal.get_diet_blueprint_by_record(record_id)
    if not blueprint:
        raise HTTPException(status_code=404, detail="Diet blueprint not found for this record")
    if blueprint.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this blueprint")
    return blueprint

@app.get("/api/users/{user_id}/diets")
async def get_diets_by_user(user_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    dal: FitGuardDAL = request.app.state.dal
    if user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access these blueprints")
    blueprints = await dal.get_diet_blueprints_by_user(user_id)
    return blueprints

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 3001))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=DEBUG)
