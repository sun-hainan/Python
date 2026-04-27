# -*- coding: utf-8 -*-
"""
算法实现：07_贪心与分治 / gas_station

本文件实现 gas_station 相关的算法功能。
"""

from dataclasses import dataclass


@dataclass
# GasStation 类
class GasStation:
    # GasStation class

    # GasStation class
    gas_quantity: int
    cost: int


def get_gas_stations(
    # get_gas_stations function

    # get_gas_stations function
    gas_quantities: list[int], costs: list[int]
) -> tuple[GasStation, ...]:
    """
    This function returns a tuple of gas stations.

    Args:
        gas_quantities: Amount of gas available at each station
        costs: The cost of gas required to move from one station to the next

    Returns:
        A tuple of gas stations

    >>> gas_stations = get_gas_stations([1, 2, 3, 4, 5], [3, 4, 5, 1, 2])
    >>> len(gas_stations)
    5
    >>> gas_stations[0]
    GasStation(gas_quantity=1, cost=3)
    >>> gas_stations[-1]
    GasStation(gas_quantity=5, cost=2)
    """
    return tuple(
        GasStation(quantity, cost) for quantity, cost in zip(gas_quantities, costs)
    )


def can_complete_journey(gas_stations: tuple[GasStation, ...]) -> int:
    # can_complete_journey function

    # can_complete_journey function
    """
    This function returns the index from which to start the journey
    in order to reach the end.

    Args:
        gas_quantities [list]: Amount of gas available at each station
        cost [list]: The cost of gas required to move from one station to the next

    Returns:
        start [int]: start index needed to complete the journey

    Examples:
    >>> can_complete_journey(get_gas_stations([1, 2, 3, 4, 5], [3, 4, 5, 1, 2]))
    3
    >>> can_complete_journey(get_gas_stations([2, 3, 4], [3, 4, 3]))
    -1
    """
    total_gas = sum(gas_station.gas_quantity for gas_station in gas_stations)
    total_cost = sum(gas_station.cost for gas_station in gas_stations)
    if total_gas < total_cost:
        return -1

    start = 0
    net = 0
    for i, gas_station in enumerate(gas_stations):
        net += gas_station.gas_quantity - gas_station.cost
        if net < 0:
            start = i + 1
            net = 0
    return start


if __name__ == "__main__":
    import doctest

    doctest.testmod()
