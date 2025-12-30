from utils.util_file import get_config

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

        self.battle_ctx = BattleContext(actor_team, target_team, 0, "None")

    def process(self):
        config = get_config()

        MAX_BATTLE_TURNS = config["settings"]["max_battle_turns"]

        for turn_number in range(0, MAX_BATTLE_TURNS):
            pass