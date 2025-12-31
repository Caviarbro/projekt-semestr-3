from utils.util_file import get_config
from battle_util import BattleMonster, BattleWeapon, BattleWeaponPassive, BattleTeam

class BattleLogEntry:
    def __init__(self, turn_number, actor, target, action_name, result):
        self.turn_number = turn_number
        self.actor_id = actor.bm_id
        self.target_ids = [t.bm_id for t in target]
        self.action_name = action_name
        self.result = result
        pass

class BattleLog:
    def __init__(self):
        self.logs = []
        pass

    def add_entry(self, entry : BattleLogEntry):
        turn_number = entry.turn_number

        if (turn_number > (len(self.logs) - 1)):
            self.logs.append({
                "turn_number": turn_number,
                "entries": []
            })

        turn_log = self.logs[turn_number]

        turn_log["entries"].append(entry)

class ActionContext:
    def __init__(self, actor, target, battle_ctx):
        self.actor = actor
        self.target = target
        self.battle_ctx = battle_ctx

        self.actor_team = self.get_team(self.actor)
        self.target_team = self.get_team(self.target)
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
        self.actor_team = actor_team
        self.target_team = target_team
        self.turn_number = turn_number
        self.battle_state = battle_state
        self.logs = BattleLog()

class Battle:
    def __init__(self, actor_team, target_team):
        self.actor_team = actor_team 
        self.target_team = target_team
        self.winner_id = None

        self.battle_ctx = BattleContext(actor_team, target_team, 0, "None")

    def process(self):
        config = get_config()

        MAX_BATTLE_TURNS = config["settings"]["max_battle_turns"]
        MAX_MONSTERS_PER_TEAM = config["settings"]["max_monsters_per_team"]
        TEAM_POSITION_START_INDEX = config["settings"]["team_position_start_index"]

        # sort from lowest to highest position
        self.actor_team.monsters.sort(key=lambda m: m.pos)
        self.target_team.monsters.sort(key=lambda m: m.pos)

        for turn_number in range(0, MAX_BATTLE_TURNS):
            battle_states = ["pre_turn", "during_turn", "after_turn"]

            # TODO: Check if monsters are alive, to determine the winner of the battle at the end of the turn
            
            for battle_state in battle_states:
                self.battle_ctx.battle_state = battle_state
                
                for pos in range(TEAM_POSITION_START_INDEX, MAX_MONSTERS_PER_TEAM):
                    actor_battle_monster : BattleMonster = self._get_monster_on_position(pos, self.actor_team)
                    target_battle_monster : BattleMonster = self._get_monster_on_position(pos, self.target_team)

                    if (actor_battle_monster is not None):
                        actor_action_ctx = self._process_state_action(actor_battle_monster, self.target_team.monsters)

                    if (target_battle_monster is not None):
                        target_action_ctx = self._process_state_action(target_battle_monster, self.actor_team.monsters)

    def _process_state_action(self, actor_battle_monster : BattleMonster, target : list[BattleMonster]):
        action_ctx = ActionContext(actor_battle_monster, target, self.battle_ctx)
        actor_battle_weapon : BattleWeapon = actor_battle_monster.weapon
        
        battle_state = self.battle_ctx.battle_state

        if (battle_state == "pre_turn"):
            if (actor_battle_weapon is not None):
                actor_battle_weapon.before_turn(action_ctx)

                for passive in actor_battle_weapon.passives:
                    passive.before_turn(action_ctx)
        elif (battle_state == "during_turn"):
            if (actor_battle_weapon is not None):
                actor_battle_weapon.during_turn(action_ctx)

                for passive in actor_battle_weapon.passives:
                    passive.during_turn(action_ctx)
        elif (battle_state == "after_turn"):
            if (actor_battle_weapon is not None):
                actor_battle_weapon.after_turn(action_ctx)

                for passive in actor_battle_weapon.passives:
                    passive.after_turn(action_ctx)

        return action_ctx

    def _get_monster_on_position(self, pos, battle_team):
        return next(
            (battle_monster for battle_monster in battle_team.monsters if battle_monster.pos == pos),
            None
        )