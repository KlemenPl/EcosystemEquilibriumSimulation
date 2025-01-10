import random
from typing import Callable, Optional

from .abc import SimulatorBackend, SimulatedTick
from .options import SimulationOptions
from .models import SimulationState, EntityId
from .models.predator import Predator, PredatorId, PredatorGenes, PredatorMindState, PredatorHuntingState, PredatorReproductionState, PredatorPregnantState, PredatorIdleState
from .models.prey import Prey, PreyId, PreyGenes, PreyIdleState, PreyMindState, PreyFoodSearchState, PreyReproductionState, PreyPregnantState
from .models.food import Food, FoodId
from .utilities import generate_random_position_in_world
from .behaviour import PreyTickChanges, PredatorTickChanges, tick_prey, tick_predator


class DraftSimulationState:
    predator_by_id: dict[PredatorId, Predator]
    prey_by_id: dict[PreyId, Prey]
    food_by_id: dict[FoodId, Food]

    predator_by_position: dict[tuple[int, int], "Predator"]
    prey_by_position: dict[tuple[int, int], "Prey"]
    food_by_position: dict[tuple[int, int], "Food"]

    food_spawning_accumulator: float

    def __init__(self):
        self.predator_by_id = {}
        self.prey_by_id = {}
        self.food_by_id = {}

        self.predator_by_position = {}
        self.prey_by_position = {}
        self.food_by_position = {}

        self.food_spawning_accumulator = 0

    def set_food_spawning_accumulator(self, value: float):
        self.food_spawning_accumulator = value

    def add_predator(self, predator: Predator):
        self.predator_by_id[predator.id] = predator
        self.predator_by_position[predator.position.to_tuple()] = predator

    def add_prey(self, prey: Prey):
        self.prey_by_id[prey.id] = prey
        self.prey_by_position[prey.position.to_tuple()] = prey

    def copy_over_food_from_previous_world(
        self,
        previous_world: SimulationState
    ):
        self.food_by_id = previous_world.food_by_id.copy()
        self.food_by_position = previous_world.food_by_position.copy()

    def remove_food_item(self, food_item_id: FoodId):
        food_item: Optional[Food] = self.food_by_id.get(food_item_id)
        if food_item is None:
            return

        del self.food_by_id[food_item_id]
        del self.food_by_position[food_item.position.to_tuple()]

    def add_food(self, food_item: Food):
        self.food_by_id[food_item.id] = food_item
        self.food_by_position[food_item.position.to_tuple()] = food_item

    def into_final_simulation_state(self) -> SimulationState:
        return SimulationState(
            predator_by_id=self.predator_by_id,
            prey_by_id=self.prey_by_id,
            food_by_id=self.food_by_id,
            predator_by_position=self.predator_by_position,
            prey_by_position=self.prey_by_position,
            food_by_position=self.food_by_position,
            food_spawning_accumulator=self.food_spawning_accumulator
        )




def _prepare_initial_simulation_state(
    simulation_options: SimulationOptions
) -> SimulationState:
    draft_state = DraftSimulationState()
    draft_state.set_food_spawning_accumulator(0)

    for _ in range(simulation_options.predator.initial_number):
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
            satiation=simulation_options.predator.initial_satiation_on_spawn,
            reproductive_urge=simulation_options.predator.initial_reproductive_urge_on_spawn,
        )

        draft_state.add_predator(predator)


    for _ in range(simulation_options.prey.initial_number):
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
            satiation=simulation_options.prey.initial_satiation_on_spawn,
            reproductive_urge=simulation_options.prey.initial_reproductive_urge_on_spawn
        )

        draft_state.add_prey(prey)


    for _ in range(simulation_options.initial_number_of_food_items):
        food = Food(
            id=FoodId.new_random(),
            position=generate_random_position_in_world(
                simulation_options.world_width,
                simulation_options.world_height
            )
        )

        draft_state.add_food(food)

    return draft_state.into_final_simulation_state()


def _run_simulation_for_one_tick(
    world: SimulationState,
    simulation_options: SimulationOptions
) -> SimulationState:
    """
    Will perform a single simulation tick. Because we want to track changes
    over time, **THIS FUNCTION MUST NOT MUTATE `state`**, but instead return a new one!
    """
    draft_world = DraftSimulationState()
    eaten_prey_set: set[PreyId] = set()

    draft_world.copy_over_food_from_previous_world(world)

    for predator in world.predators():
        predator_tick_result: PredatorTickChanges = tick_predator(
            world,
            predator,
            simulation_options
        )

        if predator_tick_result.is_alive is False:
            continue

        if len(predator_tick_result.eaten) > 0:
            for eaten_prey in predator_tick_result.eaten:
                eaten_prey_set.add(eaten_prey.id)

        if len(predator_tick_result.children) > 0:
            for predator_child in predator_tick_result.children:
                draft_world.add_predator(predator_child)

        draft_world.add_predator(Predator(
            id=predator.id,
            mind_state=predator_tick_result.new_mind_state,
            genes=predator.genes,
            position=predator_tick_result.new_position,
            satiation=predator_tick_result.new_satiation,
            reproductive_urge=predator_tick_result.new_reproductive_urge
        ))


    # TODO Prey should see the predator and run away (see also: `_move_away_from`).

    for prey in world.prey():
        if prey.id in eaten_prey_set:
            continue

        prey_tick_result: PreyTickChanges = tick_prey(
            world,
            prey,
            simulation_options
        )

        if prey_tick_result.is_alive is False:
            continue

        if len(prey_tick_result.eaten) > 0:
            for eaten_food in prey_tick_result.eaten:
                draft_world.remove_food_item(eaten_food.id)

        if len(prey_tick_result.children) > 0:
            for prey_child in prey_tick_result.children:
                draft_world.add_prey(prey_child)


        draft_world.add_prey(Prey(
            id=prey.id,
            mind_state=prey_tick_result.new_mind_state,
            genes=prey.genes,
            position=prey_tick_result.new_position,
            satiation=prey_tick_result.new_satiation,
            reproductive_urge=prey_tick_result.new_reproductive_urge
        ))


    # Spawns some additional food based on the spawning rate.
    new_food_spawning_accumulator = world.food_spawning_accumulator + simulation_options.food_item_spawning_rate_per_tick

    while new_food_spawning_accumulator >= 1.0:
        draft_world.add_food(Food(
            id=FoodId.new_random(),
            position=generate_random_position_in_world(
                simulation_options.world_width,
                simulation_options.world_height
            )
        ))

        new_food_spawning_accumulator -= 1.0

    draft_world.set_food_spawning_accumulator(new_food_spawning_accumulator)


    return draft_world.into_final_simulation_state()


class EcosystemSimulator(SimulatorBackend):
    _options: SimulationOptions
    _current_tick_number: int
    _current_state: SimulationState
    _on_tick: Optional[Callable[[SimulatedTick], None]]

    def __init__(self, options_: SimulationOptions):
        self._options = options_
        self._current_tick_number = 0
        self._on_tick = None

        random.seed(self._options.randomness_seed)

        self._current_state = _prepare_initial_simulation_state(self._options)

    def next_simulation_tick(self) -> SimulatedTick:
        next_state = _run_simulation_for_one_tick(self._current_state, self._options)
        next_tick_number = self._current_tick_number + 1

        self._current_state = next_state
        self._current_tick_number = next_tick_number

        if self._on_tick is not None:
            self._on_tick(SimulatedTick(
                tick_number=next_tick_number,
                state=next_state
            ))

        return SimulatedTick(
            tick_number=next_tick_number,
            state=next_state
        )
