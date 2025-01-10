import time
import argparse

from ecosystem_simulation.simulator import EcosystemSimulator
from ecosystem_simulation.simulator.options import PredatorSimulationOptions, SimulationOptions, PreySimulationOptions
from ecosystem_simulation.visualizer import EcosystemVisualizer
from ecosystem_simulation.simulation_player import *


def main():
    parser = argparse.ArgumentParser(description="Run the ecosystem simulation.")
    parser.add_argument("--filename", type=str, default="recordings/simulation_data.json", help="The filename to save the simulation data to.")
    args = parser.parse_args()

    player = SimulationPlayer(mode=PlayerMode.FILE, source=args.filename)

    visualizer = EcosystemVisualizer(player=player)
    visualizer.run()

if __name__ == '__main__':
    main()
