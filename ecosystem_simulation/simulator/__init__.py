import random

from .abc import SimulatorBackend, SimulatedTick
from .models import Prey, Predator, PreyGenes, PredatorGenes, WorldPosition, SimulationState, PreyId, PredatorId, Food
from .models.predator import PredatorIdleState
from .models.prey import PreyIdleState
from .options import SimulatorOptions
from .utilities import generate_random_position_in_world



def _prepare_initial_simulation_state(
    simulation_options: SimulatorOptions
) -> SimulationState:
    initial_predators: list[Predator] = []

    for _ in range(simulation_options.initial_number_of_predators):
        # Spawn the predator at a random position in the world.
        predator_position = generate_random_position_in_world(
            simulation_options.world_width,
            simulation_options.world_height
        )

        # Give the predator uniformly random genes in the configured range.
        predator_genes = PredatorGenes(
            aggression=random.uniform(0, 1),
            fertility=random.uniform(0, 1),
            charisma=random.uniform(0, 1),
            vision=random.uniform(0, 1),
            reproductive_urge_quickness=random.uniform(0, 1)
        )

        predator = Predator(
            id=PredatorId.new_random(),
            mind_state=PredatorIdleState(),
            genes=predator_genes,
            position=predator_position,
            satiation=simulation_options.predator_initial_satiation_on_spawn,
            reproductive_urge=simulation_options.predator_initial_reproductive_urge_on_spawn,
        )

        initial_predators.append(predator)


    initial_prey: list[Prey] = []

    for _ in range(simulation_options.initial_number_of_prey):
        # Spawn the prey at a random position in the world.
        prey_position = generate_random_position_in_world(
            simulation_options.world_width,
            simulation_options.world_height
        )

        # Give the prey uniformly random genes in the configured range.
        prey_genes = PreyGenes(
            appetite=random.uniform(0, 1),
            fertility=random.uniform(0, 1),
            charisma=random.uniform(0, 1),
            vision=random.uniform(0, 1),
            reproductive_urge_quickness=random.uniform(0, 1)
        )

        prey = Prey(
            id=PreyId.new_random(),
            mind_state=PreyIdleState(),
            genes=prey_genes,
            position=prey_position,
            satiation=simulation_options.prey_initial_satiation_on_spawn,
            reproductive_urge=simulation_options.prey_initial_reproductive_urge_on_spawn
        )

        initial_prey.append(prey)


    initial_food_items: list[Food] = []

    for _ in range(simulation_options.initial_number_of_food_items):
        food = Food(
            position=generate_random_position_in_world(
                simulation_options.world_width,
                simulation_options.world_height
            )
        )

        initial_food_items.append(food)


    return SimulationState(
        predators=initial_predators,
        prey=initial_prey,
        food=initial_food_items
    )


class DraftSimulationState:
    predators: list[Predator]
    prey: list[Prey]
    food: list[Food]

    def __init__(self):
        self.predators = []
        self.prey = []
        self.food = []

    def add_predator(self, predator: Predator):
        self.predators.append(predator)

    def add_prey(self, prey: Prey):
        self.prey.append(prey)

    def add_food_item(self, food_item: Food):
        self.food.append(food_item)

    def into_final_simulation_state(self) -> SimulationState:
        return SimulationState(
            predators=self.predators,
            prey=self.prey,
            food=self.food
        )


def _run_simulation_for_one_tick(state: SimulationState) -> SimulationState:
    """
    Will perform a single simulation tick. Because we want to track changes,
    **THIS FUNCTION MUST NOT MUTATE `state`**!
    """
    draft_state = DraftSimulationState()

    for predator in state.predators:
        # TODO
        raise NotImplementedError()

    for prey in state.prey:
        # TODO
        raise NotImplementedError()

    # TODO spawn some food based on the spawning rate
    
    # TODO a single simulation tick (see TODOs above).
    raise NotImplementedError()


class EcosystemSimulator(SimulatorBackend):
    _options: SimulatorOptions
    _current_tick_number: int
    _current_state: SimulationState

    def __init__(self, options_: SimulatorOptions):
        self._options = options_
        self._current_tick_number = 0
        self._current_state = _prepare_initial_simulation_state(self._options)

    def next_simulation_tick(self) -> SimulatedTick:
        next_state = _run_simulation_for_one_tick(self._current_state)
        next_tick_number = self._current_tick_number + 1

        self._current_state = next_state
        self._current_tick_number = next_tick_number

        return SimulatedTick(
            tick_number=next_tick_number,
            state=next_state
        )
