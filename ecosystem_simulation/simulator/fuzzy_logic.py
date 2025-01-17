import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from enum import Enum, StrEnum
import matplotlib.pyplot as plot
import matplotlib
from dataclasses import dataclass, fields
from skfuzzy.control import Antecedent, Consequent
from sys import maxsize

from ecosystem_simulation.simulator.models.creature import Creature, Predator, Prey

#matplotlib.rcParams['figure.dpi'] = 200  # Use this to upscale plots (for hidpi screens)


@dataclass(slots=True)
class FuzzyGenes:
    """
    The fuzzy genes follow genes from ordinary logic structure.
    """
    appetite: Antecedent
    lifespan: Antecedent
    maturity_age: Antecedent
    gestation_age: Antecedent
    speed: Antecedent
    min_children: Antecedent
    max_children: Antecedent
    vision: Antecedent
    reproductive_urge_quickness: Antecedent
    timidity: Antecedent

class Label(StrEnum):
    APPETITE='appetite'
    LIFESPAN='lifespan'
    MATURITY_AGE='maturity_age'
    GESTATION_AGE='gestation_age'
    SPEED='speed'
    MIN_CHILDREN='min_children'
    MAX_CHILDREN='max_children'
    VISION='vision'
    REPRODUCTIVE_URGE_QUICKNESS='reproductive_urge_quickness'
    TIMIDITY='timidity'

    SATIATION='satiation'
    REPRODUCTIVE_URGE='reproductive_urge'
    DISTANCE_MATE='distance_mate'
    DISTANCE_FOOD='distance_food'
    PREGNANCY='pregnancy'
    MATURITY='maturity'

    STATE='state'

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
    FAR = 'far'
    OUT_OF_RANGE = 'out_of_range'

class State(Enum):
    FOOD = 0
    IDLE = 1
    REPRODUCTION = 2

IDLE_STATE_SCALE = 0.2
GENE_SCALE = 0.1  # Genes are less impactful than other attributes like satiation
DISTANCE_SCALE = 0.8
standard_range = np.arange(0, 11)

