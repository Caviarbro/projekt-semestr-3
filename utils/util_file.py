import os, json, discord
from .database import get_db
from .models import UserModel, MonsterModel, WeaponModel, PassiveModel, TeamModel, TeamMonsterModel


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

        return user_data
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

async def get_counter(type):
    try:
        db = get_db()
        counter = await db.counters.find_one({"c_type": type})
        
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

async def save_team(user_id):
    try:
        user_data = await get_user(user_id)
        config = get_config()
        db = get_db()

        if (not user_data):
            raise ValueError("No user data found!")
        
        if (len(user_data.t_ids) >= config["settings"]["max_teams_per_user"]):
            raise ValueError("Limit of teams reached!")
        
        new_id = await counter("team")

        if (not isinstance(new_id, int)):
            raise ValueError("Sequence id couldn't be generated!")
        
        activate_team = True if len(user_data.t_ids) <= 0 else False 

        team_data = TeamModel(
            u_id = user_id,
            t_id = new_id,
            active = activate_team,
        )

        await db.users.update_one(
            {"u_id": user_id},
            {"$addToSet": {"t_ids": new_id}}
        )
        await db.teams.insert_one(team_data.model_dump())

        return team_data
    except Exception as e:
        raise ValueError(e)

def get_monster_config(*, m_type : int = None, monster_name : str = None):
    config = get_config()
    
    monster_config = None 

    if (m_type is None and monster_name is None):
        raise ValueError("Required at least one argumet (m_type / monster_name)")
    
    if (m_type):
        monster_config = next(
            (m for m in config["monsters"] if m["type"] == m_type),
            None 
        )

    if (monster_name):
        monster_config = next(
            (m for m in config["monsters"] if m["name"] == monster_name.lower().strip()),
            None 
        )

    return monster_config

def get_weapon_config(*, w_type : int = None, weapon_name : str = None):
    config = get_config()
    
    weapon_config = None 

    if (w_type is None and weapon_name is None):
        raise ValueError("Required at least one argumet (w_type / weapon_name)")
    
    if (w_type):
        weapon_config = next(
            (w for w in config["weapons"] if w["type"] == w_type),
            None 
        )

    if (weapon_name):
        weapon_config = next(
            (w for w in config["weapons"] if w["name"] == weapon_name.lower().strip()),
            None 
        )

    return weapon_config

def get_passive_config(*, p_type : int = None, passive_name : str = None):
    config = get_config()
    
    passive_config = None 

    if (p_type is None and passive_name is None):
        raise ValueError("Required at least one argumet (p_type / passive_name)")
    
    if (p_type):
        passive_config = next(
            (p for p in config["passives"] if p["type"] == p_type),
            None 
        )

    if (passive_name):
        passive_config = next(
            (p for p in config["passives"] if p["name"] == passive_name.lower().strip()),
            None 
        )

    return passive_config

async def get_monster(user_id, 
                      *, name = None, id = None):
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
        
        monster_config = get_monster_config(m_type = monster_in_data.m_type)
        
        return monster_in_data, monster_config
    
    # returning all monsters that are owned by the user
    if (not isinstance(name, str)):
        return user_data.monsters
    
    # find monster in config
    monster_config = get_monster_config(monster_name = name)

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
    
    weapon_config = get_weapon_config(w_type = weapon_data.w_type)

    if (weapon_config is None):
        raise ValueError(f"Weapon doesn't exist in config!")
    
    return weapon_data, weapon_config  

async def get_team(user_id: int,
    *,
    team_number: int | None = None,
    team_id: int | None = None,
    create_if_not_exist: bool = False
):
    db = get_db()

    # Resolve team id
    if team_id:
        t_id = team_id
    elif team_number:
        user_data = await get_user(user_id)

        if (team_number < len(user_data.t_ids)):
            t_id = user_data.t_ids[team_number]
    else:
        t_id = None

    # Fetch or create team
    if t_id is None:
        if not create_if_not_exist:
            raise ValueError(
                f"Team with number {team_number} does not exist for user <@{user_id}>!"
            )
        team_data = await save_team(user_id)  # already a TeamModel
    else:
        raw = await db.teams.find_one({"t_id": t_id})
        if raw is None:
            raise ValueError(f"Team with id {t_id} does not have any data!")
        team_data = TeamModel(**raw)
        user_id = team_data.u_id # user id is not always passed

    # Build monster list
    team_monsters = []

    for t_monster in team_data.t_monsters:
        monster_data, monster_config = await get_monster(user_id, id = t_monster.m_id)

        weapon_data = None
        weapon_config = None 

        if monster_data.e_wid != -1:
            weapon_data, weapon_config = await get_weapon(user_id, monster_data.e_wid)

        team_monsters.append(
            [monster_data, monster_config, t_monster, weapon_data, weapon_config]
        )

    return team_data, team_monsters

