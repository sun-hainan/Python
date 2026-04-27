# -*- coding: utf-8 -*-
"""
算法实现：25_其他工具 / activity_selection

本文件实现 activity_selection 相关的算法功能。
"""

    """
# start[]--> An array that contains start time of all activities
# finish[] --> An array that contains finish time of all activities



# print_max_activities 函数实现
def print_max_activities(start: list[int], finish: list[int]) -> None:
    """
    >>> start = [1, 3, 0, 5, 8, 5]
    >>> finish = [2, 4, 6, 7, 9, 9]
    >>> print_max_activities(start, finish)
    The following activities are selected:
    0,1,3,4,
    """
    n = len(finish)
    print("The following activities are selected:")

    # The first activity is always selected
    i = 0
    print(i, end=",")

    # Consider rest of the activities
    for j in range(n):
    # 遍历循环
        # If this activity has start time greater than
        # or equal to the finish time of previously
        # selected activity, then select it
        if start[j] >= finish[i]:
    # 条件判断
            print(j, end=",")
            i = j


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()

    start = [1, 3, 0, 5, 8, 5]
    finish = [2, 4, 6, 7, 9, 9]
    print_max_activities(start, finish)
