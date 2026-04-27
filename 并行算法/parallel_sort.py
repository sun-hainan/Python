# -*- coding: utf-8 -*-
"""
算法实现：并行算法 / parallel_sort

本文件实现 parallel_sort 相关的算法功能。
"""

import math
from typing import List, Callable
import threading
import queue


def parallel_merge_sort(data: List, num_threads: int = 4, 
                       key: Callable = None, reverse: bool = False) -> List:
    """
    并行归并排序
    
    算法步骤：
    1. 将数据分成num_threads份
    2. 并行对每份进行排序
    3. 逐步合并已排序的片段
    
    参数:
        data: 输入数据
        num_threads: 线程数量
        key: 排序关键字函数
        reverse: 是否降序
    
    返回:
        排序后的新列表
    """
    if len(data) <= 1:
        return list(data)
    
    # 计算每份的大小
    chunk_size = max(1, len(data) // num_threads)
    chunks = []
    
    # 分割数据
    for i in range(num_threads):
        start = i * chunk_size
        end = min(start + chunk_size, len(data))
        if start < len(data):
            chunks.append(list(data[start:end]))
        else:
            chunks.append([])
    
    # 并行排序每块
    sorted_chunks = []
    threads = []
    
    def sort_chunk(chunk):
        sorted_chunks.append(sorted(chunk, key=key, reverse=reverse))
    
    for chunk in chunks:
        if chunk:
            thread = threading.Thread(target=sort_chunk, args=(chunk,))
            thread.start()
            threads.append(thread)
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    # 依次合并
    while len(sorted_chunks) > 1:
        new_chunks = []
        for i in range(0, len(sorted_chunks), 2):
            if i + 1 < len(sorted_chunks):
                merged = merge_sorted(sorted_chunks[i], sorted_chunks[i+1], key, reverse)
                new_chunks.append(merged)
            else:
                new_chunks.append(sorted_chunks[i])
        sorted_chunks = new_chunks
    
    return sorted_chunks[0] if sorted_chunks else []


def merge_sorted(list_a: List, list_b: List, 
                key: Callable = None, reverse: bool = False) -> List:
    """
    合并两个已排序的列表
    
    参数:
        list_a: 第一个已排序列表
        list_b: 第二个已排序列表
        key: 排序关键字
        reverse: 是否降序
    
    返回:
        合并后的已排序列表
    """
    result = []
    i = j = 0
    
    while i < len(list_a) and j < len(list_b):
        a_val = list_a[i]
        b_val = list_b[j]
        
        if key:
            a_cmp = key(a_val)
            b_cmp = key(b_val)
        else:
            a_cmp = a_val
            b_cmp = b_val
        
        if reverse:
            cond = a_cmp >= b_cmp
        else:
            cond = a_cmp <= b_cmp
        
        if cond:
            result.append(a_val)
            i += 1
        else:
            result.append(b_val)
            j += 1
    
    # 添加剩余元素
    result.extend(list_a[i:])
    result.extend(list_b[j:])
    
    return result


def parallel_quick_sort(data: List, num_threads: int = 4,
                       key: Callable = None, reverse: bool = False) -> List:
    """
    并行快速排序
    
    算法步骤：
    1. 选择pivot
    2. 划分数据为小于pivot和大于pivot两组
    3. 递归并行排序两个子数组
    
    参数:
        data: 输入数据
        num_threads: 可用线程数
        key: 排序关键字
        reverse: 是否降序
    
    返回:
        排序后的新列表
    """
    if len(data) <= 1:
        return list(data)
    
    if num_threads <= 1:
        return sorted(data, key=key, reverse=reverse)
    
    # 选择pivot（使用中位数）
    mid = len(data) // 2
    sorted_pivots = sorted([data[0], data[mid], data[-1]], key=key, reverse=reverse)
    pivot = sorted_pivots[1]
    
    # 划分
    if key:
        less = [x for x in data if key(x) < key(pivot)]
        greater = [x for x in data if key(x) > key(pivot)]
        equal = [x for x in data if key(x) == key(pivot)]
    else:
        less = [x for x in data if x < pivot]
        greater = [x for x in data if x > pivot]
        equal = [x for x in data if x == pivot]
    
    # 并行排序两个子数组
    threads = []
    results = [None, None]
    
    half_threads = max(1, num_threads // 2)
    
    def sort_less():
        results[0] = parallel_quick_sort(less, half_threads, key, reverse)
    
    def sort_greater():
        results[1] = parallel_quick_sort(greater, half_threads, key, reverse)
    
    t1 = threading.Thread(target=sort_less)
    t2 = threading.Thread(target=sort_greater)
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()
    
    # 合并结果
    if reverse:
        return results[1] + equal + results[0]
    else:
        return results[0] + equal + results[1]


def parallel_sample_sort(data: List, num_samples: int = 10) -> List:
    """
    样本排序 - 基于采样的并行排序
    
    适合大规模数据的分布式排序
    
    参数:
        data: 输入数据
        num_samples: 采样点数量
    
    返回:
        排序后的列表
    """
    if len(data) <= 1:
        return list(data)
    
    n = len(data)
    
    # 1. 将数据分成多个桶
    num_buckets = num_samples + 1
    bucket_size = max(1, n // num_buckets)
    
    # 2. 在每个桶中选择采样点
    samples = []
    for i in range(num_buckets):
        start = i * bucket_size
        end = min(start + bucket_size, n)
        if start < n:
            bucket_data = data[start:end]
            # 从每个桶中采样
            sample_size = min(3, len(bucket_data))
            step = max(1, len(bucket_data) // sample_size)
            for j in range(0, len(bucket_data), step):
                samples.append(bucket_data[j])
                if len([s for s in samples if s == bucket_data[j]]) >= sample_size:
                    break
    
    # 3. 对采样点排序得到splitters
    samples = sorted(set(samples))[:num_samples]
    
    # 4. 根据splitters划分数据
    buckets = [[] for _ in range(len(samples) + 1)]
    
    for item in data:
        # 找到应该放入的桶
        pos = 0
        for i, splitter in enumerate(samples):
            if item > splitter:
                pos = i + 1
        buckets[pos].append(item)
    
    # 5. 并行排序每个桶
    sorted_buckets = []
    threads = []
    
    def sort_bucket(bucket):
        sorted_buckets.append(sorted(bucket))
    
    for bucket in buckets:
        if bucket:
            thread = threading.Thread(target=sort_bucket, args=(bucket,))
            thread.start()
            threads.append(thread)
    
    for thread in threads:
        thread.join()
    
    # 6. 合并所有桶
    result = []
    for bucket in sorted_buckets:
        result.extend(bucket)
    
    return result


def parallel_radix_sort(data: List, num_bits: int = 8,
                       base: int = 2) -> List:
    """
    并行基数排序
    
    基于位的排序，从低位到高位排序
    
    参数:
        data: 输入数据
        num_bits: 每轮处理的位数
        base: 基数（默认2表示二进制）
    
    返回:
        排序后的列表
    """
    if len(data) <= 1:
        return list(data)
    
    # 确定最大值的位数
    max_val = max(abs(x) for x in data if isinstance(x, (int, float)))
    num_bits_needed = max(1, int(math.log2(max_val + 1)) + 1)
    
    result = list(data)
    
    # 逐轮排序
    num_buckets = 2 ** num_bits
    
    for bit_offset in range(0, num_bits_needed, num_bits):
        # 创建桶
        buckets = [[] for _ in range(num_buckets)]
        
        # 分配到桶
        for item in result:
            mask = (1 << num_bits) - 1
            bucket_idx = (abs(item) >> bit_offset) & mask if item >= 0 else 0
            buckets[bucket_idx].append(item)
        
        # 合并桶
        result = []
        for bucket in buckets:
            result.extend(bucket)
    
    return result


# ==================== 测试代码 ====================
if __name__ == "__main__":
    import random
    import time
    
    # 测试用例1：并行归并排序
    print("=" * 50)
    print("测试1: 并行归并排序")
    print("=" * 50)
    
    data = [5, 2, 8, 1, 9, 3, 7, 4, 6]
    
    result = parallel_merge_sort(data, num_threads=4)
    print(f"输入: {data}")
    print(f"输出: {result}")
    print(f"正确: {result == sorted(data)}")
    
    # 测试用例2：并行快速排序
    print("\n" + "=" * 50)
    print("测试2: 并行快速排序")
    print("=" * 50)
    
    data = [5, 2, 8, 1, 9, 3, 7, 4, 6]
    
    result = parallel_quick_sort(data, num_threads=4)
    print(f"输入: {data}")
    print(f"输出: {result}")
    print(f"正确: {result == sorted(data)}")
    
    # 测试用例3：大规模性能对比
    print("\n" + "=" * 50)
    print("测试3: 性能对比")
    print("=" * 50)
    
    sizes = [1000, 10000]
    
    for size in sizes:
        data = [random.randint(1, 10000) for _ in range(size)]
        
        # Python内置排序
        start = time.time()
        _ = sorted(data)
        builtin_time = time.time() - start
        
        # 并行归并排序
        start = time.time()
        _ = parallel_merge_sort(data, num_threads=4)
        merge_time = time.time() - start
        
        # 并行快速排序
        start = time.time()
        _ = parallel_quick_sort(data, num_threads=4)
        quick_time = time.time() - start
        
        print(f"\nn={size}:")
        print(f"  内置排序: {builtin_time*1000:.2f}ms")
        print(f"  并行归并: {merge_time*1000:.2f}ms (加速 {builtin_time/merge_time:.2f}x)")
        print(f"  并行快排: {quick_time*1000:.2f}ms (加速 {builtin_time/quick_time:.2f}x)")
    
    # 测试用例4：样本排序
    print("\n" + "=" * 50)
    print("测试4: 样本排序")
    print("=" * 50)
    
    data = [random.randint(1, 100) for _ in range(20)]
    print(f"输入: {data}")
    
    result = parallel_sample_sort(data, num_samples=5)
    print(f"输出: {result}")
    print(f"正确: {result == sorted(data)}")
    
    # 测试用例5：带key的排序
    print("\n" + "=" * 50)
    print("测试5: 带key的并行排序")
    print("=" * 50)
    
    students = [('Alice', 85), ('Bob', 92), ('Charlie', 78), ('David', 95)]
    
    result = parallel_merge_sort(students, key=lambda x: x[1], reverse=True)
    print("按分数降序:")
    for name, score in result:
        print(f"  {name}: {score}")
