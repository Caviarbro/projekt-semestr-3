from pydantic import BaseModel, Field
from typing import List, Optional

# Monster model
class MonsterModel(BaseModel):
    m_id: int
    m_type: int
    e_wid: int = -1
    xp: int = 0
    seq: int = 1

# Weapon model
class PassiveModel(BaseModel):
    p_type: int
    qualities: List = []

class WeaponModel(BaseModel):
    w_id: int
    w_type: int
    qualities: List = []
    passives: List[PassiveModel] = []

# User model
class UserModel(BaseModel):
    _id: int
    u_id: int
    cash: int = 0
    monsters: List[MonsterModel] = []
    weapons: List[WeaponModel] = []

class Counter(BaseModel):
    c_type: str
    seq: int = 0


