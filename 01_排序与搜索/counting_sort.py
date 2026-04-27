# -*- coding: utf-8 -*-
"""
算法实现：01_排序与搜索 / counting_sort

本文件实现 counting_sort 相关的算法功能。
"""

def counting_sort(collection):
    """
    计数排序

    参数:
        collection: 可变集合，包含可比较的元素

    返回:
        同一集合，按升序排列

    示例:
        >>> counting_sort([0, 5, 3, 2, 2])
        [0, 2, 2, 3, 5]
        >>> counting_sort([])
        []
        >>> counting_sort([-2, -5, -45])
        [-45, -5, -2]
    """
    # 空数组直接返回
    if collection == []:
        return []

    coll_len = len(collection)
    coll_max = max(collection)
    coll_min = min(collection)

    # 创建计数数组，长度为元素范围
    counting_arr_length = coll_max + 1 - coll_min
    counting_arr = [0] * counting_arr_length

    # 统计每个元素出现的次数
    for number in collection:
        counting_arr[number - coll_min] += 1

    # 累加前缀和：counting_arr[i] 表示 <= i+coll_min 的元素个数
    for i in range(1, counting_arr_length):
        counting_arr[i] = counting_arr[i] + counting_arr[i - 1]

    # 从后向前遍历，稳定地放置元素到输出数组
    ordered = [0] * coll_len
    for i in reversed(range(coll_len)):
        ordered[counting_arr[collection[i] - coll_min] - 1] = collection[i]
        counting_arr[collection[i] - coll_min] -= 1

    return ordered


def counting_sort_string(string):
    """
    计数排序 - 字符串版本

    示例:
        >>> counting_sort_string("thisisthestring")
        'eghhiiinrsssttt'
    """
    return "".join([chr(i) for i in counting_sort([ord(c) for c in string])])


if __name__ == "__main__":
    # 测试字符串排序
    assert counting_sort_string("thisisthestring") == "eghhiiinrsssttt"

    user_input = input("输入以逗号分隔的数字:\n").strip()
    unsorted = [int(item) for item in user_input.split(",")]
    print(counting_sort(unsorted))
