from utils.util_file import get_config, get_active_team, get_monster_stats_raw, get_monster_config, get_weapon_stats_raw, get_passive_stats_raw
from battle_main import ActionContext
from file_loader import load_weapons, load_passives
import uuid
from typing import Optional, List
from random import sample
from utils.models import WeaponModel

# Load classes for all weapon files and passive files
WEAPON_REGISTRY = load_weapons()
PASSIVE_REGISTRY = load_passives()

class Effect():
    def __init__(self, turn_number, actor):
        # TODO: move to util file, get effect
        effect_config = next(
            (e for e in get_config()["effects"] if e["type"] == self.e_type)
        )

        self.from_turn_number = turn_number
        self.duration = effect_config["duration"]
        self.apply_immediately = effect_config["apply_immediately"] 
        self.apply_at_state = effect_config["apply_at_state"]
        self.from_actor_id = actor.bm_id

        # Turn-based hooks
    def before_turn(self, action_ctx : ActionContext):
        pass

    def during_turn(self, action_ctx : ActionContext):
        pass

    def after_turn(self, action_ctx : ActionContext):
        pass

    # Action-based hooks
    def before_action(self, action_ctx : ActionContext):
        pass

    def after_action(self, action_ctx : ActionContext):
        pass

    def use(self, action_ctx : ActionContext):
        pass

class BattleWeaponPassive:
    def __init__(self, pos, qualities):
        self.pos = pos 
        self.qualities = qualities
        self.stats = get_passive_stats_raw(self.p_type, self.qualities)

        # p_type defined in the subclass

    # Turn-based hooks
    def before_turn(self, action_ctx : ActionContext):
        pass

    def during_turn(self, action_ctx : ActionContext):
        pass

    def after_turn(self, action_ctx : ActionContext):
        pass

    # Action-based hooks
    def before_action(self, action_ctx : ActionContext):
        pass

    def after_action(self, action_ctx : ActionContext):
        pass

    def use(self, action_ctx : ActionContext):
        pass

class BattleWeapon:
    def __init__(self, pos, qualities, passives : Optional[List[BattleWeaponPassive]]):
        self.pos = pos
        self.qualities = qualities
        self.passives = passives
        self.stats = get_weapon_stats_raw(self.w_type, self.qualities)

        # w_type defined in the subclass

     # Turn-based hooks
    def before_turn(self, action_ctx : ActionContext):
        pass

    def during_turn(self, action_ctx : ActionContext):
        pass

    def after_turn(self, action_ctx : ActionContext):
        pass

    # Action-based hooks
    def before_action(self, action_ctx : ActionContext):
        pass

    def after_action(self, action_ctx : ActionContext):
        pass

    def use(self, action_ctx : ActionContext):
        pass

    def get_mana_cost(self):
        return self.stats[0]

class BattleMonster:
    def __init__(self, pos, m_type, xp, weapon : BattleWeapon = None, m_id = None):
        monster_config = get_monster_config(m_type = m_type)

        self.pos = pos 
        self.m_type = m_type
        self.xp = xp 
        self.weapon = weapon
        self.bm_id = m_id if m_id is not None else uuid.uuid4()
        self.name = monster_config["name"]
        self.effects : list[Effect] = []

        weapon_data = WeaponModel(
            w_type = self.weapon.w_type,
            qualities = self.weapon.qualities,
            passives = self.weapon.passives
        )

        self.stats = get_monster_stats_raw(self.m_type, self.xp, weapon_data)
        self.stats = [[stat, stat] for stat in self.stats] # first element is current stat, second total stat

    def is_alive(self):
        [current_hp, total_hp] = self.stats[0]

        if  (current_hp > 0):
            return True
        
        return False
    
    def can_use_weapon(self):
        [current_mana, total_mana] = self.stats[3]

        # TODO: Add freeze
        
        if (current_mana >= self.weapon.get_mana_cost()):
            return True
        
        return False


class BattleTeam:
    def __init__(self, monsters = list[BattleMonster], t_id = None):
        self.monsters = monsters
        self.bt_id = t_id if t_id is not None else uuid.uuid4()

    def is_alive(self):
        for battle_monster in self.monsters:
            [current_hp, total_hp] = battle_monster.stats[0]

            if (current_hp > 0):
                return True
            
        return False
    
    def get_monster(self, *, position : int = None, id : int | str = None):
        for battle_monster in self.monsters:
            if (position is not None):
                if (battle_monster.pos == position):
                    return battle_monster
            if (id is not None):
                if (battle_monster.bm_id == id):
                    return battle_monster
                
    def get_target(
            self,
            *,
            amount : int|str = 1,
            random = True,
            positions : list[int] = []
    ):
        if (amount == "all"):
            amount = len(self.monsters)
        elif (amount < 0):
            amount = 1
        elif (amount > len(self.monsters)): # case when amount is higher number than team has monsters
            amount = len(self.monsters)

        selected_targets = []

        if (random):
            generated_indexes = sample(range(len(self.monsters)), k = amount)

            selected_targets = [self.monsters[index] for index in generated_indexes]
        else:
            if (len(positions) > 0):
                selected_targets = [self.get_monster(position = pos) for pos in positions]

        return selected_targets


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