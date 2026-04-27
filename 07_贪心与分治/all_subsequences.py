# -*- coding: utf-8 -*-
"""
算法实现：07_贪心与分治 / all_subsequences

本文件实现 all_subsequences 相关的算法功能。
"""

from __future__ import annotations

"""
Project Euler Problem  - Chinese comment version
https://projecteuler.net/problem=

问题描述: (请补充关于此题目具体问题描述)
解题思路: (请补充关于此题目的解题思路和算法原理)
"""


"""
Project Euler Problem  -- Chinese comment version
https://projecteuler.net/problem=

Description: (placeholder - add problem description)
Solution: (placeholder - add solution explanation)
"""



from typing import Any


def generate_all_subsequences(sequence: list[Any]) -> None:
    # generate_all_subsequences function

    # generate_all_subsequences function
    # generate_all_subsequences 函数实现
    create_state_space_tree(sequence, [], 0)


def create_state_space_tree(
    # create_state_space_tree function

    # create_state_space_tree function
    # create_state_space_tree 函数实现
    sequence: list[Any], current_subsequence: list[Any], index: int
) -> None:
    """
    Creates a state space tree to iterate through each branch using DFS.
    We know that each state has exactly two children.
    It terminates when it reaches the end of the given sequence.

    :param sequence: The input sequence for which subsequences are generated.
    :param current_subsequence: The current subsequence being built.
    :param index: The current index in the sequence.

    Example:
    >>> sequence = [3, 2, 1]
    >>> current_subsequence = []
    >>> create_state_space_tree(sequence, current_subsequence, 0)
    []
    [1]
    [2]
    [2, 1]
    [3]
    [3, 1]
    [3, 2]
    [3, 2, 1]

    >>> sequence = ["A", "B"]
    >>> current_subsequence = []
    >>> create_state_space_tree(sequence, current_subsequence, 0)
    []
    ['B']
    ['A']
    ['A', 'B']

    >>> sequence = []
    >>> current_subsequence = []
    >>> create_state_space_tree(sequence, current_subsequence, 0)
    []

    >>> sequence = [1, 2, 3, 4]
    >>> current_subsequence = []
    >>> create_state_space_tree(sequence, current_subsequence, 0)
    []
    [4]
    [3]
    [3, 4]
    [2]
    [2, 4]
    [2, 3]
    [2, 3, 4]
    [1]
    [1, 4]
    [1, 3]
    [1, 3, 4]
    [1, 2]
    [1, 2, 4]
    [1, 2, 3]
    [1, 2, 3, 4]
    """

    if index == len(sequence):
        print(current_subsequence)
        return

    create_state_space_tree(sequence, current_subsequence, index + 1)
    current_subsequence.append(sequence[index])
    create_state_space_tree(sequence, current_subsequence, index + 1)
    current_subsequence.pop()


if __name__ == "__main__":
    seq: list[Any] = [1, 2, 3]
    generate_all_subsequences(seq)

    seq.clear()
    seq.extend(["A", "B", "C"])
    generate_all_subsequences(seq)
