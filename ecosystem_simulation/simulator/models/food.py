
from dataclasses import dataclass


from .entity import Entity


@dataclass(slots=True)
class Food(Entity):
    max_age: int
