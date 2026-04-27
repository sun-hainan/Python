# -*- coding: utf-8 -*-
"""
算法实现：外部内存算法 / cache_oblivious_sort

本文件实现 cache_oblivious_sort 相关的算法功能。
"""

import math


def min_cache_size(data_size, block_size):
    """
    计算最小缓存大小估计。

    参数:
        data_size: 数据大小 N
        block_size: 块大小 B

    返回:
        最小缓存大小 M
    """
    # 选择 M 使得 M^2 = N * B 时最优
    return int(math.sqrt(data_size * block_size))


def blocked_memory_access(data, block_size, cache_size):
    """
    模拟分块内存访问。

    参数:
        data: 数据数组
        block_size: 块大小 B
        cache_size: 缓存大小 M

    返回:
        内存传输次数
    """
    n = len(data)
    num_blocks = (n + block_size - 1) // block_size
    # 每块第一次访问会导致缓存未命中
    # 简化：假设缓存可以容纳 num_blocks 块
    cache_blocks = cache_size // block_size
    cache_misses = (num_blocks + cache_blocks - 1) // cache_blocks
    return cache_misses


def k_way_merge(sorted_lists, working_memory):
    """
    K路归并：将 K 个已排序列表合并为一个排序列表。

    参数:
        sorted_lists: 已排序列表的列表
        working_memory: 工作内存（用于小规模归并）

    返回:
        合并后的排序列表
    """
    if not sorted_lists:
        return []
    if len(sorted_lists) == 1:
        return sorted_lists[0]

    # 使用最小堆（优先级队列）进行 K 路归并
    import heapq

    heap = []
    result = []

    # 初始化：将每个列表的第一个元素入堆
    for i, lst in enumerate(sorted_lists):
        if lst:
            heapq.heappush(heap, (lst[0], i, 0))

    while heap:
        val, list_idx, element_idx = heapq.heappop(heap)
        result.append(val)

        # 从同一列表取下一个元素
        next_idx = element_idx + 1
        if next_idx < len(sorted_lists[list_idx]):
            next_val = sorted_lists[list_idx][next_idx]
            heapq.heappush(heap, (next_val, list_idx, next_idx))

    return result


def cache_oblivious_merge_sort(data, block_size, depth=0):
    """
    缓存无关的归并排序。

    特点：
    - 递归地将数据分成两半
    - 在子数组小于缓存时使用 naively 排序
    - 大于缓存时递归归并

    参数:
        data: 待排序数组
        block_size: 内存块大小 B
        depth: 递归深度（用于分析）

    返回:
        排序后的数组
    """
    n = len(data)
    if n <= block_size:
        # 缓存内排序：直接插入排序
        return sorted(data)
    else:
        # 分成两半
        mid = n // 2
        left = data[:mid]
        right = data[mid:]

        # 递归排序
        sorted_left = cache_oblivious_merge_sort(left, block_size, depth + 1)
        sorted_right = cache_oblivious_merge_sort(right, block_size, depth + 1)

        # 归并
        return k_way_merge([sorted_left, sorted_right], block_size)


def multi_way_merge_sort(data, k, block_size):
    """
    多路归并排序：将数据分成 K 段，递归排序后 K 路归并。

    参数:
        data: 待排序数组
        k: 分段数（影响缓存命中率）
        block_size: 块大小

    返回:
        排序后的数组
    """
    n = len(data)
    if n <= block_size * k:
        return sorted(data)

    # 分成 k 段
    segment_size = (n + k - 1) // k
    segments = []
    for i in range(k):
        start = i * segment_size
        end = min(start + segment_size, n)
        if start < n:
            segments.append(data[start:end])

    # 递归排序每段
    sorted_segments = []
    for seg in segments:
        sorted_seg = multi_way_merge_sort(seg, k, block_size)
        sorted_segments.append(sorted_seg)

    # K 路归并
    return k_way_merge(sorted_segments, block_size)


if __name__ == "__main__":
    print("=== 缓存无关排序测试 ===")

    # 测试数据
    import random
    random.seed(42)
    test_data = [random.randint(0, 100) for _ in range(64)]

    block_size = 4  # 块大小 B
    cache_size = min_cache_size(len(test_data), block_size)

    print(f"数据大小 N = {len(test_data)}")
    print(f"块大小 B = {block_size}")
    print(f"缓存大小 M = {cache_size}")

    # 内存传输估计
    transfers = blocked_memory_access(test_data, block_size, cache_size)
    print(f"估计内存传输次数: {transfers}")

    # 二路归并排序
    sorted_2way = cache_oblivious_merge_sort(test_data[:], block_size)
    print(f"\n二路归并排序结果前10个: {sorted_2way[:10]}")
    print(f"是否有序: {sorted_2way == sorted(test_data)}")

    # 多路归并排序
    for k in [2, 4, 8]:
        sorted_kway = multi_way_merge_sort(test_data[:], k, block_size)
        print(f"\n{k}路归并排序前10个: {sorted_kway[:10]}")
        print(f"是否有序: {sorted_kway == sorted(test_data)}")

    print("\n缓存无关排序特性:")
    print("  不假设缓存层次：天然适配多层缓存")
    print("  K路归并：减少内存传输次数")
    print("  递归分治：每层递归都接近最优 I/O 复杂度")
