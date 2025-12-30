from utils.util_file import get_config, get_active_team, get_monster_stats, get_monster_config
from battle_main import ActionContext
from file_loader import load_weapons, load_passives
import uuid

# Load classes for all weapon files and passive files
WEAPON_REGISTRY = load_weapons()
PASSIVE_REGISTRY = load_passives()

class BattleWeaponPassive:
    def __init__(self, pos, qualities):
        self.pos = pos 
        self.qualities = qualities

        # p_type defined in the subclass

    # Turn-based hooks
    def before_turn(self, action_ctx):
        pass

    def during_turn(self, action_ctx):
        pass

    def after_turn(self, action_ctx):
        pass

    # Action-based hooks
    def before_action(self, action_ctx):
        pass

    def after_action(self, action_ctx):
        pass

    def use(self, action_ctx):
        pass

class BattleWeapon:
    def __init__(self, pos, qualities, passives):
        self.pos = pos
        self.qualities = qualities
        self.passives = passives

        # w_type defined in the subclass
    
     # Turn-based hooks
    def before_turn(self, action_ctx):
        pass

    def during_turn(self, action_ctx):
        pass

    def after_turn(self, action_ctx):
        pass

    # Action-based hooks
    def before_action(self, action_ctx):
        pass

    def after_action(self, action_ctx):
        pass

    def use(self, action_ctx):
        pass

class BattleMonster:
    def __init__(self, pos, m_type, xp, weapon = None, m_id = None):
        monster_config = get_monster_config(m_type = m_type)

        self.pos = pos 
        self.m_type = m_type
        self.xp = xp 
        self.weapon = weapon
        self.bm_id = m_id if m_id is not None else uuid.uuid4()
        self.name = monster_config["name"]
        self.stats = get_monster_stats(None, None, defined_m_type = self.m_type, defined_weapon_data = self.weapon, defined_xp = self.xp)

class BattleTeam:
    def __init__(self, monsters = list[BattleMonster], t_id = None):
        self.monsters = monsters
        self.id = t_id if t_id is not None else uuid.uuid4()


def create_from_team_data(team_data, team_monsters):
    battle_monsters = []

    for monster in team_monsters:
        [monster_data, monster_config, t_monster, weapon_data, weapon_config] = monster 

        position_in_team = t_monster.pos
        battle_weapon = None 
        battle_weapon_passives = []

        if (monster_data.e_wid != -1):
            weapon_class : BattleWeapon = WEAPON_REGISTRY[weapon_data.w_type]

            if (weapon_class is None):
                raise ValueError(f"Missing file for weapon type: {weapon_data.w_type}")

            for passive_data in weapon_data.passives:
                passive_class : BattleWeaponPassive = PASSIVE_REGISTRY[passive_data.p_type]

                if (passive_class is None):
                    raise ValueError(f"Missing file for passive type: {weapon_data.w_type}")

                battle_weapon_passive = passive_class(position_in_team, passive_data.qualities)
                battle_weapon_passives.append(battle_weapon_passive)

            battle_weapon = weapon_class(position_in_team, weapon_data.qualities, battle_weapon_passives)

        battle_monster = BattleMonster(position_in_team, monster_data.m_type, monster_data.xp, battle_weapon, monster_data.m_id)
        battle_monsters.append(battle_monster)

    battle_team = BattleTeam(battle_monsters, team_data.t_id)

    return battle_team