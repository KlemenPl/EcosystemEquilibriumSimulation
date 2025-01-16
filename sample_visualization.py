from ecosystem_simulation.visualizer import EcosystemVisualizer, EcosystemRecorder
from ecosystem_simulation.simulation_player import *


def main():
    '''opts: SimulationOptions = SimulationOptions.from_json_file("optimization_results/best_20250116-224426_5000.json")
    simulator = EcosystemSimulator(
        options_=opts,
    )'''

    simulator = EcosystemSimulator(
        options_=SimulationOptions(
            randomness_seed=77779113,
            logic_determine_creature_state=LogicType.FUZZY,
            world_width=10,
            world_height=10,
            max_vision_distance=16,
            child_gene_mutation_chance_when_mating=0.1,
            child_gene_mutation_magnitude_when_mating=0.05,
            food_item_spawning_rate_per_tick=1,
            food_item_life_tick=80,
            initial_number_of_food_items=3,
            max_number_of_food_items=5,
            predator=EntitySimulationOptions(
                initial_number=2,
                initial_satiation_on_spawn=0.7,
                max_juvenile_in_ticks=30,
                max_gestation_in_ticks=20,
                max_age_in_ticks=300,
                max_children_per_birth=3,
                satiation_per_feeding=0.8,
                satiation_loss_per_tick=0.025,
            ),
            prey=EntitySimulationOptions(
                initial_number=5,
                initial_satiation_on_spawn=0.5,
                max_juvenile_in_ticks=30,
                max_gestation_in_ticks=20,
                max_age_in_ticks=10000,
                max_children_per_birth=5,
                satiation_per_feeding=0.6,
                satiation_loss_per_tick=0.005,
            )
        )
    )

    player = SimulationPlayer(mode=PlayerMode.SIMULATOR, source=simulator)
    visualizer = EcosystemVisualizer(player=player)
    visualizer.run()
    #recoreder = EcosystemRecorder(simulator=simulator, num_ticks=700)
    #recoreder.record("out.gif")


if __name__ == '__main__':
    main()
