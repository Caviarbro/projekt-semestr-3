from random import sample
from utils.util_file import get_config
from .battle_classes import BattleMonster, BattleWeapon, BattleWeaponPassive, BattleTeam, Effect, BattleContext, ActionContext, BattleLogSnapshot

class Battle:
    def __init__(self, actor_team, target_team):
        self.actor_team : BattleTeam = actor_team 
        self.target_team : BattleTeam = target_team
        self.end_state = None
        self.battle_ctx = BattleContext(actor_team, target_team, 0, "None")

    def process(self):
        config = get_config()

        MAX_BATTLE_TURNS = config["settings"]["max_battle_turns"]
        MAX_MONSTERS_PER_TEAM = config["settings"]["max_monsters_per_team"]
        TEAM_POSITION_START_INDEX = config["settings"]["team_position_start_index"]

        # sort from lowest to highest position
        self.actor_team.monsters.sort(key=lambda m: m.pos)
        self.target_team.monsters.sort(key=lambda m: m.pos)

        for turn_number in range(MAX_BATTLE_TURNS):
            battle_states = ["pre_turn", "during_turn", "after_turn"]

            self.battle_ctx.turn_number = turn_number
            # TODO:  Add attack without weapon | Check if monster can attack (in individual files) | Add mana consumption and corresponding stuff (can't attack if mana is less than..)
            
            for battle_state in battle_states:
                self.battle_ctx.battle_state = battle_state
                
                # TODO: maybe redo the logic for position using weapons, so even if monster is not present on certain position it gets the next one that is in the team?
                for pos in range(TEAM_POSITION_START_INDEX, MAX_MONSTERS_PER_TEAM + 1):
                    actor_battle_monster : BattleMonster = self.actor_team.get_monster(position = pos)
                    target_battle_monster : BattleMonster = self.target_team.get_monster(position = pos)

                    if (actor_battle_monster is not None):
                        actor_action_ctx = self._process_state_action(actor_battle_monster, self.target_team.monsters)

                    if (target_battle_monster is not None):
                        target_action_ctx = self._process_state_action(target_battle_monster, self.actor_team.monsters)

               
                if (battle_state == "after_turn"):
                     # add snapshot after every turn, so we can get back to all of the properties
                    snapshot_after_turn = BattleLogSnapshot(self.battle_ctx)

                    self.battle_ctx.logs.add_snapshot(snapshot_after_turn)

                    # remove inactive effects
                    for battle_monster in [*self.actor_team.monsters, *self.target_team.monsters]:
                        battle_monster.remove_effects(inactive = True, current_turn_number = turn_number)

                    # check if teams are alive to determine user
                    is_actor_team_alive = self.actor_team.is_alive()
                    is_target_team_alive = self.target_team.is_alive()

                    if (is_actor_team_alive and not is_target_team_alive): # actor team is winner
                        self.end_state = "actor_win"
                    elif (not is_actor_team_alive and is_target_team_alive): # target team is winner
                        self.end_state = "target_win"
                    elif (not is_actor_team_alive and not is_target_team_alive): # both died = tie
                        self.end_state = "tie_death"
                    elif (turn_number + 1 >= MAX_BATTLE_TURNS): # turn limit = tie
                        self.end_state = "tie"

                    if (self.end_state):
                        return self.end_state

    def _process_state_action(self, actor_battle_monster : BattleMonster, target : list[BattleMonster]):
        action_ctx = ActionContext(actor_battle_monster, target, self.battle_ctx)
        actor_battle_weapon : BattleWeapon = actor_battle_monster.weapon
        actor_effects : list[Effect] = actor_battle_monster.effects

        battle_state = self.battle_ctx.battle_state

        if (not actor_battle_monster.is_alive()):
            return action_ctx
        
        if (actor_battle_weapon is None or not actor_battle_monster.can_use_weapon()):
            actor_battle_monster.basic_attack(action_ctx)

        match(battle_state):
            case "pre_turn":
                for effect in actor_effects:
                    effect.before_turn(action_ctx)

                if (actor_battle_monster.can_use_weapon()):
                    actor_battle_weapon.before_turn(action_ctx)

                    for passive in actor_battle_weapon.passives:
                        passive.before_turn(action_ctx)
            case "during_turn":
                for effect in actor_effects:
                    effect.during_turn(action_ctx)

                if (actor_battle_monster.can_use_weapon()):
                    actor_battle_weapon.during_turn(action_ctx)

                    for passive in actor_battle_weapon.passives:
                        passive.during_turn(action_ctx)
            case "after_turn":
                for effect in actor_effects:
                    effect.after_turn(action_ctx)

                if (actor_battle_monster.can_use_weapon()):
                    actor_battle_weapon.after_turn(action_ctx)

                    for passive in actor_battle_weapon.passives:
                        passive.after_turn(action_ctx)
            
        return action_ctx