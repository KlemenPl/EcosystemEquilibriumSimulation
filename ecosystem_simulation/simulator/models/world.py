from collections import defaultdict
from dataclasses import dataclass, field
from typing import Collection, Iterator

from ..models.world_position import WorldPosition
from ..models.entity import Entity
from ..models.food import Food
from ..models.creature import Prey, Predator


@dataclass(slots=True, frozen=True)
class SimulationState:
    grid_width: int
    grid_height: int
    entity_by_id: dict[int, Entity] = field(default_factory=dict)

    predator_by_position: dict[tuple[int, int], list[Predator]] = field(default_factory=lambda: defaultdict(list))
    prey_by_position: dict[tuple[int, int], list[Prey]] = field(default_factory=lambda: defaultdict(list))
    food_by_position: dict[tuple[int, int], list[Food]] = field(default_factory=lambda: defaultdict(list))

    food_spawning_accumulator: float = 0

    def predators(self) -> Iterator[Predator]:
        for pred_list in self.predator_by_position.values():
            for pred in pred_list:
                yield pred

    def prey(self) -> Iterator[Prey]:
        for prey_list in self.prey_by_position.values():
            for prey in prey_list:
                yield prey

    def food(self) -> Iterator[Food]:
        for food_list in self.food_by_position.values():
            for food in food_list:
                yield food

    def predator_count(self) -> int:
        return sum(len(preds) for preds in self.predator_by_position.values())

    def prey_count(self) -> int:
        return sum(len(preys) for preys in self.prey_by_position.values())

    def food_count(self) -> int:
        return sum(len(foods) for foods in self.food_by_position.values())

    def iter_entities(self) -> Iterator[Entity]:
        for predator in self.predators():
            yield predator
        for prey in self.prey():
            yield prey
        for food in self.food():
            yield food

    def iter_nearby(self, pos: WorldPosition, radius: int) -> Iterator[Entity]:
        for dx in range(max(pos.x - radius, 0), min(pos.x + radius, self.grid_width)):
            for dy in range(max(pos.y - radius, 0), min(pos.y + radius, self.grid_height)):
                for e in self.food_by_position[(dx, dy)]:
                    yield e
                for e in self.prey_by_position[(dx, dy)]:
                    yield e
                for e in self.predator_by_position[(dx, dy)]:
                    yield e

    def iter_nearby_food(self, pos: WorldPosition, radius: int) -> Iterator[Food]:
        for dx in range(max(pos.x - radius, 0), min(pos.x + radius, self.grid_width)):
            for dy in range(max(pos.y - radius, 0), min(pos.y + radius, self.grid_height)):
                for e in self.food_by_position[(dx, dy)]:
                    yield e

    def iter_nearby_prey(self, pos: WorldPosition, radius: int) -> Iterator[Prey]:
        for dx in range(max(pos.x - radius, 0), min(pos.x + radius, self.grid_width)):
            for dy in range(max(pos.y - radius, 0), min(pos.y + radius, self.grid_height)):
                for e in self.prey_by_position[(dx, dy)]:
                    yield e

    def iter_nearby_predator(self, pos: WorldPosition, radius: int) -> Iterator[Predator]:
        for dx in range(max(pos.x - radius, 0), min(pos.x + radius, self.grid_width)):
            for dy in range(max(pos.y - radius, 0), min(pos.y + radius, self.grid_height)):
                for e in self.predator_by_position[(dx, dy)]:
                    yield e


    def serialize(self):
        return {
            "predators": [predator.serialize() for predator in self.predators()],
            "prey": [prey.serialize() for prey in self.prey()],
            "food": [food.serialize() for food in self.food()],
            "food_spawning_accumulator": self.food_spawning_accumulator
        }

"""
    @staticmethod
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
"""
