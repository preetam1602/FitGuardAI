import os
import sys
import asyncio
import hashlib
import json
import logging
import math
import secrets
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from urllib.parse import urlparse, unquote

from fastapi import FastAPI, HTTPException, status, Request, Response, Depends
from pydantic import BaseModel, EmailStr, Field, field_validator
import bcrypt
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from dotenv import load_dotenv
from typing import Optional, Any
import asyncpg
from groq import AsyncGroq
import jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from dal import FitGuardDAL
from rate_limit import SlidingWindowLimiter
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

# No default: a guessable key (or the .env.example placeholder) would let anyone forge JWTs
SECRET_KEY = os.environ.get("SECRET_KEY", "")
if len(SECRET_KEY) < 32 or SECRET_KEY == "your_jwt_secret_key_here":
    raise RuntimeError(
        "SECRET_KEY must be set to a random value of at least 32 characters in backend/.env; "
        "generate one with: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
    )
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
# Access tokens live only in the browser's memory and are short-lived; the long-lived refresh
# token sits in an httpOnly cookie that page scripts (and so XSS) can't read
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
REFRESH_COOKIE_NAME = "fitguard_refresh"
REFRESH_COOKIE_PATH = "/api/auth"  # the browser sends the cookie to the refresh/logout endpoints only
# Browsers accept Secure cookies on http://localhost, so this only needs to be false for plain-HTTP non-localhost hosts
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "true").lower() == "true"

# Brute-force protection for the auth endpoints
LOGIN_WINDOW_S = int(os.environ.get("LOGIN_WINDOW_S", "900"))                       # 15 min
LOGIN_MAX_ATTEMPTS_PER_EMAIL = int(os.environ.get("LOGIN_MAX_ATTEMPTS_PER_EMAIL", "5"))
LOGIN_MAX_ATTEMPTS_PER_IP = int(os.environ.get("LOGIN_MAX_ATTEMPTS_PER_IP", "20"))
REGISTER_WINDOW_S = int(os.environ.get("REGISTER_WINDOW_S", "3600"))                # 1 h
REGISTER_MAX_PER_IP = int(os.environ.get("REGISTER_MAX_PER_IP", "5"))

# Each diet blueprint costs several LLM calls, so cap how often one user / IP can trigger them
DIET_WINDOW_S = int(os.environ.get("DIET_WINDOW_S", "3600"))                        # 1 h
DIET_MAX_PER_USER = int(os.environ.get("DIET_MAX_PER_USER", "10"))
DIET_MAX_PER_IP_ANONYMOUS = int(os.environ.get("DIET_MAX_PER_IP_ANONYMOUS", "3"))

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
# ERROR RESPONSES
# =========================
# Exception text can expose SQL, file paths or upstream API details, so it is logged
# server-side and clients only get a generic message.
def internal_error(message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR) -> HTTPException:
    """Log the exception currently being handled (with traceback) and build a generic error response."""
    logger.exception(message)
    return HTTPException(status_code=status_code, detail=f"{message}. Please try again.")

def assess_or_422(health_data: dict) -> dict:
    try:
        return run_assessment(health_data)
    except ValueError as e:
        # risk.py raises ValueError only for invalid inputs, with messages written for the user.
        # Kept narrow on purpose: asyncpg's DataError is also a ValueError and must not leak.
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception:
        raise internal_error("Could not compute the risk assessment")

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
    password = plain_password.encode('utf-8')
    if len(password) > 72:
        return False  # can't match: registration rejects passwords longer than bcrypt's 72-byte limit
    return await asyncio.to_thread(bcrypt.checkpw, password, hashed_password.encode('utf-8'))

