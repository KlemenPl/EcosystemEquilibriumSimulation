from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Optional

from . import SimulationState


@dataclass(slots=True, frozen=True)
class SimulatedTick:
    tick_number: int
    state: SimulationState


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
