# -*- coding: utf-8 -*-
"""
算法实现：Sorting / 08_Counting_Sort

本文件实现 08_Counting_Sort 相关的算法功能。
"""

def counting_sort(arr):
    """
    计数排序
    """
    if not arr:
        return []
    min_val, max_val = min(arr), max(arr)
    count = [0] * (max_val - min_val + 1)
    for num in arr:
        count[num - min_val] += 1
    for i in range(1, len(count)):
        count[i] += count[i - 1]
    result = [0] * len(arr)
    for num in reversed(arr):
        result[count[num - min_val] - 1] = num
        count[num - min_val] -= 1
    return result


if __name__ == "__main__":
    # 测试: counting_sort
    result = counting_sort()
    print(result)
