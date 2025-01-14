from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from .models.world import SimulationState


@dataclass(slots=True, frozen=True)
class SimulatedTick:
    tick_number: int
    state: "SimulationState"

    def serialize(self) -> dict:
        return {
            "tick_number": self.tick_number,
            "state": self.state.serialize(),
        }

    @staticmethod
    def deserialize(data: dict):
        return SimulatedTick(tick_number=data["tick_number"], state=SimulationState.deserialize(data["state"]))


class SimulatorBackend(metaclass=ABCMeta):
    @abstractmethod
    def next_simulation_tick(self) -> Optional[SimulatedTick]:
        """
        Returns the results of the next simulation tick.
        Returns `None` if the simulation has concluded.

        This method may or may not block for some time (for example,
        unless we are reading from a saved simulation file, we need to
        actually simulate another tick before returning).
        """
        return NotImplemented
