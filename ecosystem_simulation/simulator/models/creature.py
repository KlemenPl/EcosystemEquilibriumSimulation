from dataclasses import dataclass

from .state import EntityState
from .entity import Entity
from ecosystem_simulation.simulator.models.genes import Genes

@dataclass(slots=True)
class Creature(Entity):
    generation: int

    state: EntityState

    alive: bool

    move_accum: float

    # Current satiation (opposite of hunger) of this entity (non-negative float).
    # When this value reaches 0, the entity dies.
    satiation: float


    # Current reproductive urge of this entity (non-negative float).
    # The larger the value, the more likely it is the entity
    # will enter its mating state.
    reproductive_urge: float

    # Specimen genes
    genes: Genes

    mature: bool

    pregnant: bool
    pregnant_duration: int
    pregnant_partner_genes: Genes


@dataclass(slots=True)
class Predator(Creature):
    pass

@dataclass(slots=True)
class Prey(Creature):
    pass
