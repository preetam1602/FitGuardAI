from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ReturnDocument
from pydantic import BaseModel,EmailStr
from datetime import datetime
from typing import Optional

class UserSummary(BaseModel):
    id:str
    name:str
    email:str

    @staticmethod
    def from_doc(doc)->"UserSummary":
        return UserSummary(
            id=str(doc["_id"]),
            name=doc["name"],
            email=doc["email"],
        )
    
class HealthRecord(BaseModel):
    id: str
    user_id: str        # who submitted this record
    age: int
    gender: str
    height_cm: float
    weight_kg: float
    bmi: float
    blood_pressure: str
    heart_rate: int
    physical_activity: str
    sleep_hours: float
    smoking_habit: bool   # stored as True/False in MongoDB
    created_at: datetime

    @staticmethod
    def from_doc(doc)->"HealthRecord":
        return HealthRecord(
            id=str(doc["_id"]),
            user_id=str(doc["user_id"]),  # ObjectId → string
            age=doc["age"],
            gender=doc["gender"],
            height_cm=doc["height_cm"],
            weight_kg=doc["weight_kg"],
            bmi=doc["bmi"],
            blood_pressure=doc["blood_pressure"],
            heart_rate=doc["heart_rate"],
            physical_activity=doc["physical_activity"],
            sleep_hours=doc["sleep_hours"],
            smoking_habit=doc["smoking_habit"],
            created_at=doc["created_at"],
        )
    
class FitGuardDAL:
    def __init__(self,
                 users_collection:AsyncIOMotorCollection,
                 health_collection:AsyncIOMotorCollection,
            ):
        self._users=users_collection
        self._health=health_collection

    async def get_user_by_email(self,email:str,session=None)->Optional[dict]:
        return await self._users.find_one({'email':email},session=session)
    
    async def create_user(
            self,
            name:str,
            email:str,
            hashed_password:str,
            session=None
    )->str:
        response=await self._users.insert_one({
            "name": name,
            "email": email,
            "password": hashed_password,
            "created_at": datetime.utcnow(),
        },
            session=session
        )
        return str(response.inserted_id)
    
    async def create_health_record(
        self,
        user_id: str,
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
        session=None,
    ) -> str:
        response = await self._health.insert_one(
            {
                "user_id": ObjectId(user_id),
                "age": age,
                "gender": gender,
                "height_cm": height_cm,
                "weight_kg": weight_kg,
                "bmi": bmi,
                "blood_pressure": blood_pressure,
                "heart_rate": heart_rate,
                "physical_activity": physical_activity,
                "sleep_hours": sleep_hours,
                "smoking_habit": smoking_habit,
                "created_at": datetime.utcnow(),
            },
            session=session,
        )
        return str(response.inserted_id)
    
    async def get_health_records_by_user(
            self,user_id:str,session=None
    )->list[HealthRecord]:
        records=[]
        async for doc in self._health.find(
            {"user_id":ObjectId(user_id)},
            sort={"created_at":-1},
            session=session
        ):
            records.append(HealthRecord.from_doc(doc))
        return records
    
    async def get_health_record(
        self, record_id: str, session=None
    ) -> Optional[HealthRecord]:
        doc = await self._health.find_one(
            {"_id": ObjectId(record_id)}, session=session
        )
        if doc:
            return HealthRecord.from_doc(doc)