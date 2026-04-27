# -*- coding: utf-8 -*-
"""
算法实现：07_贪心与分治 / optimal_merge_pattern

本文件实现 optimal_merge_pattern 相关的算法功能。
"""

def optimal_merge_pattern(files: list) -> float:
    # optimal_merge_pattern function

    # optimal_merge_pattern function
    # optimal_merge_pattern 函数实现
    """Function to merge all the files with optimum cost

    Args:
        files [list]: A list of sizes of different files to be merged

    Returns:
        optimal_merge_cost [int]: Optimal cost to merge all those files

    Examples:
    >>> optimal_merge_pattern([2, 3, 4])
    14
    >>> optimal_merge_pattern([5, 10, 20, 30, 30])
    205
    >>> optimal_merge_pattern([8, 8, 8, 8, 8])
    96
    """
    optimal_merge_cost = 0
    while len(files) > 1:
        temp = 0
        # Consider two files with minimum cost to be merged
        for _ in range(2):
            min_index = files.index(min(files))
            temp += files[min_index]
            files.pop(min_index)
        files.append(temp)
        optimal_merge_cost += temp
    return optimal_merge_cost


if __name__ == "__main__":
    import doctest

    doctest.testmod()