# Checked against when the email is unknown, so a missing account takes as long as a wrong
# password and response timing doesn't reveal which emails are registered
_DUMMY_PASSWORD_HASH = bcrypt.hashpw(secrets.token_bytes(16), bcrypt.gensalt()).decode('utf-8')

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
    # Callers log failures with a traceback and decide what the client sees
    return await generate_rag_diet_blueprint(_groq_client, health_data, prediction_result, **kwargs)

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
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name must not be blank")
        return value

    @field_validator("password")
    @classmethod
    def _bcrypt_limit(cls, value: str) -> str:
        # bcrypt only uses the first 72 bytes (and bcrypt>=5 raises on longer input)
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 bytes")
        return value

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

login_attempts_by_email = SlidingWindowLimiter(LOGIN_MAX_ATTEMPTS_PER_EMAIL, LOGIN_WINDOW_S)
login_attempts_by_ip = SlidingWindowLimiter(LOGIN_MAX_ATTEMPTS_PER_IP, LOGIN_WINDOW_S)
registrations_by_ip = SlidingWindowLimiter(REGISTER_MAX_PER_IP, REGISTER_WINDOW_S)
diet_generations_by_user = SlidingWindowLimiter(DIET_MAX_PER_USER, DIET_WINDOW_S)
anonymous_diet_generations_by_ip = SlidingWindowLimiter(DIET_MAX_PER_IP_ANONYMOUS, DIET_WINDOW_S)
DIET_LIMIT_MESSAGE = "Too many diet plans requested"

def _client_ip(request: Request) -> str:
    # Behind a reverse proxy, run uvicorn with --proxy-headers so this is the real client address
    return request.client.host if request.client else "unknown"

def _enforce_limits(*checks: tuple, message: str = "Too many attempts") -> None:
    """Raise 429 if any (limiter, key) pair is over its limit."""
    wait = max(limiter.retry_after(key) for limiter, key in checks)
    if wait:
        minutes = math.ceil(wait / 60)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"{message}. Please try again in {minutes} minute{'s' if minutes != 1 else ''}.",
            headers={"Retry-After": str(wait)},
        )

async def authenticate(request: Request, email: str, password: str) -> dict:
    """Check credentials with per-email and per-IP brute-force limits."""
    ip, email_key = _client_ip(request), email.strip().lower()
    _enforce_limits((login_attempts_by_email, email_key), (login_attempts_by_ip, ip))
    # Count the attempt before the (slow) password check so parallel guesses can't all slip
    # past the limit; a successful login then clears it
    login_attempts_by_email.hit(email_key)
    login_attempts_by_ip.hit(ip)

    dal: FitGuardDAL = request.app.state.dal
    user = await dal.get_user_by_email(email)
    password_ok = await verify_password(password, user["password"] if user else _DUMMY_PASSWORD_HASH)
    if not user or not password_ok:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    login_attempts_by_email.reset(email_key)
    login_attempts_by_ip.undo(ip)
    return user

# =========================
# SESSIONS (refresh-token cookie)
# =========================
def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def _new_refresh_token() -> tuple:
    token = secrets.token_urlsafe(32)
    return token, _hash_token(token), datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        REFRESH_COOKIE_NAME, token,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path=REFRESH_COOKIE_PATH,
        httponly=True,        # unreadable from JavaScript
        secure=COOKIE_SECURE,
        samesite="strict",    # never sent on cross-site requests, which blocks CSRF on refresh/logout
    )

def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH,
                           httponly=True, secure=COOKIE_SECURE, samesite="strict")

