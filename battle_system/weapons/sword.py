from utils.util_file import get_config
from battle_system.files.battle_classes import BattleWeapon, BattleWeaponPassive, BattleMonster, ActionContext, BattleLogEntry
from typing import List, Optional

class Sword(BattleWeapon):
    # CONSTANTS
    w_type = 0

    # METHODS
    def __init__(self, pos: int, qualities: list, passives: Optional[List[BattleWeaponPassive]] = None):
        super().__init__(pos, qualities, passives)

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

    def use(self, action_ctx : ActionContext):
        battle_ctx = action_ctx.battle_ctx
        actor = action_ctx.actor
        target = action_ctx.target_team.get_target(random = True)
        
        actor.use_mana(actor.weapon.get_mana_cost(), action_ctx)

        # set new target
        action_ctx.target = target 

        self.before_action(action_ctx)

        # % of str
        strength = actor.get_stat("strength")
        damage = (self.stats[1] / 100) * strength["total"]

        for battle_monster in target:
            # damage gets negated etc. so we overwrite the value with what return
            damage = battle_monster.deal_damage("strength", damage)
        
        battle_ctx.logs.add_entry(BattleLogEntry(
            battle_ctx.turn_number,
            actor,
            target,
            "damage",
            f"{actor.name} damaged {target.name} for {damage} HP!"
        ))

        self.after_action(action_ctx)