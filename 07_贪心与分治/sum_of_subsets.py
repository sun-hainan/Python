# -*- coding: utf-8 -*-
"""
算法实现：07_贪心与分治 / sum_of_subsets

本文件实现 sum_of_subsets 相关的算法功能。
"""

def generate_sum_of_subsets_solutions(nums: list[int], max_sum: int) -> list[list[int]]:
    # generate_sum_of_subsets_solutions function

    # generate_sum_of_subsets_solutions function
    # generate_sum_of_subsets_solutions 函数实现
    """
    The main function. For list of numbers 'nums' find the subsets with sum
    equal to 'max_sum'

    >>> generate_sum_of_subsets_solutions(nums=[3, 34, 4, 12, 5, 2], max_sum=9)
    [[3, 4, 2], [4, 5]]
    >>> generate_sum_of_subsets_solutions(nums=[3, 34, 4, 12, 5, 2], max_sum=3)
    [[3]]
    >>> generate_sum_of_subsets_solutions(nums=[3, 34, 4, 12, 5, 2], max_sum=1)
    []
    """

    result: list[list[int]] = []
    path: list[int] = []
    num_index = 0
    remaining_nums_sum = sum(nums)
    create_state_space_tree(nums, max_sum, num_index, path, result, remaining_nums_sum)
    return result


def create_state_space_tree(
    # create_state_space_tree function

    # create_state_space_tree function
    # create_state_space_tree 函数实现
    nums: list[int],
    max_sum: int,
    num_index: int,
    path: list[int],
    result: list[list[int]],
    remaining_nums_sum: int,
) -> None:
    """
    Creates a state space tree to iterate through each branch using DFS.
    It terminates the branching of a node when any of the two conditions
    given below satisfy.
    This algorithm follows depth-fist-search and backtracks when the node is not
    branchable.

    >>> path = []
    >>> result = []
    >>> create_state_space_tree(
    ...     nums=[1],
    ...     max_sum=1,
    ...     num_index=0,
    ...     path=path,
    ...     result=result,
    ...     remaining_nums_sum=1)
    >>> path
    []
    >>> result
    [[1]]
    """

    if sum(path) > max_sum or (remaining_nums_sum + sum(path)) < max_sum:
        return
    if sum(path) == max_sum:
        result.append(path)
        return
    for index in range(num_index, len(nums)):
        create_state_space_tree(
            nums,
            max_sum,
            index + 1,
            [*path, nums[index]],
            result,
            remaining_nums_sum - nums[index],
        )


if __name__ == "__main__":
    import doctest

    doctest.testmod()
