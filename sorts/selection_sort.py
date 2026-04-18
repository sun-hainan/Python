"""
选择排序 (Selection Sort) - 中文注释版
==========================================

算法原理：
    选择排序首先在未排序序列中找到最小（大）元素，放到排序序列的起始位置，
    然后再从剩余未排序元素中继续寻找最小（大）元素，放到已排序序列的末尾。
    以此类推，直到所有元素排序完毕。

算法步骤：
    1. 假设第一个元素是最小值，记录其位置
    2. 遍历剩余元素，寻找真正的最小值
    3. 如果找到更小的，与记录的位置交换
    4. 将最小值放到已排序序列的末尾
    5. 重复以上步骤，每次减少一个未排序元素

时间复杂度：
    - 平均: O(n²)
    - 最坏: O(n²)
    - 最好: O(n²)（即使有序也要进行全部比较）

空间复杂度：O(1) - 原地排序

算法特点：
    - 不稳定排序（相等元素可能被交换到后面）
    - 移动次数少，最多 n-1 次交换
    - 实现简单，但效率较低
"""


def selection_sort(collection: list[int]) -> list[int]:
    """
    选择排序

    参数:
        collection: 要排序的整数列表

    返回:
        排序后的列表

    示例:
        >>> selection_sort([0, 5, 3, 2, 2])
        [0, 2, 2, 3, 5]
        >>> selection_sort([])
        []
        >>> selection_sort([-2, -5, -45])
        [-45, -5, -2]
    """
    length = len(collection)

    # 只需遍历到倒数第二个元素（最后一个自然有序）
    for i in range(length - 1):
        min_index = i  # 假设当前位置是最小值

        # 在剩余未排序元素中寻找真正的最小值
        for k in range(i + 1, length):
            if collection[k] < collection[min_index]:
                min_index = k

        # 如果最小值不在当前位置，则交换
        if min_index != i:
            collection[i], collection[min_index] = collection[min_index], collection[i]

    return collection


if __name__ == "__main__":
    user_input = input("输入以逗号分隔的数字:\n").strip()
    unsorted = [int(item) for item in user_input.split(",")]
    sorted_list = selection_sort(unsorted)
    print("排序结果:", sorted_list)