def _session_body(user: dict) -> dict:
    access_token = create_access_token(
        data={"sub": user["email"], "user_id": user["id"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {"id": user["id"], "name": user["name"], "email": user["email"]},
    }

async def start_session(response: Response, dal: FitGuardDAL, user: dict) -> dict:
    """Begin a new login: a fresh refresh-token family in the cookie plus an access token in the body."""
    token, token_hash, expires_at = _new_refresh_token()
    await dal.create_refresh_token(user["id"], token_hash, secrets.token_hex(16), expires_at)
    _set_refresh_cookie(response, token)
    return _session_body(user)

@app.post("/api/auth/refresh")
async def refresh_session(request: Request, response: Response):
    """Exchange the refresh cookie for a new access token, rotating the refresh token."""
    dal: FitGuardDAL = request.app.state.dal
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    result, user = {"status": "invalid"}, None
    if token:
        new_token, new_hash, expires_at = _new_refresh_token()
        result = await dal.rotate_refresh_token(_hash_token(token), new_hash, expires_at)
        if result["status"] == "ok":
            user = await dal.get_user_by_id(result["user_id"])

    if user is None:
        if result["status"] == "reused":
            logger.warning(f"Refresh token reuse for user {result['user_id']}; revoked that login's sessions")
        unauthorized = JSONResponse({"detail": "Session expired. Please log in again."}, status_code=401)
        _clear_refresh_cookie(unauthorized)
        return unauthorized

    _set_refresh_cookie(response, new_token)
    return _session_body(user)

@app.post("/api/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response):
    token = request.cookies.get(REFRESH_COOKIE_NAME)
    if token:
        await request.app.state.dal.revoke_refresh_token_family(_hash_token(token))
    _clear_refresh_cookie(response)

@app.post("/api/register")
async def register(payload: RegisterRequest, request: Request, response: Response):
    ip = _client_ip(request)
    _enforce_limits((registrations_by_ip, ip))
    registrations_by_ip.hit(ip)

    dal: FitGuardDAL = request.app.state.dal
    user = await dal.get_user_by_email(payload.email)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_password = await hash_password(payload.password)
    user_id = await dal.create_user(payload.name, payload.email, hashed_password)
    user = {"id": user_id, "name": payload.name, "email": payload.email}
    return await start_session(response, dal, user)

@app.post("/api/login")
async def login(payload: LoginRequest, request: Request, response: Response):
    user = await authenticate(request, payload.email, payload.password)
    return await start_session(response, request.app.state.dal, user)

# OAuth2 password flow for the Swagger UI "Authorize" button: access token only, no session cookie
@app.post("/api/token")
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate(request, form_data.username, form_data.password)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"], "user_id": user["id"]}, expires_delta=access_token_expires
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
    return PredictionResponse(**assess_or_422(payload.model_dump()))

@app.post("/api/health-assessment", response_model=HealthAssessmentResponse)
async def submit_health_assessment(
    payload: HealthInputs, request: Request, current_user: dict = Depends(get_current_user)
):
    dal: FitGuardDAL = request.app.state.dal
    user_id = current_user["id"]
    input_data = payload.model_dump()

    # 1. Risk assessment
    prediction_result = assess_or_422(input_data)

    # 2. Save the record for the authenticated user
    smoking_bool = True if str(payload.smokingHabit).lower() in ("yes", "true") else False
    try:
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
    except Exception:
        raise internal_error("Could not save your health assessment")

    # The diet blueprint takes 5-15 s, so it is generated separately via
    # POST /api/records/{record_id}/diet/stream and the risk result is shown immediately
    return HealthAssessmentResponse(
        message="Health assessment submitted successfully",
        record_id=record_id,
        prediction=prediction_result,
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
    user_key = str(current_user["id"])
    _enforce_limits((diet_generations_by_user, user_key), message=DIET_LIMIT_MESSAGE)
    diet_generations_by_user.hit(user_key)

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
        except Exception:
            logger.exception(f"Failed to generate or save diet blueprint for record {record_id}")
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
async def recommend_diet(payload: HealthInputs, request: Request):
    """Risk assessment + RAG-grounded diet blueprint, without creating a user or saving records."""
    ip = _client_ip(request)
    _enforce_limits((anonymous_diet_generations_by_ip, ip), message=DIET_LIMIT_MESSAGE)
    input_data = payload.model_dump()
    prediction_result = assess_or_422(input_data)
    anonymous_diet_generations_by_ip.hit(ip)  # counted only once the inputs are valid
    try:
        diet_blueprint = await generate_diet_blueprint(input_data, prediction_result)
    except Exception:
        raise internal_error("Diet generation failed", status_code=status.HTTP_502_BAD_GATEWAY)
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
