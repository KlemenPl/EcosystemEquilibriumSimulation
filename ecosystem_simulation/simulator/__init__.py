import copy
import dataclasses
import math
import random
from dataclasses import dataclass
from typing import Optional, assert_never

from .abc import SimulatorBackend, SimulatedTick
from .models import Prey, Predator, PreyGenes, PredatorGenes, WorldPosition, SimulationState, PreyId, PredatorId, Food, \
    FoodId, EntityId
from .models.predator import PredatorIdleState, PredatorMindState, PredatorHuntingState, PredatorReproductionState, \
    PredatorPregnantState
from .models.prey import PreyIdleState, PreyMindState, PreyFoodSearchState, PreyReproductionState, PreyPregnantState
from .options import SimulationOptions
from .utilities import generate_random_position_in_world, clamp


def _prepare_initial_simulation_state(
    simulation_options: SimulationOptions
) -> SimulationState:
    entity_id_by_position: dict[tuple[int, int], EntityId] = {}

    initial_predators_by_id: dict[PredatorId, Predator] = {}

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

        initial_predators_by_id[predator.id] = predator
        entity_id_by_position[predator_position.to_tuple()] = predator.id

    initial_prey_by_id: dict[PreyId, Prey] = {}

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

        initial_prey_by_id[prey.id] = prey
        entity_id_by_position[prey_position.to_tuple()] = prey.id

    initial_food_items_by_id: dict[FoodId, Food] = {}

    for _ in range(simulation_options.initial_number_of_food_items):
        food = Food(
            id=FoodId.new_random(),
            position=generate_random_position_in_world(
                simulation_options.world_width,
                simulation_options.world_height
            )
        )

        initial_food_items_by_id[food.id] = food
        entity_id_by_position[food.position.to_tuple()] = food.id

    return SimulationState(
        predator_by_id=initial_predators_by_id,
        prey_by_id=initial_prey_by_id,
        food_by_id=initial_food_items_by_id,
        entity_id_by_position=entity_id_by_position,
        food_spawning_accumulator=0
    )


class DraftSimulationState:
    entity_id_by_position: dict[tuple[int, int], EntityId]
    predator_by_id: dict[PredatorId, Predator]
    prey_by_id: dict[PreyId, Prey]
    food_by_id: dict[FoodId, Food]
    food_spawning_accumulator: float

    def __init__(self):
        self.entity_id_by_position = {}
        self.predator_by_id = {}
        self.prey_by_id = {}
        self.food_by_id = {}
        self.food_spawning_accumulator = 0

    def set_food_spawning_accumulator(self, value: float):
        self.food_spawning_accumulator = value

    def add_predator(self, predator: Predator):
        self.predator_by_id[predator.id] = predator
        self.entity_id_by_position[predator.position.to_tuple()] = predator.id

    def add_prey(self, prey: Prey):
        self.prey_by_id[prey.id] = prey
        self.entity_id_by_position[prey.position.to_tuple()] = prey.id

    def set_food_items(self, food_items: dict[FoodId, Food]):
        self.food_by_id = food_items

    def remove_food_item(self, food_item_id: FoodId):
        del self.food_by_id[food_item_id]

    def add_food_item(self, food_item: Food):
        self.food_by_id[food_item.id] = food_item
        self.entity_id_by_position[food_item.position.to_tuple()] = food_item.id

    def into_final_simulation_state(self) -> SimulationState:
        return SimulationState(
            predator_by_id=self.predator_by_id,
            prey_by_id=self.prey_by_id,
            food_by_id=self.food_by_id,
            entity_id_by_position=self.entity_id_by_position,
            food_spawning_accumulator=self.food_spawning_accumulator
        )


def _find_closest_prey_for_predator(
    from_position: WorldPosition,
    current_world_state: SimulationState,
    vision_gene_value: float,
    max_vision_distance: int
) -> Optional[Prey]:
    predator_vision_in_grid_tiles: int = int(math.floor(vision_gene_value * max_vision_distance))

    closest_visible_prey: Optional[Prey] = None
    closest_visible_prey_distance: Optional[float] = None

    for prey in current_world_state.prey():
        distance_to_prey = from_position.distance_from(prey.position)

        if predator_vision_in_grid_tiles >= distance_to_prey:
            if closest_visible_prey_distance is None:
                closest_visible_prey = prey
                closest_visible_prey_distance = distance_to_prey
            elif distance_to_prey < closest_visible_prey_distance:
                closest_visible_prey = prey
                closest_visible_prey_distance = distance_to_prey

    return closest_visible_prey


