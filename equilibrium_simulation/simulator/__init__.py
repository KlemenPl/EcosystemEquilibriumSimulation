import random

from .abc import SimulatorBackend
from .models import Prey, Predator, PreyGenes, PredatorGenes, WorldPosition, SimulationState
from .options import SimulatorOptions, PreySpawnOptions, PreyGeneOptions, PredatorGeneOptions, PredatorSpawnOptions
from .utilities import generate_random_position_in_world



def _prepare_initial_simulation_state(
    simulation_options: SimulatorOptions
) -> SimulationState:
    predator_gene_options = simulation_options.predator_gene_options
    initial_predators: list[Predator] = []

    for _ in range(simulation_options.initial_number_of_predators):
        # Spawn the predator at a random position in the world.
        predator_position = generate_random_position_in_world(
            simulation_options.world_width,
            simulation_options.world_height
        )

        # Give the predator uniformly random genes in the configured range.
        predator_genes = PredatorGenes(
            aggression=random.uniform(
                predator_gene_options.aggression_min,
                predator_gene_options.aggression_max
            ),
            fertility=random.uniform(
                predator_gene_options.fertility_min,
                predator_gene_options.fertility_max,
            ),
            charisma=random.uniform(
                predator_gene_options.charisma_min,
                predator_gene_options.charisma_max,
            ),
            speed=random.uniform(
                predator_gene_options.speed_min,
                predator_gene_options.speed_max,
            ),
            vision=random.uniform(
                predator_gene_options.vision_min,
                predator_gene_options.vision_max,
            )
        )

        predator = Predator(
            genes=predator_genes,
            position=predator_position,
            hunger=simulation_options.predator_spawn_options.initial_hunger,
            energy=simulation_options.predator_spawn_options.initial_energy,
        )

        initial_predators.append(predator)


    prey_gene_options = simulation_options.prey_gene_options
    initial_prey: list[Prey] = []

    for _ in range(simulation_options.initial_number_of_prey):
        # Spawn the prey at a random position in the world.
        prey_position = generate_random_position_in_world(
            simulation_options.world_width,
            simulation_options.world_height
        )

        # Give the prey uniformly random genes in the configured range.
        prey_genes = PreyGenes(
            fertility=random.uniform(
                prey_gene_options.fertility_min,
                prey_gene_options.fertility_max,
            ),
            charisma=random.uniform(
                prey_gene_options.charisma_min,
                prey_gene_options.charisma_max,
            ),
            speed=random.uniform(
                prey_gene_options.speed_min,
                prey_gene_options.speed_max,
            ),
            vision=random.uniform(
                prey_gene_options.vision_min,
                prey_gene_options.vision_max,
            )
        )

        prey = Prey(
            genes=prey_genes,
            position=prey_position,
            hunger=simulation_options.prey_spawn_options.initial_hunger,
            energy=simulation_options.prey_spawn_options.initial_energy,
        )

        initial_prey.append(prey)


    return SimulationState(
        predators=initial_predators,
        prey=initial_prey
    )


def _run_simulation_for_one_tick(state: SimulationState) -> SimulationState:
    """
    Will perform a single simulation tick. Because we want to track changes,
    **THIS FUNCTION MUST NOT MUTATE `state`**!
    """

    # TODO a single simulation tick

    raise NotImplementedError()


class EcosystemSimulator(SimulatorBackend):
    _options: SimulatorOptions
    _state: SimulationState

    def __init__(self, options_: SimulatorOptions):
        self._options = options_
        self._state = _prepare_initial_simulation_state(self._options)

    def get_simulation_results(self) -> list[SimulationState]:
        # TODO this comes from the SimulationBackend abstract base class and
        #  just has to run the simulation for some number of ticks
        #  (supposedly until the environment collapses or some other max number of ticks)
        raise NotImplementedError()
