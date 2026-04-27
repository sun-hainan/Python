# -*- coding: utf-8 -*-
"""
算法实现：Sorting / 09_Radix_Sort

本文件实现 09_Radix_Sort 相关的算法功能。
"""

def radix_sort(arr):
    """
    基数排序
    """
    RADIX = 10
    max_val = max(arr)
    exp = 1
    while max_val // exp > 0:
        buckets = [[] for _ in range(RADIX)]
        for num in arr:
            digit = (num // exp) % RADIX
            buckets[digit].append(num)
        arr = []
        for bucket in buckets:
            arr.extend(bucket)
        exp *= RADIX
    return arr


if __name__ == "__main__":
    # 测试: radix_sort
    result = radix_sort()
    print(result)
