from utils.util_file import get_config, get_weapon_config
from battle_system.files.battle_classes import BattleWeapon, BattleWeaponPassive, BattleMonster, ActionContext, BattleLogEntry, Effect
from typing import List, Optional
import secrets

class Wand(BattleWeapon):
    # CONSTANTS
    w_type = 2

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
        target : list[BattleMonster] = []
        
        actor.use_mana(actor.weapon.get_mana_cost(), action_ctx)

        for battle_monster in [*action_ctx.actor_team.monsters, *action_ctx.target_team.monsters]:
            if (not battle_monster.is_alive()):
                continue

            if (battle_monster.m_type != 7):
                target.append(battle_monster)
        
        # set new target
        action_ctx.target = target 

        self.before_action(action_ctx)

        if (secrets.randbits(100) == 100):
            for battle_monster in target:
                # damage gets negated etc. so we overwrite the value with what return
                total_hp = battle_monster.get_stat("hp")["total"]

                battle_monster.deal_damage("true", total_hp)
        
        battle_ctx.logs.add_entry(BattleLogEntry(
            battle_ctx.turn_number,
            actor,
            target,
            "damage",
            f"**{actor.emoji} {actor.name} {self.emoji}** just **killed** {','.join([f'**{battle_monster.emoji} {battle_monster.name}**' for battle_monster in action_ctx.target]) if action_ctx.target else "nobody"}!"
        ))

        self.after_action(action_ctx)

        # death message
        for battle_monster in target:
            battle_monster.on_dead(action_ctx)