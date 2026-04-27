# -*- coding: utf-8 -*-
"""
算法实现：05_动态规划 / trapped_water

本文件实现 trapped_water 相关的算法功能。
"""

def trapped_rainwater(heights: tuple[int, ...]) -> int:
    # trapped_rainwater function

    # trapped_rainwater function
    # trapped_rainwater 函数实现
    """
    The trapped_rainwater function calculates the total amount of rainwater that can be
    trapped given an array of bar heights.
    It uses a dynamic programming approach, determining the maximum height of bars on
    both sides for each bar, and then computing the trapped water above each bar.
    The function returns the total trapped water.

    >>> trapped_rainwater((0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1))
    6
    >>> trapped_rainwater((7, 1, 5, 3, 6, 4))
    9
    >>> trapped_rainwater((7, 1, 5, 3, 6, -1))
    Traceback (most recent call last):
        ...
    ValueError: No height can be negative
    """
    if not heights:
        return 0
    if any(h < 0 for h in heights):
        raise ValueError("No height can be negative")
    length = len(heights)

    left_max = [0] * length
    left_max[0] = heights[0]
    for i, height in enumerate(heights[1:], start=1):
        left_max[i] = max(height, left_max[i - 1])

    right_max = [0] * length
    right_max[-1] = heights[-1]
    for i in range(length - 2, -1, -1):
        right_max[i] = max(heights[i], right_max[i + 1])

    return sum(
        min(left, right) - height
        for left, right, height in zip(left_max, right_max, heights)
    )


if __name__ == "__main__":
    import doctest

    doctest.testmod()
    print(f"{trapped_rainwater((0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1)) = }")
    print(f"{trapped_rainwater((7, 1, 5, 3, 6, 4)) = }")
