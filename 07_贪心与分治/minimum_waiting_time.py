# -*- coding: utf-8 -*-
"""
算法实现：07_贪心与分治 / minimum_waiting_time

本文件实现 minimum_waiting_time 相关的算法功能。
"""

def minimum_waiting_time(queries: list[int]) -> int:
    # minimum_waiting_time function

    # minimum_waiting_time function
    # minimum_waiting_time 函数实现
    """
    This function takes a list of query times and returns the minimum waiting time
    for all queries to be completed.

    Args:
        queries: A list of queries measured in picoseconds

    Returns:
        total_waiting_time: Minimum waiting time measured in picoseconds

    Examples:
    >>> minimum_waiting_time([3, 2, 1, 2, 6])
    17
    >>> minimum_waiting_time([3, 2, 1])
    4
    >>> minimum_waiting_time([1, 2, 3, 4])
    10
    >>> minimum_waiting_time([5, 5, 5, 5])
    30
    >>> minimum_waiting_time([])
    0
    """
    n = len(queries)
    if n in (0, 1):
        return 0
    return sum(query * (n - i - 1) for i, query in enumerate(sorted(queries)))


if __name__ == "__main__":
    import doctest

    doctest.testmod()
