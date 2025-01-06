import random
from typing import Optional, Generator

from ..models.world import WorldPosition
from ..options import SimulationOptions


def iter_nearby_visible_positions(
    center_position: WorldPosition,
    maximum_distance_in_grid_cells: int,
    world_width: int,
    world_height: int,
) -> Generator[WorldPosition, None, None]:
    for horizontal_offset in range(-maximum_distance_in_grid_cells, maximum_distance_in_grid_cells + 1):
        for vertical_offset in range(-maximum_distance_in_grid_cells, maximum_distance_in_grid_cells + 1):
            generated_x = center_position.x + horizontal_offset
            if generated_x < 0 or generated_x >= world_width:
                continue

            generated_y = center_position.y + vertical_offset
            if generated_y < 0 or generated_y >= world_height:
                continue

            yield WorldPosition(x=generated_x, y=generated_y)


def move_in_random_direction(
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


def move_towards(
    current_position: WorldPosition,
    target_position: WorldPosition,
) -> WorldPosition:
    if current_position == target_position:
        return current_position


    if current_position.x == target_position.x:
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
    elif current_position.y == target_position.y:
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


def move_away_from(
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



def mix_and_mutate_gene(
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
