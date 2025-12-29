import os, json, discord
from .database import get_db
from .models import UserModel, MonsterModel, WeaponModel, PassiveModel


def get_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

def to_base36(num: int) -> str:
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if num == 0:
        return "0"

    # Make sure it's an int
    if not isinstance(num, int):
        try:
            num = int(num)
        except Exception:
            raise ValueError(f"to_base36 expected int but got {type(num)}: {num}")
                             
    result = ""
    while num:
        num, rem = divmod(num, 36)
        result = chars[rem] + result
    return result

def to_base36_spaced(num: int, width: int = 6) -> str:
    return to_base36(num).rjust(width, " ")

def from_base36(s: str) -> int:
    return int(s, 36)

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

async def get_monster(user_id, name = None, id = None):
    config = get_config()
    user_data = await get_user(user_id)

    if (not user_data):
        raise ValueError("No user data found!")

    if (id is not None):
        monster_in_data = next(
            (m for m in user_data.monsters if m.m_id == id),
            None
        )

        if (monster_in_data is None):
            return ValueError(f"User doesn't own monster with id: {id}")
        
        monster_config = next(
            (m for m in config["monsters"] if m["type"] == monster_in_data.m_type),
            None
        )
        
        return monster_in_data, monster_config
    
    # returning all monsters that are owned by the user
    if (not isinstance(name, str)):
        return user_data.monsters
    
    # find monster in config
    monster_config = next(
        (m for m in config["monsters"] if m["name"].lower() == name.lower().strip()),
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
    
async def get_weapon(user_id, id=None):
    config = get_config()
    user_data = await get_user(user_id)

    if (not user_data):
        raise ValueError("No user data found!")
    
    # return all user's weapons
    if (id is None):
        return user_data.weapons
    
    # for cases when the original numerical id is passed
    id_to_compare = id if type(id) == int else from_base36(id)

    weapon_data = next(
        (w for w in user_data.weapons if w.w_id == id_to_compare),
        None
    )

    if (weapon_data is None):
        raise ValueError(f"User does not own this weapon!")
    
    weapon_config = next(
        (w for w in config["weapons"] if w["type"] == weapon_data.w_type),
        None
    )

    if (weapon_config is None):
        raise ValueError(f"Weapon doesn't exist in config!")
    
    return weapon_data, weapon_config  

async def unequip_weapon(user_id, w_id):
    db = get_db()
    weapon_data, _ = await get_weapon(user_id, w_id)

    if (weapon_data.e_mid == -1):
        raise ValueError("No weapon to be unequipped!")
    
    monster_data, _ = await get_monster(user_id, None, weapon_data.e_mid)

    weapon_data.e_mid = -1
    monster_data.e_wid = -1

    # update weapon
    await db.users.update_one(
        {"u_id": user_id, "weapons.w_id": weapon_data.w_id},
        {"$set": {
            "weapons.$": weapon_data.model_dump()  
        }}
    )

    # update monster
    await db.users.update_one(
        {"u_id": user_id, "monsters.m_id": monster_data.m_id},
        {"$set": {"monsters.$": monster_data.model_dump()}}
    )


async def equip_weapon(user_id, w_id, monster_name):
    db = get_db()

    monster_data, _ = await get_monster(user_id, monster_name)
    weapon_data, _ = await get_weapon(user_id, w_id)

    if (monster_data.e_wid != -1):
        await unequip_weapon(user_id, monster_data.e_wid)

    weapon_data.e_mid = monster_data.m_id
    monster_data.e_wid = weapon_data.w_id

    # update weapon
    await db.users.update_one(
        {"u_id": user_id, "weapons.w_id": weapon_data.w_id},
        {"$set": {
            "weapons.$": weapon_data.model_dump()  
        }}
    )

    # update monster
    await db.users.update_one(
        {"u_id": user_id, "monsters.m_id": monster_data.m_id},
        {"$set": {"monsters.$": monster_data.model_dump()}}
    )

    return True


def get_emoji(name):
    config = get_config()

    if (config is None):
        raise ValueError("Config not found!")
    
    if (name not in config["emojis"]):
        raise ValueError("Emoji is not available!")
    
    return config["emojis"][name]

def get_rarity_info(name = None, quality = None):
    config = get_config()

    if (config is None):
        raise ValueError("Config not found!")
    
    rarities : dict = config["rarities"]

    if (name is None and 
        quality is None and not isinstance(quality, (int, float))):
        raise ValueError(f"Quality expected int got {type(quality)}!")
    
    # get rarity from quality
    if (quality is not None):
        for name, info in rarities.items():
            [lower, upper] = info["quality"]

            if (quality >= lower and quality <= upper):
                return info

    if (name not in rarities):
        raise ValueError("Rarity doesn't exist!")
    
    return rarities[name]

def get_quality_info(quality_data):
    if (quality_data is None):
        raise ValueError(f"Expected data when getting quality got {type(quality_data)}")
    
    quality = sum(quality_data) / len(quality_data)

    rarity_info = get_rarity_info(None, quality)

    return quality, rarity_info

async def get_weapon_string(user_id, w_id, display="normal", passed_data=None):
    try:
        config = get_config()

        weapon_data, weapon_config = None, None
        
        if (w_id):
            weapon_data, weapon_config = await get_weapon(user_id, w_id)
        elif (passed_data is not None):
            weapon_data = passed_data
            weapon_config = next(
                (w for w in config["weapons"] if w["type"] == weapon_data.w_type),
                None
            )

            if (weapon_config is None):
                raise ValueError(f"Weapon with type {weapon_data.w_type} does not exist in config!")
        else:
            raise ValueError("Weapon id/data is needed received nothing!")

        weapon_quality, weapon_rarity_info = get_quality_info(weapon_data.qualities)

        weapon_emoji = weapon_config["emojis"][weapon_rarity_info["type"]]

        passive_emojis = []
        for passive_data in weapon_data.passives:
            passive_config = next(
                (p for p in config["passives"] if p["type"] == passive_data.p_type),
                None
            )

            if (not passive_config):
                raise ValueError(f"Passive with type {passive_data.p_type} does not exist in config!")
            
            _, passive_rarity_info = get_quality_info(passive_data.qualities)

            passive_emojis.append(passive_config["emojis"][passive_rarity_info["type"]])

        if (display == "normal"):
            return f"{weapon_rarity_info['emoji']}{weapon_emoji}{''.join(passive_emojis)}"
        if (display == "id"):
            return f"**`{to_base36(weapon_data.w_id)}`** {weapon_rarity_info['emoji']}{weapon_emoji}{''.join(passive_emojis)}"
    except Exception as e:
        raise ValueError(f"[ERROR]: While constructing a weapon string, message: {e}")
