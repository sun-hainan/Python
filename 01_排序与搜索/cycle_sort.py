# -*- coding: utf-8 -*-
"""
算法实现：01_排序与搜索 / cycle_sort

本文件实现 cycle_sort 相关的算法功能。
"""

# cycle_sort 函数实现
def cycle_sort(array: list) -> list:
    """
    >>> cycle_sort([4, 3, 2, 1])
    [1, 2, 3, 4]

    >>> cycle_sort([-4, 20, 0, -50, 100, -1])
    [-50, -4, -1, 0, 20, 100]

    >>> cycle_sort([-.1, -.2, 1.3, -.8])
    [-0.8, -0.2, -0.1, 1.3]

    >>> cycle_sort([])
    []
    """
    array_len = len(array)
    for cycle_start in range(array_len - 1):
    # 遍历循环
        item = array[cycle_start]

        pos = cycle_start
        for i in range(cycle_start + 1, array_len):
    # 遍历循环
            if array[i] < item:
    # 条件判断
                pos += 1

        if pos == cycle_start:
    # 条件判断
            continue

        while item == array[pos]:
    # 条件循环
            pos += 1

        array[pos], item = item, array[pos]
        while pos != cycle_start:
    # 条件循环
            pos = cycle_start
            for i in range(cycle_start + 1, array_len):
    # 遍历循环
                if array[i] < item:
    # 条件判断
                    pos += 1

            while item == array[pos]:
    # 条件循环
                pos += 1

            array[pos], item = item, array[pos]

    return array
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    assert cycle_sort([4, 5, 3, 2, 1]) == [1, 2, 3, 4, 5]
    assert cycle_sort([0, 1, -10, 15, 2, -2]) == [-10, -2, 0, 1, 2, 15]
