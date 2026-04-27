# -*- coding: utf-8 -*-
"""
算法实现：并行算法 / parallel_prefix_sum

本文件实现 parallel_prefix_sum 相关的算法功能。
"""

import math
from typing import List


def sequential_prefix_sum(arr: List[float]) -> List[float]:
    """串行前缀和"""
    result = [arr[0]]
    for i in range(1, len(arr)):
        result.append(result[-1] + arr[i])
    return result


def parallel_prefix_sum(arr: List[float], num_threads: int = 4) -> List[float]:
    """
    并行前缀和（Blelloch算法）

    参数：
        arr: 输入数组
        num_threads: 线程数

    返回：前缀和数组
    """
    n = len(arr)
    if n <= 1:
        return arr.copy()

    # 限制线程数
    num_threads = min(num_threads, n)

    # 分配给每个线程的工作量
    chunk_size = (n + num_threads - 1) // num_threads

    # 阶段1：局部前缀和（在每个线程内）
    local_sums = [0.0] * num_threads

    def local_scan(thread_id: int):
        start = thread_id * chunk_size
        end = min(start + chunk_size, n)
        if start >= n:
            return

        # 计算局部前缀和
        for i in range(start + 1, end):
            arr[i] += arr[i - 1]

        # 记录最后一个元素（用于后续合并）
        if end > start:
            local_sums[thread_id] = arr[end - 1]

    # 并行计算局部前缀和
    import threading
    threads = []
    for tid in range(num_threads):
        t = threading.Thread(target=local_scan, args=(tid,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    # 阶段2：合并局部结果
    for i in range(1, num_threads):
        local_sums[i] += local_sums[i - 1]

    # 调整：每个块的元素加上前一个块的局部和
    def adjust(thread_id: int):
        if thread_id == 0:
            return
        start = thread_id * chunk_size
        end = min(start + chunk_size, n)
        offset = local_sums[thread_id - 1]
        for i in range(start, end):
            arr[i] += offset

    threads = []
    for tid in range(num_threads):
        t = threading.Thread(target=adjust, args=(tid,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    return arr


def parallel_prefix_sum_hill_steel(arr: List[float]) -> List[float]:
    """
    Hill-Steele算法（更标准的并行前缀和）

    两个阶段：up-sweep 和 down-sweep
    """
    n = len(arr)
    if n <= 1:
        return arr.copy()

    # 工作数组
    work = arr.copy()

    # 阶段1：up-sweep（自底向上配对合并）
    offset = 1
    for d in range(int(math.log2(n)) + 1):
        mask = 2 * offset
        for i in range(n):
            if i & mask:
                work[i] += work[i - offset]
        offset *= 2

    # 阶段2：down-sweep（自顶向下）
    for d in range(int(math.log2(n)) - 1, -1, -1):
        offset = 2 ** d
        for i in range(n):
            if i & (offset - 1) == offset - 1:
                if i + offset < n:
                    work[i + offset] += work[i]

    return work


def verify_prefix_sum(arr: List[float]) -> bool:
    """验证结果正确性"""
    expected = sequential_prefix_sum(arr)
    result = parallel_prefix_sum(arr.copy())
    return expected == result


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 并行前缀和测试 ===\n")

    import random
    import time

    # 测试用例
    test_arrays = [
        [1, 2, 3, 4, 5, 6, 7, 8],
        [5, 1, 3, 2, 8, 4, 7, 6],
        list(range(1, 9)),
        [100] * 8,
    ]

    print("正确性验证：")
    for arr in test_arrays:
        original = arr.copy()
        result = parallel_prefix_sum(arr.copy())
        expected = sequential_prefix_sum(original)
        correct = result == expected
        print(f"  输入: {original}")
        print(f"  期望: {expected}")
        print(f"  结果: {result}")
        print(f"  {'✅ 通过' if correct else '❌ 失败'}\n")

    # 性能测试
    print("性能测试：")
    sizes = [100, 1000, 10000]

    for size in sizes:
        arr = [random.random() for _ in range(size)]

        start = time.time()
        sequential_prefix_sum(arr.copy())
        seq_time = time.time() - start

        start = time.time()
        parallel_prefix_sum(arr.copy(), num_threads=4)
        par_time = time.time() - start

        start = time.time()
        parallel_prefix_sum_hill_steel(arr.copy())
        hs_time = time.time() - start

        print(f"  n={size:5d}: 串行={seq_time*1000:.2f}ms, 并行={par_time*1000:.2f}ms, Hill-Steel={hs_time*1000:.2f}ms")
        print(f"           加速比: {seq_time/par_time:.2f}x / {seq_time/hs_time:.2f}x")

    print("\n注意：对于小规模数据，并行开销可能超过收益")
    print("      前缀和在GPU/大规模并行机上效果更好")
