from dataclasses import dataclass

from . import WorldPosition


@dataclass(slots=True)
class Food:
    position: WorldPosition
