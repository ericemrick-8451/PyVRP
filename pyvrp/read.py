import functools
import pathlib
from numbers import Number
from typing import Callable, Dict, List, Union
from warnings import warn

import numpy as np
import vrplib

from pyvrp.constants import MAX_USER_VALUE
from pyvrp.exceptions import ScalingWarning

from ._ProblemData import Client, ProblemData

_Routes = List[List[int]]
_RoundingFunc = Callable[[np.ndarray], np.ndarray]

_INT_MAX = np.iinfo(np.int32).max


def round_nearest(vals: np.ndarray):
    return np.round(vals).astype(int)


def convert_to_int(vals: np.ndarray):
    return vals.astype(int)


def scale_and_truncate_to_decimals(vals: np.ndarray, decimals: int = 0):
    return (vals * (10**decimals)).astype(int)


def no_rounding(vals):
    return vals


INSTANCE_FORMATS = ["vrplib", "solomon"]
ROUND_FUNCS: Dict[str, _RoundingFunc] = {
    "round": round_nearest,
    "trunc": convert_to_int,
    "trunc1": functools.partial(scale_and_truncate_to_decimals, decimals=1),
    "dimacs": functools.partial(scale_and_truncate_to_decimals, decimals=1),
    "none": no_rounding,
}


def read(
    where: Union[str, pathlib.Path],
    instance_format: str = "vrplib",
    round_func: Union[str, _RoundingFunc] = no_rounding,
) -> ProblemData:
    """
    Reads the VRPLIB file at the given location, and returns a ProblemData
    instance.

    Parameters
    ----------
    where
        File location to read. Assumes the data on the given location is in
        VRPLIB format.
    instance_format, optional
        File format of the instance to read, one of ``'vrplib'`` (default) or
        ``'solomon'``.
    round_func, optional
        Optional rounding function. Will be applied to round data if the data
        is not already integer. This can either be a function or a string:

            * ``'round'`` rounds the values to the nearest integer;
            * ``'trunc'`` truncates the values to be integral;
            * ``'trunc1'`` or ``'dimacs'`` scale and truncate to the nearest
              decimal;
            * ``'none'`` does no rounding. This is the default.

    Returns
    -------
    ProblemData
        Data instance constructed from the read data.
    """
    if (key := str(round_func)) in ROUND_FUNCS:
        round_func = ROUND_FUNCS[key]

    if not callable(round_func):
        raise ValueError(
            f"round_func = {round_func} is not understood. Can be a function,"
            f" or one of {ROUND_FUNCS.keys()}."
        )

    instance = vrplib.read_instance(where, instance_format=instance_format)

    # A priori checks
    if "dimension" in instance:
        dimension: int = instance["dimension"]
    else:
        if "weight_demand" not in instance:
            raise ValueError("File should either contain dimension or weight demands")
        if "volume_demand" not in instance:
            raise ValueError("File should either contain dimension or volume demands")
        dimension = len(instance["weight_demand"])

    if "salvage_demand" not in instance:
        raise ValueError("File should contain salvage demands")

    if "suborder_to_order" not in instance:
        raise ValueError("File should contain unit to client mappings")

    if "order_to_store" not in instance:
        raise ValueError("File should contain unit to client to client group mappings")

    depots: np.ndarray = instance.get("depot", np.array([0]))
    num_vehicles: int = instance.get("vehicles", dimension - 1)
    weight_capacity: int = instance.get("weight_capacity", _INT_MAX)
    volume_capacity: int = instance.get("volume_capacity", _INT_MAX)
    salvage_capacity: int = instance.get("salvage_capacity", _INT_MAX)
    stop_limit: int = instance.get("stop_limit", _INT_MAX)
    client_route_limit: int = instance.get("client_route_limit", _INT_MAX)

    distances: np.ndarray = round_func(instance["edge_weight"]/10).astype(int)

    if "weight_demand" in instance:
        weight_demands: np.ndarray = instance["weight_demand"]
    else:
        weight_demands = np.zeros(dimension, dtype=int)

    if "volume_demand" in instance:
        volume_demands: np.ndarray = instance["volume_demand"]
    else:
        volume_demands = np.zeros(dimension, dtype=int)

    if "salvage_demand" in instance:
        salvage_demands: np.ndarray = instance["salvage_demand"]
    else:
        salvage_demands = np.zeros(dimension, dtype=int)

    if "suborder_to_order" in instance:
        print("FOUND SUBORDER SECTION")
        suborder_to_order_map: np.ndarray = instance["suborder_to_order"]
    else:
        suborder_to_order_map = np.zeros(dimension, dtype=int)

    if "order_to_store" in instance:
        print("ORDER SECTION")
        order_to_store_map: np.ndarray = instance["order_to_store"]
    else:
        order_to_store_map = np.zeros(dimension, dtype=int)

    if "node_coord" in instance:
        coords: np.ndarray = round_func(instance["node_coord"])
    else:
        coords = np.zeros((dimension, 2), dtype=int)

    if "service_time" in instance:
        if isinstance(instance["service_time"], Number):
            # Some instances describe a uniform service time as a single value
            # that applies to all clients.
            service_times = np.full(dimension, instance["service_time"], int)
            service_times[0] = 0
        else:
            service_times = round_func(instance["service_time"])
    else:
        service_times = np.zeros(dimension, dtype=int)

    if "time_window" in instance:
        # VRPLIB instances typically do not have a duration data field, so we
        # assume duration == distance if the instance has time windows.
        durations = distances
        time_windows: np.ndarray = round_func(instance["time_window"])
    else:
        # No time window data. So the time window component is not relevant,
        # and we set all time-related fields to zero.
        durations = np.zeros_like(distances)
        service_times = np.zeros(dimension, dtype=int)
        time_windows = np.zeros((dimension, 2), dtype=int)

    prizes = round_func(instance.get("prize", np.zeros(dimension, dtype=int)))

    # Checks
    if len(depots) != 1 or depots[0] != 0:
        raise ValueError(
            "Source file should contain single depot with index 1 "
            + "(depot index should be 0 after subtracting offset 1)"
        )

    if weight_demands[0] != 0:
        raise ValueError("Weight demand of depot must be 0")

    if volume_demands[0] != 0:
        raise ValueError("Volume demand of depot must be 0")

    if salvage_demands[0] != 0:
        raise ValueError("Salvage demand of depot must be 0")

    if time_windows[0, 0] != 0:
        raise ValueError("Depot start of time window must be 0")

    if service_times[0] != 0:
        raise ValueError("Depot service duration must be 0")

    if (time_windows[:, 0] > time_windows[:, 1]).any():
        raise ValueError("Time window cannot start after end")

    clients = [
        Client(
            coords[idx][0],  # x
            coords[idx][1],  # y
            weight_demands[idx],
            volume_demands[idx],
            salvage_demands[order_to_store_map[suborder_to_order_map[idx-1]]],
            suborder_to_order_map[idx-1],
            order_to_store_map[suborder_to_order_map[idx-1]]+1,
            service_times[idx],
            time_windows[idx][0],  # TW early
            time_windows[idx][1],  # TW late
            prizes[idx],
            np.isclose(prizes[idx], 0),  # required only when prize is zero
        )
        for idx in range(dimension)
    ]

    if max(distances.max(), durations.max()) > MAX_USER_VALUE:
        msg = """
        The maximum distance or duration value is very large. This might
        impact numerical stability. Consider rescaling your input data.
        """
        warn(msg, ScalingWarning)

    return ProblemData(
        clients,
        num_vehicles,
        weight_capacity,
        volume_capacity,
        salvage_capacity,
        client_route_limit,
        stop_limit,
        distances,
        durations
    )


def read_solution(where: Union[str, pathlib.Path]) -> _Routes:
    """
    Reads a solution in VRPLIB format from file at the given location, and
    returns the routes contained in it.

    Parameters
    ----------
    where
        File location to read. Assumes the solution in the file on the given
        location is in VRPLIB solution format.

    Returns
    -------
    list
        List of routes, where each route is a list of client numbers.
    """
    sol = vrplib.read_solution(str(where))
    return sol["routes"]  # type: ignore
