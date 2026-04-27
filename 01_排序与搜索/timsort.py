# -*- coding: utf-8 -*-

"""

算法实现：01_排序与搜索 / timsort



本文件实现 timsort 相关的算法功能。

"""



from typing import List, Tuple





# 最小run长度，经验最优值

MIN_RUN = 32





def calc_min_run(n: int) -> int:

    """

    计算最小run长度

    

    Args:

        n: 数组长度

    

    Returns:

        最小run长度（16-32之间）

    """

    r = 0

    while n >= MIN_RUN:

        r |= n & 1

        n >>= 1

    return n + r





def insertion_sort(arr: List, left: int, right: int) -> None:

    """

    插入排序（用于小规模run的排序）

    

    Args:

        arr: 目标数组

        left: 左边界索引

        right: 右边界索引

    """

    for i in range(left + 1, right + 1):

        key = arr[i]              # 待插入元素

        j = i - 1

        

        # 向左寻找插入位置

        while j >= left and arr[j] > key:

            arr[j + 1] = arr[j]   # 元素右移

            j -= 1

        

        arr[j + 1] = key          # 插入元素





def merge(arr: List, left: int, mid: int, right: int) -> None:

    """

    合并两个相邻的已排序run

    

    Args:

        arr: 目标数组

        left: 左run起始索引

        mid: 左右run的分界索引（左run结束 = mid, 右run开始 = mid+1）

        right: 右run结束索引

    """

    # 左右两个run的长度

    left_len = mid - left + 1

    right_len = right - mid

    

    # 复制左右两部分

    left_part = arr[left:mid + 1].copy()    # 左run [left, mid]

    right_part = arr[mid + 1:right + 1].copy()  # 右run [mid+1, right]

    

    # 归并回原数组

    i = j = 0                               # i: left索引, j: right索引

    k = left                                # k: 写入位置

    

    while i < left_len and j < right_len:

        if left_part[i] <= right_part[j]:

            arr[k] = left_part[i]

            i += 1

        else:

            arr[k] = right_part[j]

            j += 1

        k += 1

    

    # 剩余元素直接复制（只有一个run会有剩余）

    while i < left_len:

        arr[k] = left_part[i]

        i += 1

        k += 1

    

    while j < right_len:

        arr[k] = right_part[j]

        j += 1

        k += 1





def tim_sort(arr: List) -> List:

    """

    TimSort 主函数

    

    Args:

        arr: 待排序数组

    

    Returns:

        排序后的数组（原地修改）

    

    示例:

        >>> tim_sort([64, 25, 12, 22, 11, 90, 38])

        [11, 12, 22, 25, 38, 64, 90]

    """

    n = len(arr)

    

    if n <= 1:

        return arr

    

    # 第一步：计算最小run长度

    min_run = calc_min_run(n)

    

    # 第二步：构建初始runs并做插入排序

    # 遍历数组，每个run长度 >= min_run 的段先标记

    i = 0

    while i < n:

        # 起始位置

        run_start = i

        

        # 扩展run（寻找升序序列）

        run_end = i

        while run_end + 1 < n and arr[run_end + 1] >= arr[run_end]:

            run_end += 1

        

        # 反转严格降序的段（转升序）

        # 例如 [5, 4, 3, 2, 1] -> [1, 2, 3, 4, 5]

        left = run_start

        right = run_end

        while left < right:

            arr[left], arr[right] = arr[right], arr[left]

            left += 1

            right -= 1

        

        # 如果run太短，用插入排序扩展到min_run

        run_len = run_end - run_start + 1

        if run_len < min_run:

            # 扩展run到刚好包含min_run个元素（或到数组末尾）

            end = min(i + min_run - 1, n - 1)

            insertion_sort(arr, run_start, end)

        

        i += max(run_len, min_run) if run_len < min_run else run_len

    

    # 第三步：合并runs

    # 从min_run开始，逐渐扩大合并范围

    size = min_run

    while size < n:

        # 合并相距2*size的两个相邻run

        left = 0

        while left < n:

            mid = left + size - 1

            right = min(left + 2 * size - 1, n - 1)

            

            if mid < right:

                merge(arr, left, mid, right)

            

            left += 2 * size

        

        size *= 2  # 合并窗口翻倍

    

    return arr





def find_runs(arr: List) -> List[Tuple[int, int]]:

    """

    找出数组中所有自然runs

    

    Args:

        arr: 输入数组

    

    Returns:

        runs列表，每个元素为 (start, end) 元组

    """

    n = len(arr)

    runs = []

    

    i = 0

    while i < n:

        start = i

        end = i

        

        # 扩展升序run

        while end + 1 < n and arr[end + 1] >= arr[end]:

            end += 1

        

        runs.append((start, end))

        i = end + 1

    

    return runs





if __name__ == "__main__":

    # 功能测试

    test_cases = [

        [64, 25, 12, 22, 11, 90, 38],

        [5, 3, 8, 3, 9, 1, 5, 7],

        [1],

        [],

        [3, 3, 3, 1, 1, 2, 2],

        list(range(20, 0, -1)),  # 完全逆序

        [1, 2, 3, 4, 5],        # 已有序

        [2, 2, 2, 2],

    ]

    

    print("TimSort 测试:")

    for i, arr in enumerate(test_cases):

        original = arr.copy()

        result = tim_sort(arr)

        status = "✓" if result == sorted(original) else "✗"

        print(f"  测试 {i+1}: {status} | 结果: {result}")

    

    # 自然run检测测试

    print("\n自然runs检测:")

    test_arr = [1, 3, 5, 7, 2, 4, 6, 8, 9, 1, 2, 5]

    runs = find_runs(test_arr)

    print(f"  数组: {test_arr}")

    print(f"  Runs: {runs}")

    

    # 性能对比

    import random

    import time

    

    sizes = [1000, 5000, 10000]

    print("\n性能对比:")

    for size in sizes:

        test_arr = [random.randint(0, 10000) for _ in range(size)]

        

        arr1 = test_arr.copy()

        start = time.time()

        tim_sort(arr1)

        tim_time = time.time() - start

        

        arr2 = test_arr.copy()

        start = time.time()

        arr2.sort()

        py_time = time.time() - start

        

        print(f"  n={size}: TimSort={tim_time:.4f}s, Python.sort()={py_time:.4f}s")

