import json
from typing import Union

from ecosystem_simulation.simulator import *

class PlayerMode:
    SIMULATOR = 0
    FILE = 1

class SimulationPlayer:
    _options: SimulationOptions

    def __init__(self, mode: PlayerMode, source: Union[str, EcosystemSimulator]):
        if mode == PlayerMode.FILE:
            readData = self.read_json(source)
            self.data = readData["data"]
            self._options = SimulationOptions.deserialize(readData["options"])
            self.mode = PlayerMode.FILE
        elif mode == PlayerMode.SIMULATOR:
            self.simulator = source
            self._options = source.options
            self.mode = PlayerMode.SIMULATOR
        else:
            raise ValueError("Invalid mode")
        self.tick = 0

    def read_json(self, filename: str):
        with open(filename, "r") as f:
            return json.load(f)
        
    def next_tick(self) -> SimulatedTick:
        self.tick += 1
        if self.mode == PlayerMode.SIMULATOR:
            return self.simulator.next_simulation_tick()
        elif self.mode == PlayerMode.FILE:
            tick_count = self.tick_count()
            if self.tick >= tick_count:
                self.tick = tick_count - 1
            return SimulatedTick.deserialize(self.data[self.tick])
        else:
            raise ValueError("Invalid mode")
        
    def tick_count(self) -> int:
        if self.mode == PlayerMode.SIMULATOR:
            return self.simulator._current_tick_number
        elif self.mode == PlayerMode.FILE:
            return len(self.data)
        else:
            raise ValueError("Invalid mode")