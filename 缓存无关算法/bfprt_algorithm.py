# -*- coding: utf-8 -*-
"""
算法实现：缓存无关算法 / bfprt_algorithm

本文件实现 bfprt_algorithm 相关的算法功能。
"""

from typing import List, Tuple
import random


def median_of_medians(arr: List[int], k: int) -> int:
    """
    BFPRT算法(Blum-Floyd-Pratt-Tarjan-Ruben)
    线性时间选择第k小的元素
    
    Args:
        arr: 输入数组
        k: 第k小(k从1开始)
    
    Returns:
        第k小的元素
    """
    n = len(arr)
    if n <= 5:
        return sorted(arr)[k - 1]
    
    # 1. 将数组分成5个一组,计算每组的中位数
    medians = []
    for i in range(0, n, 5):
        group = arr[i:min(i + 5, n)]
        medians.append(sorted(group)[len(group) // 2])
    
    # 2. 递归找中位数的中位数
    pivot = median_of_medians(medians, len(medians) // 2 + 1)
    
    # 3. 根据pivot分割数组
    left = [x for x in arr if x < pivot]
    equal = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    # 4. 递归查找
    if k <= len(left):
        return median_of_medians(left, k)
    elif k <= len(left) + len(equal):
        return pivot
    else:
        return median_of_medians(right, k - len(left) - len(equal))


def partition(arr: List[int], pivot_idx: int) -> Tuple[int, int, int]:
    """
    三路划分
    
    Args:
        arr: 数组
        pivot_idx: pivot索引
    
    Returns:
        (左部分长度, pivot部分长度, 右部分长度)
    """
    pivot = arr[pivot_idx]
    
    left = []
    middle = []
    right = []
    
    for x in arr:
        if x < pivot:
            left.append(x)
        elif x == pivot:
            middle.append(x)
        else:
            right.append(x)
    
    return len(left), len(middle), len(right)


def bfprt_select(arr: List[int], k: int) -> int:
    """
    BFPRT选择算法的优化实现
    
    Args:
        arr: 输入数组
        k: 第k小(k从1开始)
    
    Returns:
        第k小的元素
    """
    n = len(arr)
    if n == 0:
        raise ValueError("数组为空")
    if k < 1 or k > n:
        raise ValueError(f"k必须在1到{n}之间")
    
    working = arr.copy()
    
    while True:
        if len(working) <= 5:
            return sorted(working)[k - 1]
        
        # 计算中位数的中位数作为pivot
        groups = [working[i:i+5] for i in range(0, len(working), 5)]
        medians = [sorted(g)[len(g)//2] for g in groups]
        
        if len(medians) <= 5:
            pivot = sorted(medians)[len(medians)//2]
        else:
            pivot = bfprt_select(medians, len(medians)//2 + 1)
        
        # 三路划分
        left_len, mid_len, right_len = partition(working, working.index(pivot))
        
        if k <= left_len:
            working = working[:left_len]
        elif k <= left_len + mid_len:
            return pivot
        else:
            working = working[left_len + mid_len:]
            k -= left_len + mid_len


def quick_select(arr: List[int], k: int) -> int:
    """
    快速选择算法(期望线性,最坏O(n²))
    
    Args:
        arr: 输入数组
        k: 第k小
    
    Returns:
        第k小的元素
    """
    working = arr.copy()
    
    while True:
        if len(working) == 1:
            return working[0]
        
        # 随机选择pivot
        pivot_idx = random.randint(0, len(working) - 1)
        pivot = working[pivot_idx]
        
        # 划分
        left = [x for x in working if x < pivot]
        equal = [x for x in working if x == pivot]
        right = [x for x in working if x > pivot]
        
        if k <= len(left):
            working = left
        elif k <= len(left) + len(equal):
            return pivot
        else:
            working = right
            k -= len(left) + len(equal)


def find_kth_smallest(arr: List[int], k: int, method: str = 'bfprt') -> int:
    """
    找第k小元素的便捷函数
    
    Args:
        arr: 输入数组
        k: 第k小
        method: 'bfprt' 或 'quick'
    
    Returns:
        第k小的元素
    """
    if method == 'bfprt':
        return bfprt_select(arr, k)
    else:
        return quick_select(arr, k)


def order_statistics(arr: List[int]) -> List[int]:
    """
    计算所有顺序统计量(排序后的结果)
    
    Args:
        arr: 输入数组
    
    Returns:
        排序后的数组
    """
    return sorted(arr)


# 测试代码
if __name__ == "__main__":
    import time
    
    # 测试1: 基本功能
    print("测试1 - 基本功能:")
    arr1 = [7, 2, 1, 6, 8, 5, 3, 4]
    
    for k in range(1, len(arr1) + 1):
        result = bfprt_select(arr1, k)
        expected = sorted(arr1)[k - 1]
        print(f"  第{k}小: {result} (期望{expected})")
    
    # 测试2: 重复元素
    print("\n测试2 - 重复元素:")
    arr2 = [3, 3, 1, 2, 3, 1, 2, 3]
    
    for k in range(1, 5):
        result = bfprt_select(arr2, k)
        print(f"  第{k}小: {result}")
    
    # 测试3: BFPRT vs Quick Select
    print("\n测试3 - BFPRT vs Quick Select:")
    arr3 = [random.randint(1, 1000) for _ in range(100)]
    k = 50
    
    start = time.time()
    for _ in range(1000):
        bfprt_select(arr3, k)
    time_bfprt = time.time() - start
    
    start = time.time()
    for _ in range(1000):
        quick_select(arr3, k)
    time_quick = time.time() - start
    
    print(f"  BFPRT: {time_bfprt:.4f}s")
    print(f"  QuickSelect: {time_quick:.4f}s")
    
    # 测试4: 大规模数据
    print("\n测试4 - 大规模数据:")
    for n in [1000, 10000, 100000]:
        arr_large = [random.randint(1, n * 10) for _ in range(n)]
        k = n // 2
        
        start = time.time()
        result = bfprt_select(arr_large, k)
        time_bfprt = time.time() - start
        
        start = time.time()
        expected = sorted(arr_large)[k - 1]
        time_sort = time.time() - start
        
        print(f"  n={n}: BFPRT={time_bfprt:.4f}s, 排序={time_sort:.4f}s")
        print(f"    第{n//2}小={result}, 正确={result==expected}")
    
    # 测试5: 验证线性时间界
    print("\n测试5 - 线性时间界验证:")
    print("  BFPRT保证O(n)最坏情况")
    print("  QuickSelect期望O(n),但最坏O(n²)")
    
    # 故意构造最坏情况
    print("  构造有序数组测试:")
    arr_sorted = list(range(1, 101))
    
    start = time.time()
    result = quick_select(arr_sorted, 50)
    time_qs = time.time() - start
    
    start = time.time()
    result = bfprt_select(arr_sorted, 50)
    time_bfprt = time.time() - start
    
    print(f"    QuickSelect: {time_qs:.6f}s")
    print(f"    BFPRT: {time_bfprt:.6f}s")
    
    print("\n所有测试完成!")
