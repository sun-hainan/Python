# -*- coding: utf-8 -*-
"""
Project Euler Problem 122

解决 Project Euler 第 122 题的 Python 实现。
https://projecteuler.net/problem=122
"""

# =============================================================================
# Project Euler 问题 122
# =============================================================================
def solve(nums: list[int], goal: int, depth: int) -> bool:
    """
    Checks if nums can have a sum equal to goal, given that length of nums does
    not exceed depth.

    >>> solve([1], 2, 2)
    True
    >>> solve([1], 2, 0)
    False
    """
    if len(nums) > depth:
        return False
    # 返回结果
    for el in nums:
        if el + nums[-1] == goal:
            return True
    # 返回结果
        nums.append(el + nums[-1])
        if solve(nums=nums, goal=goal, depth=depth):
            return True
    # 返回结果
        del nums[-1]
    return False
    # 返回结果


def solution(n: int = 200) -> int:
    # solution 函数实现
    """
    Calculates sum of smallest number of multiplactions for each number up to
    and including n.

    >>> solution(1)
    0
    >>> solution(2)
    1
    >>> solution(14)
    45
    >>> solution(15)
    50
    """
    total = 0
    for i in range(2, n + 1):
    # 遍历循环
        max_length = 0
        while True:
    # 条件循环
            nums = [1]
            max_length += 1
            if solve(nums=nums, goal=i, depth=max_length):
                break
        total += max_length
    return total
    # 返回结果


if __name__ == "__main__":
    print(f"{solution() = }")
