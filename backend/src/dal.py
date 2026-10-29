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
    diabetes: bool = False
    bp_medication: bool = False
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
            diabetes=row["diabetes"],
            bp_medication=row["bp_medication"],
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

                -- Risk-equation inputs added after the first release
                ALTER TABLE health_records ADD COLUMN IF NOT EXISTS diabetes BOOLEAN NOT NULL DEFAULT FALSE;
                ALTER TABLE health_records ADD COLUMN IF NOT EXISTS bp_medication BOOLEAN NOT NULL DEFAULT FALSE;

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

                -- Refresh tokens are stored as SHA-256 hashes. Each login starts a family; every
                -- refresh revokes the used token and issues the next one in the same family.
                CREATE TABLE IF NOT EXISTS refresh_tokens (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    token_hash CHAR(64) UNIQUE NOT NULL,
                    family_id VARCHAR(32) NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    revoked_at TIMESTAMP,
                    created_at TIMESTAMP NOT NULL
                );
                CREATE INDEX IF NOT EXISTS refresh_tokens_family_idx ON refresh_tokens (family_id);
                CREATE INDEX IF NOT EXISTS refresh_tokens_expires_idx ON refresh_tokens (expires_at);
            """)

    async def get_user_by_email(self, email: str) -> Optional[dict]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
            return dict(row) if row else None
    
    async def get_user_by_id(self, user_id: int) -> Optional[dict]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
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
        smoking_habit: bool,
        diabetes: bool = False,
        bp_medication: bool = False
    ) -> int:
        async with self._pool.acquire() as conn:
            record_id = await conn.fetchval(
                """
                INSERT INTO health_records (
                    user_id, age, gender, height_cm, weight_kg, bmi, 
                    blood_pressure, heart_rate, physical_activity, sleep_hours, 
                    smoking_habit, diabetes, bp_medication, created_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
                ) RETURNING id
                """,
                user_id, age, gender, height_cm, weight_kg, bmi,
                blood_pressure, heart_rate, physical_activity, sleep_hours,
                smoking_habit, diabetes, bp_medication, datetime.utcnow()
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
    # ---------- refresh tokens ----------

    async def create_refresh_token(self, user_id: int, token_hash: str, family_id: str, expires_at: datetime) -> None:
        async with self._pool.acquire() as conn:
            # Opportunistic cleanup keeps the table small without a scheduled job
            await conn.execute("DELETE FROM refresh_tokens WHERE expires_at < $1", datetime.utcnow())
            await conn.execute(
                """
                INSERT INTO refresh_tokens (user_id, token_hash, family_id, expires_at, created_at)
                VALUES ($1, $2, $3, $4, $5)
                """,
                user_id, token_hash, family_id, expires_at, datetime.utcnow()
            )

    async def rotate_refresh_token(self, old_hash: str, new_hash: str, expires_at: datetime) -> Dict[str, Any]:
        """
        Atomically swap a refresh token for a new one in the same family.
        Returns {"status": "ok", "user_id": ...}, or {"status": "invalid" | "expired" | "reused"}.
        A revoked token being presented again means it was copied, so its whole family is revoked.
        """
        now = datetime.utcnow()
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    "SELECT user_id, family_id, expires_at, revoked_at FROM refresh_tokens WHERE token_hash = $1 FOR UPDATE",
                    old_hash
                )
                if row is None:
                    return {"status": "invalid"}
                if row["revoked_at"] is not None:
                    await conn.execute(
                        "UPDATE refresh_tokens SET revoked_at = $2 WHERE family_id = $1 AND revoked_at IS NULL",
                        row["family_id"], now
                    )
                    return {"status": "reused", "user_id": row["user_id"]}
                if row["expires_at"] <= now:
                    return {"status": "expired"}
                await conn.execute("UPDATE refresh_tokens SET revoked_at = $2 WHERE token_hash = $1", old_hash, now)
                await conn.execute(
                    """
                    INSERT INTO refresh_tokens (user_id, token_hash, family_id, expires_at, created_at)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    row["user_id"], new_hash, row["family_id"], expires_at, now
                )
                return {"status": "ok", "user_id": row["user_id"]}

    async def revoke_refresh_token_family(self, token_hash: str) -> None:
        """Log out: revoke the presented token and every other token from the same login."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE refresh_tokens SET revoked_at = $2
                WHERE revoked_at IS NULL
                  AND family_id = (SELECT family_id FROM refresh_tokens WHERE token_hash = $1)
                """,
                token_hash, datetime.utcnow()
            )
