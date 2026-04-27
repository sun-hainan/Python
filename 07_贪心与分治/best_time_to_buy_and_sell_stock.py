# -*- coding: utf-8 -*-
"""
算法实现：07_贪心与分治 / best_time_to_buy_and_sell_stock

本文件实现 best_time_to_buy_and_sell_stock 相关的算法功能。
"""

def max_profit(prices: list[int]) -> int:
    # max_profit function

    # max_profit function
    # max_profit 函数实现
    """
    >>> max_profit([7, 1, 5, 3, 6, 4])
    5
    >>> max_profit([7, 6, 4, 3, 1])
    0
    """
    if not prices:
        return 0

    min_price = prices[0]
    max_profit: int = 0

    for price in prices:
        min_price = min(price, min_price)
        max_profit = max(price - min_price, max_profit)

    return max_profit


if __name__ == "__main__":
    import doctest

    doctest.testmod()
    print(max_profit([7, 1, 5, 3, 6, 4]))
