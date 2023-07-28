import math
from dataclasses import dataclass

from .Statistics import Statistics
from ._CostEvaluator import CostEvaluator
from ._Solution import Solution
from ._ProblemData import ProblemData


@dataclass
class Result:
    """
    Stores the outcomes of a single run. An instance of this class is returned
    once the GeneticAlgorithm completes.

    Parameters
    ----------
    best
        The best observed solution.
    stats
        A Statistics object containing runtime statistics. These are only
        collected and available if statistics were collected for the given run.
    num_iterations
        Number of iterations performed by the genetic algorithm.
    runtime
        Total runtime of the main genetic algorithm loop.
    data
        Problem data instance. Need this to aggregate output appropriately.

    Raises
    ------
    ValueError
        When the number of iterations or runtime are negative.
    """

    best: Solution
    stats: Statistics
    num_iterations: int
    runtime: float
    data: ProblemData

    def __post_init__(self):
        if self.num_iterations < 0:
            raise ValueError("Negative number of iterations not understood.")

        if self.runtime < 0:
            raise ValueError("Negative runtime not understood.")

    def cost(self) -> float:
        """
        Returns the cost (objective) value of the best solution. Returns inf
        if the best solution is infeasible.

        Returns
        -------
        float
            Objective value.
        """
        if not self.best.is_feasible():
            return math.inf
        return CostEvaluator().cost(self.best)

    def is_feasible(self) -> bool:
        """
        Returns whether the best solution is feasible.

        Returns
        -------
        bool
            True when the solution is feasible, False otherwise.
        """
        return self.best.is_feasible()

    def has_statistics(self) -> bool:
        """
        Returns whether detailed statistics were collected. If statistics are
        not availabe, the plotting methods cannot be used.

        Returns
        -------
        bool
            True when detailed statistics are available, False otherwise.
        """
        return (
            self.num_iterations > 0
            and self.num_iterations == self.stats.num_iterations
        )

#     def __str__(self) -> str:
#         obj_str = f"{self.cost():.2f}" if self.is_feasible() else "INFEASIBLE"
#         summary = [
#             "Solution results",
#             "================",
#             f"    # routes: {self.best.num_routes()}",
#             f"   # clients: {self.best.num_clients()}",
#             f"   objective: {obj_str}",
#             f"# iterations: {self.num_iterations}",
#             f"    run-time: {self.runtime:.2f} seconds",
#             "",
#             "Routes",
#             "------",
#         ]
# 
#         for idx, route in enumerate(self.best.get_routes(), 1):
#             if route:
#                 summary.append(f"Route {idx:>2}: {route}")
# 
#         return "\n".join(summary)

    def store_type_to_str(self, demandSalvage: int, demandWeight: int) -> str:
        if demandSalvage:
            if demandWeight:
                return 'B'
            else:
                return 'S'
        else:
            if demandWeight:
                return 'D'

    def __str__(self) -> str:
        obj_str = f"{self.cost():.2f}" if self.is_feasible() else "INFEASIBLE"
        summary = [
            "Solution results",
            "================",
            f"    # routes: {self.best.num_routes()}",
            f"   # clients: {self.best.num_clients()}",
            f"   objective: {obj_str}",
            f"# iterations: {self.num_iterations}",
            f"    run-time: {self.runtime:.2f} seconds",
            "",
            "Routes",
            "------",
        ]
        tot_dist = 0

        for idx, route in enumerate(self.best.get_routes(), 1):
            if route:
                route_info = [f"Route {idx:>2}: "]
                for r in route:
                    client_data = self.data.client(r)
                    store_type_str = self.store_type_to_str(client_data.demandSalvage, client_data.demandWeight)
                    route_info.append(f"{store_type_str}-{client_data.clientStore}-{client_data.clientOrder}")
                route_info.append(f"Demand Salvage: {route.demandSalvage()}")
                route_info.append(f"Route Stores: {route.routeStores()}")
                route_info.append(f"Distance: {route.distance()}")
                tot_dist += route.distance()
                route_info.append(f"Tot Distance: {tot_dist}")
                route_info.append(f"E salvage: {route.excess_salvage()}")
                route_info.append(f"E stores: {route.excess_stores()}")
                route_info.append(f"Store limit: {self.data.route_store_limit}")
            
                summary.append(", ".join(route_info))

        return "\n".join(summary)


