import random

from .models import WorldPosition

def generate_random_position_in_world(
    world_width: int,
    world_height: int,
) -> WorldPosition:
    return WorldPosition(
        x=random.randrange(0, world_width, 1),
        y=random.randrange(0, world_height, 1)
    )


def clamp(value: float, minimum: float, maximum: float) -> float:
    if value < minimum:
        return minimum

    if value > maximum:
        return maximum

    return value

