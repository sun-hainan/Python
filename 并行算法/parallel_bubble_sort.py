# -*- coding: utf-8 -*-
"""
算法实现：并行算法 / parallel_bubble_sort

本文件实现 parallel_bubble_sort 相关的算法功能。
"""

import threading
import random


def bubble_sort_single_pass(arr: list) -> bool:
    """
    冒泡排序的一轮

    返回：是否发生了交换（如果没交换说明已经有序）
    """
    n = len(arr)
    swapped = False

    for i in range(0, n - 1, 2):  # 奇偶配对
        if arr[i] > arr[i + 1]:
            arr[i], arr[i + 1] = arr[i + 1], arr[i]
            swapped = True

    # 如果还有第二个线程在处理奇数位置（如果有的话）
    for i in range(1, n - 1, 2):
        if arr[i] > arr[i + 1]:
            arr[i], arr[i + 1] = arr[i + 1], arr[i]
            swapped = True

    return swapped


def bubble_sort_sequential(arr: list) -> list:
    """普通串行冒泡排序"""
    arr = arr.copy()
    n = len(arr)

    for _ in range(n):
        if not bubble_sort_single_pass(arr):
            break

    return arr


def parallel_bubble_sort(arr: list, num_threads: int = 4) -> list:
    """
    并行冒泡排序

    参数：
        arr: 输入数组
        num_threads: 线程数

    返回：排序后的新数组
    """
    arr = arr.copy()
    n = len(arr)

    if n <= 1:
        return arr

    if num_threads < 2:
        return bubble_sort_sequential(arr)

    # 将数组分成若干块
    chunk_size = max(1, (n + num_threads - 1) // num_threads)
    chunks = []
    for i in range(0, n, chunk_size):
        chunks.append((i, min(i + chunk_size, n), arr[i:min(i + chunk_size, n)]))

    # 多轮直到完成
    rounds = 0
    while rounds < n:
        swapped = False

        # 并行处理每个块
        threads = []
        results = [None] * len(chunks)

        def sort_chunk(chunk_idx: int):
            chunk = chunks[chunk_idx][2]
            start = chunks[chunk_idx][0]
            c = chunk.copy()
            for _ in range(len(c)):
                if not bubble_sort_single_pass(c):
                    break
            results[chunk_idx] = c

        for i in range(len(chunks)):
            t = threading.Thread(target=sort_chunk, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # 合并结果
        new_arr = []
        for r in results:
            new_arr.extend(r)

        arr = new_arr
        rounds += 1

        # 检查是否已经有序
        sorted_flag = all(arr[i] <= arr[i + 1] for i in range(len(arr) - 1))
        if sorted_flag:
            break

    return arr


def odd_even_parallel_sort(arr: list, num_threads: int = 4) -> list:
    """
    奇偶排序（另一种并行冒泡变体）

    思路：
        - 奇数阶段：比较交换 (0,1), (2,3), (4,5)...
        - 偶数阶段：比较交换 (1,2), (3,4), (5,6)...
        - 交替直到完成
    """
    arr = arr.copy()
    n = len(arr)

    sorted_flag = False
    while not sorted_flag:
        sorted_flag = True

        # 奇数阶段
        for i in range(0, n - 1, 2):
            if arr[i] > arr[i + 1]:
                arr[i], arr[i + 1] = arr[i + 1], arr[i]
                sorted_flag = False

        # 偶数阶段
        for i in range(1, n - 1, 2):
            if arr[i] > arr[i + 1]:
                arr[i], arr[i + 1] = arr[i + 1], arr[i]
                sorted_flag = False

    return arr


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 并行冒泡排序测试 ===\n")

    # 测试数据
    test_arrays = [
        [64, 34, 25, 12, 22, 11, 90, 45, 33, 77, 55],
        list(range(20, 0, -1)),
        [random.randint(1, 100) for _ in range(20)],
        [1],
        [2, 1],
        [1, 2, 3, 4, 5],
    ]

    for arr in test_arrays:
        original = arr.copy()
        print(f"原始: {arr}")

        # 串行
        result_seq = bubble_sort_sequential(arr)
        print(f"串行结果: {result_seq}")

        # 并行（奇偶）
        result_par = odd_even_parallel_sort(arr.copy())
        print(f"并行结果: {result_par}")

        # 验证
        is_sorted = all(result_par[i] <= result_par[i + 1] for i in range(len(result_par) - 1))
        matches = result_seq == result_par
        print(f"排序正确: {'✅' if is_sorted else '❌'}, 结果一致: {'✅' if matches else '❌'}")
        print()

    # 性能测试
    import time

    large_arr = [random.randint(1, 10000) for _ in range(1000)]

    start = time.time()
    bubble_sort_sequential(large_arr.copy())
    seq_time = time.time() - start

    start = time.time()
    odd_even_parallel_sort(large_arr.copy(), num_threads=4)
    par_time = time.time() - start

    print(f"性能对比（n=1000）：")
    print(f"  串行: {seq_time*1000:.2f}ms")
    print(f"  并行: {par_time*1000:.2f}ms")
    print(f"  加速比: {seq_time/par_time:.2f}x")
