from typing import Dict, Optional
import sys

import matplotlib.pyplot as plt
import vrplib
import numpy as np

from pyvrp import (
    GeneticAlgorithm,
    GeneticAlgorithmParams,
    Solution,
    PenaltyManager,
    Population,
    PopulationParams,
    ProblemData,
    Result,
    XorShift128,
    plotting,
    read,
)
from pyvrp.crossover import selective_route_exchange as srex
from pyvrp.diversity import broken_pairs_distance as bpd
from pyvrp.search import (
    NODE_OPERATORS,
    ROUTE_OPERATORS,
    LocalSearch,
    NeighbourhoodParams,
    compute_neighbours,
)
from pyvrp.stop import MaxIterations, MaxRuntime

# instance = read("/Users/e550705/workspaces/PyVRP/examples/data/X-n439-k37.vrp", round_func="round")
# instance = read("/Users/e550705/workspaces/PyVRP/examples/data/outbound.vrp", round_func="round")
# instance = read("/Users/e550705/workspaces/PyVRP/examples/data/outbound_time.vrp", round_func="round")
# instance = read("/Users/e550705/workspaces/PyVRP/examples/data/outbound_distance.vrp", round_func="round")
# instance = read("/Users/e550705/workspaces/PyVRP/examples/data/outbound_distance_new.vrp", round_func="round")
# instance = read("/Users/e550705/workspaces/PyVRP/examples/data/outbound_time_new.vrp", round_func="round")

instance = read(sys.argv[1])

salvage = {}
for c in np.arange(instance.num_clients):
    salvage[c] = instance.client(c).demandSalvage

# fig = plt.figure(figsize=(15, 9))
# gs = fig.add_gridspec(2, 4, width_ratios=(2 / 5, 2 / 5, 3 / 5, 4 / 5))

# ax1 = fig.add_subplot(gs[:, 0])
# plotting.plot_demands(instance, 'weight', ax=ax1)
# ax1.set_title('Weight Demands')

# ax2 = fig.add_subplot(gs[:, 1])
# plotting.plot_demands(instance, 'volume', ax=ax2)
# ax2.set_title('Volume Demands')

# ax3 = fig.add_subplot(gs[:, 2])
# plotting.plot_demands(instance, 'salvage', ax=ax3)
# ax3.set_title('Salvage Demands')

# plotting.plot_coordinates(instance, ax=fig.add_subplot(gs[:, 3]))

# plt.tight_layout()
# plt.show()

def solve(
    data: ProblemData,
    seed: int,
    max_runtime: Optional[float] = None,
    max_iterations: Optional[int] = None,
    **kwargs,
):
    rng = XorShift128(seed=seed)
    pen_manager = PenaltyManager()

    pop_params = PopulationParams()
    pop = Population(bpd, params=pop_params)

    nb_params = NeighbourhoodParams(nb_granular=20)
    neighbours = compute_neighbours(data, nb_params)
    ls = LocalSearch(data, rng, neighbours)

    for op in NODE_OPERATORS:
        # print(f"Adding Node operator: {op}")
        ls.add_node_operator(op(data))

    for op in ROUTE_OPERATORS:
        # print(f"Adding Route operator: {op}")
        ls.add_route_operator(op(data))

    init = [
        Solution.make_random(data, rng) for _ in range(pop_params.min_pop_size)
    ]
    ga_params = GeneticAlgorithmParams(collect_statistics=True)
    algo = GeneticAlgorithm(
        data, pen_manager, rng, pop, ls, srex, init, params=ga_params
    )

    if max_runtime is not None:
        stop = MaxRuntime(max_runtime)
    else:
        assert max_iterations is not None
        stop = MaxIterations(max_iterations)

    return algo.run(stop)

def invert_normalize_and_scale(array, original_max, target_scale=1000):
    """
    Invert the normalization and scaling of an array
    """
    array = array / target_scale * original_max
    return array.astype(int)

cost_evaluator = PenaltyManager().get_cost_evaluator()
result = solve(instance, seed=42, max_runtime=3)
# result = solve(instance, seed=42, max_iterations=50)
print(f"Result: {result}")

def plot_result(result: Result, instance: ProblemData, salvage: dict):
    fig = plt.figure(figsize=(15, 9))
    plotting.plot_result(result, instance, fig, salvage)
    fig.tight_layout()

# 16492095.00
target_scale = 100000
original_time_max = 11006
original_distance_max = 338026
distance_meter_factor = 1609.34
time_meter_factor = 1

# plot_result(result, instance, salvage)

print("OUT", invert_normalize_and_scale(np.array([result.cost()]), original_max=original_distance_max, target_scale=target_scale*10)/distance_meter_factor, result.is_feasible(), result.best.num_routes())
# print("Original_max", original_distance_max)

# print(invert_normalize_and_scale(np.array([result.cost()]), original_max=original_time_max, target_scale=target_scale*10)/time_meter_factor, result.is_feasible(), result.best.num_routes())
# print("Original_max", original_time_max)

# print("Result Cost", result.cost())
# print("Target Scale", target_scale*10)
# plt.show()
