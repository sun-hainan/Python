# -*- coding: utf-8 -*-

"""

算法实现：缓存无关算法 / cache_oblivious_sort



本文件实现 cache_oblivious_sort 相关的算法功能。

"""



from typing import List

import math





def cache_oblivious_sort(arr: List[int]) -> List[int]:

    """

    缓存无关排序(简化版Funnelsort)

    

    Args:

        arr: 输入数组

    

    Returns:

        排序后的数组

    """

    n = len(arr)

    if n <= 1:

        return arr.copy()

    

    # 分割数组

    mid = n // 2

    left = cache_oblivious_sort(arr[:mid])

    right = cache_oblivious_sort(arr[mid:])

    

    # 合并

    return merge_sorted(left, right)





def merge_sorted(a: List[int], b: List[int]) -> List[int]:

    """

    合并两个有序数组

    

    Args:

        a: 有序数组1

        b: 有序数组2

    

    Returns:

        合并后的有序数组

    """

    result = []

    i = j = 0

    

    while i < len(a) and j < len(b):

        if a[i] < b[j]:

            result.append(a[i])

            i += 1

        else:

            result.append(b[j])

            j += 1

    

    result.extend(a[i:])

    result.extend(b[j:])

    

    return result





def funnel_sort(arr: List[int], k: int = None) -> List[int]:

    """

    Funnelsort算法

    

    Args:

        arr: 输入数组

        k: 参数(默认为sqrt(n))

    

    Returns:

        排序后的数组

    """

    n = len(arr)

    if n <= 1:

        return arr.copy()

    

    if k is None:

        k = max(1, int(math.sqrt(n)))

    

    # 将数组分成k大小的块,递归排序

    blocks = [arr[i:i+k] for i in range(0, n, k)]

    sorted_blocks = [sorted(block) for block in blocks]

    

    # 合并所有块

    return k_way_merge(sorted_blocks, k)





def k_way_merge(sorted_lists: List[List[int]], k: int) -> List[int]:

    """

    k路归并

    

    Args:

        sorted_lists: 有序列表列表

        k: 路数

    

    Returns:

        合并后的有序列表

    """

    import heapq

    

    result = []

    heap = []

    

    # 初始化堆

    for i, lst in enumerate(sorted_lists):

        if lst:

            heapq.heappush(heap, (lst[0], i, 0))

    

    while heap:

        val, list_idx, elem_idx = heapq.heappop(heap)

        result.append(val)

        

        # 推入同一个列表的下一个元素

        if elem_idx + 1 < len(sorted_lists[list_idx]):

            next_val = sorted_lists[list_idx][elem_idx + 1]

            heapq.heappush(heap, (next_val, list_idx, elem_idx + 1))

    

    return result





def mergesort_bu(arr: List[int]) -> List[int]:

    """

    自底向上归并排序

    

    Args:

        arr: 输入数组

    

    Returns:

        排序后的数组

    """

    n = len(arr)

    if n <= 1:

        return arr.copy()

    

    result = arr.copy()

    width = 1

    

    while width < n:

        i = 0

        while i < n:

            left = i

            mid = min(i + width, n)

            right = min(i + 2 * width, n)

            

            # 合并

            result[left:right] = _merge(result[left:mid], result[mid:right])

            i += 2 * width

        

        width *= 2

    

    return result





def _merge(left: List[int], right: List[int]) -> List[int]:

    """合并两个有序数组"""

    result = []

    i = j = 0

    

    while i < len(left) and j < len(right):

        if left[i] <= right[j]:

            result.append(left[i])

            i += 1

        else:

            result.append(right[j])

            j += 1

    

    result.extend(left[i:])

    result.extend(right[j:])

    

    return result





# 测试代码

if __name__ == "__main__":

    import time

    import random

    

    # 测试1: 基本功能

    print("测试1 - 基本功能:")

    arr1 = [5, 2, 8, 1, 9, 3, 7, 4, 6]

    

    result1 = cache_oblivious_sort(arr1)

    print(f"  输入: {arr1}")

    print(f"  CO排序: {result1}")

    

    result2 = mergesort_bu(arr1)

    print(f"  BU归并: {result2}")

    

    # 测试2: 不同大小数组

    print("\n测试2 - 性能对比:")

    

    for n in [100, 1000, 10000]:

        arr = [random.randint(1, 10000) for _ in range(n)]

        

        # 缓存无关排序

        start = time.time()

        r1 = cache_oblivious_sort(arr.copy())

        time1 = time.time() - start

        

        # 自底向上归并

        start = time.time()

        r2 = mergesort_bu(arr.copy())

        time2 = time.time() - start

        

        # Python内置排序

        start = time.time()

        r3 = sorted(arr.copy())

        time3 = time.time() - start

        

        print(f"  n={n}:")

        print(f"    CO排序: {time1:.4f}s")

        print(f"    BU归并: {time2:.4f}s")

        print(f"    内置排序: {time3:.4f}s")

        print(f"    结果正确: {r1 == r2 == r3}")

    

    # 测试3: Funnelsort

    print("\n测试3 - Funnelsort:")

    arr3 = [random.randint(1, 1000) for _ in range(100)]

    result3 = funnel_sort(arr3, k=10)

    print(f"  结果正确: {result3 == sorted(arr3)}")

    

    # 测试4: 边界情况

    print("\n测试4 - 边界情况:")

    for arr in [[], [1], [1, 2], [2, 1], [1, 1, 1]]:

        result = cache_oblivious_sort(arr)

        print(f"  {arr} -> {result}")

    

    # 测试5: 已排序数组

    print("\n测试5 - 已排序数组:")

    arr5 = list(range(100))

    result5 = cache_oblivious_sort(arr5)

    print(f"  结果正确: {result5 == arr5}")

    

    # 测试6: 逆序数组

    print("\n测试6 - 逆序数组:")

    arr6 = list(range(100, 0, -1))

    result6 = cache_oblivious_sort(arr6)

    print(f"  结果正确: {result6 == list(range(1, 101))}")

    

    print("\n所有测试完成!")

