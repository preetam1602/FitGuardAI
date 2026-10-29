import os
import sys
import asyncio
import json
import logging
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from urllib.parse import urlparse, unquote

from fastapi import FastAPI, HTTPException, status, Request, Depends
from pydantic import BaseModel, EmailStr, Field, field_validator
import bcrypt
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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

# No default: a guessable fallback would let anyone forge JWTs
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is not set. Add it to backend/.env; generate one with: "
        "python -c \"import secrets; print(secrets.token_urlsafe(48))\""
    )
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# =========================
# FIX ML PATH
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ML_PATH = os.path.join(BASE_DIR, "..", "health_recommendation", "src")
sys.path.insert(0, ML_PATH)

from risk import assess_risk, parse_bp
from recommend import get_recommendations


def run_assessment(health_data: dict) -> dict:
    """Framingham CVD risk + ACC/AHA BP staging + guideline advice for one set of inputs."""
    assessment = assess_risk(health_data)
    assessment["recommendations"] = get_recommendations(assessment, health_data)
    return assessment

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

# bcrypt is deliberately slow (~0.2-0.3 s); run it in a thread so it doesn't block the event loop
async def verify_password(plain_password: str, hashed_password: str) -> bool:
    return await asyncio.to_thread(bcrypt.checkpw, plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

async def hash_password(password: str) -> str:
    hashed = await asyncio.to_thread(bcrypt.hashpw, password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

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

async def generate_diet_blueprint(health_data: dict, prediction_result: dict, **kwargs) -> dict:
    """Diet blueprint grounded in the dietary-guideline knowledge base (see src/rag). kwargs go to the pipeline."""
    global _groq_client
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set in environment")

    # Reused across requests: building a client costs ~400 ms (SSL context) and drops warm connections
    if _groq_client is None:
        _groq_client = AsyncGroq(api_key=GROQ_API_KEY)
    client = _groq_client
    try:
        return await generate_rag_diet_blueprint(client, health_data, prediction_result, **kwargs)
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

class HealthInputs(BaseModel):
    age: int = Field(ge=18, le=110)
    gender: str
    height: float = Field(ge=100, le=250)   # cm
    weight: float = Field(ge=25, le=350)    # kg
    bmi: float = 0                          # ignored for risk; recomputed from height/weight
    bloodPressure: str
    heartRate: int = Field(ge=30, le=220)
    physicalActivity: str
    sleepHours: float = Field(ge=0, le=24)
    smokingHabit: str
    diabetes: str = "no"
    bpMedication: str = "no"

    @field_validator("bloodPressure")
    @classmethod
    def _valid_bp(cls, value: str) -> str:
        systolic, diastolic = parse_bp(value)
        return f"{systolic}/{diastolic}"

class HealthAssessmentResponse(BaseModel):
    message: str
    record_id: int
    prediction: Optional[dict] = None

class PredictionResponse(BaseModel):
    risk_level: str
    cvd_risk_percent: Optional[float] = None
    cvd_category: Optional[str] = None
    heart_age: Optional[int] = None
    bmi: float
    bp: dict
    risk_factors: list
    recommendations: list
    notes: list
    model: dict

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
        
    hashed_password = await hash_password(payload.password)
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
    if not user or not await verify_password(payload.password, user["password"]):
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
    if not user or not await verify_password(form_data.password, user["password"]):
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
async def get_prediction(payload: HealthInputs):
    try:
        return PredictionResponse(**run_assessment(payload.model_dump()))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Prediction error: {str(e)}"
        )

@app.post("/api/health-assessment", response_model=HealthAssessmentResponse)
async def submit_health_assessment(
    payload: HealthInputs, request: Request, current_user: dict = Depends(get_current_user)
):
    dal: FitGuardDAL = request.app.state.dal
    user_id = current_user["id"]
    try:
        input_data = payload.model_dump()

        # 1. Risk assessment
        prediction_result = run_assessment(input_data)

        # 2. Save the record for the authenticated user
        smoking_bool = True if str(payload.smokingHabit).lower() in ("yes", "true") else False
        
        record_id = await dal.create_health_record(
            user_id=user_id,
            age=payload.age,
            gender=payload.gender,
            height_cm=payload.height,
            weight_kg=payload.weight,
            bmi=prediction_result["bmi"],
            blood_pressure=payload.bloodPressure,
            heart_rate=payload.heartRate,
            physical_activity=payload.physicalActivity,
            sleep_hours=payload.sleepHours,
            smoking_habit=smoking_bool,
            diabetes=payload.diabetes.lower() in ("yes", "true"),
            bp_medication=payload.bpMedication.lower() in ("yes", "true"),
        )

        # The diet blueprint takes 5-15 s, so it is generated separately via
        # POST /api/records/{record_id}/diet/stream and the risk result is shown immediately
        return HealthAssessmentResponse(
            message="Health assessment submitted successfully",
            record_id=record_id,
            prediction=prediction_result,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

def _record_to_inputs(record) -> dict:
    """Rebuild the HealthInputs dict the risk model and RAG pipeline expect from a saved record."""
    yes_no = lambda flag: "yes" if flag else "no"
    return {
        "age": record.age,
        "gender": record.gender,
        "height": record.height_cm,
        "weight": record.weight_kg,
        "bmi": record.bmi,
        "bloodPressure": record.blood_pressure,
        "heartRate": record.heart_rate,
        "physicalActivity": record.physical_activity,
        "sleepHours": record.sleep_hours,
        "smokingHabit": yes_no(record.smoking_habit),
        "diabetes": yes_no(record.diabetes),
        "bpMedication": yes_no(record.bp_medication),
    }

def _sse(event: str, data: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"

SSE_KEEPALIVE_S = 10
# Strong references so in-flight generations aren't garbage-collected after the client disconnects
_diet_tasks: set = set()

@app.post("/api/records/{record_id}/diet/stream")
async def stream_diet_for_record(record_id: int, request: Request, current_user: dict = Depends(get_current_user)):
    """
    Generate the diet blueprint for a saved record as Server-Sent Events:
      status {stage}  -> retrieving / generating / verifying / revising
      draft  {...}    -> first draft, shown while the critic checks it
      final  {...}    -> the saved blueprint
      error  {detail} -> generation failed
    Generation runs as its own task, so the blueprint is still saved if the client disconnects.
    """
    dal: FitGuardDAL = request.app.state.dal
    record = await dal.get_health_record(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Health record not found")
    if record.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this record")

    input_data = _record_to_inputs(record)
    prediction_result = run_assessment(input_data)
    queue: asyncio.Queue = asyncio.Queue()

    async def emit(event: str, data: dict):
        await queue.put((event, data))

    async def run():
        try:
            blueprint = await generate_diet_blueprint(input_data, prediction_result, on_event=emit)
            await dal.save_diet_blueprint(
                user_id=record.user_id,
                record_id=record_id,
                macros=blueprint.get("macros", {}),
                meal_plan=blueprint.get("meal_plan", []),
                foods_to_avoid=blueprint.get("foods_to_avoid", []),
                supplements=blueprint.get("supplements", [])
            )
            await emit("final", blueprint)
        except Exception as e:
            logger.error(f"Failed to generate or save diet blueprint for record {record_id}: {e}")
            await emit("error", {"detail": "Diet generation failed. Please try again."})
        finally:
            await queue.put(None)

    task = asyncio.create_task(run())
    _diet_tasks.add(task)
    task.add_done_callback(_diet_tasks.discard)

    async def events():
        while True:
            try:
                item = await asyncio.wait_for(queue.get(), timeout=SSE_KEEPALIVE_S)
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"  # SSE comment: keeps proxies from closing an idle connection
                continue
            if item is None:
                return
            yield _sse(*item)

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

@app.post("/api/diet/recommend")
async def recommend_diet(payload: HealthInputs):
    """Risk assessment + RAG-grounded diet blueprint, without creating a user or saving records."""
    input_data = payload.model_dump()
    try:
        prediction_result = run_assessment(input_data)
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
