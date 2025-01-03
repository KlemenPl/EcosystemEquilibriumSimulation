from abc import ABCMeta, abstractmethod

from .models import SimulationState


class SimulatorBackend(metaclass=ABCMeta):
    @abstractmethod
    def get_simulation_results(self) -> list[SimulationState]:
        return NotImplemented
