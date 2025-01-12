import dataclasses
import random
from dataclasses import dataclass
from typing import Optional
import math

from ..utilities import clamp
from ..models import WorldPosition, SimulationState, Prey, Predator, PredatorId, PredatorGenes
from ..options import SimulationOptions
from ..models.predator import PredatorMindState, PredatorHuntingState, PredatorReproductionState, PredatorPregnantState, PredatorIdleState
from .shared import move_towards, move_in_random_direction, mix_and_mutate_gene, iter_nearby_visible_positions


def _find_closest_prey_for_predator(
    from_position: WorldPosition,
    world: SimulationState,
    vision_gene_value: float,
    max_vision_distance: int,
    world_width: int,
    world_height: int,
) -> Optional[Prey]:
    predator_vision_in_grid_tiles: int = int(math.floor(vision_gene_value * max_vision_distance))

    for nearby_visible_position in iter_nearby_visible_positions(
        from_position,
        predator_vision_in_grid_tiles,
        world_width,
        world_height
    ):
        position_as_tuple = nearby_visible_position.to_tuple()
        if position_as_tuple not in world.prey_by_position:
            continue

        return world.prey_by_position[position_as_tuple]

    return None




@dataclass(slots=True, frozen=True)
class PredatorMatingCallResult:
    found_mate: Optional[Predator]
    newly_denied_by: Optional[Predator]


def _find_and_call_out_to_closest_available_predator_for_mating(
    from_position: WorldPosition,
    world: SimulationState,
    so_far_denied_by: list[PredatorId],
    vision_gene_value: float,
    charisma_gene_value: float,
    max_vision_distance: int,
    world_width: int,
    world_height: int,
) -> PredatorMatingCallResult:
    predator_vision_in_grid_tiles: int = int(math.floor(vision_gene_value * max_vision_distance))

    for nearby_visible_position in iter_nearby_visible_positions(
        from_position,
        predator_vision_in_grid_tiles,
        world_width,
        world_height
    ):
        position_as_tuple = nearby_visible_position.to_tuple()
        if position_as_tuple not in world.predator_by_position:
            continue

        nearby_predator = world.predator_by_position[position_as_tuple]
        if nearby_predator.id in so_far_denied_by:
            continue

        # Roll the charisma.
        if random.uniform(0, 1) < charisma_gene_value:
            return PredatorMatingCallResult(
                found_mate=nearby_predator,
                newly_denied_by=None
            )
        else:
            return PredatorMatingCallResult(
                found_mate=None,
                newly_denied_by=nearby_predator
            )

    return PredatorMatingCallResult(
        found_mate=None,
        newly_denied_by=None
    )



@dataclass(slots=True, frozen=True, kw_only=True)
class PredatorTickChanges:
    is_alive: bool = dataclasses.field(default=True)
    children: list[Predator] = dataclasses.field(default_factory=list)
    eaten: list[Prey] = dataclasses.field(default_factory=list)
    new_satiation: float
    new_reproductive_urge: float
    new_position: WorldPosition
    new_mind_state: PredatorMindState


def tick_predator(
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
                simulation_options.max_vision_distance,
                simulation_options.world_width,
                simulation_options.world_height
            )

            next_position: WorldPosition
            if closest_prey is not None:
                next_position = move_towards(predator.position, closest_prey.position)

                return PredatorTickChanges(
                    new_satiation=next_satiation,
                    new_reproductive_urge=next_reproductive_urge,
                    new_position=next_position,
                    new_mind_state=PredatorHuntingState(found_prey_id=closest_prey.id)
                )
            else:
                next_position = move_in_random_direction(predator.position, simulation_options)

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
                predator.genes.charisma,
                simulation_options.max_vision_distance,
                simulation_options.world_width,
                simulation_options.world_height
            )

            denied_by: list[PredatorId] = []
            if mating_call_result.newly_denied_by is not None:
                denied_by.append(mating_call_result.newly_denied_by.id)

            if mating_call_result.found_mate is not None:
                next_position = move_towards(predator.position, mating_call_result.found_mate.position)

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
                next_position = move_in_random_direction(predator.position, simulation_options)

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

        next_position = move_in_random_direction(
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
        if predator.mind_state.found_prey_id not in world.prey_by_id or predator.mind_state.found_prey_id is None:
            closest_prey = _find_closest_prey_for_predator(
                predator.position,
                world,
                predator.genes.vision,
                simulation_options.max_vision_distance,
                simulation_options.world_width,
                simulation_options.world_height
            )

            if closest_prey is not None:
                next_position = move_towards(predator.position, closest_prey.position)

                return PredatorTickChanges(
                    new_satiation=next_satiation,
                    new_reproductive_urge=next_reproductive_urge,
                    new_position=next_position,
                    new_mind_state=PredatorHuntingState(found_prey_id=closest_prey.id)
                )
            else:
                next_position = move_in_random_direction(predator.position, simulation_options)

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

        next_position = move_towards(predator.position, found_prey.position)
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
                predator.genes.charisma,
                simulation_options.max_vision_distance,
                simulation_options.world_width,
                simulation_options.world_height
            )

            denied_by = list.copy(predator.mind_state.denied_by)
            if mating_call_result.newly_denied_by is not None:
                denied_by.append(mating_call_result.newly_denied_by.id)

            if mating_call_result.found_mate is not None:
                next_position = move_towards(predator.position, mating_call_result.found_mate.position)

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
                next_position = move_in_random_direction(predator.position, simulation_options)

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

        next_position = move_towards(
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
                    aggression=mix_and_mutate_gene(
                        predator.genes.aggression,
                        predator.mind_state.other_parent_genes.aggression,
                        simulation_options.child_gene_mutation_chance_when_mating,
                        simulation_options.child_gene_mutation_magnitude_when_mating,
                    ),
                    fertility=mix_and_mutate_gene(
                        predator.genes.fertility,
                        predator.mind_state.other_parent_genes.fertility,
                        simulation_options.child_gene_mutation_chance_when_mating,
                        simulation_options.child_gene_mutation_magnitude_when_mating,
                    ),
                    charisma=mix_and_mutate_gene(
                        predator.genes.charisma,
                        predator.mind_state.other_parent_genes.charisma,
                        simulation_options.child_gene_mutation_chance_when_mating,
                        simulation_options.child_gene_mutation_magnitude_when_mating,
                    ),
                    vision=mix_and_mutate_gene(
                        predator.genes.vision,
                        predator.mind_state.other_parent_genes.vision,
                        simulation_options.child_gene_mutation_chance_when_mating,
                        simulation_options.child_gene_mutation_magnitude_when_mating,
                    ),
                    reproductive_urge_quickness=mix_and_mutate_gene(
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


        next_position = move_in_random_direction(
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
