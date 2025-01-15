from ecosystem_simulation.visualizer import EcosystemVisualizer, EcosystemRecorder
from ecosystem_simulation.simulation_player import *


def main():
    #opts: SimulationOptions = SimulationOptions.from_json_file("optimization_results/best_20250115-214026_481.json")
    opts: SimulationOptions = SimulationOptions.from_json_file("optimization_results/best_2.json")
    simulator = EcosystemSimulator(
        options_=opts,
    )

    player = SimulationPlayer(mode=PlayerMode.SIMULATOR, source=simulator)
    visualizer = EcosystemVisualizer(player=player)
    visualizer.run()
    #recoreder = EcosystemRecorder(simulator=simulator, num_ticks=700)
    #recoreder.record("out.gif")


if __name__ == '__main__':
    main()
