import random

from .models import WorldPosition

def generate_random_position_in_world(
    world_width: int,
    world_height: int,
) -> WorldPosition:
    return WorldPosition(
        random.randrange(0, world_width, 1),
        random.randrange(0, world_height, 1)
    )

