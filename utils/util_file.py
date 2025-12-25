import os, json
from .database import get_db
from .models import UserModel, MonsterModel, WeaponModel, PassiveModel


def get_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)
    
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

async def save_weapon(user_id, weapon_type, weapon_qualities, generated_passives):
    try:
        if (not isinstance(weapon_type, int)):
            raise ValueError("Weapon type is invalid!")
        
        if (not isinstance(weapon_qualities, list) or len(weapon_qualities) <= 0):
            raise ValueError("Weapon qualities are missing!")
        
        if (not isinstance(generated_passives, list) or len(generated_passives) <= 0):
            raise ValueError("Missing passives!")
        
        db = get_db()
        
        user_data = await get_user(user_id)

        if (not user_data):
            raise ValueError("No user data found!")

       
        new_id = await counter("weapon")

        if (not isinstance(new_id, int)):
            raise ValueError("Sequence id couldn't be generated!")
    
        passives = []

        for passive in generated_passives:
            passive_config = passive[0]
            passive_qualities = passive[1]
            passive_type = passive_config["type"]

            if (not isinstance(passive_type, int)):
                raise ValueError("Passive type is invalid!")
            
            if (not isinstance(passive_qualities, list) or len(passive_qualities) <= 0):
                raise ValueError("Passive is missing qualities!")
            
            passives.append(PassiveModel(
                p_type = passive_type,
                qualities = passive_qualities
            ))

        weapon_data = WeaponModel(
            w_id = new_id,
            w_type = weapon_type,
            qualities = weapon_qualities,
            passives = passives
        )

        user_data.weapons.append(weapon_data)

        # print(f"NEW DATA: {user_data.weapons}")

        await db.users.update_one(
            {"u_id": user_id}, 
            {"$set": {"weapons": [w.model_dump() for w in user_data.weapons]}}
        )


    except Exception as e:
        raise ValueError(e)

async def get_monster(user_id, name=None):
    config = get_config()
    user_data = await get_user(user_id)

    if (not user_data):
        raise ValueError("No user data found!")

    # returning all monsters that are owned by the user
    if (not isinstance(name, str)):
        return user_data.monsters
    
    # find monster in config
    monster_config = next(
        (m for m in config["monsters"] if m["name"].lower() == name.lower()),
        None
    )

    if monster_config is None:
        raise ValueError(f"Monster '{name}' not found in config!")

    # find monster in user's data
    monster_in_data = next(
        (m for m in user_data.monsters if m.m_type == monster_config["type"]),
        None
    )

    if monster_in_data is None:
        raise ValueError(f"User does not own monster '{name}'!")

    
    return monster_in_data, monster_config
    
def get_emoji(name):
    config = get_config()

    if (config is None):
        raise ValueError("Config not found!")
    
    if (name not in config["emojis"]):
        raise ValueError("Emoji is not available!")
    
    return config["emojis"][name]

def get_rarity_info(name):
    config = get_config()

    if (config is None):
        raise ValueError("Config not found!")
    
    if (name not in config["rarities"]):
        raise ValueError("Rarity doesn't exist!")
    
    return config["rarities"][name]