from utils.util_file import get_config
from battle_system.files.battle_util import BattleWeapon, BattleWeaponPassive
from battle_system.files.battle_main import BattleContext, ActionContext, BattleLogEntry
from typing import List, Optional


class Sword(BattleWeapon):
    # CONSTANTS
    w_type = 0

    # METHODS
    def __init__(self, pos: int, qualities: list, passives: Optional[List[BattleWeaponPassive]] = None):
        super().__init__(pos, qualities, passives)

    # Turn-based hooks
    def before_turn(self, action_ctx):
        pass

    def during_turn(self, action_ctx):
        self.use(action_ctx)

    def after_turn(self, action_ctx):
        pass

    # Action-based hooks
    def before_action(self, action_ctx):
        pass

    def after_action(self, action_ctx):
        pass

    def use(self, action_ctx):
        self.before_action(action_ctx)

        # deal damage or something
        
        self.after_action(action_ctx)
        return action_ctx