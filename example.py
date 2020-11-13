from solution import Simplex
objective = ('maximize', '3x_1 + 5x_2')
constraints = ['1x_1 <= 4', '2x_2 <= 12', '3x_1 + 2x_2 <= 18']
Lp_system = Simplex(num_vars=2, constraints=constraints, objective_function=objective)
print(Lp_system.solution)
print(Lp_system.optimize_val)