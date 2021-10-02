import os
import cplex
from copy import deepcopy
import itertools
from igraph import Graph
import numpy as np


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
    paths = [os.path.join(data_path, file) for file in os.listdir(data_path) if "brock" in file]
    for path in paths[:1]:
        data = get_graph(path)
        print(data)
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
                      names=names)

# graph_matrix = np.array(graph.get_adjacency().data)
# inverted = np.where(graph_matrix==1, 0, 1)

# comb = list(itertools.combinations(names, 2))
# inverted = set(itertools.combinations(range(200), 2)) - set(graph.get_edgelist())
# inverted = list(inverted)

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

problem.set_problem_type(problem.problem_type.LP)
problem.solve()

print(problem.solution.get_values())

