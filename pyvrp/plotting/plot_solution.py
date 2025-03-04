from typing import Optional

import matplotlib.pyplot as plt
import numpy as np

from pyvrp import ProblemData, Solution


# def plot_solution(
#     solution: Solution,
#     data: ProblemData,
#     plot_customers: bool = False,
#     ax: Optional[plt.Axes] = None,
# ):
#     """
#     Plots the given solution.
# 
#     Parameters
#     ----------
#     solution
#         Solution to plot.
#     data
#         Data instance underlying the solution.
#     plot_customers, optional
#         Whether to plot customers as dots. Default False, which plots only the
#         solution's routes.
#     ax, optional
#         Axes object to draw the plot on. One will be created if not provided.
#     """
#     if not ax:
#         _, ax = plt.subplots()
# 
#     dim = data.num_clients + 1
#     x_coords = np.array([data.client(client).x for client in range(dim)])
#     y_coords = np.array([data.client(client).y for client in range(dim)])
# 
#     # This is the depot
#     kwargs = dict(c="tab:red", marker="*", zorder=3, s=500)
#     ax.scatter(x_coords[0], y_coords[0], label="Depot", **kwargs)
# 
#     for idx, route in enumerate(solution.get_routes(), 1):
#         x = x_coords[route]
#         y = y_coords[route]
# 
#         # Coordinates of customers served by this route.
#         if len(route) == 1 or plot_customers:
#             ax.scatter(x, y, label=f"Route {idx}", zorder=3, s=75)
#         ax.plot(x, y)
# 
#         # Edges from and to the depot, very thinly dashed.
#         kwargs = dict(ls=(0, (5, 15)), linewidth=0.25, color="grey")
#         ax.plot([x_coords[0], x[0]], [y_coords[0], y[0]], **kwargs)
#         ax.plot([x[-1], x_coords[0]], [y[-1], y_coords[0]], **kwargs)
# 
#     ax.grid(color="grey", linestyle="solid", linewidth=0.2)
# 
#     ax.set_title("Solution")
#     ax.set_aspect("equal", "datalim")
#     ax.legend(frameon=False, ncol=2)

# def plot_solution(
#     solution: Solution,
#     data: ProblemData,
#     plot_customers: bool = False,
#     ax: Optional[plt.Axes] = None,
#     salvage: dict = {}
# ):
#     """
#     Plots the given solution.
# 
#     Parameters
#     ----------
#     solution
#         Solution to plot.
#     data
#         Data instance underlying the solution.
#     plot_customers, optional
#         Whether to plot customers as dots. Default False, which plots only the
#         solution's routes.
#     ax, optional
#         Axes object to draw the plot on. One will be created if not provided.
#     salvage, optional
#         A dictionary where the key is the client number and the value is 1 if salvage exists, 0 otherwise.
#     """
#     if not ax:
#         _, ax = plt.subplots()
# 
#     dim = data.num_clients + 1
#     x_coords = np.array([data.client(client).x for client in range(dim)])
#     y_coords = np.array([data.client(client).y for client in range(dim)])
# 
#     # This is the depot
#     kwargs = dict(c="tab:red", marker="*", zorder=3, s=500)
#     ax.scatter(x_coords[0], y_coords[0], label="Depot", **kwargs)
# 
#     for idx, route in enumerate(solution.get_routes(), 1):
#         x = x_coords[route]
#         y = y_coords[route]
# 
#         # Mark salvage clients with a blue star
#         if salvage is not None:
#             salvage_clients = [client for client in route if salvage.get(client, 0) == 1]
#             if salvage_clients:
#                 x_salvage = x_coords[salvage_clients]
#                 y_salvage = y_coords[salvage_clients]
#                 kwargs = dict(c="blue", marker="*", zorder=3, s=100)
#                 ax.scatter(x_salvage, y_salvage, label="Salvage", **kwargs)
# 
#         # Coordinates of customers served by this route.
#         if len(route) == 1 or plot_customers:
#             ax.scatter(x, y, label=f"Route {idx}", zorder=3, s=75)
#         ax.plot(x, y)
# 
#         # Edges from and to the depot, very thinly dashed.
#         kwargs = dict(ls=(0, (5, 15)), linewidth=0.25, color="grey")
#         ax.plot([x_coords[0], x[0]], [y_coords[0], y[0]], **kwargs)
#         ax.plot([x[-1], x_coords[0]], [y[-1], y_coords[0]], **kwargs)
# 
#     ax.grid(color="grey", linestyle="solid", linewidth=0.2)
# 
#     ax.set_title("Solution")
#     ax.set_aspect("equal", "datalim")
#     ax.legend(frameon=False, ncol=2)

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

def plot_solution(
    solution: Solution,
    data: ProblemData,
    plot_customers: bool = False,
    ax: Optional[plt.Axes] = None,
    salvage: dict = {}
):
    """
    Plots the given solution.

    Parameters
    ----------
    solution
        Solution to plot.
    data
        Data instance underlying the solution.
    plot_customers, optional
        Whether to plot customers as dots. Default False, which plots only the
        solution's routes.
    ax, optional
        Axes object to draw the plot on. One will be created if not provided.
    salvage, optional
        A dictionary where the key is the client number and the value is 1 if salvage exists, 0 otherwise.
    """
    if not ax:
        _, ax = plt.subplots()

    dim = data.num_clients + 1
    x_coords = np.array([data.client(client).x for client in range(dim)])
    y_coords = np.array([data.client(client).y for client in range(dim)])

    kwargs = dict(color="tab:red", marker="*", zorder=3, s=500)
    ax.scatter(x_coords[0], y_coords[0], label="Depot", **kwargs)

    color_map = plt.cm.get_cmap('tab10')
    
    for idx, route in enumerate(solution.get_routes(), 1):
        x = x_coords[route]
        y = y_coords[route]
        current_color = color_map(idx % color_map.N)

        if salvage is not None:
            salvage_clients = [client for client in route if salvage.get(client) == 1]
            for salvage_client in salvage_clients:
                x_salvage = x_coords[salvage_client]
                y_salvage = y_coords[salvage_client]
                kwargs = dict(c="blue", marker="*", zorder=2, s=75)
                ax.scatter(x_salvage, y_salvage, label=f"Salvage at Client {salvage_client}", **kwargs)

        if len(route) == 1 or plot_customers:
            ax.scatter(x, y, label=f"Route {idx}", zorder=3, s=75)
            if len(route) == 1 and route[0] in salvage_clients:
                kwargs = dict(color="white", marker="*", zorder=3, s=50)
                ax.scatter(x, y, **kwargs)

        ax.scatter(x[0], y[0], marker='s', s=10, color='orange', edgecolors='black', zorder=4)
        ax.plot(x, y, color=current_color, linewidth=0.35)

        kwargs = dict(ls=(0, (5, 15)), linewidth=0.25, color="grey")
        ax.plot([x_coords[0], x[0]], [y_coords[0], y[0]], **kwargs)
        ax.plot([x[-1], x_coords[0]], [y[-1], y_coords[0]], **kwargs)

    ax.grid(color="grey", linestyle="solid", linewidth=0.2)

    ax.set_title("Solution")
    ax.set_aspect("equal", "datalim")
    ax.legend(frameon=False, ncol=2)
