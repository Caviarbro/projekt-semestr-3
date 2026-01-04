from utils.util_file import get_config
from battle_system.files.battle_classes import BattleWeaponPassive, ActionContext, BattleLogEntry
from typing import List, Optional
import random

class Regeneration(BattleWeaponPassive):
    # CONSTANTS
    p_type = 0

    # METHODS
    def __init__(self, pos: int, qualities: list):
        super().__init__(pos, qualities)

     # Turn-based hooks
    def before_turn(self, action_ctx : ActionContext):
        pass

    def during_turn(self, action_ctx : ActionContext):
        pass

    def after_turn(self, action_ctx : ActionContext):
        self.use(action_ctx)

    # Action-based hooks
    def before_action(self, action_ctx : ActionContext):
        pass

    def after_action(self, action_ctx : ActionContext):
        pass

    def use(self, action_ctx : ActionContext):
        battle_ctx = action_ctx.battle_ctx
        actor = action_ctx.actor
        hp = actor.get_stat("hp")
        [chance, heal] = self.stats

        # we are targeting ourselves
        action_ctx.target = [actor]

        self.before_action(action_ctx)

        to_heal = hp["total"] * (heal / 100)

        if (random.randint(0, 100) <= chance):
            to_heal = actor.heal(to_heal)
        
            battle_ctx.logs.add_entry(BattleLogEntry(
                battle_ctx.turn_number,
                actor,
                action_ctx.target,
                "heal",
                f"**{actor.emoji} {actor.name}** got lucky and healed for **`{round(to_heal, 1)}`** HP!"
            ))

        self.after_action(action_ctx)