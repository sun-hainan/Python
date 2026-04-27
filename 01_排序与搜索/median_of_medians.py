# -*- coding: utf-8 -*-

"""

算法实现：01_排序与搜索 / median_of_medians



本文件实现 median_of_medians 相关的算法功能。

"""



def median_of_five(arr: list) -> int:

    """

    求5元素组的中位数



    原理：对5个元素排序，取中间位置（第3个）



    参数:

        arr: 长度不超过5的数组



    返回:

        中位数（排序后位于中间的元素）



    示例:

        >>> median_of_five([2, 4, 5, 7, 899])

        5

        >>> median_of_five([5, 7, 899, 54, 32])

        32

        >>> median_of_five([5, 4, 3, 2])

        4

        >>> median_of_five([3, 5, 7, 10, 2])

        5

    """

    arr = sorted(arr)  # 排序

    return arr[len(arr) // 2]  # 返回中位数





def median_of_medians(arr: list) -> int:

    """

    求中位数的中位数（作为快速选择的基准）



    步骤：

        1. 将数组按5个一组分组（最后一个组可能不满）

        2. 每组求中位数，组成 medians 数组

        3. 如果 medians 长度 > 5，递归求其中位数

        4. 否则取直接的中位数



    参数:

        arr: 输入数组



    返回:

        中位数的中位数（可靠的基准值）



    示例:

        >>> median_of_medians([2, 4, 5, 7, 899, 54, 32])

        54

        >>> median_of_medians([5, 7, 899, 54, 32])

        32

        >>> median_of_medians([5, 4, 3, 2])

        4

        >>> median_of_medians([3, 5, 7, 10, 2, 12])

        12

    """



    # 递归终止：数组长度小于等于5，直接求中位数

    if len(arr) <= 5:

        return median_of_five(arr)



    # 分组求中位数

    medians = []

    i = 0

    while i < len(arr):

        # 取连续的5个元素（最后一组可能不足5个）

        if (i + 4) <= len(arr):

            medians.append(median_of_five(arr[i:].copy()))

        else:

            medians.append(median_of_five(arr[i : i + 5].copy()))

        i += 5



    # 递归求中位数的中位数

    return median_of_medians(medians)





def quick_select(arr: list, target: int) -> int:

    """

    快速选择算法（使用中位数的中位数作为基准）



    功能：在无序数组中找到第 target 小的元素



    参数:

        arr: 输入数组

        target: 目标排名（1-based，例如 target=1 是最小值）



    返回:

        第 target 小的元素值



    示例:

        >>> quick_select([2, 4, 5, 7, 899, 54, 32], 5)

        32

        >>> quick_select([2, 4, 5, 7, 899, 54, 32], 1)

        2

        >>> quick_select([5, 4, 3, 2], 2)

        3

        >>> quick_select([3, 5, 7, 10, 2, 12], 3)

        5

    """



    # 非法输入：目标排名超过数组长度

    if target > len(arr):

        return -1



    # 使用中位数的中位数作为基准（保证最坏情况 O(n)）

    x = median_of_medians(arr)



    # partition：分为 left（小于x）、right（大于x）

    left = []

    right = []

    check = False  # 是否已处理等于x的情况（避免重复添加）

    for i in range(len(arr)):

        if arr[i] < x:

            left.append(arr[i])

        elif arr[i] > x:

            right.append(arr[i])

        elif arr[i] == x and not check:

            # 第一个等于x的元素，作为基准不归入left或right

            check = True

        else:

            # 第二个及后续等于x的元素，归入right

            right.append(arr[i])



    # 计算基准元素在排序后的位置

    rank_x = len(left) + 1  # 1-based



    # 根据 rank 与 target 的关系决定递归方向

    if rank_x == target:

        answer = x  # 找到目标

    elif rank_x > target:

        # 目标在 left 部分，递归

        answer = quick_select(left, target)

    else:

        # 目标在 right 部分，递归（注意 target - rank_x）

        answer = quick_select(right, target - rank_x)



    return answer





if __name__ == "__main__":

    # 功能测试

    print("=== 中位数选取算法测试 ===")

    print(f"median_of_five([5, 4, 3, 2]): {median_of_five([5, 4, 3, 2])}")

    print(f"median_of_five([2, 4, 5, 7, 899]): {median_of_five([2, 4, 5, 7, 899])}")

    print()



    test_arrays = [

        ([2, 4, 5, 7, 899, 54, 32], 5),

        ([2, 4, 5, 7, 899, 54, 32], 1),

        ([5, 4, 3, 2], 2),

        ([3, 5, 7, 10, 2, 12], 3),

        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 7),

    ]



    print("快速选择测试：")

    for arr, k in test_arrays:

        result = quick_select(arr, k)

        print(f"  quick_select({arr}, {k}) = {result}")



    print()

    print("=== 正确性验证 ===")

    for arr, k in test_arrays:

        result = quick_select(arr, k)

        expected = sorted(arr)[k - 1]

        status = "✓" if result == expected else "✗"

        print(f"  {status} 第{k}小元素: 期望{expected}, 实际{result}")

