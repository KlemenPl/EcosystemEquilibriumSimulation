import json
from dataclasses import dataclass
from enum import IntEnum


class LogicType(IntEnum):
    NORMAL = 1
    FUZZY = 2


@dataclass(slots=True, frozen=True)
class EntitySimulationOptions:
    # The number of predators to spawn when initializing the simulation grid.
    initial_number: int

    # Satiation value of initially spawned or newly born predators.
    initial_satiation_on_spawn: float

    # Combines with maturity age gene to determine ticks until maturity.
    max_juvenile_in_ticks: int

    # Combines with gestation age gene to determine ticks until new offspring is born.
    max_gestation_in_ticks: int

    max_age_in_ticks: int

    # The maximum number of children a single predator specimen can birth at once.
    max_children_per_birth: int

    # How much satiation a specimen gains by eating one prey.
    satiation_per_feeding: float

    satiation_loss_per_tick: float


@dataclass(slots=True, frozen=True)
class SimulationOptions:
    randomness_seed: int

    # This sets the logic used for determining creature next creature state
    logic_determine_creature_state: LogicType

    # This means the x position values will go from `0` to `world_width` (exclusive).
    world_width: int

    # This means the y position values will go from `0` to `world_height` (exclusive).
    world_height: int

    # The maximum distance the vision gene can improve a predator or prey's vision,
    # measured in a grid radius.
    max_vision_distance: int

    # A range between 0 and 1, 1 being a guaranteed mutation when mating.
    child_gene_mutation_chance_when_mating: float

    # Magnitude of the positive or negative changes to a gene when mutating.
    # Whether a change is positive or negative is uniformly chosen, and so is
    # the magnitude of the change, after which it is multiplied with this value.
    child_gene_mutation_magnitude_when_mating: float

    # The spawning rate of food items per second.
    food_item_spawning_rate_per_tick: float
    food_item_life_tick: int
    initial_number_of_food_items: int
    max_number_of_food_items: int

    predator: EntitySimulationOptions
    prey: EntitySimulationOptions

    @staticmethod
    def from_json_str(json_str: str) -> "SimulationOptions":
        params = json.loads(json_str)

        predator = EntitySimulationOptions(**params.pop("predator"))
        prey = EntitySimulationOptions(**params.pop("prey"))

        return SimulationOptions(**params, predator=predator, prey=prey)

    @staticmethod
    def from_json_file(path: str) -> "SimulationOptions":
        with open(path, "r") as f:
            res = json.loads(f.read())
            return SimulationOptions.from_json_str(res["params"])
