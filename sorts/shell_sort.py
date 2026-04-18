"""
希尔排序 (Shell Sort) - 中文注释版
==========================================

算法原理：
    希尔排序是插入排序的改进版，又称"缩小增量排序"。
    它通过引入"增量"概念，将数组分成若干子数组分别排序，
    最后再用插入排序对整体排序。

插入排序的问题：
    当数据距离正确位置很远时，需要一步一步地移动，效率低。

希尔排序的改进：
    1. 先用较大的增量，将数据分成若干组
    2. 对每组数据进行插入排序
    3. 逐步缩小增量，直到 1
    4. 最后进行一次完整的插入排序

增量序列（决定性能）：
    本实现使用 Marcin Ciura 的最优增量序列：
    [701, 301, 132, 57, 23, 10, 4, 1]

时间复杂度：
    - 平均: O(n^1.3) 左右
    - 取决于增量序列的选择
空间复杂度：O(1) - 原地排序

算法特点：
    - 不稳定排序
    - 插入排序的改进，适合大规模数据
    - 实现简单，比快速排序稍微慢一点，但更简单
"""

from __future__ import annotations


def shell_sort(collection: list[int]) -> list[int]:
    """
    希尔排序

    参数:
        collection: 可变集合，包含可比较的元素

    返回:
        同一集合，按升序排列

    示例:
        >>> shell_sort([0, 5, 3, 2, 2])
        [0, 2, 2, 3, 5]
        >>> shell_sort([])
        []
        >>> shell_sort([-2, -5, -45])
        [-45, -5, -2]
    """
    # Marcin Ciura 的最优增量序列
    gaps = [701, 301, 132, 57, 23, 10, 4, 1]

    # 逐步缩小增量
    for gap in gaps:
        # 对每个子数组进行插入排序
        for i in range(gap, len(collection)):
            insert_value = collection[i]  # 待插入元素
            j = i

            # 在子数组中找到正确位置
            # 子数组间隔为 gap
            while j >= gap and collection[j - gap] > insert_value:
                collection[j] = collection[j - gap]
                j -= gap

            if j != i:
                collection[j] = insert_value

    return collection


if __name__ == "__main__":
    user_input = input("输入以逗号分隔的数字:\n").strip()
    unsorted = [int(item) for item in user_input.split(",")]
    print(f"排序结果: {shell_sort(unsorted)}")