def _find_closest_food_for_prey(
    from_position: WorldPosition,
    current_world_state: SimulationState,
    vision_gene_value: float,
    max_vision_distance: int
) -> Optional[Food]:
    prey_vision_in_grid_tiles: int = int(math.floor(vision_gene_value * max_vision_distance))

    closest_visible_food: Optional[Food] = None
    closest_visible_food_distance: Optional[float] = None

    for food in current_world_state.food():
        distance_to_food = from_position.distance_from(food.position)

        if prey_vision_in_grid_tiles >= distance_to_food:
            if closest_visible_food_distance is None:
                closest_visible_food = food
                closest_visible_food_distance = distance_to_food
            elif distance_to_food < closest_visible_food_distance:
                closest_visible_food = food
                closest_visible_food_distance = distance_to_food

    return closest_visible_food



@dataclass(slots=True, frozen=True)
class PredatorMatingCallResult:
    found_mate: Optional[Predator]
    newly_denied_by: Optional[Predator]


def _find_and_call_out_to_closest_available_predator_for_mating(
    from_position: WorldPosition,
    current_world_state: SimulationState,
    so_far_denied_by: list[PredatorId],
    vision_gene_value: float,
    max_vision_distance: int,
    charisma_gene_value: float
) -> PredatorMatingCallResult:
    predator_vision_in_grid_tiles: int = int(math.floor(vision_gene_value * max_vision_distance))

    closest_visible_available_predator: Optional[Predator] = None
    closest_visible_available_predator_distance: Optional[float] = None

    for predator in current_world_state.predators():
        if predator.id in so_far_denied_by:
            continue

        distance_to_predator = from_position.distance_from(predator.position)

        if predator_vision_in_grid_tiles >= distance_to_predator:
            if closest_visible_available_predator_distance is None:
                closest_visible_available_predator = predator
                closest_visible_available_predator_distance = distance_to_predator
            elif distance_to_predator < closest_visible_available_predator_distance:
                closest_visible_available_predator = predator
                closest_visible_available_predator_distance = distance_to_predator

    # Roll the charisma.
    if random.uniform(0, 1) < charisma_gene_value:
        return PredatorMatingCallResult(
            found_mate=closest_visible_available_predator,
            newly_denied_by=None
        )
    else:
        return PredatorMatingCallResult(
            found_mate=None,
            newly_denied_by=closest_visible_available_predator
        )




@dataclass(slots=True, frozen=True)
class PreyMatingCallResult:
    found_mate: Optional[Prey]
    newly_denied_by: Optional[Prey]


def _find_and_call_out_to_closest_available_prey_for_mating(
    from_position: WorldPosition,
    current_world_state: SimulationState,
    so_far_denied_by: list[PreyId],
    vision_gene_value: float,
    max_vision_distance: int,
    charisma_gene_value: float
) -> PreyMatingCallResult:
    prey_vision_in_grid_tiles: int = int(math.floor(vision_gene_value * max_vision_distance))

    closest_visible_available_prey: Optional[Prey] = None
    closest_visible_available_prey_distance: Optional[float] = None

    for prey in current_world_state.prey():
        if prey.id in so_far_denied_by:
            continue

        distance_to_prey = from_position.distance_from(prey.position)

        if prey_vision_in_grid_tiles >= distance_to_prey:
            if closest_visible_available_prey_distance is None:
                closest_visible_available_prey = prey
                closest_visible_available_prey_distance = distance_to_prey
            elif distance_to_prey < closest_visible_available_prey_distance:
                closest_visible_available_prey = prey
                closest_visible_available_prey_distance = distance_to_prey

    # Roll the charisma.
    if random.uniform(0, 1) < charisma_gene_value:
        return PreyMatingCallResult(
            found_mate=closest_visible_available_prey,
            newly_denied_by=None
        )
    else:
        return PreyMatingCallResult(
            found_mate=None,
            newly_denied_by=closest_visible_available_prey
        )


def _move_in_random_direction(
    from_position: WorldPosition,
    simulation_options: SimulationOptions
) -> WorldPosition:
    # We cannot travel diagonally, so we choose an axis.
    if random.uniform(0, 1) <= 0.5:
        # If `go_left` is false, we will go right.
        if from_position.x == 0:
            go_left: bool = False
        elif from_position.x == (simulation_options.world_width - 1):
            go_left = True
        else:
            go_left = random.uniform(0, 1) <= 0.5

        # Travel left/right.
        new_x: int
        if go_left:
            new_x = from_position.x - 1
        else:
            new_x = from_position.x + 1

        return WorldPosition(
            x=new_x,
            y=from_position.y
        )
    else:
        # If `go_up` is false, we will go down.
        if from_position.y == 0:
            go_up = False
        elif from_position.y == (simulation_options.world_height - 1):
            go_up = True
        else:
            go_up = random.uniform(0, 1) <= 0.5

        # Travel up/down.
        new_y: int
        if go_up:
            new_y = from_position.y - 1
        else:
            new_y = from_position.y + 1

        return WorldPosition(
            x=from_position.x,
            y=new_y
        )


