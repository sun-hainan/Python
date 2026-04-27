# -*- coding: utf-8 -*-

"""

算法实现：01_排序与搜索 / selection_sort



本文件实现 selection_sort 相关的算法功能。

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

