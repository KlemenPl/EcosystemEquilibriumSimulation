import time

from ecosystem_simulation.simulator import EcosystemSimulator, SimulatedTick
from ecosystem_simulation.simulator.options import PredatorSimulationOptions, SimulationOptions, PreySimulationOptions


def print_tick_state_summary(simulated_tick: SimulatedTick):
    print(f"Tick number: {simulated_tick.tick_number}")

    for predator in simulated_tick.state.predators():
        print(
            f"Predator {predator.id}: at [{predator.position.x},{predator.position.y}], "
            f"mind: {predator.mind_state} (satiation={round(predator.satiation, 2)})"
        )

    for prey in simulated_tick.state.prey():
        print(
            f"Prey {prey.id}: at [{prey.position.x},{prey.position.y}], "
            f"mind: {prey.mind_state} (satiation={round(prey.satiation, 2)})"
        )

    for food in simulated_tick.state.food():
        print(f"Food {food.id}: at [{food.position.x},{food.position.y}]")


def main():
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

    tick_state = simulator.next_simulation_tick()
    print_tick_state_summary(tick_state)

    print("\n\n---\n\n", end="")

    tick_state = simulator.next_simulation_tick()
    print_tick_state_summary(tick_state)


    time_before = time.time()

    for _ in range(1000):
        simulator.next_simulation_tick()

    time_elapsed_for_hundred_ticks = time.time() - time_before

    print(f"Simulated 1000 more ticks in {round(time_elapsed_for_hundred_ticks, 2)} seconds.")





if __name__ == '__main__':
    main()