def _move_towards(
    current_position: WorldPosition,
    target_position: WorldPosition,
) -> WorldPosition:
    if current_position == target_position:
        return current_position


    if current_position.x == target_position.x:
        # We only need to move left/right.
        if current_position.x < target_position.x:
            return WorldPosition(
                x=current_position.x + 1,
                y=current_position.y
            )
        else:
            return WorldPosition(
                x=current_position.x - 1,
                y=current_position.y
            )
    elif current_position.y == target_position.y:
        # We only need to move up/down.
        if current_position.y < target_position.y:
            return WorldPosition(
                x=current_position.x,
                y=current_position.y + 1
            )
        else:
            return WorldPosition(
                x=current_position.x,
                y=current_position.y - 1
            )

    # Otherwise we are on different axis for both x and y.
    # We'll pick one axis to move on.
    if random.uniform(0, 1) < 0.5:
        # We'll move left/right.
        if current_position.x < target_position.x:
            return WorldPosition(
                x=current_position.x + 1,
                y=current_position.y
            )
        else:
            return WorldPosition(
                x=current_position.x - 1,
                y=current_position.y
            )
    else:
        # We'll move up/down.
        if current_position.y < target_position.y:
            return WorldPosition(
                x=current_position.x,
                y=current_position.y + 1
            )
        else:
            return WorldPosition(
                x=current_position.x,
                y=current_position.y - 1
            )


def _move_away_from(
    current_position: WorldPosition,
    target_position: WorldPosition,
    simulation_options: SimulationOptions
) -> WorldPosition:
    # True indicates only being able to move to the left (due to world size limits),
    # False indicates only being able to move to the right,
    # None indicates no such limit.
    limited_horizontal_move: Optional[bool] = None

    # True indicates only being able to move up (due to world size limits),
    # False indicates only being able to move down,
    # None indicates no such limit.
    limited_vertical_move: Optional[bool] = None

    if current_position.x == (simulation_options.world_width - 1):
        # We cannot move right.
        limited_horizontal_move = True
    elif current_position.x == 0:
        # We cannot move left.
        limited_horizontal_move = False

    if current_position.y == (simulation_options.world_height - 1):
        # We cannot move down.
        limited_vertical_move = True
    elif current_position.y == 0:
        # We cannot move up.
        limited_vertical_move = False


    if limited_vertical_move is not None and limited_horizontal_move is not None:
        # There is only one possible move
        # (we are on a corner of the world).

        new_x: int
        if limited_vertical_move is True:
            new_x = current_position.x - 1
        else:
            new_x = current_position.x + 1

        new_y: int
        if limited_horizontal_move is True:
            new_y = current_position.y - 1
        else:
            new_y = current_position.y + 1

        return WorldPosition(
            x=new_x,
            y=new_y
        )

    if limited_vertical_move is not None:
        # Vertical movement is partially restricted
        # (we are either on the top or bottom edge of the world).

        # Perform horizontal movement away from the target.
        if current_position.x < target_position.x:
            return WorldPosition(
                x=current_position.x - 1,
                y=current_position.y
            )
        else:
            return WorldPosition(
                x=current_position.x + 1,
                y=current_position.y
            )

    if limited_horizontal_move is not None:
        # Horizontal movement is partially restricted
        # (we are either on the left or right edge of the world).

        # Perform vertical movement away from the target.
        if current_position.y < target_position.y:
            return WorldPosition(
                x=current_position.x,
                y=current_position.y - 1,
            )
        else:
            return WorldPosition(
                x=current_position.x,
                y=current_position.y + 1
            )



    # We are not restricted in our movement: we'll pick one axis to move on.
    if random.uniform(0, 1) < 0.5:
        # We'll move left/right away from the target.
        if current_position.x < target_position.x:
            return WorldPosition(
                x=current_position.x + 1,
                y=current_position.y
            )
        else:
            return WorldPosition(
                x=current_position.x - 1,
                y=current_position.y
            )
    else:
        # We'll move up/down away from the target.
        if current_position.y < target_position.y:
            return WorldPosition(
                x=current_position.x,
                y=current_position.y + 1
            )
        else:
            return WorldPosition(
                x=current_position.x,
                y=current_position.y - 1
            )



