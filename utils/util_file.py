from motor.motor_asyncio import AsyncIOMotorClient
from models import UserModel


async def create_user(user_id: int):
    user_data = UserModel(_id=user_id)
    await db.users.insert_one(user_data.dict())

async def get_user(user_id: int) -> UserModel:
    data = await db.users.find_one({"_id": user_id})
    if not data:
        return UserModel(_id=user_id)
    return UserModel(**data)