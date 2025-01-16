from dataclasses import asdict
from pathlib import Path
from queue import Empty

import multiprocessing as mp
from datetime import datetime
import random

from ecosystem_simulation.simulator import EcosystemSimulator
from ecosystem_simulation.simulator.options import *

def generate_random_entity_options() -> EntitySimulationOptions:
    return EntitySimulationOptions(
        initial_number=random.randint(200, 800),
        initial_satiation_on_spawn=random.randint(10, 25) / 100,
        max_juvenile_in_ticks=20,
        max_gestation_in_ticks=20,
        max_age_in_ticks=80,
        max_children_per_birth=8,
        satiation_per_feeding=random.randint(4, 9) / 10,
        satiation_loss_per_tick=random.randint(1, 40) / 100,
    )

def generate_random_sim_options(seed: int) -> SimulationOptions:
    return SimulationOptions(
        randomness_seed=seed,
        world_width=256,
        world_height=256,
        max_vision_distance=8,
        child_gene_mutation_chance_when_mating=random.randint(1, 20) / 100,
        child_gene_mutation_magnitude_when_mating=random.randint(1, 20) / 100,
        food_item_spawning_rate_per_tick=random.randint(10, 40),
        food_item_life_tick=random.randint(50, 100),
        initial_number_of_food_items=random.randint(500, 1000),
        max_number_of_food_items=random.randint(1000, 3000),
        predator=generate_random_entity_options(),
        prey=generate_random_entity_options(),
    )


def evaluate_sim(max_ticks: int, options: SimulationOptions) -> int:
    simulator = EcosystemSimulator(options)

    for i_tick in range(max_ticks):
        state = simulator.next_simulation_tick().state
        if state.prey_count() == 0 or state.predator_count() == 0:
            return i_tick

    return max_ticks

import traceback

def evaluate_worker(worker_id: int, max_ticks: int, result_queue: mp.Queue) -> (int, SimulationOptions):
    while True:
        try:
            params = generate_random_sim_options(random.randint(1, 2 ** 32))
            num_ticks = evaluate_sim(max_ticks, params)
            result_queue.put((num_ticks, params))
        except Exception as e:
            print(traceback.format_exc())
            print(f"Worker {worker_id} encountered error: {e}")


def save_best_params(score: int, params: SimulationOptions):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = Path("optimization_results")
    output_dir.mkdir(exist_ok=True)

    data = {
        "timestamp": timestamp,
        "seed": params.randomness_seed,
        "score": score,
        "params": json.dumps(asdict(params)),
    }

    output_path = output_dir / f"best_{timestamp}_{score}.json"
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=4)

    print(f"Saved best parameters to {output_path}")


def random_search(max_simulations: int, max_ticks: int=5000):
    best_score: int = 0
    best_params: SimulationOptions = generate_random_sim_options(0)
    simulation_count: int = 0

    num_cores = mp.cpu_count()
    print(f"Using {num_cores} CPU cores")

    result_queue = mp.Queue(maxsize=num_cores - 2)


    workers = []
    for i in range(num_cores):
        p = mp.Process(
            target=evaluate_worker,
            args=(i, max_ticks, result_queue),
            daemon=True,
        )
        workers.append(p)
        p.start()

    try:
        while simulation_count < max_simulations:
            try:
                score, options = result_queue.get()
                simulation_count += 1
                if score > best_score:
                    best_score = score
                    best_params = options
                    print(f"New best score at simulation_count {simulation_count}: {best_score} ticks survived")
                    save_best_params(best_score, best_params)

                if simulation_count % 10000 == 0:
                    print(f"Completed {simulation_count} simulations. Current best: {best_score} ticks")

            except Empty:
                continue
    except KeyboardInterrupt:
        print("\nSearch interrupted by user. Saving best results so far...")
        if best_params is not None:
            save_best_params(best_score, best_params)
        print("Results saved. Exiting...")
        return best_score, best_params

    return best_params


if __name__ == '__main__':
    best = random_search(max_simulations=100000000, max_ticks=5000)

    print("\nOptimization complete. Best parameters:")
    print(json.dumps(best, indent=4))