def _mix_and_mutate_gene(
    first_parent_gene_value: float,
    second_parent_gene_value: float,
    mutation_chance: float,
    mutation_magnitude: float,
) -> float:
    purely_mixed_gene = (first_parent_gene_value + second_parent_gene_value) / 2

    final_gene = purely_mixed_gene

    if random.uniform(0, 1) < mutation_chance:
        if random.uniform(0, 1) < 0.5:
            # Negative mutation.
            final_gene -= random.uniform(0, mutation_magnitude)
        else:
            # Positive mutation.
            final_gene += random.uniform(0, mutation_magnitude)

    return final_gene


@dataclass(slots=True, frozen=True, kw_only=True)
class PredatorTickChanges:
    is_alive: bool = dataclasses.field(default=True)
    children: list[Predator] = dataclasses.field(default_factory=list)
    eaten: list[Prey] = dataclasses.field(default_factory=list)
    new_satiation: float
    new_reproductive_urge: float
    new_position: WorldPosition
    new_mind_state: PredatorMindState


def _tick_predator(
    world: SimulationState,
    predator: Predator,
    simulation_options: SimulationOptions
) -> PredatorTickChanges:
    next_satiation: float = max(
        0.0,
        predator.satiation
        - simulation_options.predator.satiation_loss_per_tick
    )

    if next_satiation == 0.0:
        return PredatorTickChanges(
            is_alive=False,
            # The rest of these parameters don't matter because this predator
            # will die in this tick due to hunger.
            new_satiation=0.0,
            new_reproductive_urge=0.0,
            new_position=predator.position,
            new_mind_state=predator.mind_state
        )


    next_reproductive_urge: float = clamp(
        predator.reproductive_urge
        + predator.genes.reproductive_urge_quickness,
        0.0,
        1.0
    )

    if isinstance(predator.mind_state, PredatorIdleState):
        if predator.genes.aggression > predator.satiation:
            # Enter hunting state.
            closest_prey = _find_closest_prey_for_predator(
                predator.position,
                world,
                predator.genes.vision,
                simulation_options.max_vision_distance
            )

            next_position: WorldPosition
            if closest_prey is not None:
                next_position = _move_towards(predator.position, closest_prey.position)

                return PredatorTickChanges(
                    new_satiation=next_satiation,
                    new_reproductive_urge=next_reproductive_urge,
                    new_position=next_position,
                    new_mind_state=PredatorHuntingState(found_prey_id=closest_prey.id)
                )
            else:
                next_position = _move_in_random_direction(predator.position, simulation_options)

                return PredatorTickChanges(
                    new_satiation=next_satiation,
                    new_reproductive_urge=next_reproductive_urge,
                    new_position=next_position,
                    new_mind_state=PredatorHuntingState(found_prey_id=None)
                )

        if random.uniform(0, 1) < predator.reproductive_urge:
            # Enter mating state.
            mating_call_result = _find_and_call_out_to_closest_available_predator_for_mating(
                predator.position,
                world,
                [],
                predator.genes.vision,
                simulation_options.max_vision_distance,
                predator.genes.charisma
            )

            denied_by: list[PredatorId] = []
            if mating_call_result.newly_denied_by is not None:
                denied_by.append(mating_call_result.newly_denied_by.id)

            if mating_call_result.found_mate is not None:
                next_position = _move_towards(predator.position, mating_call_result.found_mate.position)

                return PredatorTickChanges(
                    new_satiation=next_satiation,
                    new_reproductive_urge=next_reproductive_urge,
                    new_position=next_position,
                    new_mind_state=PredatorReproductionState(
                        found_mate_id=mating_call_result.found_mate.id,
                        denied_by=denied_by
                    )
                )
            else:
                next_position = _move_in_random_direction(predator.position, simulation_options)

                return PredatorTickChanges(
                    new_satiation=next_satiation,
                    new_reproductive_urge=next_reproductive_urge,
                    new_position=next_position,
                    new_mind_state=PredatorReproductionState(
                        found_mate_id=None,
                        denied_by=denied_by
                    )
                )

        # If the predator is neither hungry nor willing to mate,
        # it persists its idle state and moves in a random direction.

        next_position = _move_in_random_direction(
            predator.position,
            simulation_options
        )

        return PredatorTickChanges(
            new_satiation=next_satiation,
            new_reproductive_urge=next_reproductive_urge,
            new_position=next_position,
            new_mind_state=predator.mind_state
        )

    elif isinstance(predator.mind_state, PredatorHuntingState):
        # If the predator hasn't been able to find any prey, it will try again this tick.
        if predator.mind_state.found_prey_id is None:
            closest_prey = _find_closest_prey_for_predator(
                predator.position,
                world,
                predator.genes.vision,
                simulation_options.max_vision_distance
            )

            if closest_prey is not None:
                next_position = _move_towards(predator.position, closest_prey.position)

                return PredatorTickChanges(
                    new_satiation=next_satiation,
                    new_reproductive_urge=next_reproductive_urge,
                    new_position=next_position,
                    new_mind_state=PredatorHuntingState(found_prey_id=closest_prey.id)
                )
            else:
                next_position = _move_in_random_direction(predator.position, simulation_options)

                return PredatorTickChanges(
                    new_satiation=next_satiation,
                    new_reproductive_urge=next_reproductive_urge,
                    new_position=next_position,
                    new_mind_state=PredatorHuntingState(found_prey_id=None)
                )




        # The predator has already chosen the target - move towards it until we reach it.

        # If we reach the target, despawn the prey and give the predator some satiation.
        found_prey = world.prey_by_id[predator.mind_state.found_prey_id]

        if predator.position == found_prey.position:
            # Eat the prey and transition back to the idle state.
            next_satiation += simulation_options.predator.satiation_per_one_eaten_prey

            return PredatorTickChanges(
                eaten=[found_prey],
                new_satiation=next_satiation,
                new_reproductive_urge=next_reproductive_urge,
                new_position=predator.position,
                new_mind_state=PredatorIdleState()
            )

        next_position = _move_towards(predator.position, found_prey.position)
        return PredatorTickChanges(
            new_satiation=next_satiation,
            new_reproductive_urge=next_reproductive_urge,
            new_position=next_position,
            new_mind_state=predator.mind_state
        )

    elif isinstance(predator.mind_state, PredatorReproductionState):
        # If the found mate dies before reproduction, we will look for another one.
        target_mate: Optional[Predator] = None
        if predator.mind_state.found_mate_id is not None:
            target_mate = world.predator_by_id.get(predator.mind_state.found_mate_id)

        # If the predator hasn't been able to find any mate, it will try again this tick.
        if target_mate is None:
            mating_call_result = _find_and_call_out_to_closest_available_predator_for_mating(
                predator.position,
                world,
                predator.mind_state.denied_by,
                predator.genes.vision,
                simulation_options.max_vision_distance,
                predator.genes.charisma
            )

            denied_by = list.copy(predator.mind_state.denied_by)
            if mating_call_result.newly_denied_by is not None:
                denied_by.append(mating_call_result.newly_denied_by.id)

            if mating_call_result.found_mate is not None:
                next_position = _move_towards(predator.position, mating_call_result.found_mate.position)

                return PredatorTickChanges(
                    new_satiation=next_satiation,
                    new_reproductive_urge=next_reproductive_urge,
                    new_position=next_position,
                    new_mind_state=PredatorReproductionState(
                        found_mate_id=mating_call_result.found_mate.id,
                        denied_by=denied_by
                    )
                )
            else:
                next_position = _move_in_random_direction(predator.position, simulation_options)

                return PredatorTickChanges(
                    new_satiation=next_satiation,
                    new_reproductive_urge=next_reproductive_urge,
                    new_position=next_position,
                    new_mind_state=PredatorReproductionState(
                        found_mate_id=None,
                        denied_by=denied_by
                    )
                )

        # The predator has found its mate - it will move towards it.

        # If they collide, reproduction is performed.
        if predator.position == target_mate.position:
            return PredatorTickChanges(
                new_satiation=next_satiation,
                new_reproductive_urge=next_reproductive_urge,
                new_position=predator.position,
                new_mind_state=PredatorPregnantState(
                    ticks_until_birth=simulation_options.predator.pregnancy_duration_in_ticks,
                    other_parent_genes=target_mate.genes
                )
            )

        next_position = _move_towards(
            predator.position,
            target_mate.position
        )

        return PredatorTickChanges(
            new_satiation=next_satiation,
            new_reproductive_urge=next_reproductive_urge,
            new_position=next_position,
            new_mind_state=predator.mind_state
        )

    elif isinstance(predator.mind_state, PredatorPregnantState):
        if predator.mind_state.ticks_until_birth == 0:
            number_of_children: int = random.randint(1, simulation_options.predator.max_children_per_birth)

            children: list[Predator] = []
            for _ in range(number_of_children):
                new_child_genes = PredatorGenes(
                    aggression=_mix_and_mutate_gene(
                        predator.genes.aggression,
                        predator.mind_state.other_parent_genes.aggression,
                        simulation_options.child_gene_mutation_chance_when_mating,
                        simulation_options.child_gene_mutation_magnitude_when_mating,
                    ),
                    fertility=_mix_and_mutate_gene(
                        predator.genes.fertility,
                        predator.mind_state.other_parent_genes.fertility,
                        simulation_options.child_gene_mutation_chance_when_mating,
                        simulation_options.child_gene_mutation_magnitude_when_mating,
                    ),
                    charisma=_mix_and_mutate_gene(
                        predator.genes.charisma,
                        predator.mind_state.other_parent_genes.charisma,
                        simulation_options.child_gene_mutation_chance_when_mating,
                        simulation_options.child_gene_mutation_magnitude_when_mating,
                    ),
                    vision=_mix_and_mutate_gene(
                        predator.genes.vision,
                        predator.mind_state.other_parent_genes.vision,
                        simulation_options.child_gene_mutation_chance_when_mating,
                        simulation_options.child_gene_mutation_magnitude_when_mating,
                    ),
                    reproductive_urge_quickness=_mix_and_mutate_gene(
                        predator.genes.reproductive_urge_quickness,
                        predator.mind_state.other_parent_genes.reproductive_urge_quickness,
                        simulation_options.child_gene_mutation_chance_when_mating,
                        simulation_options.child_gene_mutation_magnitude_when_mating,
                    ),
                )

                children.append(Predator(
                    id=PredatorId.new_random(),
                    mind_state=PredatorIdleState(),
                    genes=new_child_genes,
                    position=predator.position,
                    satiation=simulation_options.predator.initial_satiation_on_spawn,
                    reproductive_urge=simulation_options.predator.initial_reproductive_urge_on_spawn
                ))

            return PredatorTickChanges(
                children=children,
                new_satiation=next_satiation,
                new_reproductive_urge=next_reproductive_urge,
                new_position=predator.position,
                new_mind_state=PredatorIdleState()
            )


        next_position = _move_in_random_direction(
            predator.position,
            simulation_options
        )

        return PredatorTickChanges(
            new_satiation=next_satiation,
            new_reproductive_urge=next_reproductive_urge,
            new_position=next_position,
            new_mind_state=PredatorPregnantState(
                ticks_until_birth=predator.mind_state.ticks_until_birth - 1,
                other_parent_genes=predator.mind_state.other_parent_genes
            )
        )

    else:
        raise RuntimeError("somehow got unhandled predator mind state")



