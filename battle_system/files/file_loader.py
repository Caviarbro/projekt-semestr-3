import pkgutil
import importlib
import inspect

from battle_classes import BattleWeapon, BattleWeaponPassive
import battle_system.weapons as weapons_pkg
import battle_system.passives as passives_pkg

def load_weapons():
    weapons = {}

    for _, module_name, _ in pkgutil.iter_modules(weapons_pkg.__path__):
        module = importlib.import_module(f"{weapons_pkg.__name__}.{module_name}")

        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BattleWeapon) and obj is not BattleWeapon:
                weapons[obj.w_type] = obj  # map type -> class

    return weapons

def load_passives():
    passives = {}

    for _, module_name, _ in pkgutil.iter_modules(passives_pkg.__path__):
        module = importlib.import_module(f"{passives_pkg.__name__}.{module_name}")

        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BattleWeaponPassive) and obj is not BattleWeaponPassive:
                passives[obj.p_type] = obj  # map type -> class

    return passives
