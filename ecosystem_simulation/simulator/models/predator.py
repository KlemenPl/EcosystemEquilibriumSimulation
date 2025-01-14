import random
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from .world_position import WorldPosition
from .abc import EntityId

from .prey import PreyId


@dataclass(slots=True, frozen=True)
class PredatorId(EntityId):
    id: int

    @classmethod
    def new_random(cls) -> "PredatorId":
        return cls(id=random.randint(0, 2**16))
    
    def serialize(self):
        return self.id

    @staticmethod
    def deserialize(data):
        return PredatorId(id=data)


@dataclass(slots=True)
class PredatorGenes:
    # This gene controls how aggressive a given specimen is, meaning
    # how quickly it will decide to hunt again after eating.
    aggression: float

    # This gene controls how many children a single specimen will carry.
    # Upon birthing, a value between 0 and the value of this gene is uniformly sampled
    # and multiplied with the `predator_max_children_per_birth` simulation option.
    fertility: float

    # This gene controls how attractive this specimen is when attempting to reproduce.
    charisma: float

    # This gene controls how far the specimen can see. To obtain the number
    # of grid blocks of vision, this value is multiplied with the `max_vision_distance`
    # simulation option.
    vision: float

    # This gene controls how quickly the `reproductive_urge` value
    # rises for a given specimen.
    reproductive_urge_quickness: float

    def serialize(self):
        return {
            "aggression": self.aggression,
            "fertility": self.fertility,
            "charisma": self.charisma,
            "vision": self.vision,
            "reproductive_urge_quickness": self.reproductive_urge_quickness
        }

    @staticmethod
    def deserialize(data):
        return PredatorGenes(
            aggression=data["aggression"],
            fertility=data["fertility"],
            charisma=data["charisma"],
            vision=data["vision"],
            reproductive_urge_quickness=data["reproductive_urge_quickness"]
        )


@dataclass(slots=True)
class Predator:
    # A persistent ID for this predator.
    id: "PredatorId"

    # Current mind state (idling, hunting, ...).
    mind_state: "PredatorMindState"

    # Static genes of this predator. Will be mixed in when mating.
    genes: "PredatorGenes"

    # Current position of the predator.
    position: "WorldPosition"

    # Current satiation (opposite of hunger) of this predator (non-negative float).
    # When this value reaches 0, the predator dies.
    satiation: float

    # Current reproductive urge of this predator (non-negative float).
    # The larger the value, the more likely it is the predator
    # will enter its mating state.
    reproductive_urge: float

    def serialize(self):
        return {
            "id": self.id.serialize(),
            "mind_state": self.mind_state.serialize(),
            "genes": self.genes.serialize(),
            "position": self.position.serialize(),
            "satiation": self.satiation,
            "reproductive_urge": self.reproductive_urge
        }

    @staticmethod
    def deserialize(data):
        return Predator(
            id=PredatorId.deserialize(data["id"]),
            mind_state=PredatorMindState.deserialize(data["mind_state"]),
            genes=PredatorGenes.deserialize(data["genes"]),
            position=WorldPosition.deserialize(data["position"]),
            satiation=data["satiation"],
            reproductive_urge=data["reproductive_urge"]
        )



# The following describes one of multiple possible predator states akin to a
# finite state machine. The predator can only decide to pursue one goal at once.
# All possible FSM states are implementations of `PredatorMindState`.

class PredatorMindState(metaclass=ABCMeta):
    @abstractmethod
    def serialize(self):
        return NotImplemented

    @staticmethod
    def deserialize(data):
        type = data["type"]
        if type == "idle":
            return PredatorIdleState.deserialize(data)
        elif type == "reproduction":
            return PredatorReproductionState.deserialize(data)
        elif type == "pregnant":
            return PredatorPregnantState.deserialize(data)
        elif type == "hunting":
            return PredatorHuntingState.deserialize(data)
        else:
            raise ValueError(f"Unknown predator mind state: {type}")

