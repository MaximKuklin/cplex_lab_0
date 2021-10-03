import os
import cplex
from copy import deepcopy
import itertools
from igraph import Graph
import numpy as np

EPS = 1e-5

def get_graph(path):
    assert path.endswith(".clq")

    with open(path, 'r') as graph:
        data = graph.readlines()

    name = data[0][-1].split(' ')[-1]
    edges = []
    for line in data:
        if line.startswith("p"):
            graph_info = line[:-1].split(' ')
            n, m = graph_info[-2:]
            n, m = int(n), int(m)
        if line.startswith("e"):
            edge = line[:-1].split(' ')[-2:]
            edge = (int(edge[0])-1, int(edge[1])-1)  # to start from 0
            edges.append(edge)

    g = Graph(n=n, edges=edges)

    return n, m, g


def read_files(data_path):
    paths = sorted([os.path.join(data_path, file) for file in os.listdir(data_path) if "brock" in file])
    for path in paths[:1]:
        data = get_graph(path)
    return data

def get_constraint(ind, names, use_ind=True):
    size = len(names)
    if use_ind:
        indexes = list(range(size))
    else:
        indexes = deepcopy(names)
    values = [0] * size
    values[ind[0]] = 1
    values[ind[1]] = 1
    return [indexes, values]


n, m, graph = read_files("/old_ssd/media/data/Projects/magistratura/cplex/data/DIMACS_all_ascii")

names = [f"x{i}" for i in range(0, n)]
obj = [1]*n
lower_bounds = [0]*n
upper_bounds = [1]*n

problem = cplex.Cplex()
problem.objective.set_sense(problem.objective.sense.maximize)
problem.variables.add(obj=obj,
                      lb=lower_bounds,
                      ub=upper_bounds,
                      names=names,
                      types=[problem.variables.type.binary]*len(lower_bounds)
                      )

for i in range(len(obj)):
    problem.variables.set_types(i, problem.variables.type.binary)

inverted = graph.complementer().get_edgelist()

f_e = inverted[0]
first_constraint = get_constraint(f_e, names, use_ind=False)
other_constraints = [get_constraint(edge, names) for edge in inverted[1:]]

constraints = [first_constraint]
constraints.extend(other_constraints)

rhs = [1]*len(constraints)

constraint_senses = ["L"]*len(constraints)
constraint_names = [f"с{i}" for i in range(0, len(constraints))]

problem.linear_constraints.add(lin_expr = constraints,
                               senses = constraint_senses,
                               rhs = rhs,
                               names = constraint_names)


problem.set_log_stream(None)
problem.set_results_stream(None)
problem.solve()

solution = problem.solution.get_values()

print(np.argwhere(np.array(solution) > 1-EPS))