def determine_state_fuzzy(creature: Creature, vision: int, food_distance: float, mate_distance: float) -> State:
    # RANGES#############################################################################
    distance_range = np.arange(0, 21)  # An extended range to cover OUT_OF_RANGE

    # Output range - two times the number of states (to easier construct graphical representation)
    output_state_range = np.arange(0, 7)

    # CLASSIFICATION ###################################################################
    genes = FuzzyGenes(appetite=Antecedent(standard_range, Label.APPETITE),
                       lifespan=Antecedent(standard_range, Label.LIFESPAN),
                       maturity_age=Antecedent(standard_range, Label.MATURITY_AGE),
                       gestation_age=Antecedent(standard_range, Label.GESTATION_AGE),
                       speed=Antecedent(standard_range, Label.SPEED),
                       min_children=Antecedent(standard_range, Label.MIN_CHILDREN),
                       max_children=Antecedent(standard_range, Label.MAX_CHILDREN),
                       vision=Antecedent(standard_range, Label.VISION),
                       reproductive_urge_quickness=Antecedent(standard_range, Label.REPRODUCTIVE_URGE_QUICKNESS),
                       timidity=Antecedent(standard_range, Label.TIMIDITY)
                       )

    # Other attributes
    satiation = Antecedent(standard_range, Label.SATIATION)
    reproductive_urge = Antecedent(standard_range, Label.REPRODUCTIVE_URGE)
    distance_mate = Antecedent(distance_range, Label.DISTANCE_MATE)
    distance_food = Antecedent(distance_range, Label.DISTANCE_FOOD)
    pregnancy = Antecedent(standard_range, Label.PREGNANCY)
    maturity = Antecedent(standard_range, Label.MATURITY)

    # Output
    state = Consequent(output_state_range, Label.STATE)

    lower_triangle_shape = [0, 0, 5]
    upper_triangle_shape = [5, 10, 10]

    # All gene (and other attributes except for distance) graphical representation
    # is the same with two triangles to form a "V" position
    for gene in fields(genes):
        getattr(genes, gene.name)[Level.LOW] = fuzz.trimf(getattr(genes, gene.name).universe, lower_triangle_shape) * GENE_SCALE
        getattr(genes, gene.name)[Level.HIGH] = fuzz.trimf(getattr(genes, gene.name).universe, upper_triangle_shape) * GENE_SCALE

    satiation[Level.LOW] = fuzz.trimf(satiation.universe, lower_triangle_shape)
    satiation[Level.HIGH] = fuzz.trimf(satiation.universe, upper_triangle_shape)

    reproductive_urge[Level.LOW] = fuzz.trimf(reproductive_urge.universe, lower_triangle_shape)
    reproductive_urge[Level.HIGH] = fuzz.trimf(reproductive_urge.universe, upper_triangle_shape)

    distance_food[Distance.CLOSE] = fuzz.trimf(distance_food.universe, [0, 0, 10]) * DISTANCE_SCALE
    distance_food[Distance.FAR] = fuzz.trimf(distance_food.universe, [0, 10, 10]) * DISTANCE_SCALE
    distance_food[Distance.OUT_OF_RANGE] = fuzz.trapmf(distance_food.universe, [11, 11, 20, 20])

    distance_mate[Distance.CLOSE] = fuzz.trimf(distance_mate.universe, [0, 0, 10]) * DISTANCE_SCALE
    distance_mate[Distance.FAR] = fuzz.trimf(distance_mate.universe, [0, 10, 10]) * DISTANCE_SCALE
    distance_mate[Distance.OUT_OF_RANGE] = fuzz.trapmf(distance_mate.universe, [11, 11, 20, 20])

    # Pregnancy and maturity are both boolean variables so only the lowest and highest value will be needed
    pregnancy[Level.LOW] = fuzz.trimf(pregnancy.universe, lower_triangle_shape)
    pregnancy[Level.HIGH] = fuzz.trimf(pregnancy.universe, upper_triangle_shape)

    maturity[Level.LOW] = fuzz.trimf(maturity.universe, lower_triangle_shape)
    maturity[Level.HIGH] = fuzz.trimf(maturity.universe, upper_triangle_shape)

    state[State.FOOD.name] = fuzz.trimf(state.universe, [0, 0, 3])
    # Idle shape is scaled down to reduce the likelihood of character being in idle mode
    state[State.IDLE.name] = IDLE_STATE_SCALE * fuzz.trimf(state.universe, [2, 3, 4])
    state[State.REPRODUCTION.name] = fuzz.trimf(state.universe, [3, 6, 6])

    # RULES ###########################################################################
    # Note: all inputs have to be used to avoid error

    rules = [
        # Main rules for FOOD and REPRODUCTION states
        ctrl.Rule((satiation[Level.LOW] & reproductive_urge[Level.LOW]) | maturity[Level.LOW] | pregnancy[Level.HIGH], state[State.FOOD.name]),
        ctrl.Rule(reproductive_urge[Level.HIGH] & maturity[Level.HIGH] & satiation[Level.HIGH], state[State.REPRODUCTION.name]),

        # Rules for targets' distances
        ctrl.Rule(distance_mate[Distance.CLOSE] & maturity[Level.HIGH] & pregnancy[Level.LOW], state[State.REPRODUCTION.name]),
        ctrl.Rule(distance_mate[Distance.OUT_OF_RANGE] & distance_food[Distance.OUT_OF_RANGE], state[State.IDLE.name]),
        ctrl.Rule(distance_food[Distance.CLOSE], state[State.FOOD.name]),
        ctrl.Rule(distance_food[Distance.OUT_OF_RANGE] & satiation[Level.HIGH], state[State.IDLE.name]),
        ctrl.Rule(distance_mate[Distance.OUT_OF_RANGE] & reproductive_urge[Level.LOW], state[State.IDLE.name]),
        ctrl.Rule(distance_food[Distance.FAR] & distance_mate[Distance.CLOSE] & maturity[Level.HIGH] & pregnancy[Level.LOW], state[State.REPRODUCTION.name]),
        ctrl.Rule(distance_mate[Distance.FAR] & distance_food[Distance.CLOSE], state[State.FOOD.name]),

        # Less impactful genes' rules
        ctrl.Rule(genes.appetite[Level.HIGH], state[State.FOOD.name]),
        ctrl.Rule(genes.reproductive_urge_quickness[Level.HIGH], state[State.REPRODUCTION.name]),
        ctrl.Rule(genes.lifespan[Level.HIGH], state[State.FOOD.name]),
        ctrl.Rule(genes.lifespan[Level.LOW], state[State.REPRODUCTION.name]),
        ctrl.Rule(genes.maturity_age[Level.HIGH], state[State.IDLE.name]),
        ctrl.Rule(genes.gestation_age[Level.HIGH], state[State.FOOD.name]),
        ctrl.Rule(genes.speed[Level.LOW], state[State.IDLE.name]),
        ctrl.Rule(genes.min_children[Level.HIGH], state[State.FOOD.name]),
        ctrl.Rule(genes.max_children[Level.LOW], state[State.REPRODUCTION.name]),
        ctrl.Rule(genes.vision[Level.LOW], state[State.REPRODUCTION.name]),
        ctrl.Rule(genes.timidity[Level.HIGH], state[State.IDLE.name]),
    ]

    # FUZZY INFERENCE SYSTEM ###########################################################
    state_ctrl = ctrl.ControlSystem(rules)
    state_sim = ctrl.ControlSystemSimulation(state_ctrl)

    # FUZZYFICATION #########################################################################

    # It the target is too far away set the distance to 15
    if food_distance != 0:
        food_distance = (food_distance / vision) * 10 if food_distance < maxsize else 15

    if mate_distance != 0:
        mate_distance = (mate_distance / vision) * 10 if mate_distance < maxsize else 15

    state_sim.inputs({
        Label.APPETITE: creature.genes.appetite * 10,
        Label.LIFESPAN: creature.genes.lifespan * 10,
        Label.MATURITY_AGE: creature.genes.maturity_age * 10,
        Label.GESTATION_AGE: creature.genes.gestation_age * 10,
        Label.SPEED: creature.genes.speed * 10,
        Label.MIN_CHILDREN: creature.genes.min_children * 10,
        Label.MAX_CHILDREN: creature.genes.max_children * 10,
        Label.VISION: creature.genes.vision * 10,
        Label.REPRODUCTIVE_URGE_QUICKNESS: creature.genes.reproductive_urge_quickness * 10,
        Label.TIMIDITY: creature.genes.timidity * 10,

        Label.SATIATION: creature.satiation * 10,
        Label.REPRODUCTIVE_URGE: creature.reproductive_urge * 10,
        Label.DISTANCE_FOOD: food_distance,
        Label.DISTANCE_MATE: mate_distance,
        Label.PREGNANCY: 10 if creature.pregnant else 0,
        Label.MATURITY: 10 if creature.mature else 0,
    })

    # Compute output with centroid method
    state_sim.compute()

    # OUTPUT STATE #################################################################################

    output_state_num = state_sim.output[Label.STATE] / 3
    # We should avoid Idle state, so it is smaller than other states
    if output_state_num < 0.8:
        output_state = State.FOOD
    elif output_state_num > 1.2:
        output_state = State.REPRODUCTION
    else:
        output_state = State.IDLE

    #output_state = State(output_state_num)
    #if isinstance(creature, Predator):
    #    print(f"OUTPUT STATE of predator {creature.id}: {output_state.name}")
    #else:
    #    print(f"OUTPUT STATE of prey {creature.id}: {output_state.name}")

    # Plot the result
    #state.view(sim=state_sim)
    #plot.show()

    return output_state
