from utils.util_file import get_config
from battle_system.files.battle_classes import BattleWeaponPassive, ActionContext, BattleLogEntry
from typing import List, Optional
import random

class Manapoint(BattleWeaponPassive):
    # CONSTANTS
    p_type = 1

    # METHODS
    def __init__(self, pos: int, qualities: list):
        super().__init__(pos, qualities)

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

    def bonus(self, monster_stats = None, *, stat_value : int = None):
        if (self.monster_stat_types):
            monster_stat_type = self.monster_stat_types[0] # gives stat type on zero index, 0 doesn't mean hp stat type (stat type 0)
            monster_stat = monster_stats[monster_stat_type] if isinstance(monster_stats, list) else stat_value

            if (monster_stat is None):
                return

            bonus_stat = monster_stat * (1 + (self.stats[0] / 100))
            bonus_without_current_stat = abs(monster_stat - bonus_stat) 

            # monster_stats can be None because stat_value is used to get the bonus amount
            if (isinstance(monster_stats, list)):
                monster_stats[monster_stat_type] = bonus_stat 
            
            return bonus_without_current_stat