@dataclass(slots=True, frozen=True, kw_only=True)
class PreyTickChanges:
    is_alive: bool = dataclasses.field(default=True)
    children: list[Prey] = dataclasses.field(default_factory=list)
    eaten: list[Food] = dataclasses.field(default_factory=list)
    new_satiation: float
    new_reproductive_urge: float
    new_position: WorldPosition
    new_mind_state: PreyMindState


def _tick_prey(
    world: SimulationState,
    prey: Prey,
    simulation_options: SimulationOptions
) -> PreyTickChanges:
    next_satiation: float = max(
        0.0,
        prey.satiation
        - simulation_options.prey.satiation_loss_per_tick
    )

    if next_satiation == 0.0:
        return PreyTickChanges(
            is_alive=False,
            # The rest of these parameters don't matter because this prey
            # will die in this tick due to hunger.
            new_satiation=0.0,
            new_reproductive_urge=0.0,
            new_position=prey.position,
            new_mind_state=prey.mind_state
        )


    next_reproductive_urge: float = clamp(
        prey.reproductive_urge
        + prey.genes.reproductive_urge_quickness,
        0.0,
        1.0
    )


    if isinstance(prey.mind_state, PreyIdleState):
        if prey.genes.appetite > prey.satiation:
            # Enter food searching state.
            closest_visible_food = _find_closest_food_for_prey(
                prey.position,
                world,
                prey.genes.vision,
                simulation_options.max_vision_distance
            )

            next_position: WorldPosition
            if closest_visible_food is not None:
                next_position = _move_towards(
                    prey.position,
                    closest_visible_food.position
                )

                return PreyTickChanges(
                    new_satiation=next_satiation,
                    new_reproductive_urge=next_reproductive_urge,
                    new_position=next_position,
                    new_mind_state=PreyFoodSearchState(
                        found_food_tile_id=closest_visible_food.id
                    )
                )
            else:
                next_position = _move_in_random_direction(
                    prey.position,
                    simulation_options
                )

                return PreyTickChanges(
                    new_satiation=next_satiation,
                    new_reproductive_urge=next_reproductive_urge,
                    new_position=next_position,
                    new_mind_state=PreyFoodSearchState(
                        found_food_tile_id=None
                    )
                )


        if random.uniform(0, 1) < prey.reproductive_urge:
            # Enter mating state.
            mating_call_result = _find_and_call_out_to_closest_available_prey_for_mating(
                prey.position,
                world,
                [],
                prey.genes.vision,
                simulation_options.max_vision_distance,
                prey.genes.charisma
            )

            denied_by = []
            if mating_call_result.newly_denied_by is not None:
                denied_by.append(mating_call_result.newly_denied_by.id)


            if mating_call_result.found_mate is not None:
                next_position = _move_towards(prey.position, mating_call_result.found_mate.position)

                return PreyTickChanges(
                    new_satiation=next_satiation,
                    new_reproductive_urge=next_reproductive_urge,
                    new_position=next_position,
                    new_mind_state=PreyReproductionState(
                        found_mate_id=mating_call_result.found_mate.id,
                        denied_by=denied_by
                    )
                )
            else:
                next_position = _move_in_random_direction(prey.position, simulation_options)

                return PreyTickChanges(
                    new_satiation=next_satiation,
                    new_reproductive_urge=next_reproductive_urge,
                    new_position=next_position,
                    new_mind_state=PreyReproductionState(
                        found_mate_id=None,
                        denied_by=denied_by
                    )
                )


        # If the prey is neither hungry nor willing to mate,
        # it persists its idle state and moves in a random direction.

        next_position = _move_in_random_direction(
            prey.position,
            simulation_options
        )

        return PreyTickChanges(
            new_satiation=next_satiation,
            new_reproductive_urge=next_reproductive_urge,
            new_position=next_position,
            new_mind_state=prey.mind_state
        )

    elif isinstance(prey.mind_state, PreyFoodSearchState):
        # Look up the food item. If the item is eaten by another prey
        # before this specimen can reach it, it will look for another food item.
        food_item: Optional[Food] = None
        if prey.mind_state.found_food_tile_id is not None:
            food_item = world.food_by_id.get(prey.mind_state.found_food_tile_id)


        # If the prey hasn't been able to find any food items (or the current one has been eaten),
        # it will look for the closest one this tick.
        if food_item is None:
            closest_visible_food = _find_closest_food_for_prey(
                prey.position,
                world,
                prey.genes.vision,
                simulation_options.max_vision_distance
            )

            if closest_visible_food is not None:
                next_position = _move_towards(
                    prey.position,
                    closest_visible_food.position
                )

                return PreyTickChanges(
                    new_satiation=next_satiation,
                    new_reproductive_urge=next_reproductive_urge,
                    new_position=next_position,
                    new_mind_state=PreyFoodSearchState(
                        found_food_tile_id=closest_visible_food.id
                    )
                )
            else:
                next_position = _move_in_random_direction(
                    prey.position,
                    simulation_options
                )

                return PreyTickChanges(
                    new_satiation=next_satiation,
                    new_reproductive_urge=next_reproductive_urge,
                    new_position=next_position,
                    new_mind_state=PreyFoodSearchState(
                        found_food_tile_id=None
                    )
                )



        # The prey has already chosen which food tile to eat - move towards it until we reach it.

        # If we reach the target, despawn the food item and give the predator
        # some satiation.
        if prey.position == food_item.position:
            # Eat the food item and transition back to the idle state.
            next_satiation += simulation_options.prey.satiation_per_food_item

            return PreyTickChanges(
                eaten=[food_item],
                new_satiation=next_satiation,
                new_reproductive_urge=next_reproductive_urge,
                new_position=prey.position,
                new_mind_state=PreyIdleState()
            )

        next_position = _move_towards(prey.position, food_item.position)
        return PreyTickChanges(
            new_satiation=next_satiation,
            new_reproductive_urge=next_reproductive_urge,
            new_position=next_position,
            new_mind_state=prey.mind_state
        )

    elif isinstance(prey.mind_state, PreyReproductionState):
        # If the found mate dies before reproduction, we will look for another one.
        target_mate: Optional[Prey] = None
        if prey.mind_state.found_mate_id is not None:
            target_mate = world.prey_by_id.get(prey.mind_state.found_mate_id)

        # If the prey hasn't been able to find a mate, it will try again this tick.
        if target_mate is None:
            mating_call_result = _find_and_call_out_to_closest_available_prey_for_mating(
                prey.position,
                world,
                prey.mind_state.denied_by,
                prey.genes.vision,
                simulation_options.max_vision_distance,
                prey.genes.charisma
            )

            denied_by = list.copy(prey.mind_state.denied_by)
            if mating_call_result.newly_denied_by is not None:
                denied_by.append(mating_call_result.newly_denied_by.id)

            if mating_call_result.found_mate is not None:
                next_position = _move_towards(prey.position, mating_call_result.found_mate.position)

                return PreyTickChanges(
                    new_satiation=next_satiation,
                    new_reproductive_urge=next_reproductive_urge,
                    new_position=next_position,
                    new_mind_state=PreyReproductionState(
                        found_mate_id=mating_call_result.found_mate.id,
                        denied_by=denied_by
                    )
                )
            else:
                next_position = _move_in_random_direction(prey.position, simulation_options)

                return PreyTickChanges(
                    new_satiation=next_satiation,
                    new_reproductive_urge=next_reproductive_urge,
                    new_position=next_position,
                    new_mind_state=PreyReproductionState(
                        found_mate_id=None,
                        denied_by=denied_by
                    )
                )

        # The prey has found its mate - it will move towards it.
        # If they collide, reproduction is performed.
        if prey.position == target_mate.position:
            return PreyTickChanges(
                new_satiation=next_satiation,
                new_reproductive_urge=next_reproductive_urge,
                new_position=prey.position,
                new_mind_state=PreyPregnantState(
                    ticks_until_birth=simulation_options.prey.pregnancy_duration_in_ticks,
                    other_parent_genes=target_mate.genes
                )
            )

        next_position = _move_towards(
            prey.position,
            target_mate.position
        )

        return PreyTickChanges(
            new_satiation=next_satiation,
            new_reproductive_urge=next_reproductive_urge,
            new_position=next_position,
            new_mind_state=prey.mind_state
        )

    elif isinstance(prey.mind_state, PreyPregnantState):
        if prey.mind_state.ticks_until_birth == 0:
            number_of_children: int = random.randint(1, simulation_options.prey.max_children_per_birth)

            children: list[Prey] = []
            for _ in range(number_of_children):
                new_child_genes = PreyGenes(
                    appetite=_mix_and_mutate_gene(
                        prey.genes.appetite,
                        prey.mind_state.other_parent_genes.appetite,
                        simulation_options.child_gene_mutation_chance_when_mating,
                        simulation_options.child_gene_mutation_magnitude_when_mating,
                    ),
                    fertility=_mix_and_mutate_gene(
                        prey.genes.fertility,
                        prey.mind_state.other_parent_genes.fertility,
                        simulation_options.child_gene_mutation_chance_when_mating,
                        simulation_options.child_gene_mutation_magnitude_when_mating,
                    ),
                    charisma=_mix_and_mutate_gene(
                        prey.genes.charisma,
                        prey.mind_state.other_parent_genes.charisma,
                        simulation_options.child_gene_mutation_chance_when_mating,
                        simulation_options.child_gene_mutation_magnitude_when_mating,
                    ),
                    vision=_mix_and_mutate_gene(
                        prey.genes.vision,
                        prey.mind_state.other_parent_genes.vision,
                        simulation_options.child_gene_mutation_chance_when_mating,
                        simulation_options.child_gene_mutation_magnitude_when_mating,
                    ),
                    reproductive_urge_quickness=_mix_and_mutate_gene(
                        prey.genes.reproductive_urge_quickness,
                        prey.mind_state.other_parent_genes.reproductive_urge_quickness,
                        simulation_options.child_gene_mutation_chance_when_mating,
                        simulation_options.child_gene_mutation_magnitude_when_mating,
                    ),
                )

                children.append(Prey(
                    id=PreyId.new_random(),
                    mind_state=PreyIdleState(),
                    genes=new_child_genes,
                    position=prey.position,
                    satiation=simulation_options.prey.initial_satiation_on_spawn,
                    reproductive_urge=simulation_options.prey.initial_reproductive_urge_on_spawn
                ))

            return PreyTickChanges(
                children=children,
                new_satiation=next_satiation,
                new_reproductive_urge=next_reproductive_urge,
                new_position=prey.position,
                new_mind_state=prey.mind_state
            )

        next_position = _move_in_random_direction(
            prey.position,
            simulation_options
        )

        return PreyTickChanges(
            new_satiation=next_satiation,
            new_reproductive_urge=next_reproductive_urge,
            new_position=next_position,
            new_mind_state=prey.mind_state
        )

    else:
        raise RuntimeError("somehow got unhandled prey mind state")


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

    draft_world.set_food_items(world.food_by_id)

    for predator in world.predators():
        predator_tick_result: PredatorTickChanges = _tick_predator(
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

        prey_tick_result: PreyTickChanges = _tick_prey(
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
        draft_world.add_food_item(Food(
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

    def __init__(self, options_: SimulationOptions):
        self._options = options_
        self._current_tick_number = 0

        random.seed(self._options.randomness_seed)

        self._current_state = _prepare_initial_simulation_state(self._options)

    def next_simulation_tick(self) -> SimulatedTick:
        next_state = _run_simulation_for_one_tick(self._current_state, self._options)
        next_tick_number = self._current_tick_number + 1

        self._current_state = next_state
        self._current_tick_number = next_tick_number

        return SimulatedTick(
            tick_number=next_tick_number,
            state=next_state
        )
