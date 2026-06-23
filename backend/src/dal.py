import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr
import asyncpg

class UserSummary(BaseModel):
    id: int
    name: str
    email: str

    @staticmethod
    def from_row(row: asyncpg.Record) -> "UserSummary":
        return UserSummary(
            id=row["id"],
            name=row["name"],
            email=row["email"],
        )
    
class HealthRecord(BaseModel):
    id: int
    user_id: int
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    bmi: float
    blood_pressure: str
    heart_rate: int
    physical_activity: str
    sleep_hours: float
    smoking_habit: bool
    created_at: datetime

    @staticmethod
    def from_row(row: asyncpg.Record) -> "HealthRecord":
        return HealthRecord(
            id=row["id"],
            user_id=row["user_id"],
            age=row["age"],
            gender=row["gender"],
            height_cm=row["height_cm"],
            weight_kg=row["weight_kg"],
            bmi=row["bmi"],
            blood_pressure=row["blood_pressure"],
            heart_rate=row["heart_rate"],
            physical_activity=row["physical_activity"],
            sleep_hours=row["sleep_hours"],
            smoking_habit=row["smoking_habit"],
            created_at=row["created_at"],
        )

class DietBlueprint(BaseModel):
    id: int
    user_id: int
    record_id: int
    macros: Dict[str, Any]
    meal_plan: List[Dict[str, Any]]
    foods_to_avoid: List[str]
    supplements: List[str]
    created_at: datetime

    @staticmethod
    def from_row(row: asyncpg.Record) -> "DietBlueprint":
        return DietBlueprint(
            id=row["id"],
            user_id=row["user_id"],
            record_id=row["record_id"],
            macros=json.loads(row["macros"]) if isinstance(row["macros"], str) else row["macros"],
            meal_plan=json.loads(row["meal_plan"]) if isinstance(row["meal_plan"], str) else row["meal_plan"],
            foods_to_avoid=json.loads(row["foods_to_avoid"]) if isinstance(row["foods_to_avoid"], str) else row["foods_to_avoid"],
            supplements=json.loads(row["supplements"]) if isinstance(row["supplements"], str) else row["supplements"],
            created_at=row["created_at"],
        )

class FitGuardDAL:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def create_tables(self):
        async with self._pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP NOT NULL
                );

                CREATE TABLE IF NOT EXISTS health_records (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    age INTEGER NOT NULL,
                    gender VARCHAR(50) NOT NULL,
                    height_cm FLOAT NOT NULL,
                    weight_kg FLOAT NOT NULL,
                    bmi FLOAT NOT NULL,
                    blood_pressure VARCHAR(50) NOT NULL,
                    heart_rate INTEGER NOT NULL,
                    physical_activity VARCHAR(255) NOT NULL,
                    sleep_hours FLOAT NOT NULL,
                    smoking_habit BOOLEAN NOT NULL,
                    created_at TIMESTAMP NOT NULL
                );

                CREATE TABLE IF NOT EXISTS diet_blueprints (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    record_id INTEGER NOT NULL REFERENCES health_records(id) ON DELETE CASCADE,
                    macros JSONB NOT NULL,
                    meal_plan JSONB NOT NULL,
                    foods_to_avoid JSONB NOT NULL,
                    supplements JSONB NOT NULL,
                    created_at TIMESTAMP NOT NULL
                );
            """)

    async def get_user_by_email(self, email: str) -> Optional[dict]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
            return dict(row) if row else None
    
    async def create_user(
            self,
            name: str,
            email: str,
            hashed_password: str
    ) -> int:
        async with self._pool.acquire() as conn:
            user_id = await conn.fetchval(
                """
                INSERT INTO users (name, email, password, created_at)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                name, email, hashed_password, datetime.utcnow()
            )
            return user_id
    
    async def create_health_record(
        self,
        user_id: int,
        age: int,
        gender: str,
        height_cm: float,
        weight_kg: float,
        bmi: float,
        blood_pressure: str,
        heart_rate: int,
        physical_activity: str,
        sleep_hours: float,
        smoking_habit: bool
    ) -> int:
        async with self._pool.acquire() as conn:
            record_id = await conn.fetchval(
                """
                INSERT INTO health_records (
                    user_id, age, gender, height_cm, weight_kg, bmi, 
                    blood_pressure, heart_rate, physical_activity, sleep_hours, 
                    smoking_habit, created_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12
                ) RETURNING id
                """,
                user_id, age, gender, height_cm, weight_kg, bmi,
                blood_pressure, heart_rate, physical_activity, sleep_hours,
                smoking_habit, datetime.utcnow()
            )
            return record_id
    
    async def get_health_records_by_user(self, user_id: int) -> List[HealthRecord]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM health_records WHERE user_id = $1 ORDER BY created_at DESC",
                user_id
            )
            return [HealthRecord.from_row(row) for row in rows]
    
    async def get_health_record(self, record_id: int) -> Optional[HealthRecord]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM health_records WHERE id = $1",
                record_id
            )
            if row:
                return HealthRecord.from_row(row)
            return None

    async def save_diet_blueprint(
        self,
        user_id: int,
        record_id: int,
        macros: Dict[str, Any],
        meal_plan: List[Dict[str, Any]],
        foods_to_avoid: List[str],
        supplements: List[str]
    ) -> int:
        async with self._pool.acquire() as conn:
            blueprint_id = await conn.fetchval(
                """
                INSERT INTO diet_blueprints (
                    user_id, record_id, macros, meal_plan, foods_to_avoid, supplements, created_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7
                ) RETURNING id
                """,
                user_id,
                record_id,
                json.dumps(macros),
                json.dumps(meal_plan),
                json.dumps(foods_to_avoid),
                json.dumps(supplements),
                datetime.utcnow()
            )
            return blueprint_id

    async def get_diet_blueprint_by_record(self, record_id: int) -> Optional[DietBlueprint]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM diet_blueprints WHERE record_id = $1 ORDER BY created_at DESC LIMIT 1",
                record_id
            )
            if row:
                return DietBlueprint.from_row(row)
            return None

    async def get_diet_blueprints_by_user(self, user_id: int) -> List[DietBlueprint]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM diet_blueprints WHERE user_id = $1 ORDER BY created_at DESC",
                user_id
            )
            return [DietBlueprint.from_row(row) for row in rows]