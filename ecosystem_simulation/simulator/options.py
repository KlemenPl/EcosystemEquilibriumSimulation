from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class SimulatorOptions:
    # This means the x position values will go from `0` to `world_width` (exclusive).
    world_width: int

    # This means the y position values will go from `0` to `world_height` (exclusive).
    world_height: int

    # The maximum distance the vision gene can improve a predator or prey's vision,
    # measured in a grid radius.
    max_vision_distance: int

    initial_number_of_predators: int

    predator_initial_satiation_on_spawn: float

    predator_initial_reproductive_urge_on_spawn: float

    # The maximum number of children a single predator specimen can birth at once.
    predator_max_children_per_birth: int

    initial_number_of_prey: int

    prey_initial_satiation_on_spawn: float

    prey_initial_reproductive_urge_on_spawn: float

    # How much satiation a specimen gains by eating one food item.
    prey_satiation_per_food_item: float

    # The maximum number of children a single prey specimen can birth at once.
    prey_max_children_per_birth: int

    # A range between 0 and 1, 1 being a guaranteed mutation when mating.
    child_gene_mutation_chance_when_mating: float

    # Magnitude of the positive or negative changes to a gene when mutating.
    # Whether a change is positive or negative is uniformly chosen, and so is
    # the magnitude of the change, after which it is multiplied with this value.
    child_gene_mutation_magnitude_when_mating: float

    initial_number_of_food_items: int

    # The spawning rate of food items per second.
    #
    # The inter-arrival times for food items will be calculated using
    # an approximation of the Poisson distribution (see https://en.wikipedia.org/wiki/Poisson_distribution):
    #
    # t_i = (-1.0 / spawning rate) * log(1 - "uniformly sampled 0 to 1 value")
    #
    food_item_spawning_rate_per_second: float
