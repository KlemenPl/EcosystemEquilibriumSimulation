import math
import time
from dataclasses import dataclass
from typing import Iterable, TYPE_CHECKING

from .predator import PredatorId, Predator
from .prey import PreyId, Prey
from .food import Food, FoodId

@dataclass(slots=True, frozen=True)
class SimulationState:
    predator_by_id: dict["PredatorId", "Predator"]
    prey_by_id: dict["PreyId", "Prey"]
    food_by_id: dict["FoodId", "Food"]

    predator_by_position: dict[tuple[int, int], "Predator"]
    prey_by_position: dict[tuple[int, int], "Prey"]
    food_by_position: dict[tuple[int, int], "Food"]

    food_spawning_accumulator: float

    def predators(self) -> Iterable["Predator"]:
        return self.predator_by_id.values()

    def prey(self) -> Iterable["Prey"]:
        return self.prey_by_id.values()

    def food(self) -> Iterable["Food"]:
        return self.food_by_id.values()

    def predator_count(self) -> int:
        return len(self.predator_by_id)

    def prey_count(self) -> int:
        return len(self.prey_by_id)

    def food_count(self) -> int:
        return len(self.food_by_id)

    def serialize(self):
        return {
            "predators": [predator.serialize() for predator in self.predators()],
            "prey": [prey.serialize() for prey in self.prey()],
            "food": [food.serialize() for food in self.food()],
            "food_spawning_accumulator": self.food_spawning_accumulator
        }
    
    def deserialize(data):
        predator_by_id={PredatorId.deserialize(predator["id"]): Predator.deserialize(predator) for predator in data["predators"]}
        prey_by_id={PreyId.deserialize(prey["id"]): Prey.deserialize(prey) for prey in data["prey"]}
        food_by_id={FoodId.deserialize(food["id"]): Food.deserialize(food) for food in data["food"]}
        predator_by_position={predator.position.to_tuple(): predator for predator in predator_by_id.values()}
        prey_by_position={prey.position.to_tuple(): prey for prey in prey_by_id.values()}
        food_by_position={food.position.to_tuple(): food for food in food_by_id.values()}
        food_spawning_accumulator=data["food_spawning_accumulator"]
    
        return SimulationState(
            predator_by_id=predator_by_id,
            prey_by_id=prey_by_id,
            food_by_id=food_by_id,
            predator_by_position=predator_by_position,
            prey_by_position=prey_by_position,
            food_by_position=food_by_position,
            food_spawning_accumulator=food_spawning_accumulator
        )