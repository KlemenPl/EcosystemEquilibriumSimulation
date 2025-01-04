import dataclasses
from dataclasses import dataclass
from typing import Optional
import math
import random

from ..models import SimulationState, Food, Prey, PreyId, PreyGenes, WorldPosition
from ..models.prey import PreyIdleState, PreyMindState, PreyFoodSearchState, PreyReproductionState, PreyPregnantState
from ..options import SimulationOptions
from ..utilities import clamp
from .shared import _move_towards, _move_in_random_direction, _mix_and_mutate_gene


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




@dataclass(slots=True, frozen=True, kw_only=True)
class PreyTickChanges:
    is_alive: bool = dataclasses.field(default=True)
    children: list[Prey] = dataclasses.field(default_factory=list)
    eaten: list[Food] = dataclasses.field(default_factory=list)
    new_satiation: float
    new_reproductive_urge: float
    new_position: WorldPosition
    new_mind_state: PreyMindState


def tick_prey(
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
