import math
from dataclasses import dataclass
from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from .abc import EntityId
    from .predator import PredatorId, Predator
    from .prey import PreyId, Prey
    from .food import Food, FoodId


@dataclass(slots=True, init=True, eq=True, order=True, kw_only=True)
class WorldPosition:
    x: int
    y: int

    @classmethod
    def from_tuple(cls, t: tuple[int, int]) -> "WorldPosition":
        return cls(x=t[0], y=t[1])

    def to_tuple(self) -> tuple[int, int]:
        return self.x, self.y

    def distance_from(self, other: "WorldPosition") -> float:
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


@dataclass(slots=True, frozen=True)
class SimulationState:
    predator_by_id: dict["PredatorId", "Predator"]
    prey_by_id: dict["PreyId", "Prey"]
    food_by_id: dict["FoodId", "Food"]

    entity_id_by_position: dict[tuple[int, int], "EntityId"]

    food_spawning_accumulator: float

    def predators(self) -> Iterable["Predator"]:
        return self.predator_by_id.values()

    def prey(self) -> Iterable["Prey"]:
        return self.prey_by_id.values()

    def food(self) -> Iterable["Food"]:
        return self.food_by_id.values()