async def get_active_team(user_id):
    db = get_db()

    team_data = await db.teams.find_one({"u_id": user_id, "active": True})

    if (team_data is None):
        raise ValueError(f"No active team found for user: <@{user_id}>")
    
    team_data = TeamModel(**team_data)
    return await get_team(user_id, team_id = team_data.t_id)

async def change_team(user_id, team_number):
    db = get_db()
    team_data, team_monsters = await get_team(user_id, team_number = team_number, create_if_not_exist = True)

    # only one active team at the time
    await db.teams.update_one(
        {"u_id": user_id, "active": True},
        {"$set": {"active": False}}
    )

    await db.teams.update_one(
        {"u_id": user_id, "t_id": team_data.t_id},
        {"$set": {"active": True}}
    )

async def remove_team_monster(user_id, position):
    db = get_db()
    active_team_data, _ = await get_active_team(user_id)

    if (position is None):
        raise ValueError("Invalid team position!")
    
    t_monster = next(
        (t_m for t_m in active_team_data.t_monsters if t_m.pos == int(position)),
        None
    )

    if (t_monster is None):
        return f"No monster to remove on position: {position}!"
    
    await db.teams.update_one(
        {"u_id": user_id, "active": True},
        {"$pull": {"t_monsters": {"pos": int(position)}}}
    )

    return f"Successfully removed monster on position: {position}!"

async def add_team_monster(user_id, monster_name, position=None):
    config = get_config()
    db = get_db()

    active_team_data, _ = await get_active_team(user_id)
    monster_data, _ = await get_monster(user_id, name=monster_name)

    max_monsters_per_team = config["settings"]["max_monsters_per_team"]
    team_position_start_index = config["settings"]["team_position_start_index"]

    if position is None:
        # can't add monster to team automatically because it's full
        if len(active_team_data.t_monsters) >= max_monsters_per_team :
            raise ValueError("Monster can't be added because the team is full!")
        
        if not active_team_data.t_monsters:
            position_to_add = team_position_start_index
        else:
            position_to_add = max(t_monster.pos for t_monster in active_team_data.t_monsters) + 1
    else:
        position_to_add = int(position)

    if position_to_add > max_monsters_per_team:
        position_to_add = max_monsters_per_team

    if position_to_add < team_position_start_index:
        position_to_add = team_position_start_index

    # Remove monster already in team
    t_monster_same_id = next(
        (t_monster for t_monster in active_team_data.t_monsters if t_monster.m_id == monster_data.m_id),
        None
    )
    if t_monster_same_id:
        await remove_team_monster(user_id, t_monster_same_id.pos)

    # Remove monster at target position
    t_monster_on_position = next(
        (t_monster for t_monster in active_team_data.t_monsters if t_monster.pos == position_to_add),
        None
    )
    if t_monster_on_position:
        await remove_team_monster(user_id, position_to_add)

    t_monster_data = TeamMonsterModel(
        pos = position_to_add,
        m_id = monster_data.m_id
    )
    
    await db.teams.update_one(
        {"u_id": user_id, "active": True},
        {"$push": {"t_monsters": t_monster_data.model_dump()}}
    )



