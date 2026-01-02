from __future__ import annotations
from utils.util_file import get_config, get_active_team, get_team, get_weapon_config, get_passive_config, xp_for_level, get_counter, get_db
from file_loader import load_weapons, load_passives
from typing import Optional, List
from utils.models import WeaponModel
from battle_classes import BattleTeam, BattleMonster, BattleWeapon, BattleWeaponPassive
from battle_main import Battle
from random import randint

# Load classes for all weapon files and passive files
WEAPON_REGISTRY = load_weapons()
PASSIVE_REGISTRY = load_passives()

def create_from_team_data(team_data, team_monsters):
    battle_monsters = []

    for monster in team_monsters:
        [monster_data, monster_config, t_monster, weapon_data, weapon_config] = monster 

        position_in_team = t_monster.pos
        battle_weapon = None 
        battle_weapon_passives = []

        if (monster_data.e_wid != -1):
            if (not weapon_data.w_type in WEAPON_REGISTRY):
                raise ValueError(f"Missing file for weapon type: {weapon_data.w_type}")
            
            weapon_class : BattleWeapon = WEAPON_REGISTRY[weapon_data.w_type]

            for passive_data in weapon_data.passives:
                if (not passive_data.p_type in PASSIVE_REGISTRY):
                    raise ValueError(f"Missing file for passive type: {passive_data.p_type}")
                
                passive_class : BattleWeaponPassive = PASSIVE_REGISTRY[passive_data.p_type]

                battle_weapon_passive = passive_class(position_in_team, passive_data.qualities)
                battle_weapon_passives.append(battle_weapon_passive)

            battle_weapon = weapon_class(position_in_team, weapon_data.qualities, battle_weapon_passives)

        battle_monster = BattleMonster(position_in_team, monster_data.m_type, monster_data.xp, battle_weapon, monster_data.m_id)
        battle_monsters.append(battle_monster)

    battle_team = BattleTeam(battle_monsters, team_data.t_id)

    return 

# examples: 
    # info_monsters = [{"pos": 1, "m_type": 3, "level": 4}] 
    # info_weapons = [{"pos": 1, "w_type": 2, "qualities": [25, 49]}, {"pos": 3, "w_type": 4, "qualities": [100, 20]}] 
    # info_passives = [[{"pos": 2, "p_type": 1, "qualities": [20]}, {"pos": 2, "p_type": 2, "qualities": [40, 100]}]]

def create_team(info_monsters, info_weapons, info_passives):
    config = get_config()
    MAX_QUALITY = config["settings"]["max_quality"]

    battle_monsters = []

    for info_monster in info_monsters:
        pos = info_monster["pos"]
        m_type = info_monster["m_type"]
        level = info_monster["level"]

        battle_weapon = None
        battle_weapon_passives = []

        # find weapon for this position (or None)
        info_weapon = next(
            (w for w in info_weapons if w.get("pos") == pos),
            None
        )

        if info_weapon and "w_type" in info_weapon:
            w_type = info_weapon["w_type"]

            if (w_type not in WEAPON_REGISTRY):
                raise ValueError(f"Missing file for weapon type: {w_type}")

            weapon_config = get_weapon_config(w_type=w_type)

            # weapon qualities
            w_qualities = info_weapon.get(
                "qualities",
                [MAX_QUALITY for _ in weapon_config["stats"]]
            )

            # find passives for this weapon position
            info_weapon_passives = next(
                (p_list for p_list in info_passives if p_list and p_list[0].get("pos") == pos),
                []
            )

            for info_passive in info_weapon_passives:
                p_type = info_passive.get("p_type")
                if (p_type is None):
                    continue

                if (p_type not in PASSIVE_REGISTRY):
                    raise ValueError(f"Missing file for passive type: {p_type}")

                passive_config = get_passive_config(p_type=p_type)

                p_qualities = info_passive.get(
                    "qualities",
                    [MAX_QUALITY for _ in passive_config["stats"]]
                )

                passive_class = PASSIVE_REGISTRY[p_type]
                battle_weapon_passives.append(
                    passive_class(pos, p_qualities)
                )

            if (len(battle_weapon_passives) != weapon_config["passive_count"]):
                raise ValueError(f"Incorrect passive count for weapon {w_type}: expected {weapon_config['passive_count']}, got {len(battle_weapon_passives)}")

            weapon_class = WEAPON_REGISTRY[w_type]
            battle_weapon = weapon_class(pos, w_qualities, battle_weapon_passives)

        battle_monster = BattleMonster(
            pos,
            m_type,
            xp_for_level(level),
            battle_weapon
        )

        battle_monsters.append(battle_monster)

    if (not battle_monsters):
        raise ValueError("Can't create team with no monsters")

    return BattleTeam(battle_monsters)

async def execute_battle(*, actor_user_id : int = None, target_user_id : int = None, actor_team_data : BattleTeam = None, target_team_data : BattleTeam = None, random_target : bool = None, count_streak : bool = False):
    actor_team : BattleTeam = None
    target_team : BattleTeam = None 

    if (actor_user_id):
        actor_team = create_from_team_data(await get_active_team(actor_user_id))

    if (actor_team_data):
        actor_team = actor_team_data

    if (target_user_id):
        target_team = create_from_team_data(await get_active_team(target_user_id))

    if (target_team_data):
        target_team = target_team_data

    if (random_target):
        team_seq = await get_counter("team")

        random_t_id = randint(1, team_seq)
        target_team = create_from_team_data(await get_team(None, team_id = random_t_id))

    if (actor_team and target_team):
        new_battle = Battle(actor_team, target_team)
        db = get_db()

        end_state = new_battle.process()
        
        match(end_state):
            case "actor_win":
                if (count_streak):
                    await db.teams.find_one_and_update(
                        {"t_id": actor_team.bt_id},
                        {"$inc": {"streak": 1}},
                    )
                pass
            case "target_win":
                if (count_streak):
                    await db.teams.find_one_and_update(
                        {"t_id": actor_team.bt_id},
                        {"$set": {"streak": 0}},
                    )
                pass
            case "tie":
                pass 
            case "tie_death":
                pass
        
        return new_battle
            
            


            