@dataclass(slots=True)
class PredatorIdleState(PredatorMindState):
    """
    In its (rather rare) idle state, the predator wanders idly
    in a random direction (up, right, down, or left).

    When ticking a predator in its idle state, the logic is as follows:
      - If the value of the `aggression` gene is larger than the predator's `satiation`:
          The predator enters its hunting state (see `PredatorHuntingState`).
      - Otherwise, uniformly sample the random value between 0 and 1.
        If the value is smaller than the predator's `reproductive_urge`:
          The predator enters its reproduction state (see `PredatorReproductionState`).
    """

    def serialize(self):
        return {"type": "idle"}

    @staticmethod
    def deserialize(data):
        return PredatorIdleState()

@dataclass(slots=True)
class PredatorReproductionState(PredatorMindState):
    """
    A predator in its reproduction state is looking for fellow predators
    in a radius dependent on its vision gene.

    The radius is determined by multiplying the value of the gene by
    `max_vision_distance` from the simulation options.

    Each tick, the predator will attempt to find the closest predator that
    hasn't denied it, regardless of that predator's current state.
    Uniformly sample a value between 0 and 1. If the value is smaller than our `charisma`,
    the call succeeds - the target predator also enters the reproduction state and
    the `found_mate` values are set to refer to each other. In subsequent ticks, the
    predator shall move towards it other until they collide.

    When they do, reproduction is performed. Pick a random of the two predators
    and assign it the pregnant state. The other is assigned the idle state.
    """

    # `None` indicates the predator is searching for nearby mates.
    # A value indicates moving towards the found mate for reproduction.
    found_mate_id: Optional["PredatorId"]

    # Contains a list of all potential mates who have denied
    # mating with this predator. This is reset upon mating once.
    denied_by: list["PredatorId"]

    def serialize(self):
        return {
            "type": "reproduction",
            "found_mate_id": self.found_mate_id.serialize() if self.found_mate_id is not None else None,
            "denied_by": [id.serialize() for id in self.denied_by if self.denied_by is not None]
            }

    @staticmethod
    def deserialize(data):
        return PredatorReproductionState(
            found_mate_id=PredatorId.deserialize(data["found_mate_id"]) if data["found_mate_id"] is not None else None,
            denied_by=[PredatorId.deserialize(id) for id in data["denied_by"]]
        )

@dataclass(slots=True)
class PredatorPregnantState(PredatorMindState):
    """
    After reproduction is complete (see `PredatorReproductionState`), one of
    the predators becomes pregnant.

    It stands still until it births another predator (as specified by `ticks_until_birth`,
    which decrements each tick until birth).
    """
    ticks_until_birth: int

    other_parent_genes: "PredatorGenes"

    def serialize(self):
        return {
            "type": "pregnant",
            "ticks_until_birth": self.ticks_until_birth,
            "other_parent_genes": self.other_parent_genes.serialize()
        }

    @staticmethod
    def deserialize(data):
        return PredatorPregnantState(
            ticks_until_birth=data["ticks_until_birth"],
            other_parent_genes=PredatorGenes.deserialize(data["other_parent_genes"])
        )

@dataclass(slots=True)
class PredatorHuntingState(PredatorMindState):
    """
    A predator in its hunting state is looking for prey
    in a radius dependent on its vision gene.

    The radius is determined by multiplying the value of the gene by
    `max_vision_distance` from the simulation options.

    The predator will attempt to find the closest prey in that radius.
    If it does not find it, it will try again next tick.
    """

    # `None` indicates the predator is searching for nearby prey.
    # A value indicates moving towards the prey in order to eat it.
    found_prey_id: Optional["PreyId"]

    def serialize(self):
        if self.found_prey_id is None:
            return {
                "type": "hunting",
                "found_prey_id": ""
            }
        else:
            return {
                "type": "hunting",
                "found_prey_id": self.found_prey_id.id
            }

    @staticmethod
    def deserialize(data):
        if data["found_prey_id"] == "":
            return PredatorHuntingState(found_prey_id=None)
        else:
            return PredatorHuntingState(found_prey_id=PreyId.deserialize(data["found_prey_id"]))
