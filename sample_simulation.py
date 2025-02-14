import time

from ecosystem_simulation.simulator import EcosystemSimulator, SimulatedTick
from ecosystem_simulation.simulator.options import SimulationOptions, EntitySimulationOptions
from ecosystem_simulation.simulator.options import LogicType


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
