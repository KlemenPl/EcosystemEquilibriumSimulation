
from dataclasses import dataclass

@dataclass(slots=True, init=True, eq=True, order=True, kw_only=True)
class WorldPosition:
    x: int
    y: int

    @classmethod
    def from_tuple(cls, t: tuple[int, int]) -> "WorldPosition":
        return cls(x=t[0], y=t[1])

    def to_tuple(self) -> tuple[int, int]:
        return self.x, self.y

    def distance_from(self, other: "WorldPosition") -> float:
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
    
    def serialize(self):
        return {
            "x": self.x,
            "y": self.y
        }
    
    def deserialize(data):
        return WorldPosition(x=data["x"], y=data["y"])