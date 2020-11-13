from fractions import Fraction
from warnings import warn


class Simplex(object):
    def __init__(self, num_vars, constraints, objective_function):
       
        self.num_vars = num_vars
        self.constraints = constraints
        self.objective = objective_function[0]
        self.objective_function = objective_function[1]
        self.coefficients, self.r_rows, self.num_s_vars, self.num_r_vars = self.create_using_constraints()
        del self.constraints
        self.basic_vars = [0 for i in range(len(self.coefficients))]
        self.phase1()
        r_index = self.num_r_vars + self.num_s_vars

        for i in self.basic_vars:
            if i > r_index:
                raise ValueError("not optimal solution")

        self.delete_r_vars()

        if 'min' in self.objective.lower():
            self.solution = self.objective_minimize()

        else:
            self.solution = self.objective_maximize()
        self.optimize_val = self.coefficients[0][-1]

    def create_using_constraints(self):
        num_s_vars = 0  # number of slack and surplus variables
        num_r_vars = 0  # number of additional variables to balance equality and less than equal to
        for expression in self.constraints:
            if '>=' in expression:
                num_s_vars += 1

            elif '<=' in expression:
                num_s_vars += 1
                num_r_vars += 1

            elif '=' in expression:
                num_r_vars += 1
        total_vars = self.num_vars + num_s_vars + num_r_vars

        coefficients = [[Fraction("0/1") for i in range(total_vars+1)] for j in range(len(self.constraints)+1)]
        s_index = self.num_vars
        r_index = self.num_vars + num_s_vars
        r_rows = [] # stores the non -zero index of r
        for i in range(1, len(self.constraints)+1):
            constraint = self.constraints[i-1].split(' ')

            for j in range(len(constraint)):

                if '_' in constraint[j]:
                    coeff, index = constraint[j].split('_')
                    if constraint[j-1] is '-':
                        coefficients[i][int(index)-1] = Fraction("-" + coeff[:-1] + "/1")
                    else:
                        coefficients[i][int(index)-1] = Fraction(coeff[:-1] + "/1")

                elif constraint[j] == '<=':
                    coefficients[i][s_index] = Fraction("1/1")  # add surplus variable
                    s_index += 1

                elif constraint[j] == '>=':
                    coefficients[i][s_index] = Fraction("-1/1")  # slack variable
                    coefficients[i][r_index] = Fraction("1/1")   # r variable
                    s_index += 1
                    r_index += 1
                    r_rows.append(i)

                elif constraint[j] == '=':
                    coefficients[i][r_index] = Fraction("1/1")  # r variable
                    r_index += 1
                    r_rows.append(i)

            coefficients[i][-1] = Fraction(constraint[-1] + "/1")

        return coefficients, r_rows, num_s_vars, num_r_vars

    def phase1(self):
        
        r_index = self.num_vars + self.num_s_vars
        for i in range(r_index, len(self.coefficients[0])-1):
            self.coefficients[0][i] = Fraction("-1/1")
        coeff_0 = 0
        for i in self.r_rows:
            self.coefficients[0] = add_row(self.coefficients[0], self.coefficients[i])
            self.basic_vars[i] = r_index
            r_index += 1
        s_index = self.num_vars
        for i in range(1, len(self.basic_vars)):
            if self.basic_vars[i] == 0:
                self.basic_vars[i] = s_index
                s_index += 1

        key_column = max_index(self.coefficients[0])
        condition = self.coefficients[0][key_column] > 0

        while condition is True:

            key_row = self.find_row(key_column = key_column)
            self.basic_vars[key_row] = key_column
            pivot = self.coefficients[key_row][key_column]
            self.find_pivot(key_row, pivot)
            self.make_key_column_zero(key_column, key_row)

            key_column = max_index(self.coefficients[0])
            condition = self.coefficients[0][key_column] > 0

    def find_row(self, key_column):
        min_val = float("inf")
        min_i = 0
        for i in range(1, len(self.coefficients)):
            if self.coefficients[i][key_column] > 0:
                val = self.coefficients[i][-1] / self.coefficients[i][key_column]
                if val <  min_val:
                    min_val = val
                    min_i = i
        if min_val == float("inf"):
            raise ValueError("Unbounded solution")
        if min_val == 0:
            warn("Dengeneracy")
        return min_i

    def find_pivot(self, key_row, pivot):
        for i in range(len(self.coefficients[0])):
            self.coefficients[key_row][i] /= pivot

    def make_key_column_zero(self, key_column, key_row):
        num_columns = len(self.coefficients[0])
        for i in range(len(self.coefficients)):
            if i != key_row:
                factor = self.coefficients[i][key_column]
                for j in range(num_columns):
                    self.coefficients[i][j] -= self.coefficients[key_row][j] * factor

    def delete_r_vars(self):
        for i in range(len(self.coefficients)):
            non_r_length = self.num_vars + self.num_s_vars + 1
            length = len(self.coefficients[i])
            while length != non_r_length:
                del self.coefficients[i][non_r_length-1]
                length -= 1

    def update_objective_function(self):
        objective_function_coeffs = self.objective_function.split()
        for i in range(len(objective_function_coeffs)):
            if '_' in objective_function_coeffs[i]:
                coeff, index = objective_function_coeffs[i].split('_')
                if objective_function_coeffs[i-1] is '-':
                    self.coefficients[0][int(index)-1] = Fraction(coeff[:-1] + "/1")
                else:
                    self.coefficients[0][int(index)-1] = Fraction("-" + coeff[:-1] + "/1")

    def check_alternate_solution(self):
        for i in range(len(self.coefficients[0])):
            if self.coefficients[0][i] and i not in self.basic_vars[1:]:
                warn("Alternate Solution exists")
                break

    def objective_minimize(self):
        self.update_objective_function()

        for row, column in enumerate(self.basic_vars[1:]):
            if self.coefficients[0][column] != 0:
                self.coefficients[0] = add_row(self.coefficients[0], multiply_const_row(-self.coefficients[0][column], self.coefficients[row+1]))

        key_column = max_index(self.coefficients[0])
        condition = self.coefficients[0][key_column] > 0

        while condition is True:

            key_row = self.find_row(key_column = key_column)
            self.basic_vars[key_row] = key_column
            pivot = self.coefficients[key_row][key_column]
            self.find_pivot(key_row, pivot)
            self.make_key_column_zero(key_column, key_row)

            key_column = max_index(self.coefficients[0])
            condition = self.coefficients[0][key_column] > 0

        solution = {}
        for i, var in enumerate(self.basic_vars[1:]):
            if var < self.num_vars:
                solution['x_'+str(var+1)] = self.coefficients[i+1][-1]

        for i in range(0, self.num_vars):
            if i not in self.basic_vars[1:]:
                solution['x_'+str(i+1)] = Fraction("0/1")
        self.check_alternate_solution()
        return solution

    def objective_maximize(self):
        self.update_objective_function()

        for row, column in enumerate(self.basic_vars[1:]):
            if self.coefficients[0][column] != 0:
                self.coefficients[0] = add_row(self.coefficients[0], multiply_const_row(-self.coefficients[0][column], self.coefficients[row+1]))

        key_column = min_index(self.coefficients[0])
        condition = self.coefficients[0][key_column] < 0

        while condition is True:

            key_row = self.find_row(key_column = key_column)
            self.basic_vars[key_row] = key_column
            pivot = self.coefficients[key_row][key_column]
            self.find_pivot(key_row, pivot)
            self.make_key_column_zero(key_column, key_row)

            key_column = min_index(self.coefficients[0])
            condition = self.coefficients[0][key_column] < 0

        solution = {}
        for i, var in enumerate(self.basic_vars[1:]):
            if var < self.num_vars:
                solution['x_'+str(var+1)] = self.coefficients[i+1][-1]

        for i in range(0, self.num_vars):
            if i not in self.basic_vars[1:]:
                solution['x_'+str(i+1)] = Fraction("0/1")

        self.check_alternate_solution()

        return solution

def add_row(row1, row2):
    row_sum = [0 for i in range(len(row1))]
    for i in range(len(row1)):
        row_sum[i] = row1[i] + row2[i]
    return row_sum

def max_index(row):
    max_i = 0
    for i in range(0, len(row)-1):
        if row[i] > row[max_i]:
            max_i = i

    return max_i

def multiply_const_row(const, row):
    mul_row = []
    for i in row:
        mul_row.append(const*i)
    return mul_row

def min_index(row):
    min_i = 0
    for i in range(0, len(row)):
        if row[min_i] > row[i]:
            min_i = i

    return min_i

