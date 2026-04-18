"""
Tim Sort - 中文注释版
==========================================

算法原理：
    Tim Sort 是 Python 的内置排序算法，是一种稳定的混合排序算法。
    它结合了归并排序和插入排序的优点，被设计用于处理真实数据（通常已有部分有序）。

核心思想：
    1. 利用真实数据中已有的有序片段（称为 "run"）
    2. 对每个 run 使用插入排序使其有序
    3. 将多个 run 进行归并，形成最终的有序数组

关键参数：
    - MIN_MERGE：最小 run 长度，通常为 32 或 64
    - 当 run 长度 < MIN_MERGE 时，用插入排序扩展它

Tim Sort vs 普通归并：
    - 普通归并：无视数据的有序性，始终二分
    - Tim Sort：识别已有的有序片段，减少排序工作量

时间复杂度：O(n log n)（最坏），实际应用中接近 O(n)
空间复杂度：O(n)
"""

from __future__ import annotations


def binary_search(lst, item, start, end):
    """
    二分查找：在有序列表 lst[start:end] 中找到 item 应插入的位置

    返回:
        插入位置的索引
    """
    if start == end:
        return start if lst[start] > item else start + 1
    if start > end:
        return start

    mid = (start + end) // 2
    if lst[mid] < item:
        return binary_search(lst, item, mid + 1, end)
    elif lst[mid] > item:
        return binary_search(lst, item, start, mid - 1)
    else:
        return mid


def insertion_sort(lst):
    """
    插入排序 - 用于对单个 run 排序

    参数:
        lst: 输入列表

    返回:
        排序后的列表
    """
    length = len(lst)
    for index in range(1, length):
        value = lst[index]
        # 二分查找插入位置，比线性查找更快
        pos = binary_search(lst, value, 0, index - 1)
        # 插入元素到正确位置
        lst = [*lst[:pos], value, *lst[pos:index], *lst[index + 1:]]
    return lst


def merge(left, right):
    """
    归并两个有序数组

    参数:
        left: 左半部分有序数组
        right: 右半部分有序数组

    返回:
        合并后的有序数组
    """
    if not left:
        return right
    if not right:
        return left
    if left[0] < right[0]:
        return [left[0], *merge(left[1:], right)]
    return [right[0], *merge(left, right[1:])]


def tim_sort(lst):
    """
    Tim Sort 混合排序算法

    参数:
        lst: 输入列表

    返回:
        排序后的列表

    示例:
        >>> tim_sort([5, 9, 10, 3, -4, 5, 178, 92, 46, -18, 0, 7])
        [-18, -4, 0, 3, 5, 5, 7, 9, 10, 46, 92, 178]
        >>> tim_sort([3, 2, 1]) == sorted([3, 2, 1])
        True
    """
    length = len(lst)
    runs, sorted_runs = [], []
    new_run = [lst[0]]

    # 步骤1：识别并提取 runs
    # run 是已经有序的连续子数组（升序或严格降序）
    i = 1
    while i < length:
        if lst[i] < lst[i - 1]:
            runs.append(new_run)
            new_run = [lst[i]]
        else:
            new_run.append(lst[i])
        i += 1
    runs.append(new_run)

    # 步骤2：对每个 run 进行插入排序
    for run in runs:
        sorted_runs.append(insertion_sort(run))

    # 步骤3：归并所有有序 runs
    sorted_array = []
    for run in sorted_runs:
        sorted_array = merge(sorted_array, run)

    return sorted_array


def main():
    lst = [5, 9, 10, 3, -4, 5, 178, 92, 46, -18, 0, 7]
    sorted_lst = tim_sort(lst)
    print(f"排序结果: {sorted_lst}")


if __name__ == "__main__":
    main()
