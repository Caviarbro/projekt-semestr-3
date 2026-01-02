from __future__ import annotations
from utils.util_file import get_config, get_active_team, get_monster_stats_raw, get_monster_config, get_weapon_stats_raw, get_passive_stats_raw, get_weapon_config, get_passive_config, xp_for_level
import uuid
from typing import Optional, List
from random import sample
from utils.models import WeaponModel

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
        self.e_id = uuid.uuid4()
        self.name = effect_config["name"]

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

    def attach(self, action_ctx : ActionContext, effect : Effect):
        battle_ctx = action_ctx.battle_ctx
        actor = action_ctx.actor        
        target = action_ctx.target

        battle_ctx.logs.add_entry(BattleLogEntry(
            battle_ctx.turn_number,
            actor,
            target,
            action_name = effect,
            result = f"{actor.name} applied {effect.name} to {target.name} for {effect.duration} turns!"
        ))

        for battle_monster in target:
            battle_monster.effects.append(effect.__class__(action_ctx.battle_ctx.turn_number, actor))
        
    def on_remove(self, actor):
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
        self.passives = passives or []
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

        weapon_data = None 

        if (self.weapon):
            weapon_data = WeaponModel(
                w_type = self.weapon.w_type,
                qualities = self.weapon.qualities,
                passives = self.weapon.passives
            )

        self.stats = get_monster_stats_raw(self.m_type, self.xp, weapon_data)
        self.stats = [[stat, stat] for stat in self.stats] # first element is current stat, second total stat

    def get_stat(self, stat_name):
        config = get_config()
        STAT_NAMES = config["settings"]["stat_names"]

        try:
            stat = self.stats[STAT_NAMES.index(stat_name)] 

            # TODO: Add bonus
            return { "current": stat[0], "total": stat[1], "bonus": 0}
        except Exception:
            raise ValueError(f"Stat {stat_name} does not exist!")

    def set_stat(self, stat_name, value):
        config = get_config()
        STAT_NAMES = config["settings"]["stat_names"]

        try:
            stat = self.stats[STAT_NAMES.index(stat_name)] 
            
            # sets current value to the specified value
            stat[0] = value
        except Exception as e:
            raise ValueError(f"Stat {stat_name} does not exist!")
        
    def is_alive(self):
        hp = self.get_stat("hp")

        if  (hp["current"] > 0):
            return True
        
        return False
    
    def can_use_weapon(self):
        mana = self.get_stat("mana")

        # TODO: Add freeze
        if (self.weapon is None):
            return False 
        
        if (self.weapon.unusable):
            return False
        
        if (mana["current"] >= self.weapon.get_mana_cost()):
            return True
        
        return False
    
    def remove_effects(self, *, effects : list[Effect] = None, effect_ids : list[int] = None, effect_types : list[int] = None, inactive = False, current_turn_number : int = None):
        def should_remove(effect: Effect) -> bool:
            if (effects is not None and effect in effects):
                return True

            if (effect_ids is not None and effect.e_id in effect_ids):
                return True

            if (effect_types is not None and effect.e_type in effect_types):
                return True

            if (inactive and current_turn_number is not None):
                end_turn = effect.from_turn_number + effect.duration + (0 if effect.apply_immediately else 1)

                return current_turn_number >= end_turn

            return False

        new_effects = []

        for effect in self.effects:
            if (should_remove(effect)):
                effect.on_remove(self)
            else:
                new_effects.append(effect)

        # apply remaining effects back
        self.effects = new_effects

    def deal_damage(self, damage_type : str, amount : int):
        hp = self.get_stat("hp")
        strength_defense = self.get_stat("strength_defense")
        mag_defense = self.get_stat("mag_defense")

        damage = 0

        match(damage_type):
            case "true":
                damage = amount
            case "strength":
                damage = amount * (strength_defense / 100)
            case "mag":
                damage = amount * (mag_defense / 100)

        self.set_stat("hp", hp["current"] - damage)

        return damage

    def use_mana(self, amount : int, action_ctx : ActionContext):
        battle_ctx = action_ctx.battle_ctx
        actor = self
        mana = self.get_stat("mana")

        if (not isinstance(amount, (int, float))):
            raise ValueError(f"Amount for mana constumption expected int got {type(amount)}")

        mana["current"] -= amount

        battle_ctx.logs.add_entry(BattleLogEntry(
            battle_ctx.turn_number,
            actor,
            actor,
            "mana",
            f"{actor.name} used {amount} mana!"
        ))

    def heal(self, amount : int, *, over_heal = False):
        hp = self.get_stat("hp")

        to_heal = amount

        if (hp["current"] + to_heal >= hp["total"]):
            if (over_heal):
                self.set_stat("hp", hp["total"] + to_heal)
            else:
                to_heal = (hp["current"] + to_heal) - hp["total"]
                self.set_stat("hp", hp["total"])

        return to_heal

