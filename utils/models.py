from pydantic import BaseModel, Field
from typing import List, Optional

# User model
class UserModel(BaseModel):
    _id: int  # Discord user ID
    cash: int = 0
    monsters: List[MonsterModel] = []

# Monster model
class MonsterModel(BaseModel):
    _id: str  # unique monster ID
    xp: int = 0
    stats: List = []