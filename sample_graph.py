from ecosystem_simulation.simulation_grapher import SimulationGrapher, GraphOpts
from ecosystem_simulation.simulation_player import *


def main():
    opts: SimulationOptions = SimulationOptions.from_json_file("optimization_results/best_2.json")
    simulator = EcosystemSimulator(
        options_=opts,
    )

    grapher = SimulationGrapher(simulator=simulator)

    graphs = [
        GraphOpts(
            title="Ecosystem Population",
            x_label="Tick",
            y_label="Population",
            filled=True,
            out_file="graphs/sim_population.pdf",
            tracking_func=SimulationGrapher.population,
        ),
        GraphOpts(
            title="Ecosystem Appetite/Aggressiveness",
            x_label="Tick",
            y_label="Appetite/Aggressiveness",
            filled=False,
            out_file="graphs/sim_appetite.pdf",
            tracking_func=SimulationGrapher.appetite,
        ),

        GraphOpts(
            title="Ecosystem Lifespan Gene",
            x_label="Tick",
            y_label="Lifespan",
            filled=False,
            out_file="graphs/sim_lifespan.pdf",
            tracking_func=SimulationGrapher.lifespan,
        ),

        GraphOpts(
            title="Ecosystem Maturity Age Gene",
            x_label="Tick",
            y_label="Maturity Age",
            filled=False,
            out_file="graphs/sim_maturity_age.pdf",
            tracking_func=SimulationGrapher.maturity_age,
        ),

        GraphOpts(
            title="Ecosystem Gestation Age Gene",
            x_label="Tick",
            y_label="Gestation Age",
            filled=False,
            out_file="graphs/sim_gestation_age.pdf",
            tracking_func=SimulationGrapher.gestation_age,
        ),

        GraphOpts(
            title="Ecosystem Speed Gene",
            x_label="Tick",
            y_label="Gestation Age",
            filled=False,
            out_file="graphs/sim_speed.pdf",
            tracking_func=SimulationGrapher.speed,
        ),

        GraphOpts(
            title="Ecosystem Children Gene",
            x_label="Tick",
            y_label="Children",
            filled=False,
            out_file="graphs/sim_children.pdf",
            tracking_func=SimulationGrapher.num_children,
        ),

        GraphOpts(
            title="Ecosystem Vision Gene",
            x_label="Tick",
            y_label="Vision",
            filled=False,
            out_file="graphs/sim_vision.pdf",
            tracking_func=SimulationGrapher.vision,
        ),

        GraphOpts(
            title="Ecosystem Reproductive Urge Gene",
            x_label="Tick",
            y_label="Reproductive Urge",
            filled=False,
            out_file="graphs/sim_reproductive_urge.pdf",
            tracking_func=SimulationGrapher.reproduction_urge,
        ),

        GraphOpts(
            title="Ecosystem Timidity Gene",
            x_label="Tick",
            y_label="Timidity",
            filled=False,
            out_file="graphs/sim_timidity.pdf",
            tracking_func=SimulationGrapher.timidity,
            plot_pred=False, # Only relevant for prey
        ),

    ]

    grapher.plot(1720, graphs)


if __name__ == '__main__':
    main()
