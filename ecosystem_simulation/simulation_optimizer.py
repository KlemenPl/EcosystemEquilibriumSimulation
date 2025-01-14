from pathlib import Path
from queue import Empty

import multiprocessing as mp
import json
from datetime import datetime
import random

from skopt import gp_minimize
from skopt.space import Real, Integer
from skopt.utils import use_named_args

from ecosystem_simulation.simulator import EcosystemSimulator
from ecosystem_simulation.simulator.options import PredatorSimulationOptions, PreySimulationOptions, SimulationOptions


def generate_random_sim_options() -> SimulationOptions:
    return SimulationOptions(
        randomness_seed=random.randint(0, 2 ** 32),
        world_width=256,
        world_height=256,
        max_vision_distance=random.randint(0, 20),
        child_gene_mutation_chance_when_mating=random.uniform(0.01, 0.5),
        child_gene_mutation_magnitude_when_mating=random.uniform(0.01, 0.5),
        initial_number_of_food_items=random.randint(0, 1000),
        food_item_spawning_rate_per_tick=random.uniform(0, 100),
        predator=PredatorSimulationOptions(
            initial_number=random.randint(1, 1000),
            initial_satiation_on_spawn=1,
            initial_reproductive_urge_on_spawn=random.uniform(0.1, 0.8),
            pregnancy_duration_in_ticks=random.randint(1, 50),
            max_children_per_birth=random.randint(1, 20),
            satiation_per_one_eaten_prey=random.uniform(0.2, 0.8),
            satiation_loss_per_tick=random.uniform(0.01, 0.1),
        ),
        prey=PreySimulationOptions(
            initial_number=random.randint(1, 1000),
            initial_satiation_on_spawn=1,
            pregnancy_duration_in_ticks=random.randint(1, 50),
            initial_reproductive_urge_on_spawn=random.uniform(0.1, 0.8),
            satiation_per_food_item=random.uniform(0.2, 0.8),
            max_children_per_birth=random.randint(1, 20),
            satiation_loss_per_tick=random.uniform(0.01, 0.1),
        ),
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
            params = generate_random_sim_options()
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
        "params": params.serialize(),
    }

    output_path = output_dir / f"best_{timestamp}_{score}.json"
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=4)

    print(f"Saved best parameters to {output_path}")


def random_search(max_ticks: int):
    best_score: int = 0
    best_params: SimulationOptions = generate_random_sim_options()
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
        while True:
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

space = [
        Integer(0, 20, name='max_vision_distance'),
        Real(0, 1, name='child_gene_mutation_chance'),
        Real(0, 1, name='child_gene_mutation_magnitude'),
        Integer(0, 1000, name='initial_food_items'),
        Real(0, 100, name='food_spawn_rate'),
        # Predator parameters
        Integer(1, 1000, name='predator_initial_number'),
        Real(0.1, 0.8, name='predator_initial_satiation'),
        Real(0.1, 0.8, name='predator_initial_reproductive_urge'),
        Integer(1, 100, name='predator_pregnancy_duration'),
        Integer(1, 20, name='predator_max_children'),
        Real(0.2, 0.8, name='predator_satiation_per_prey'),
        Real(0.01, 0.1, name='predator_satiation_loss'),
        # Prey parameters
        Integer(1, 1000, name='prey_initial_number'),
        Real(0.1, 0.8, name='prey_initial_satiation'),
        Real(0.1, 0.8, name='prey_initial_reproductive_urge'),
        Integer(1, 100, name='prey_pregnancy_duration'),
        Integer(1, 20, name='prey_max_children'),
        Real(0.2, 0.8, name='prey_satiation_per_food'),
        Real(0.01, 0.1, name='prey_satiation_loss'),
]

def create_sim_options(**kwargs) -> SimulationOptions:
    return SimulationOptions(
        randomness_seed=random.randint(1, 2 ** 32),
        world_width=256,
        world_height=256,
        max_vision_distance=kwargs['max_vision_distance'],
        child_gene_mutation_chance_when_mating=kwargs['child_gene_mutation_chance'],
        child_gene_mutation_magnitude_when_mating=kwargs['child_gene_mutation_magnitude'],
        initial_number_of_food_items=kwargs['initial_food_items'],
        food_item_spawning_rate_per_tick=kwargs['food_spawn_rate'],
        predator=PredatorSimulationOptions(
            initial_number=kwargs['predator_initial_number'],
            initial_satiation_on_spawn=kwargs['predator_initial_satiation'],
            initial_reproductive_urge_on_spawn=kwargs['predator_initial_reproductive_urge'],
            pregnancy_duration_in_ticks=kwargs['predator_pregnancy_duration'],
            max_children_per_birth=kwargs['predator_max_children'],
            satiation_per_one_eaten_prey=kwargs['predator_satiation_per_prey'],
            satiation_loss_per_tick=kwargs['predator_satiation_loss'],
        ),
        prey=PreySimulationOptions(
            initial_number=kwargs['prey_initial_number'],
            initial_satiation_on_spawn=kwargs['prey_initial_satiation'],
            initial_reproductive_urge_on_spawn=kwargs['prey_initial_reproductive_urge'],
            pregnancy_duration_in_ticks=kwargs['prey_pregnancy_duration'],
            max_children_per_birth=kwargs['prey_max_children'],
            satiation_per_food_item=kwargs['prey_satiation_per_food'],
            satiation_loss_per_tick=kwargs['prey_satiation_loss'],
        ),
    )


@use_named_args(space)
def objective(**kwargs) -> float:
    options = create_sim_options(**kwargs)
    return -evaluate_sim(max_ticks=20000, options=options)

def qp_minimize(max_ticks: int):
    result = gp_minimize(
        objective,
        space,
        n_calls=80,
        n_initial_points=40,
        n_random_starts=20,
        noise=0.1,
        random_state=42,
        n_jobs=-1,
        acq_func='EI',
        verbose=True,
    )

    best_params = result.x
    best_score = -result.fun

    print(f"Best score (ticks survived): {best_score}")
    print("\nBest parameters found:")
    for param, value in zip([dim.name for dim in space], best_params):
        print(f"{param}: {value}")


if __name__ == '__main__':
    best = random_search(max_ticks=100000)
    #qp_minimize(max_ticks=100000)

    print("\nOptimization complete. Best parameters:")
    print(json.dumps(best, indent=4))
