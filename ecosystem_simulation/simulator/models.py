from dataclasses import dataclass


@dataclass(slots=True)
class WorldPosition:
    x: int
    y: int



@dataclass(slots=True)
class PredatorGenes:
    aggression: float
    fertility: float
    charisma: float
    speed: float
    vision: float


@dataclass(slots=True)
class Predator:
    genes: PredatorGenes
    position: WorldPosition
    hunger: float
    energy: float


@dataclass(slots=True)
class PreyGenes:
    fertility: float
    charisma: float
    speed: float
    vision: float


@dataclass(slots=True)
class Prey:
    genes: PreyGenes
    position: WorldPosition
    hunger: float
    energy: float



@dataclass(slots=True)
class SimulationState:
    predators: list[Predator]
    prey: list[Prey]