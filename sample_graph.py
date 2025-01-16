from ecosystem_simulation.simulation_grapher import SimulationGrapher, GraphOpts
from ecosystem_simulation.simulation_player import *


def main():
    opts: SimulationOptions = SimulationOptions.from_json_file("optimization_results/best_20250116-224426_5000.json")
    simulator = EcosystemSimulator(
        options_=opts,
    )

    grapher = SimulationGrapher(simulator=simulator)

    graphs = [
        GraphOpts(
            title="Populacija ekosistema",
            x_label="Korak",
            y_label="Populacija",
            filled=True,
            out_file="graphs/sim_population.pdf",
            tracking_func=SimulationGrapher.population,
        ),
        GraphOpts(
            title="Apetit/Agresivnost ekosistema",
            x_label="Korak",
            y_label="Apetit/Agresivnost",
            filled=False,
            out_file="graphs/sim_appetite.pdf",
            tracking_func=SimulationGrapher.appetite,
        ),

        GraphOpts(
            title="Gen življenske dobe",
            x_label="Korak",
            y_label="Trajanje življenske dobe",
            filled=False,
            out_file="graphs/sim_lifespan.pdf",
            tracking_func=SimulationGrapher.lifespan,
        ),

        GraphOpts(
            title="Gen dozorelosti",
            x_label="Korak",
            y_label="Mladostno trajanje",
            filled=False,
            out_file="graphs/sim_maturity_age.pdf",
            tracking_func=SimulationGrapher.maturity_age,
        ),

        GraphOpts(
            title="Gen nosečnosti",
            x_label="Korak",
            y_label="Trajanje nosečnosti",
            filled=False,
            out_file="graphs/sim_gestation_age.pdf",
            tracking_func=SimulationGrapher.gestation_age,
        ),

        GraphOpts(
            title="Gen hitrosti",
            x_label="Korak",
            y_label="Hitrost",
            filled=False,
            out_file="graphs/sim_speed.pdf",
            tracking_func=SimulationGrapher.speed,
        ),

        GraphOpts(
            title="Gen plodnosti",
            x_label="Korak",
            y_label="Povprečno št. otrok",
            filled=False,
            out_file="graphs/sim_children.pdf",
            tracking_func=SimulationGrapher.num_children,
        ),

        GraphOpts(
            title="Gen za vid",
            x_label="Korak",
            y_label="Vid (polja)",
            filled=False,
            out_file="graphs/sim_vision.pdf",
            tracking_func=SimulationGrapher.vision,
        ),

        GraphOpts(
            title="Gen za reproduktivno željo",
            x_label="Korak",
            y_label="Reproduktivna želja",
            filled=False,
            out_file="graphs/sim_reproductive_urge.pdf",
            tracking_func=SimulationGrapher.reproduction_urge,
        ),

        GraphOpts(
            title="Gen preplašenosti",
            x_label="Korak",
            y_label="Preplašenost",
            filled=False,
            out_file="graphs/sim_timidity.pdf",
            tracking_func=SimulationGrapher.timidity,
            plot_pred=False, # Only relevant for prey
        ),

    ]

    grapher.plot(5000, graphs)


if __name__ == '__main__':
    main()
