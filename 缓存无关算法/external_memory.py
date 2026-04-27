# -*- coding: utf-8 -*-
"""
算法实现：缓存无关算法 / external_memory

本文件实现 external_memory 相关的算法功能。
"""

from typing import List, Tuple


def buffer_tree_insert(items: List[int], buffer_size: int = 4) -> int:
    """
    缓冲区树插入
    使用缓冲区减少I/O次数
    
    Args:
        items: 要插入的元素列表
        buffer_size: 缓冲区大小
    
    Returns:
        I/O次数
    """
    # 简化:每buffer_size个元素触发一次I/O
    ios = len(items) // buffer_size
    if len(items) % buffer_size != 0:
        ios += 1
    return ios


def external_merge_sort(n: int, M: int) -> Tuple[int, List[List[int]]]:
    """
    外存归并排序的I/O复杂度分析
    
    Args:
        n: 元素总数
        M: 内存大小(能容纳的元素数)
    
    Returns:
        (I/O次数, 生成的runs列表)
    """
    # 每个runs的大小为M
    num_runs = (n + M - 1) // M
    runs = [list(range(i * M, min((i + 1) * M, n))) for i in range(num_runs)]
    
    # 排序每个run
    for run in runs:
        run.sort()
    
    # 归并runs
    # 每趟归并处理2*M个元素
    ios = 0
    while len(runs) > 1:
        new_runs = []
        
        for i in range(0, len(runs), 2):
            if i + 1 < len(runs):
                # 归并两个runs
                merged = merge_two_runs(runs[i], runs[i + 1])
                new_runs.append(merged)
                ios += 2  # 读两个runs,写一个新run
            else:
                new_runs.append(runs[i])
                ios += 1  # 写最后一个run
        
        runs = new_runs
    
    return ios, runs


def merge_two_runs(a: List[int], b: List[int]) -> List[int]:
    """归并两个有序数组"""
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


def scan_disk_block(n: int, block_size: int) -> int:
    """
    扫描磁盘的I/O次数
    
    Args:
        n: 元素总数
        block_size: 块大小
    
    Returns:
        I/O次数
    """
    return (n + block_size - 1) // block_size


def sorted_access_analysis(queries: List[Tuple[int, int]], 
                          block_size: int = 4) -> int:
    """
    有序访问模式的I/O分析
    
    Args:
        queries: 查询列表[(起始, 结束), ...]
        block_size: 块大小
    
    Returns:
        估计的I/O次数
    """
    if not queries:
        return 0
    
    # 按起始位置排序
    sorted_queries = sorted(queries, key=lambda x: x[0])
    
    ios = 0
    current_block = -1
    
    for start, end in sorted_queries:
        start_block = start // block_size
        end_block = end // block_size
        
        if start_block != current_block:
            ios += 1
            current_block = start_block
        
        # 计算连续块
        ios += max(0, end_block - start_block)
        current_block = end_block
    
    return ios


def cache_oblivious_analysis(n: int, M: int, B: int) -> dict:
    """
    缓存无关算法的I/O分析
    
    Args:
        n: 问题大小
        M: 缓存大小
        B: 缓存块大小
    
    Returns:
        分析结果字典
    """
    import math
    
    results = {}
    
    # 扫描
    results['scan'] = n / B
    
    # 排序(O(n log n)次操作)
    # 归并排序的I/O复杂度: O((n/B) * log_{M/B}(n/M))
    log_factor = math.log(n / M) / math.log(M / B) if M > 0 and M / B > 1 else 1
    results['merge_sort'] = (n / B) * log_factor
    
    # 矩阵乘法
    # O(n^3 / (B * sqrt(M))) for n x n矩阵
    results['matrix_multiply'] = (n ** 3) / (B * math.sqrt(M))
    
    # FFT
    # O((n/B) * log_n)
    results['fft'] = (n / B) * math.log(n) / math.log(2)
    
    return results


def optimal_block_transfer(N: int, M: int, B: int) -> int:
    """
    计算最优的块传输大小
    
    Args:
        N: 总数据大小
        M: 内存大小
        B: 最小块大小
    
    Returns:
        最优块大小
    """
    import math
    
    # 在I/O模型中,最优的块大小通常是M/B的某种组合
    # 这里简化:返回M/2或N/B中的较大者
    
    optimal = max(M // 2, N // B)
    return optimal


# 测试代码
if __name__ == "__main__":
    # 测试1: 缓冲区树
    print("测试1 - 缓冲区树:")
    items = list(range(100))
    ios = buffer_tree_insert(items, buffer_size=10)
    print(f"  插入100个元素, buffer_size=10: {ios}次I/O")
    
    # 测试2: 外存归并排序
    print("\n测试2 - 外存归并排序:")
    n = 1000
    M = 100
    
    ios, final_runs = external_merge_sort(n, M)
    print(f"  n={n}, M={M}")
    print(f"  I/O次数: {ios}")
    print(f"  最终runs数: {len(final_runs)}")
    
    # 测试3: 扫描分析
    print("\n测试3 - 磁盘扫描:")
    for n, B in [(1000, 10), (1000, 100), (10000, 100)]:
        ios = scan_disk_block(n, B)
        print(f"  n={n}, B={B}: {ios}次I/O")
    
    # 测试4: 有序访问
    print("\n测试4 - 有序访问:")
    queries = [(10, 50), (30, 70), (60, 90), (5, 15)]
    ios = sorted_access_analysis(queries, block_size=10)
    print(f"  查询: {queries}")
    print(f"  I/O次数: {ios}")
    
    # 测试5: 缓存无关分析
    print("\n测试5 - 缓存无关分析:")
    results = cache_oblivious_analysis(1000, 100, 10)
    print(f"  n=1000, M=100, B=10:")
    for algo, ios in results.items():
        print(f"    {algo}: {ios:.2f}次I/O")
    
    # 测试6: 最优块大小
    print("\n测试6 - 最优块大小:")
    for N, M in [(10000, 1000), (100000, 10000), (1000000, 100000)]:
        optimal = optimal_block_transfer(N, M, 10)
        print(f"  N={N}, M={M}: 最优块大小={optimal}")
    
    print("\n所有测试完成!")
