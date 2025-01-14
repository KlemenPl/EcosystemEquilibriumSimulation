import time
import argparse

from ecosystem_simulation.simulator import EcosystemSimulator, SimulatedTick
from ecosystem_simulation.simulator.options import PredatorSimulationOptions, SimulationOptions, PreySimulationOptions
from ecosystem_simulation.simulation_recorder import SimulationRecorder

def main():
    parser = argparse.ArgumentParser(description="Run the ecosystem simulation.")
    parser.add_argument("--filename", type=str, default="recordings/simulation_data.json", help="The filename to save the simulation data to.")
    args = parser.parse_args()

    simulator = EcosystemSimulator(
        options_=SimulationOptions(
            randomness_seed=43098592,
            world_width=64,
            world_height=64,
            max_vision_distance=14,
            child_gene_mutation_chance_when_mating=0.1,
            child_gene_mutation_magnitude_when_mating=0.05,
            initial_number_of_food_items=8,
            food_item_spawning_rate_per_tick=0.5,
            predator=PredatorSimulationOptions(
                initial_number=6,
                initial_satiation_on_spawn=0.7,
                initial_reproductive_urge_on_spawn=0,
                pregnancy_duration_in_ticks=20,
                max_children_per_birth=2,
                satiation_per_one_eaten_prey=1,
                satiation_loss_per_tick=0.025
            ),
            prey=PreySimulationOptions(
                initial_number=30,
                initial_satiation_on_spawn=0.75,
                pregnancy_duration_in_ticks=16,
                initial_reproductive_urge_on_spawn=0.05,
                satiation_per_food_item=1,
                max_children_per_birth=4,
                satiation_loss_per_tick=0.02
            )
        )
    )

    sim_recorder = SimulationRecorder(simulator)
    time_before = time.time()
    tick_count = 1000
    for _ in range(tick_count):
        simulator.next_simulation_tick()

    time_elapsed = time.time() - time_before
    print(f"Simulated {tick_count} more ticks in {round(time_elapsed, 2)} seconds.")

    sim_recorder.saveJson(args.filename)

    # Uncomment to record
    #gif_recorder = EcosystemRecorder(simulator)
    #gif_recorder.record("ecosystem_simulation.gif")


if __name__ == '__main__':
    main()
