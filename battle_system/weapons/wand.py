from utils.util_file import get_config, get_weapon_config
from battle_system.files.battle_classes import BattleWeapon, BattleWeaponPassive, BattleMonster, ActionContext, BattleLogEntry, Effect
from typing import List, Optional
from battle_system.files.file_loader import load_effects

EFFECTS_REGISTRY = load_effects()

class Wand(BattleWeapon):
    # CONSTANTS
    w_type = 1

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

        # % of mag
        mag = actor.get_stat("mag")
        damage = (self.stats[1] / 100) * mag["total"]

        for battle_monster in target:
            # damage gets negated etc. so we overwrite the value with what return
            damage = battle_monster.deal_damage("mag", damage)
        
        battle_ctx.logs.add_entry(BattleLogEntry(
            battle_ctx.turn_number,
            actor,
            target,
            "damage",
            f"**{actor.emoji} {actor.name} {self.emoji}** damaged {''.join([f'**{battle_monster.emoji} {battle_monster.name}**' for battle_monster in action_ctx.target])} for **`{round(damage, 1)}`** HP!"
        ))

        weapon_config = get_weapon_config(w_type = self.w_type)
        freeze_e_type = weapon_config["effect_types"][0]
        freeze : Effect = EFFECTS_REGISTRY[freeze_e_type]

        if (freeze):
            new_freeze : Effect = freeze(battle_ctx.turn_number, actor)
            new_freeze.attach(action_ctx)

        self.after_action(action_ctx)

        # death message
        for battle_monster in target:
            battle_monster.on_dead(action_ctx)