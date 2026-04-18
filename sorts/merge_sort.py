"""
归并排序 (Merge Sort) - 中文注释版
==========================================

算法原理：
    归并排序是一种高效、稳定、基于分治思想的排序算法。
    它将数组分成两半，分别排序后再合并，从而实现整体有序。

分治三步曲：
    1. 分解：将数组从中间分成两部分
    2. 解决：递归地对两个子数组进行归并排序
    3. 合并：将两个有序子数组合并成一个有序数组

时间复杂度：
    - 平均: O(n log n)
    - 最坏: O(n log n)
    - 最好: O(n log n)

空间复杂度：O(n) - 需要额外的数组空间来合并

算法特点：
    - 稳定排序（相等元素的相对顺序不变）
    - 适用于链表排序（可以实现 O(1) 空间）
    - 适合外部排序（大数据集排序）
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
