from utils.util_file import get_config
from battle_system.files.battle_classes import Effect, BattleMonster, BattleContext, ActionContext, BattleLogEntry
from typing import List, Optional

class Freeze(Effect):
    # CONSTANTS
    e_type = 0

    # METHODS
    def __init__(self, turn_number : int, actor : BattleMonster):
        super().__init__(turn_number, actor)

     # Turn-based hooks
    def before_turn(self, action_ctx : ActionContext):
        self.use(action_ctx)

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
        battle_ctx = action_ctx.battle_ctx
        actor = action_ctx.actor

        # freeze effect is negative effect, that is directly affecting the actor
        action_ctx.target = [actor]

        self.before_action(action_ctx)

        # it's a negative effect that's why it yields the actor's weapon unusable (and not using any target)
        actor.weapon_unusable = True

        battle_ctx.logs.add_entry(BattleLogEntry(
            battle_ctx.turn_number,
            actor,
            action_ctx.target,
            "freeze",
            f"**{actor.emoji} {actor.name}** is frozen and can't attack!"
        ))
        
        self.after_action(action_ctx)

    def on_remove(self, actor : BattleMonster):
        actor.weapon_unusable = False