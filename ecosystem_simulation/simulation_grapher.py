from collections.abc import Callable
from dataclasses import dataclass

import matplotlib.pyplot as plt
from typing import List, Optional

from ecosystem_simulation.simulator import Creature, EcosystemSimulator, EntitySimulationOptions, SimulationOptions


@dataclass(frozen=True)
class GraphOpts:
    title: str
    x_label: str
    y_label: str
    filled: bool
    out_file: str
    tracking_func: Callable[[List[Creature], SimulationOptions, EntitySimulationOptions], Optional[float]]
    plot_prey: bool = True
    plot_pred: bool = True

class SimulationGrapher:
    def __init__(self, simulator: EcosystemSimulator):
        self.simulator = simulator

    def plot(self, num_ticks: int, opts: List[GraphOpts]):

        for opt in opts:
            assert opt.tracking_func is not None


        plt.figure(figsize=(10, 6))

        pred_values = [[] for _ in range(len(opts))]
        prey_values = [[] for _ in range(len(opts))]

        options = self.simulator.options
        for tick in range(num_ticks):
            print(tick)
            state = self.simulator.next_simulation_tick().state
            pred = list(state.predators())
            prey = list(state.prey())
            for i, opt in enumerate(opts):
                pred_values[i].append(opt.tracking_func(pred, options, options.predator))
                prey_values[i].append(opt.tracking_func(prey, options, options.prey))

        timestamps = list(range(num_ticks))

        for i, opt in enumerate(opts):
            plt.title(opt.title)
            plt.xlabel(opt.x_label)
            plt.ylabel(opt.y_label)

            if opt.filled:
                if opt.plot_pred:
                    plt.fill_between(timestamps, pred_values[i], color="red", label="Plenilec", alpha=1.0)
                if opt.plot_prey:
                    plt.fill_between(timestamps, prey_values[i], color="green", label="Plen", alpha=0.4)
            else:
                if opt.plot_pred:
                    plt.plot(timestamps, pred_values[i], 'r-', label="Plenilec")
                if opt.plot_prey:
                    plt.plot(timestamps, prey_values[i], 'g-', label="Plen")

            plt.legend()
            plt.grid(True)
            plt.savefig(opt.out_file, format="pdf", bbox_inches="tight")
            plt.close()

    @staticmethod
    def population(entities: list[Creature], opts: SimulationOptions, entity_opts: EntitySimulationOptions) -> Optional[float]:
        return len(entities)

    @staticmethod
    def appetite(entities: list[Creature], opts: SimulationOptions, entity_opts: EntitySimulationOptions) -> Optional[float]:
        if len(entities) == 0:
            return None
        return sum([x.genes.appetite for x in entities]) / len(entities)

    @staticmethod
    def lifespan(entities: list[Creature], opts: SimulationOptions, entity_opts: EntitySimulationOptions) -> Optional[float]:
        if len(entities) == 0:
            return None
        return sum([x.genes.lifespan  * entity_opts.max_age_in_ticks for x in entities]) / len(entities)

    @staticmethod
    def maturity_age(entities: list[Creature], opts: SimulationOptions, entity_opts: EntitySimulationOptions) -> Optional[float]:
        if len(entities) == 0:
            return None
        return sum([round(x.genes.maturity_age * entity_opts.max_juvenile_in_ticks) for x in entities]) / len(entities)

    @staticmethod
    def gestation_age(entities: list[Creature], opts: SimulationOptions, entity_opts: EntitySimulationOptions) -> Optional[float]:
        if len(entities) == 0:
            return None
        return sum([x.genes.gestation_age * entity_opts.max_gestation_in_ticks for x in entities]) / len(entities)

    @staticmethod
    def speed(entities: list[Creature], opts: SimulationOptions, entity_opts: EntitySimulationOptions) -> Optional[float]:
        if len(entities) == 0:
            return None
        return sum([x.genes.speed for x in entities]) / len(entities)

    @staticmethod
    def num_children(entities: list[Creature], opts: SimulationOptions, entity_opts: EntitySimulationOptions) -> Optional[float]:
        if len(entities) == 0:
            return None
        return sum([round((x.genes.min_children + x.genes.max_children) * 0.5 * entity_opts.max_children_per_birth) for x in entities]) / len(entities)

    @staticmethod
    def vision(entities: list[Creature], opts: SimulationOptions, entity_opts: EntitySimulationOptions) -> Optional[float]:
        if len(entities) == 0:
            return None
        return sum([round(x.genes.vision * opts.max_vision_distance) for x in entities]) / len(entities)

    @staticmethod
    def reproduction_urge(entities: list[Creature], opts: SimulationOptions, entity_opts: EntitySimulationOptions) -> Optional[float]:
        if len(entities) == 0:
            return None
        return sum([x.genes.reproductive_urge_quickness for x in entities]) / len(entities)

    @staticmethod
    def timidity(entities: list[Creature], opts: SimulationOptions, entity_opts: EntitySimulationOptions) -> Optional[float]:
        if len(entities) == 0:
            return None
        return sum([x.genes.timidity for x in entities]) / len(entities)






