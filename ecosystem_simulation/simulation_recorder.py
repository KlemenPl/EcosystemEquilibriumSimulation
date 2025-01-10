import json

from ecosystem_simulation.simulator import *

class SimulationRecorder:
    def __init__(self, simulator: EcosystemSimulator):
        self.data = []
        self.options = simulator._options
        simulator._on_tick = self.recordTick

    def recordTick(self, tick: SimulatedTick):
        self.data.append(tick.serialize())

    def saveJson(self, filename):
        with open(filename, "w") as f:
            save_data = {
                "options": self.options.serialize(),
                "data": self.data
            }

            json.dump(save_data, f)