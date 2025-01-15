import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from enum import Enum, auto, StrEnum
import matplotlib.pyplot as plot

# Clockwise direction
class Direction(Enum):
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3

class Level(StrEnum):
    LOW = 'low'
    #MEDIUM = 'medium' # Reduced gene complexity
    HIGH = 'high'

class Distance(StrEnum):
    CLOSE = 'close'
    NEAR = 'near'
    FAR = 'far'

class State(Enum):
    FOOD = 0
    IDLE = 1
    REPRODUCTION = 2

WORLD_MAX_DISTANCE = 100
IDLE_SCALE = 0.5


# NOTES:
# how to visualize plots: Antecedent or Consequent call obj.view() and plot.show()
# geni vplivajo na videz klafikacijskega grafa, hrana in zelja po razmnozevanju pa na input vrednost
# 2 pristopa k klasifikaciji: 1. graf posameznega gena predstavlja vpliv lastnosti (gena) na obnasanje pri vhodu dolocene stopnje lakote/zelje po razmnozevanju
#                             2. graf posamezenga gena predstavlja vpliv trenutne lakote/zelje po razmnozevanju na obnasanje, pri vhodu vrednost gena posameznika
# Limit gene linguistic description to two values

# WHAT IS INCLUDED:


# WHAT IS NOT INCLUDED:
           #aggression=random.uniform(0, 1),
           # fertility=random.uniform(0, 1),
           # charisma=random.uniform(0, 1),
           # vision=random.uniform(0, 1),

def main():
    # RANGES#############################################################################
    # Input ranges
    gene_range = np.arange(0, 11)
    #distance_to_prey_range = np.arange(0, WORLD_MAX_DISTANCE)


    # Output ranges
    #direction_range = np.arange(0, 4)
    state_range = np.arange(0, 7)

    # CLASSIFICATION ###################################################################

    # Input
    aggression = ctrl.Antecedent(gene_range, 'aggression')
    fertility = ctrl.Antecedent(gene_range, 'fertility')
    charisma = ctrl.Antecedent(gene_range, 'charisma')
    #distance_to_prey = ctrl.Antecedent(distance_to_prey_range, 'distance_to_prey')

    # Output
    #direction = ctrl.Consequent(direction_range, 'direction')
    state = ctrl.Consequent(state_range, 'state')

    #
    aggression[Level.LOW] = fuzz.trimf(aggression.universe, [0, 0, 5])
    aggression[Level.HIGH] = fuzz.trimf(aggression.universe, [5, 10, 10])

    fertility[Level.LOW] = fuzz.trimf(fertility.universe, [0, 0, 5])
    fertility[Level.HIGH] = fuzz.trimf(fertility.universe, [5, 10, 10])

    charisma[Level.LOW] = fuzz.trimf(charisma.universe, [0, 0, 5])
    charisma[Level.HIGH] = fuzz.trimf(charisma.universe, [5, 10, 10])

    #

    #distance_to_prey.view()
    #plot.show()2

    state[State.FOOD] = fuzz.trimf(state.universe, [0, 0, 3])
    # Idle shape is scaled down to reduce the likelihood of character being in idle mode
    state[State.IDLE] = IDLE_SCALE * fuzz.trapmf(state.universe, [1, 2, 4, 5])
    state[State.REPRODUCTION] = fuzz.trimf(state.universe, [3, 6, 6])

    # RULES ###########################################################################

    rules = [ctrl.Rule(aggression[Level.LOW] & fertility[Level.LOW], state[State.IDLE]),
             ctrl.Rule(aggression[Level.HIGH], state[State.FOOD]),
             ctrl.Rule(charisma[Level.LOW], state[State.REPRODUCTION])]

    # FUZZY INFERENCE SYSTEM ###########################################################

    state_ctrl = ctrl.ControlSystem(rules)
    state_sim = ctrl.ControlSystemSimulation(state_ctrl)

    #rules[0].view()
    #plot.show()

    # FUZZYFICATION #########################################################################
    state_sim.input['aggression'] = 0.7 * 10
    state_sim.input['fertility'] = 0.1 * 10
    state_sim.input['charisma'] = 0.4 * 10
    #can use inputs to add dict

    state_sim.compute()
    print(state_sim.output['state'])
    state.view(sim=state_sim)
    plot.show()

    # OUTPUT STATE #################################################################################

    output_state_num = round(state_sim.output['state'] / 2)
    output_state = State(output_state_num)
    print(f"OUTPUT STATE: {output_state.name}")

    # DEFUZZIFICATION (probably not needed)
    ''''# Obtain aggregated output from the simulation
    aggregated_output = cost_benefit_sim.output['cost_benefit']

    # Convert aggregated_output to a numpy array
    aggregated_output = np.asarray(aggregated_output)

    # Define universe of discourse (range) for cost_benefit (output)
    cost_benefit_range = np.arange(0, 11, 1)[:aggregated_output.size]

    # Centroid defuzzification
    defuzzified_output = fuzz.defuzz(cost_benefit_range, aggregated_output, 'centroid')

    print("Defuzzified output:", defuzzified_output)'''

    pass


if __name__ == '__main__':
    main()

