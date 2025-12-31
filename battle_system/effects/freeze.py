from utils.util_file import get_config
from battle_system.files.battle_util import Effect, BattleMonster
from battle_system.files.battle_main import BattleContext, ActionContext, BattleLogEntry
from typing import List, Optional

class Freeze(Effect):
    # CONSTANTS
    e_type = 0

    # METHODS
    def __init__(self, turn_number : int, actor : BattleMonster):
        super().__init__(turn_number)

     # Turn-based hooks
    def before_turn(self, action_ctx : ActionContext):
        pass

    def during_turn(self, action_ctx : ActionContext):
        self.use(action_ctx)

    def after_turn(self, action_ctx : ActionContext):
        pass

    # Action-based hooks
    def before_action(self, action_ctx : ActionContext):
        pass

    def after_action(self, action_ctx : ActionContext):
        pass

    def attach(self, action_ctx : ActionContext):
        battle_ctx : BattleContext = action_ctx.battle_ctx
        actor : BattleMonster = action_ctx.actor
        target : list[BattleMonster] = action_ctx.target

        turn_number = battle_ctx.turn_number
        
        # TODO: Add log

        for battle_monster in target:
            battle_monster.effects.append(Freeze(turn_number, actor))

    def use(self, action_ctx : ActionContext):
        self.before_action(action_ctx)

        # do something
        
        self.after_action(action_ctx)