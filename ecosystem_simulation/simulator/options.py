from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class PredatorSimulationOptions:
    # The number of predators to spawn when initializing the simulation grid.
    initial_number: int

    # Satiation value of initially spawned or newly born predators.
    initial_satiation_on_spawn: float

    # Reproductive urge value of initially spawned or newly born predators.
    initial_reproductive_urge_on_spawn: float

    pregnancy_duration_in_ticks: int

    # The maximum number of children a single predator specimen can birth at once.
    max_children_per_birth: int

    # How much satiation a specimen gains by eating one prey.
    satiation_per_one_eaten_prey: float

    satiation_loss_per_tick: float

    def serialize(self):
        return {
            "initial_number": self.initial_number,
            "initial_satiation_on_spawn": self.initial_satiation_on_spawn,
            "initial_reproductive_urge_on_spawn": self.initial_reproductive_urge_on_spawn,
            "pregnancy_duration_in_ticks": self.pregnancy_duration_in_ticks,
            "max_children_per_birth": self.max_children_per_birth,
            "satiation_per_one_eaten_prey": self.satiation_per_one_eaten_prey,
            "satiation_loss_per_tick": self.satiation_loss_per_tick
        }

    @staticmethod
    def deserialize(data):
        return PredatorSimulationOptions(
            initial_number=data["initial_number"],
            initial_satiation_on_spawn=data["initial_satiation_on_spawn"],
            initial_reproductive_urge_on_spawn=data["initial_reproductive_urge_on_spawn"],
            pregnancy_duration_in_ticks=data["pregnancy_duration_in_ticks"],
            max_children_per_birth=data["max_children_per_birth"],
            satiation_per_one_eaten_prey=data["satiation_per_one_eaten_prey"],
            satiation_loss_per_tick=data["satiation_loss_per_tick"]
        )


@dataclass(slots=True, frozen=True)
class PreySimulationOptions:
    # The number of prey to spawn when initializing the simulation grid.
    initial_number: int

    # Satiation value of initially spawned or newly born prey.
    initial_satiation_on_spawn: float

    pregnancy_duration_in_ticks: int

    # Reproductive urge value of initially spawned or newly born prey.
    initial_reproductive_urge_on_spawn: float

    # How much satiation a specimen gains by eating one food item.
    satiation_per_food_item: float

    # The maximum number of children a single prey specimen can birth at once.
    max_children_per_birth: int

    satiation_loss_per_tick: float

    def serialize(self):
        return {
            "initial_number": self.initial_number,
            "initial_satiation_on_spawn": self.initial_satiation_on_spawn,
            "pregnancy_duration_in_ticks": self.pregnancy_duration_in_ticks,
            "initial_reproductive_urge_on_spawn": self.initial_reproductive_urge_on_spawn,
            "satiation_per_food_item": self.satiation_per_food_item,
            "max_children_per_birth": self.max_children_per_birth,
            "satiation_loss_per_tick": self.satiation_loss_per_tick
        }

    @staticmethod
    def deserialize(data):
        return PreySimulationOptions(
            initial_number=data["initial_number"],
            initial_satiation_on_spawn=data["initial_satiation_on_spawn"],
            pregnancy_duration_in_ticks=data["pregnancy_duration_in_ticks"],
            initial_reproductive_urge_on_spawn=data["initial_reproductive_urge_on_spawn"],
            satiation_per_food_item=data["satiation_per_food_item"],
            max_children_per_birth=data["max_children_per_birth"],
            satiation_loss_per_tick=data["satiation_loss_per_tick"]
        )    


@dataclass(slots=True, frozen=True)
class SimulationOptions:
    randomness_seed: int

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

    initial_number_of_food_items: int

    # The spawning rate of food items per second.
    food_item_spawning_rate_per_tick: float

    predator: PredatorSimulationOptions

    prey: PreySimulationOptions

    def serialize(self):
        return {
            "randomness_seed": self.randomness_seed,
            "world_width": self.world_width,
            "world_height": self.world_height,
            "max_vision_distance": self.max_vision_distance,
            "child_gene_mutation_chance_when_mating": self.child_gene_mutation_chance_when_mating,
            "child_gene_mutation_magnitude_when_mating": self.child_gene_mutation_magnitude_when_mating,
            "initial_number_of_food_items": self.initial_number_of_food_items,
            "food_item_spawning_rate_per_tick": self.food_item_spawning_rate_per_tick,
            "predator": self.predator.serialize(),
            "prey": self.prey.serialize()
        }

    @staticmethod
    def deserialize(data):
        return SimulationOptions(
            randomness_seed=data["randomness_seed"],
            world_width=data["world_width"],
            world_height=data["world_height"],
            max_vision_distance=data["max_vision_distance"],
            child_gene_mutation_chance_when_mating=data["child_gene_mutation_chance_when_mating"],
            child_gene_mutation_magnitude_when_mating=data["child_gene_mutation_magnitude_when_mating"],
            initial_number_of_food_items=data["initial_number_of_food_items"],
            food_item_spawning_rate_per_tick=data["food_item_spawning_rate_per_tick"],
            predator=PredatorSimulationOptions.deserialize(data["predator"]),
            prey=PreySimulationOptions.deserialize(data["prey"])
        )
