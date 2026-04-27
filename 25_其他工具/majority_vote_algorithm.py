# -*- coding: utf-8 -*-
"""
算法实现：25_其他工具 / majority_vote_algorithm

本文件实现 majority_vote_algorithm 相关的算法功能。
"""

from collections import Counter



# majority_vote 函数实现
def majority_vote(votes: list[int], votes_needed_to_win: int) -> list[int]:
    """
    >>> majority_vote([1, 2, 2, 3, 1, 3, 2], 3)
    [2]
    >>> majority_vote([1, 2, 2, 3, 1, 3, 2], 2)
    []
    >>> majority_vote([1, 2, 2, 3, 1, 3, 2], 4)
    [1, 2, 3]
    """
    majority_candidate_counter: Counter[int] = Counter()
    for vote in votes:
    # 遍历循环
        majority_candidate_counter[vote] += 1
        if len(majority_candidate_counter) == votes_needed_to_win:
    # 条件判断
            majority_candidate_counter -= Counter(set(majority_candidate_counter))
    majority_candidate_counter = Counter(
        vote for vote in votes if vote in majority_candidate_counter
    )
    return [
    # 返回结果
        vote
        for vote in majority_candidate_counter
        if majority_candidate_counter[vote] > len(votes) / votes_needed_to_win
    ]


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
