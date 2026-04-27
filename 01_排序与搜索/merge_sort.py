# -*- coding: utf-8 -*-
"""
算法实现：01_排序与搜索 / merge_sort

本文件实现 merge_sort 相关的算法功能。
"""

def merge_sort(collection: list) -> list:
    """
    归并排序主函数

    参数:
        collection: 一个可变的有序集合，包含可比较的元素

    返回:
        同一个集合，按升序排列

    示例:
        >>> merge_sort([0, 5, 3, 2, 2])
        [0, 2, 2, 3, 5]
        >>> merge_sort([])
        []
        >>> merge_sort([-2, -5, -45])
        [-45, -5, -2]
    """

    def merge(left: list, right: list) -> list:
        """
        合并两个有序数组

        算法步骤：
            1. 初始化结果数组
            2. 同时遍历两个数组，每次取较小的元素放入结果
            3. 将剩余的元素追加到结果末尾

        参数:
            left:  左半部分有序数组
            right: 右半部分有序数组

        返回:
            合并后的有序数组
        """
        result = []
        # 比较两个数组的元素，每次取较小的
        while left and right:
            result.append(left.pop(0) if left[0] <= right[0] else right.pop(0))
        # 追加剩余元素（必有一个数组已空）
        result.extend(left)
        result.extend(right)
        return result

    # 递归终止条件：单个元素或空数组已是有序的
    if len(collection) <= 1:
        return collection

    # 分解：从中间分割数组
    mid_index = len(collection) // 2
    left_half = merge_sort(collection[:mid_index])
    right_half = merge_sort(collection[mid_index:])

    # 合并：归并两个有序数组
    return merge(left_half, right_half)


if __name__ == "__main__":
    import doctest

    doctest.testmod()

    try:
        user_input = input("输入以逗号分隔的数字:\n").strip()
        unsorted = [int(item) for item in user_input.split(",")]
        sorted_list = merge_sort(unsorted)
        print(*sorted_list, sep=",")
    except ValueError:
        print("输入无效，请输入以逗号分隔的有效整数。")
