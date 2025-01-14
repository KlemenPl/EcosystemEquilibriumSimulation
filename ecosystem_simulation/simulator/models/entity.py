from dataclasses import dataclass

from .world_position import WorldPosition

@dataclass(slots=True)
class Entity:
    id: int
    alive: bool

    age_ticks: int

    # Current position of this entity
    position: WorldPosition
