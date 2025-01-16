import time
import argparse

from ecosystem_simulation.simulator import EcosystemSimulator, SimulatedTick
from ecosystem_simulation.simulator.options import SimulationOptions, EntitySimulationOptions
from ecosystem_simulation.simulation_recorder import SimulationRecorder
from ecosystem_simulation.simulator.options import LogicType

def main():
    parser = argparse.ArgumentParser(description="Run the ecosystem simulation.")
    parser.add_argument("--filename", type=str, default="recordings/simulation_data.json", help="The filename to save the simulation data to.")
    args = parser.parse_args()

    simulator = EcosystemSimulator(
        options_=SimulationOptions(
            randomness_seed=77779113,
            logic_determine_creature_state=LogicType.NORMAL,
            world_width=64,
            world_height=64,
            max_vision_distance=16,
            child_gene_mutation_chance_when_mating= 0.1,
            child_gene_mutation_magnitude_when_mating=0.05,
            food_item_spawning_rate_per_tick=5,
            food_item_life_tick=80,
            initial_number_of_food_items=200,
            max_number_of_food_items=400,
            predator=EntitySimulationOptions(
                initial_number=20,
                initial_satiation_on_spawn=0.3,
                max_juvenile_in_ticks=30,
                max_gestation_in_ticks=20,
                max_age_in_ticks=300,
                max_children_per_birth=3,
                satiation_per_feeding=0.8,
                satiation_loss_per_tick=0.025,
            ),
            prey=EntitySimulationOptions(
                initial_number=120,
                initial_satiation_on_spawn=0.2,
                max_juvenile_in_ticks=30,
                max_gestation_in_ticks=20,
                max_age_in_ticks=300,
                max_children_per_birth=5,
                satiation_per_feeding=0.6,
                satiation_loss_per_tick=0.005,
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
