from dataclasses import dataclass

@dataclass(slots=True, frozen=True)
class PredatorGeneOptions:
    aggression_min: float
    aggression_max: float

    fertility_min: float
    fertility_max: float

    charisma_min: float
    charisma_max: float

    speed_min: float
    speed_max: float

    vision_min: float
    vision_max: float


@dataclass(slots=True, frozen=True)
class PredatorSpawnOptions:
    initial_hunger: float
    initial_energy: float


@dataclass(slots=True, frozen=True)
class PreyGeneOptions:
    fertility_min: float
    fertility_max: float

    charisma_min: float
    charisma_max: float

    speed_min: float
    speed_max: float

    vision_min: float
    vision_max: float


@dataclass(slots=True, frozen=True)
class PreySpawnOptions:
    initial_hunger: float
    initial_energy: float



@dataclass(slots=True, frozen=True)
class SimulatorOptions:
    # This means the x position values will go from `0` to `world_width` (exclusive).
    world_width: int

    # This means the y position values will go from `0` to `world_height` (exclusive).
    world_height: int

    initial_number_of_predators: int

    predator_spawn_options: PredatorSpawnOptions

    predator_gene_options: PredatorGeneOptions

    initial_number_of_prey: int

    prey_spawn_options: PreySpawnOptions

    prey_gene_options: PreyGeneOptions

    # A range between 0 and 1, 1 being a guaranteed mutation when mating.
    child_gene_mutation_chance_when_mating: float
