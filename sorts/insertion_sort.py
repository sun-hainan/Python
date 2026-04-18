"""
插入排序 (Insertion Sort) - 中文注释版
==========================================

算法原理：
    插入排序的工作方式像整理扑克牌一样。
    从左到右遍历数组，将每个元素插入到它左侧已排序部分中的正确位置。

算法步骤：
    1. 从第二个元素开始（假设第一个元素已排序）
    2. 将当前元素与左侧已排序元素逐一比较
    3. 如果左侧元素较大，则向右移动
    4. 找到正确位置后，插入当前元素
    5. 重复直到整个数组排序完成

时间复杂度：
    - 平均: O(n²)
    - 最坏: O(n²)（逆序数组）
    - 最好: O(n)（已经有序的数组）

空间复杂度：O(1) - 原地排序

算法特点：
    - 稳定排序
    - 对于小规模数据或近乎有序的数据效率高
    - 实现简单，是"冒泡排序"的改进版
    - 适合在线排序（已排好序的部分可以立即输出）
"""

from collections.abc import MutableSequence
from typing import Any, Protocol, TypeVar


class Comparable(Protocol):
    def __lt__(self, other: Any, /) -> bool: ...


T = TypeVar("T", bound=Comparable)


def insertion_sort[T: Comparable](collection: MutableSequence[T]) -> MutableSequence[T]:
    """
    插入排序

    参数:
        collection: 可变的有序集合，包含可比较的元素

    返回:
        同一个集合，按升序排列

    示例:
        >>> insertion_sort([0, 5, 3, 2, 2])
        [0, 2, 2, 3, 5]
        >>> insertion_sort([]) == sorted([])
        True
        >>> insertion_sort([-2, -5, -45]) == sorted([-2, -5, -45])
        True
    """
    # 从第二个元素开始，将每个元素插入左侧有序部分
    for insert_index in range(1, len(collection)):
        insert_value = collection[insert_index]  # 待插入的元素
        # 向左逐个比较，找到正确的插入位置
        while insert_index > 0 and insert_value < collection[insert_index - 1]:
            # 元素右移，为待插入元素腾出位置
            collection[insert_index] = collection[insert_index - 1]
            insert_index -= 1
        # 插入元素到正确位置
        collection[insert_index] = insert_value
    return collection


if __name__ == "__main__":
    from doctest import testmod

    testmod()

    user_input = input("输入以逗号分隔的数字:\n").strip()
    unsorted = [int(item) for item in user_input.split(",")]
    print(f"排序结果: {insertion_sort(unsorted)}")
