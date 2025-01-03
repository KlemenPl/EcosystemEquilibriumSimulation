from dataclasses import dataclass

from .prey import Prey, PreyGenes, PreyId
from .predator import Predator, PredatorGenes, PredatorId
from .food import Food


@dataclass(slots=True)
class WorldPosition:
    x: int
    y: int


@dataclass(slots=True)
class SimulationState:
    predators: list[Predator]
    prey: list[Prey]
    food: list[Food]
