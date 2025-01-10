import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .world_position import WorldPosition
from .abc import EntityId

if TYPE_CHECKING:
    from .world import WorldPosition


@dataclass(slots=True, frozen=True)
class FoodId(EntityId):
    id: int

    @classmethod
    def new_random(cls) -> "FoodId":
        return cls(id=random.randint(0, 2**16))
    
    def serialize(self):
        return self.id
    
    def deserialize(data):
        return FoodId(id=data)



@dataclass(slots=True)
class Food:
    id: FoodId
    position: "WorldPosition"

    def serialize(self):
        return {
            "id": self.id.serialize(),
            "position": self.position.serialize()
        }
    
    def deserialize(data):
        return Food(
            id=FoodId.deserialize(data["id"]),
            position=WorldPosition.deserialize(data["position"])
        )
