import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# Define universe of discourse (range) for cost and benefit
cost_range = np.arange(0, 11, 1)
benefit_range = np.arange(0, 11, 1)

# Define linguistic variables: cost, benefit, and cost_benefit
cost = ctrl.Antecedent(cost_range, 'cost')
benefit = ctrl.Antecedent(benefit_range, 'benefit')
cost_benefit = ctrl.Consequent(np.arange(0, 11, 1), 'cost_benefit')

# Define membership functions for cost
cost['low'] = fuzz.trimf(cost_range, [0, 0, 5])
cost['high'] = fuzz.trimf(cost_range, [5, 10, 10])

# Define membership functions for benefit
benefit['low'] = fuzz.trimf(benefit_range, [0, 0, 5])
benefit['high'] = fuzz.trimf(benefit_range, [5, 10, 10])

# Define membership functions for cost_benefit (output)
cost_benefit['low'] = fuzz.trimf(np.arange(0, 11, 1), [0, 0, 3])
cost_benefit['medium'] = fuzz.trimf(np.arange(0, 11, 1), [2, 5, 8])
cost_benefit['high'] = fuzz.trimf(np.arange(0, 11, 1), [7, 10, 10])

# Define fuzzy rules
rule1 = ctrl.Rule(cost['low'] & benefit['high'], cost_benefit['high'])
rule2 = ctrl.Rule(cost['high'] & benefit['high'], cost_benefit['medium'])
rule3 = ctrl.Rule(cost['low'] & benefit['low'], cost_benefit['low'])
rule4 = ctrl.Rule(cost['high'] & benefit['low'], cost_benefit['low'])

# Create fuzzy control system
cost_benefit_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4])
cost_benefit_sim = ctrl.ControlSystemSimulation(cost_benefit_ctrl)

# Fuzzification: Provide input values
cost_benefit_sim.input['cost'] = 3  # low cost
cost_benefit_sim.input['benefit'] = 8  # high benefit

# Apply fuzzy rules
cost_benefit_sim.compute()

# Defuzzification: Obtain crisp output
result = cost_benefit_sim.output['cost_benefit']
print("Crisp output:", result)
# Crisp output: 8.775


# Obtain aggregated output from the simulation
aggregated_output = cost_benefit_sim.output['cost_benefit']

# Convert aggregated_output to a numpy array
aggregated_output = np.asarray(aggregated_output)

# Define universe of discourse (range) for cost_benefit (output)
cost_benefit_range = np.arange(0, 11, 1)[:aggregated_output.size]

# Centroid defuzzification
defuzzified_output = fuzz.defuzz(cost_benefit_range, aggregated_output, 'centroid')

print("Defuzzified output:", defuzzified_output)
