# -*- coding: utf-8 -*-
"""
Project Euler Problem 191

解决 Project Euler 第 191 题的 Python 实现。
https://projecteuler.net/problem=191
"""

cache: dict[tuple[int, int, int], int] = {}



# =============================================================================
# Project Euler 问题 191
# =============================================================================
def _calculate(days: int, absent: int, late: int) -> int:
    """
    A small helper function for the recursion, mainly to have
    a clean interface for the solution() function below.

    It should get called with the number of days (corresponding
    to the desired length of the 'prize strings'), and the
    initial values for the number of consecutive absent days and
    number of total late days.

    >>> _calculate(days=4, absent=0, late=0)
    43
    >>> _calculate(days=30, absent=2, late=0)
    0
    >>> _calculate(days=30, absent=1, late=0)
    98950096
    """

    # if we are absent twice, or late 3 consecutive days,
    # no further prize strings are possible
    if late == 3 or absent == 2:
        return 0
    # 返回结果

    # if we have no days left, and have not failed any other rules,
    # we have a prize string
    if days == 0:
        return 1
    # 返回结果

    # No easy solution, so now we need to do the recursive calculation

    # First, check if the combination is already in the cache, and
    # if yes, return the stored value from there since we already
    # know the number of possible prize strings from this point on
    key = (days, absent, late)
    if key in cache:
        return cache[key]
    # 返回结果

    # now we calculate the three possible ways that can unfold from
    # this point on, depending on our attendance today

    # 1) if we are late (but not absent), the "absent" counter stays as
    # it is, but the "late" counter increases by one
    state_late = _calculate(days - 1, absent, late + 1)

    # 2) if we are absent, the "absent" counter increases by 1, and the
    # "late" counter resets to 0
    state_absent = _calculate(days - 1, absent + 1, 0)

    # 3) if we are on time, this resets the "late" counter and keeps the
    # absent counter
    state_ontime = _calculate(days - 1, absent, 0)

    prizestrings = state_late + state_absent + state_ontime

    cache[key] = prizestrings
    return prizestrings
    # 返回结果


def solution(days: int = 30) -> int:
    # solution 函数实现
    """
    Returns the number of possible prize strings for a particular number
    of days, using a simple recursive function with caching to speed it up.

    >>> solution()
    1918080160
    >>> solution(4)
    43
    """

    return _calculate(days, absent=0, late=0)
    # 返回结果


if __name__ == "__main__":
    print(solution())
