import argparse
import os
import cplex
from copy import deepcopy
import itertools
from igraph import Graph
import numpy as np
from time import time

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


def read_file(data_path):
    data = get_graph(data_path)
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

if __name__ == '__main__':

    args = argparse.ArgumentParser('Solve lp or ilp problem')
    args.add_argument('-p', '--path', required=True, help='Path to file DIMACS file')
    args.add_argument('-t', '--type', required=True, choices=["ILP", "LP"])
    args = args.parse_args()

    mode = args.type
    path = args.path

    n, m, graph = read_file(path)

    names = [f"x{i}" for i in range(0, n)]
    if mode == "ILP":
        obj, lower_bounds, upper_bounds = [1]*n, [0]*n, [1]*n
    else:
        obj, lower_bounds, upper_bounds = [1.0]*n, [0.0]*n, [1.0]*n

    problem = cplex.Cplex()
    problem.objective.set_sense(problem.objective.sense.maximize)
    problem.variables.add(obj=obj,
                          lb=lower_bounds,
                          ub=upper_bounds,
                          names=names,
                          )

    if mode == "ILP":
        for i in range(len(obj)):
            problem.variables.set_types(i, problem.variables.type.binary)

    inverted = graph.complementer().get_edgelist()

    f_e = inverted[0]
    first_constraint = get_constraint(f_e, names, use_ind=False)
    other_constraints = [get_constraint(edge, names) for edge in inverted[1:]]

    constraints = [first_constraint]
    constraints.extend(other_constraints)

    if mode == "ILP":
        rhs = [1]*len(constraints)
    else:
        rhs = [1.0]*len(constraints)

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