class BattleTeam:
    def __init__(self, monsters: list[BattleMonster], t_id = None):
        self.monsters : list[BattleMonster] = monsters
        self.bt_id : int | str = t_id if t_id is not None else uuid.uuid4()

    def is_alive(self):
        for battle_monster in self.monsters:
            hp = battle_monster.get_stat("hp")

            if (hp["current"] > 0):
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
            positions : Optional[list[int]] = None,
            allow_dead : bool = False
    ) -> list[BattleMonster]:
        filtered_monsters = [battle_monster for battle_monster in self.monsters if battle_monster.is_alive()]

        # sometimes we need to target dead monsters too
        if (allow_dead):
            filtered_monsters = self.monsters

        if (amount == "all"):
            amount = len(filtered_monsters)
        elif (amount < 0):
            amount = 1
        elif (amount > len(filtered_monsters)): # case when amount is higher number than team has monsters
            amount = len(filtered_monsters)

        selected_targets = []

        if (random):
            generated_indexes = sample(range(len(filtered_monsters)), k = amount)

            selected_targets = [filtered_monsters[index] for index in generated_indexes]
        else:
            if (positions):
                selected_targets = [self.get_monster(position = pos) for pos in positions]

                if (not allow_dead):
                    selected_targets = [battle_monster for battle_monster in selected_targets if battle_monster.is_alive()]

        return selected_targets

class BattleLogEntry:
    def __init__(self, turn_number, actor : BattleMonster, target : list[BattleMonster] | None, action_name, result):
        self.turn_number = turn_number
        self.actor_id = actor.bm_id
        self.target_ids = [t.bm_id for t in target] if target else []
        self.action_name = action_name
        self.result = result
        pass

class BattleLogSnapshot:
    def __init__(self, battle_ctx : BattleContext):
        self.turn_number = battle_ctx.turn_number
        self.actor_team = battle_ctx.actor_team
        self.target_team = battle_ctx.target_team
        pass 

class BattleLog:
    def __init__(self):
        self.logs = []
        pass

    def add_entry(self, entry : BattleLogEntry):
        turn_number = entry.turn_number
        turn_log = self._get_turn_log(turn_number)

        turn_log["entries"].append(entry)

    def add_snapshot(self, snapshot : BattleLogSnapshot):
        turn_number = snapshot.turn_number
        turn_log = self._get_turn_log(turn_number)

        turn_log["snapshot"].append(snapshot)
        pass 

    def _get_turn_log(self, turn_number):
        if (not isinstance(turn_number, int)):
            raise ValueError(f"turn_number expected int got {type(turn_number)}")
        
        if (turn_number > (len(self.logs) - 1)):
            self.logs.append({
                "turn_number": turn_number,
                "entries": [],
                "snapshots": []
            })

        turn_log = self.logs[turn_number]

        return turn_log

class ActionContext:
    def __init__(self, actor, target, battle_ctx):
        self.actor : BattleMonster = actor
        self.target : list[BattleMonster] = target
        self.battle_ctx : BattleContext = battle_ctx

        self.actor_team : BattleTeam = self.get_team(self.actor)
        self.target_team : BattleTeam = self.get_team(self.target)
        pass

    def get_team(self, monster_or_list):
        if (isinstance(monster_or_list, list)):
            return next(
                (self._find_team(m) for m in monster_or_list),
                None
            )
        else:
            return self._find_team(monster_or_list)

    def _find_team(self, monster):
        teams = [self.battle_ctx.actor_team, self.battle_ctx.target_team]

        for team in teams:
            if (monster in team.monsters):
                return team
        return None

class BattleContext:
    def __init__(self, actor_team, target_team, turn_number, battle_state):
        self.actor_team : BattleTeam = actor_team
        self.target_team : BattleTeam = target_team
        self.turn_number = turn_number
        self.battle_state = battle_state
        self.logs = BattleLog()