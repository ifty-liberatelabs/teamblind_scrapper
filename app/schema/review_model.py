from pydantic import BaseModel
from typing import Any  

class Model(BaseModel):
    overall: int
    career: int
    balance: int
    compensation: int
    culture: int
    management: int
    summary: str
    pros: str
    cons: str
    reasonResign: Any
    createdAt: str
