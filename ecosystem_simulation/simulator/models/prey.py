import random
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from .world_position import WorldPosition
from .abc import EntityId

from .food import FoodId


@dataclass(slots=True, frozen=True)
class PreyId(EntityId):
    id: int

    @classmethod
    def new_random(cls) -> "PreyId":
        return cls(id=random.randint(0, 2**16))
    
    def serialize(self):
        return self.id
    
    def deserialize(data):
        return PreyId(id=data)


@dataclass(slots=True)
class PreyGenes:
    # This gene controls how quickly a prey will start to look
    # for food again after eating.
    appetite: float

    # This gene controls how many children a single specimen will carry.
    # Upon birthing, a value between 0 and the value of this gene is uniformly sampled
    # and multiplied with the `prey_max_children_per_birth` simulation option.
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
            "appetite": self.appetite,
            "fertility": self.fertility,
            "charisma": self.charisma,
            "vision": self.vision,
            "reproductive_urge_quickness": self.reproductive_urge_quickness
        }
    
    def deserialize(data):
        return PreyGenes(
            appetite=data["appetite"],
            fertility=data["fertility"],
            charisma=data["charisma"],
            vision=data["vision"],
            reproductive_urge_quickness=data["reproductive_urge_quickness"]
        )


@dataclass(slots=True)
class Prey:
    # A persistent ID for this prey.
    id: "PreyId"

    # Current mind state (idling, eating, ...).
    mind_state: "PreyMindState"

    # Static genes of this prey. Will be mixed in when mating.
    genes: "PreyGenes"

    # Current position of this prey.
    position: "WorldPosition"

    # Current satiation (opposite of hunger) of this prey (non-negative float).
    # When this value reaches 0, the prey dies.
    satiation: float

    # Current reproductive urge of this prey (non-negative float).
    # The larger the value, the more likely it is the prey
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
    
    def deserialize(data):
        return Prey(
            id=PreyId.deserialize(data["id"]),
            mind_state=PreyMindState.deserialize(data["mind_state"]),
            genes=PreyGenes.deserialize(data["genes"]),
            position=WorldPosition.deserialize(data["position"]),
            satiation=data["satiation"],
            reproductive_urge=data["reproductive_urge"]
        )


# The following describes one of multiple possible prey states akin to a
# finite state machine. The prey can only decide to pursue one goal at once.
# All possible FSM states are implementations of `PreyMindState`.

class PreyMindState(metaclass=ABCMeta):
    @abstractmethod
    def serialize(self):
        return NotImplemented
    
    def deserialize(data):
        type = data["type"]
        if type == "idle":
            return PreyIdleState.deserialize(data)
        elif type == "reproduction":
            return PreyReproductionState.deserialize(data)
        elif type == "pregnant":
            return PreyPregnantState.deserialize(data)
        elif type == "food_search":
            return PreyFoodSearchState.deserialize(data)
        else:
            raise ValueError(f"Unknown prey mind state type: {type}")


@dataclass(slots=True)
class PreyIdleState(PreyMindState):
    """
    In its (rather rare) idle state, the prey wanders idly
    in a random direction (up, right, down, or left).

    When ticking a prey in its idle state, the logic is as follows:
      - If the value of the `appetite` gene is larger than the prey's `satiation` value:
          The prey enters its food search state (see `PreyFoodSearchState`).
      - Otherwise, uniformly sample the random value between 0 and 1.
        If the value is smaller than the prey's `reproductive_urge`:
          The prey enters its reproduction state (see `PreyReproductionState`).
    """

    def serialize(self):
        return {
            "type": "idle"
        }
    
    def deserialize(data):
        return PreyIdleState()

@dataclass(slots=True)
class PreyReproductionState(PreyMindState):
    """
    In its reproduction-seeking state, the prey - based on its vision - searches
    around for nearby prey to mate with. When it finds one, it attempts to
    signal the intention to it. Success is determined by a random roll based on
    its charisma gene.

    If denied by the partner: the partner cannot be mated with this time.
    If accepted by the partner: `found_mate` is set, and both prey move towards
    each other and mate.
    """

    # `None` indicates the prey is searching for nearby mates.
    # A value indicates moving towards the found mate for reproduction.
    found_mate_id: Optional["PreyId"]

    # Contains a list of all potential mates who have denied
    # mating with this prey. This is reset upon mating once.
    denied_by: list["PreyId"]

    def serialize(self):
        return {
            "type": "reproduction",
            "found_mate_id": self.found_mate_id.serialize() if self.found_mate_id != None else None,
            "denied_by": [id.serialize() for id in self.denied_by if self.denied_by != None]
        }
    
    def deserialize(data):
        return PreyReproductionState(
            found_mate_id=PreyId.deserialize(data["found_mate_id"]) if data["found_mate_id"] != None else None,
            denied_by=[PreyId.deserialize(id) for id in data["denied_by"]]
        )


@dataclass(slots=True)
class PreyPregnantState(PreyMindState):
    """
    After reproduction is complete (see `PredatorReproductionState`), one of
    the prey specimens becomes pregnant.

    It stands still until it births another prey (as specified by `ticks_until_birth`,
    which decrements each tick until birth).
    """
    ticks_until_birth: int

    other_parent_genes: "PreyGenes"

    def serialize(self):
        return {
            "type": "pregnant",
            "ticks_until_birth": self.ticks_until_birth,
            "other_parent_genes": self.other_parent_genes.serialize()
        }
    
    def deserialize(data):
        return PreyPregnantState(
            ticks_until_birth=data["ticks_until_birth"],
            other_parent_genes=PreyGenes.deserialize(data["other_parent_genes"])
        )

@dataclass(slots=True)
class PreyFoodSearchState(PreyMindState):
    """
    In its food search state, the prey - based on its vision gene - searches
    around for available food. It stays in this state until it finds one.

    When it does, it "selects" it (by setting the `found_food_tile`). On subsequent
    ticks, it moves towards it, finally eating the food if it is still on that tile.
    Eating gives it some energy.
    """

    # `None` indicates the predator is searching for nearest food.
    # A value indicates moving towards the found food tile position.
    found_food_tile_id: Optional["FoodId"]

    def serialize(self):
        return {
            "type": "food_search",
            "found_food_tile_id": self.found_food_tile_id.serialize() if self.found_food_tile_id != None else None
        }
    
    def deserialize(data):
        return PreyFoodSearchState(
            found_food_tile_id=FoodId.deserialize(data["found_food_tile_id"]) if data["found_food_tile_id"] != None else None
        )
