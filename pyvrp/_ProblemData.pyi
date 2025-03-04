from typing import List, Tuple

class Client:
    """
    Simple data object storing all client data as (read-only) properties.

    Parameters
    ----------
    x
        Horizontal coordinate of this client, that is, the 'x' part of the
        client's (x, y) location tuple.
    y
        Vertical coordinate of this client, that is, the 'y' part of the
        client's (x, y) location tuple.
    weight_demand
        The weight amount this client's demanding. Default 0.
    volume_demand
        The volume amount this client's demanding. Default 0.
    salvage_demand
	1 if salvage pickup is required. Default 0.
    client_order 
	index to the client's order. Default -1.
    client_store
	index to the client's store. Default -1.
    service_duration
        This client's service duration, that is, the amount of time we need to
        visit the client for. Service should start (but not necessarily end)
        within the [:py:attr:`~tw_early`, :py:attr:`~tw_late`] interval.
        Default 0.
    tw_early
        Earliest time at which we can visit this client. Default 0.
    tw_late
        Latest time at which we can visit this client. Default 0.
    prize
        Prize collected by visiting this client. Default 0.
    required
        Whether this client must be part of a feasible solution. Default True.
    """

    x: int
    y: int
    weight_demand: int
    volume_demand: int
    salvage_demand: int
    client_order: int
    client_store: int
    service_duration: int
    tw_early: int
    tw_late: int
    prize: int
    required: bool

    def __init__(
        self,
        x: int,
        y: int,
        weight_demand: int = 0,
        volume_demand: int = 0,
        salvage_demand: int = 0,
        client_order: int = -1,
        client_store: int = -1,
        service_duration: int = 0,
        tw_early: int = 0,
        tw_late: int = 0,
        prize: int = 0,
        required: bool = True,
    ) -> None: ...

class ProblemData:
    """
    Creates a problem data instance. This instance contains all information
    needed to solve the vehicle routing problem.

    Parameters
    ----------
    clients
        List of clients. The first client (at index 0) is assumed to be the
        depot. The time window for the depot is assumed to describe the overall
        time horizon. The depot should have 0 weight and volume demand and 0 service duration.
    num_vehicles
        The number of vehicles in this problem instance.
    weight_cap
        Homogenous vehicle weight capacity for all vehicles in the problem instance.
    volume_cap
        Homogenous vehicle volume capacity for all vehicles in the problem instance.
    salvage_cap
        Homogenous route nonterminal pickup stops capacity for all routes in the problem instance.
    store_lim 
        Limit on the number of stores that can be associated with a route.
    duration_matrix
        A matrix that gives the travel times between clients (and the depot at
        index 0).
    """

    def __init__(
        self,
        clients: List[Client],
        num_vehicles: int,
        vehicle_cap: int,
        salvage_cap: int,
        store_lim: int,
        distance_matrix: List[List[int]],
        duration_matrix: List[List[int]],
    ): ...
    def client(self, client: int) -> Client:
        """
        Returns client data for the given client.

        Parameters
        ----------
        client
            Client number whose information to retrieve.

        Returns
        -------
        Client
            A simple data object containing the requested client's information.
        """
    def depot(self) -> Client:
        """
        Returns 'client' information for the depot, which is stored internally
        as the client with number `0`.

        Returns
        -------
        Client
            A simple data object containing the depot's information.
        """
    def centroid(self) -> Tuple[float, float]:
        """
        Center point of all client locations (excluding the depot).

        Returns
        -------
        tuple
            Centroid of all client locations.
        """
    def dist(self, first: int, second: int) -> int:
        """
        Returns the travel distance between the first and second argument,
        according to this instance's travel distance matrix.

        Parameters
        ----------
        first
            Client or depot number.
        second
            Client or depot number.

        Returns
        -------
        int
            Travel distance between the given clients.
        """
    def duration(self, first: int, second: int) -> int:
        """
        Returns the travel duration between the first and second argument,
        according to this instance's travel duration matrix.

        Parameters
        ----------
        first
            Client or depot number.
        second
            Client or depot number.

        Returns
        -------
        int
            Travel duration between the given clients.
        """
    @property
    def num_clients(self) -> int:
        """
        Number of clients in this problem instance.

        Returns
        -------
        int
            Number of clients in the instance.
        """
    @property
    def num_vehicles(self) -> int:
        """
        Number of vehicles in this problem instance.

        Returns
        -------
        int
            Number of vehicles in the instance.
        """
    @property
    def weight_capacity(self) -> int:
        """
        Returns the homogenous vehicle weight capacities of all vehicles in this
        problem data instance.

        Returns
        -------
        int
            Weight capacity of each vehicle in the instance.
        """
    @property
    def volume_capacity(self) -> int:
        """
        Returns the homogenous vehicle volume capacities of all vehicles in this
        problem data instance.
        
        Returns
        -------
        int
            Volume capacity of each vehicle in the instance.
    @property
    def salvage_capacity(self) -> int:
        """
        Returns the homogenous nonterminal salvage pickups capacity of all routes in this
        problem data instance.
        
        Returns
        -------
        int
            Non-terminal salvage pickup capacity of each route in the instance.
    @property
    def store_limit(self) -> int:
        """
        Returns the maximum number of stores permitted on a single route in this 
        problem data instance.

        Returns
        -------
        int
            Number of stores
