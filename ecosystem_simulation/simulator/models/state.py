from dataclasses import dataclass

@dataclass
class EntityState:
    pass

@dataclass
class WanderingState(EntityState):
    dir_x: int = 0
    dir_y: int = 0

@dataclass
class HuntState(EntityState):
    target_id: int = -1

@dataclass
class FleeState(EntityState):
    target_id: int = -1

@dataclass
class MateState(EntityState):
    target_id: int = -1
