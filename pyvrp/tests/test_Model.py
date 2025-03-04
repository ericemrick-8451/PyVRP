from numpy.testing import assert_, assert_equal, assert_raises, assert_warns
from pytest import mark

from pyvrp import Model
from pyvrp.constants import MAX_USER_VALUE, MAX_VALUE
from pyvrp.exceptions import ScalingWarning
from pyvrp.stop import MaxIterations
from pyvrp.tests.helpers import read


def test_model_data():
    model = Model()

    # Let's add some data: a single client, and edges from/to the depot.
    depot = model.add_depot(0, 0)
    client = model.add_client(0, 1, demand=1)
    model.add_edge(depot, client, 1, 1)
    model.add_edge(client, depot, 1, 1)
    model.add_vehicle_type(1, 1)

    # The model should now have one client.
    data = model.data()
    assert_equal(data.num_clients, 1)


def test_add_depot_raises_more_than_one_depot():
    model = Model()
    model.add_depot(0, 0)  # first depot should be OK

    with assert_raises(ValueError):
        model.add_depot(0, 1)  # second (and more) should not be


def test_add_edge_raises_negative_distance_or_duration():
    model = Model()
    depot = model.add_depot(0, 0)
    client = model.add_client(0, 1)

    model.add_edge(depot, client, distance=0, duration=0)  # zero should be OK

    with assert_raises(ValueError):  # negative distance should not be OK
        model.add_edge(client, depot, distance=-1, duration=0)

    with assert_raises(ValueError):  # negative duration should also not be OK
        model.add_edge(client, depot, distance=0, duration=-1)


def test_add_vehicle_type_raises_more_than_one_type():
    model = Model()
    model.add_vehicle_type(1, 10)  # first type should be OK

    with assert_raises(ValueError):
        model.add_vehicle_type(2, 10)  # second (and more) should not be


@mark.parametrize(
    "number, capacity",
    [
        (0, 1),  # zero vehicles is not OK (but zero capacity is)
        (-1, 1),  # negative vehicles is not OK
        (1, -1),  # negative capacity is not OK
    ],
)
def test_add_vehicle_type_raises_negative_number_or_capacity(number, capacity):
    model = Model()

    with assert_raises(ValueError):
        model.add_vehicle_type(number, capacity)


def test_add_client_attributes():
    model = Model()
    client = model.add_client(
        x=1,
        y=2,
        demand=3,
        service_duration=4,
        tw_early=5,
        tw_late=6,
        prize=7,
        required=False,
    )

    assert_equal(client.x, 1)
    assert_equal(client.y, 2)
    assert_equal(client.demand, 3)
    assert_equal(client.service_duration, 4)
    assert_equal(client.tw_early, 5)
    assert_equal(client.tw_late, 6)
    assert_equal(client.prize, 7)
    assert_(not client.required)


def test_add_depot_attributes():
    model = Model()
    depot = model.add_depot(x=1, y=0, tw_early=3, tw_late=5)

    assert_equal(depot.x, 1)
    assert_equal(depot.y, 0)
    assert_equal(depot.tw_early, 3)
    assert_equal(depot.tw_late, 5)


def test_add_edge():
    model = Model()
    depot = model.add_depot(0, 0)
    client = model.add_client(0, 1)
    edge = model.add_edge(depot, client, distance=15, duration=49)

    assert_(edge.frm is depot)
    assert_(edge.to is client)
    assert_equal(edge.distance, 15)
    assert_equal(edge.duration, 49)


def test_add_vehicle_type():
    model = Model()
    vehicle_type = model.add_vehicle_type(number=10, capacity=998)

    assert_equal(vehicle_type.number, 10)
    assert_equal(vehicle_type.capacity, 998)


def test_from_data():
    read_data = read("data/E-n22-k4.txt", round_func="dimacs")
    model = Model.from_data(read_data)
    model_data = model.data()

    # We can first check if the overall problem dimension numbers agree.
    assert_equal(model_data.num_clients, read_data.num_clients)
    assert_equal(model_data.num_vehicles, read_data.num_vehicles)
    assert_equal(model_data.vehicle_capacity, read_data.vehicle_capacity)

    # It's a bit cumbersome to compare the whole matrices, so we use a few
    # sample traces from the distance and duration matrices instead.
    assert_equal(model_data.dist(3, 4), read_data.dist(3, 4))
    assert_equal(model_data.duration(2, 1), read_data.duration(2, 1))