#    def __str__(self) -> str:
#        print("Data.client(25).clientOrder: ", self.data.client(25).clientOrder)
#        print("Data.client(25).clientStore: ", self.data.client(25).clientStore)
#        obj_str = f"{self.cost():.2f}" if self.is_feasible() else "INFEASIBLE"
#        summary = [
#            "Solution results",
#            "================",
#            f"    # routes: {self.best.num_routes()}",
#            f"   # clients: {self.best.num_clients()}",
#            f"   objective: {obj_str}",
#            f"# iterations: {self.num_iterations}",
#            f"    run-time: {self.runtime:.2f} seconds",
#            "",
#            "Routes",
#            "------",
#        ]
#        tot_dist = 0
#        for idx, route in enumerate(self.best.get_routes(), 1):
#            if route:
#                route_info = [f"Route {idx:>2}: " + ', '.join([str(self.data.client(r).clientStore) + "-" + str(self.data.client(r).clientOrder) for r in route])]
#                # route_info = [f"Route {idx:>2}: " + ', '.join([str(self.data.client(r).clientOrder) + "-" + str(self.data.client(r).clientStore) for r in route])]
#                # route_info = [f"Route {idx:>2}: {route}"]
#                # route_info.append(f"Excess weight: {route.excess_weight()}")
#                # route_info.append(f"Excess volume: {route.excess_volume()}")
#                # route_info.append(f"Excess salvage: {route.excess_salvage()}")
#                # route_info.append(f"Demand Weight: {route.demandWeight()}")
#                # route_info.append(f"Demand Volume: {route.demandVolume()}")
#                route_info.append(f"Demand Salvage: {route.demandSalvage()}")
#                route_info.append(f"Route Stores: {route.routeStores()}")
#                route_info.append(f"Distance: {route.distance()}")
#                tot_dist += route.distance()
#                route_info.append(f"Tot Distance: {tot_dist}")
##                route_info.append(f"hasSalvageBeforeDelivery: {route.has_salvage_before_deliver()}")
#
#                summary.append(", ".join(route_info))
#
#        return "\n".join(summary)


#  public:
#         [[nodiscard]] bool empty() const;
#         [[nodiscard]] size_t size() const;
#         [[nodiscard]] Client operator[](size_t idx) const;
# 
#         Visits::const_iterator begin() const;
#         Visits::const_iterator end() const;
#         Visits::const_iterator cbegin() const;
#         Visits::const_iterator cend() const;
# 
#         [[nodiscard]] Visits const &visits() const;
#         [[nodiscard]] Distance distance() const;
#         [[nodiscard]] Load demandWeight() const;
#         [[nodiscard]] Load demandVolume() const;
#         [[nodiscard]] Salvage demandSalvage() const;
#         [[nodiscard]] Load excessWeight() const;
#         [[nodiscard]] Load excessVolume() const;
#         [[nodiscard]] Salvage excessSalvage() const;
#         [[nodiscard]] Duration duration() const;
#         [[nodiscard]] Duration serviceDuration() const;
#         [[nodiscard]] Duration timeWarp() const;
#         [[nodiscard]] Duration waitDuration() const;
#         [[nodiscard]] Cost prizes() const;
# 
#         [[nodiscard]] std::pair<double, double> const &centroid() const;
# 
#         [[nodiscard]] bool isFeasible() const;
#         [[nodiscard]] bool hasExcessWeight() const;
#         [[nodiscard]] bool hasExcessVolume() const;
#         [[nodiscard]] bool hasExcessSalvage() const;
#         [[nodiscard]] bool hasSalvageBeforeDelivery() const;
#         [[nodiscard]] bool hasTimeWarp() const;
# 
#         Route() = default;  // default is empty
#         Route(ProblemData const &data, Visits const visits);
