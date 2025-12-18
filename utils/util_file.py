import os, json
from .database import get_db
from .models import UserModel, MonsterModel


async def create_user(user_id: int):
    if (not isinstance(user_id, int)):
        print(f"[ERROR]: user id: {user_id} expected int got {type(user_id)} ")

    user_id = int(user_id)

    try:
        db = get_db()
        user_data = UserModel(u_id=user_id)

        await db.users.insert_one(user_data.model_dump())

        return await db.users.find_one({"u_id": user_id})
    except Exception as e:
        print(f"[ERROR]: creating user, message: {e}")

        return None

async def get_user(user_id: int) -> UserModel:
    try:
        db = get_db()
        data = await db.users.find_one({"u_id": user_id})

        if not data:
            return await create_user(user_id)
    
        return UserModel(**data)
    except Exception as e:
        print(f"[ERROR]: Getting user, message: {e}!")

        return None
    
async def counter(type):
    try:
        db = get_db()

        counter = await db.counters.find_one_and_update(
            {"c_type": type},
            {"$inc": {"seq": 1}},
            upsert = True,
            return_document = True
        )
        
        return counter["seq"]
    except Exception as e:
        raise ValueError(f"[ERROR]: while getting id, message: {e}")
   

async def save_monster(user_id, monster_type):
    try:
        db = get_db()
        
        user_data = await get_user(user_id)

        if (not user_data):
            raise ValueError("No user data found!")

        existing_monster = next((m for m in user_data.monsters if m.m_type == monster_type), None)

        if (existing_monster):
            existing_monster.seq += 1
        else:
            new_id = await counter("monster")

            if (not isinstance(new_id, int)):
                raise ValueError("Sequence id couldn't be generated!")
        
            monster_data = MonsterModel(
                m_id = new_id,
                m_type = monster_type
            )

            user_data.monsters.append(monster_data)

        print(f"NEW DATA: {user_data.monsters}")

        await db.users.update_one(
            {"u_id": user_id}, 
            {"$set": {"monsters": [m.model_dump() for m in user_data.monsters]}}
        )


    except Exception as e:
        raise ValueError(e)

def get_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)