async def unequip_weapon(user_id, w_id):
    db = get_db()
    weapon_data, _ = await get_weapon(user_id, w_id)

    if (weapon_data.e_mid == -1):
        raise ValueError("No weapon to be unequipped!")
    
    monster_data, _ = await get_monster(user_id, id = weapon_data.e_mid)

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

    monster_data, _ = await get_monster(user_id, name = monster_name)
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

        weapon_data = None
        weapon_config = None
        
        if (w_id):
            weapon_data, weapon_config = await get_weapon(user_id, w_id)
        elif (passed_data is not None):
            weapon_data = passed_data
            weapon_config = get_weapon_config(w_type = weapon_data.w_type)

            if (weapon_config is None):
                raise ValueError(f"Weapon with type {weapon_data.w_type} does not exist in config!")
        else:
            raise ValueError("Weapon id/data is needed received nothing!")

        weapon_quality, weapon_rarity_info = get_quality_info(weapon_data.qualities)

        weapon_emoji = weapon_config["emojis"][weapon_rarity_info["type"]]

        passive_emojis = []
        for passive_data in weapon_data.passives:
            passive_config = get_passive_config(p_type = passed_data.p_type)

            if (not passive_config):
                raise ValueError(f"Passive with type {passive_data.p_type} does not exist in config!")
            
            _, passive_rarity_info = get_quality_info(passive_data.qualities)

            passive_emojis.append(passive_config["emojis"][passive_rarity_info["type"]])

        if (display == "normal"):
            return f"{weapon_rarity_info['emoji']}{weapon_emoji}{''.join(passive_emojis)}"
        if (display == "id"):
            return f"**`{to_base36(weapon_data.w_id)}`** {weapon_rarity_info['emoji']}{weapon_emoji}{''.join(passive_emojis)}"
        if (display == "full"):
            return f"**`{to_base36(weapon_data.w_id)}`** {weapon_rarity_info['emoji']}{weapon_emoji}{''.join(passive_emojis)} {weapon_quality}%"
    except Exception as e:
        raise ValueError(f"[ERROR]: While constructing a weapon string, message: {e}")

def get_level(xp):
    config = get_config()

    base = config["settings"]["level_base"]
    exp = config["settings"]["level_exponent"]

    level = int((xp / base) ** exp) + 1
    return level

def xp_for_level(level):
    config = get_config()

    base = config["settings"]["level_base"]
    exp = config["settings"]["level_exponent"]

    return int(base * (level ** (1 / exp)))

def get_monster_stats_raw(m_type, xp, weapon_data : WeaponModel = None):
    config = get_config()
    monster_config = get_monster_config(m_type = m_type)
    monster_level = get_level(xp)
    
    def get_stat(stat_type):
        stat = next(
            (s["amount"] for s in monster_config["stats"].values() if s["type"] == stat_type),
            0
        )

        return stat 
    
    defense_stat_limit = config["settings"]["defense_stat_limit"]
    stat_bases = config["settings"]["stat_bases"]

    hp = ((get_stat(0) * 1.5) * (monster_level)) + stat_bases[0]
    strength = (get_stat(1) * monster_level) + stat_bases[1]
    strength_defense = min((monster_level ** (0.5 + get_stat(2) * 0.01)) + stat_bases[2], defense_stat_limit)
    mana = ((get_stat(3) * 1.5) * (monster_level)) + stat_bases[3]
    mag = (get_stat(4) * monster_level) + stat_bases[4]
    mag_defense = min((monster_level ** (0.5 + get_stat(5) * 0.01)) + stat_bases[5], defense_stat_limit)

    if (weapon_data):
        # TODO: increase stats from passives etc.
        pass

    return [hp, strength, strength_defense, mana, mag, mag_defense]

async def get_monster_stats(user_id, m_id):
    monster_data, _ = await get_monster(user_id, id = m_id)

    weapon_data = None 

    if (monster_data.e_wid != -1):
        weapon_data, _ = await get_weapon(user_id, monster_data.e_wid)

    return get_monster_stats_raw(monster_data.m_type, monster_data.xp, weapon_data)

def get_weapon_stats_raw(w_type, qualities):
    weapon_config = get_weapon_config(w_type = w_type)
    stats = []

    # converting qualities from % to actually stat numbers
    for index, quality in enumerate(qualities):
        stat = weapon_config["stats"][index]
        value = stat["min"] + (stat["max"] - stat["min"]) * (quality / 100)

        stats.append(value)
    
    return stats

async def get_weapon_stats(user_id, w_id):
    weapon_data, weapon_config = await get_weapon(user_id, w_id)
    
    return get_weapon_stats_raw(weapon_data.w_type, weapon_data.qualities)

async def get_passive_stats_raw(p_type : int = None, qualities : list[int] = None):
    passive_config = get_passive_config(p_type = p_type)
    stats = []

    # converting qualities from % to actually stat numbers
    for index, quality in enumerate(qualities):
        stat = passive_config["stats"][index]
        value = stat["min"] + (stat["max"] - stat["min"]) * (quality / 100)

        stats.append(value)
    
    return stats