def test_from_data_and_solve():
    # Solve the small E-n22-k4 instance using the from_data constructor.
    data = read("data/E-n22-k4.txt", round_func="dimacs")
    model = Model.from_data(data)
    res = model.solve(stop=MaxIterations(100), seed=0)
    assert_equal(res.cost(), 3_743)
    assert_(res.is_feasible())

    data = read("data/OkSmall.txt")
    model = Model.from_data(data)
    res = model.solve(stop=MaxIterations(100), seed=0)
    assert_equal(res.cost(), 9_155)
    assert_(res.is_feasible())


def test_model_and_solve():
    # Solve the small OkSmall instance using the from_data constructor.
    data = read("data/OkSmall.txt")
    model = Model.from_data(data)
    res = model.solve(stop=MaxIterations(100), seed=0)
    assert_equal(res.cost(), 9_155)
    assert_(res.is_feasible())

    # Now do the same thing, but model the instance using the modelling API.
    # This should of course result in the same solution.
    model = Model()
    model.add_vehicle_type(number=3, capacity=10)
    depot = model.add_depot(x=2334, y=726, tw_early=0, tw_late=45000)
    clients = [
        model.add_client(226, 1297, 5, 360, 15600, 22500),
        model.add_client(590, 530, 5, 360, 12000, 19500),
        model.add_client(435, 718, 3, 420, 8400, 15300),
        model.add_client(1191, 639, 5, 360, 12000, 19500),
    ]

    edge_weights = [
        [0, 1544, 1944, 1931, 1476],
        [1726, 0, 1992, 1427, 1593],
        [1965, 1975, 0, 621, 1090],
        [2063, 1433, 647, 0, 818],
        [1475, 1594, 1090, 828, 0],
    ]

    for idx, client in enumerate(clients, 1):
        from_depot = edge_weights[0][idx]
        to_depot = edge_weights[idx][0]

        model.add_edge(depot, client, from_depot, from_depot)
        model.add_edge(client, depot, to_depot, to_depot)

        for other_idx, other in enumerate(clients, 1):
            from_client = edge_weights[idx][other_idx]
            to_client = edge_weights[other_idx][idx]

            model.add_edge(client, other, from_client, from_client)
            model.add_edge(other, client, to_client, to_client)

    res = model.solve(stop=MaxIterations(100), seed=0)
    assert_equal(res.cost(), 9_155)
    assert_(res.is_feasible())


def test_partial_distance_duration_matrix():
    model = Model()
    depot = model.add_depot(0, 0)
    clients = [model.add_client(0, 1), model.add_client(1, 0)]

    # Only a subset of all possible edges exist. The model should be able to
    # handle that.
    model.add_edge(depot, clients[0], distance=1)
    model.add_edge(clients[0], clients[1], distance=2)
    model.add_edge(clients[1], depot, distance=1)

    model.add_vehicle_type(number=1, capacity=0)

    # These edges were not set, so their distance values should default to the
    # maximum value we use for such edges.
    data = model.data()
    assert_equal(data.dist(0, 2), MAX_VALUE)
    assert_equal(data.dist(1, 0), MAX_VALUE)

    res = model.solve(stop=MaxIterations(100), seed=4)
    assert_equal(res.best.num_routes(), 1)
    assert_equal(res.cost(), 4)  # depot -> client 1 -> client 2 -> depot
    assert_(res.is_feasible())


def test_data_warns_about_scaling_issues(recwarn):
    model = Model()
    model.add_vehicle_type(number=1, capacity=0)
    depot = model.add_depot(0, 0)
    client = model.add_client(1, 1)

    # Normal distance sizes; should all be OK.
    for distance in [1, 10, 100, 1_000, 10_000, 100_000, MAX_USER_VALUE]:
        model.add_edge(client, depot, distance=distance)
        model.data()
        assert_equal(len(recwarn), 0)

    # But a value exceeding the maximum user value is not OK. This should warn.
    model.add_edge(depot, client, distance=MAX_USER_VALUE + 1)
    with assert_warns(ScalingWarning):
        model.data()
