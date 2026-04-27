# -*- coding: utf-8 -*-

"""

算法实现：01_排序与搜索 / insertion_sort



本文件实现 insertion_sort 相关的算法功能。

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

