from pydantic import BaseModel, Field
from typing import List, Optional

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

# Monster model
class MonsterModel(BaseModel):
    m_id: int
    m_type: int
    xp: int = 0
    seq: int = 0

# Weapon model
class WeaponModel(BaseModel):
    w_id: int
    w_type: int
    qualities: List = []