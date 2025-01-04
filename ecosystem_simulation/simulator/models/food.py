import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .abc import EntityId

if TYPE_CHECKING:
    from .world import WorldPosition


@dataclass(slots=True, frozen=True)
class FoodId(EntityId):
    id: int

    @classmethod
    def new_random(cls) -> "FoodId":
        return cls(id=random.randint(0, 2**16))



@dataclass(slots=True)
class Food:
    id: FoodId
    position: "WorldPosition"
