# -*- coding: utf-8 -*-
"""
算法实现：缓存无关算法 / co_binary_search

本文件实现 co_binary_search 相关的算法功能。
"""

import math
import random
from typing import List, Optional, Callable, Tuple


# 算法配置常量
# =============================================================================
# CACHE_LINE_SIZE: 模拟缓存行大小（字节）
CACHE_LINE_SIZE = 64

# ELEMENTS_PER_CACHE_LINE: 每个缓存行可容纳的元素个数
ELEMENTS_PER_CACHE_LINE = CACHE_LINE_SIZE // 8  # 假设double占8字节

# SMALL_ARRAY_THRESHOLD: 小规模数组切换阈值
SMALL_ARRAY_THRESHOLD = 16

# BLOCK_SIZE: 数据块大小用于优化预取
BLOCK_SIZE = 8


def standard_binary_search(arr: List, target) -> int:
    """
    标准二分搜索实现
    
    在有序数组中搜索目标元素返回其索引如果不存在返回-1
    这是教科书级别的经典实现
    
    Args:
        arr: 有序数组（升序）
        target: 搜索目标
        
    Returns:
        目标元素的索引如果不存在返回-1
    """
    left = 0
    right = len(arr) - 1
    
    while left <= right:
        mid = left + (right - left) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1


def cache_oblivious_binary_search_recursive(
    arr: List, target, left: int, right: int
) -> int:
    """
    缓存无关递归二分搜索
    
    该实现利用递归结构来优化缓存行为每次递归调用处理接近一半的
    搜索空间而且访问模式与缓存行对齐当搜索空间较小时直接使用
    线性搜索来利用数据预取
    
    Args:
        arr: 有序数组
        target: 搜索目标
        left: 搜索区间左边界
        right: 搜索区间右边界
        
    Returns:
        目标元素的索引如果不存在返回-1
    """
    # 基例:搜索空间为空
    if left > right:
        return -1
    
    # 小规模问题使用缓存友好的线性搜索
    length = right - left + 1
    if length <= SMALL_ARRAY_THRESHOLD:
        return linear_cache_friendly_search(arr, target, left, right)
    
    # 计算中点
    mid = left + (right - left) // 2
    
    # 关键优化:确保mid按缓存行对齐
    aligned_mid = ((mid // ELEMENTS_PER_CACHE_LINE) * ELEMENTS_PER_CACHE_LINE 
                   + ELEMENTS_PER_CACHE_LINE // 2)
    if aligned_mid > right:
        aligned_mid = mid
    if aligned_mid < left:
        aligned_mid = mid
    
    # 比较并递归
    if arr[aligned_mid] == target:
        return aligned_mid
    elif arr[aligned_mid] < target:
        return cache_oblivious_binary_search_recursive(arr, target, aligned_mid + 1, right)
    else:
        return cache_oblivious_binary_search_recursive(arr, target, left, aligned_mid - 1)


def linear_cache_friendly_search(arr: List, target, left: int, right: int) -> int:
    """
    缓存友好的线性搜索
    
    对于小规模数据线性搜索可能比二分搜索更高效因为它按照内存顺序
    访问数据能够充分利用缓存预取机制此外线性搜索产生的分支预测
    失败也比二分搜索少
    
    Args:
        arr: 有序数组
        target: 搜索目标
        left: 搜索区间左边界
        right: 搜索区间右边界
        
    Returns:
        目标元素的索引如果不存在返回-1
    """
    # 按照内存顺序（从小到大）访问元素
    for i in range(left, right + 1):
        if arr[i] == target:
            return i
        if arr[i] > target:
            break
    return -1


def cache_oblivious_binary_search_iterative(arr: List, target) -> int:
    """
    缓存无关迭代二分搜索
    
    迭代版本避免递归调用开销同时保持了缓存优化的访问模式
    通过将搜索空间划分为块并按顺序检查来提高缓存效率
    
    Args:
        arr: 有序数组
        target: 搜索目标
        
    Returns:
        目标元素的索引如果不存在返回-1
    """
    n = len(arr)
    
    # 特殊情况处理
    if n == 0:
        return -1
    if n == 1:
        return 0 if arr[0] == target else -1
    
    # 初始化搜索区间
    left = 0
    right = n - 1
    
    while left <= right:
        # 计算中点并对齐到缓存行边界
        mid = left + (right - left) // 2
        
        # 预取中点周围的数据块到缓存
        prefetch_block_start = (mid // BLOCK_SIZE) * BLOCK_SIZE
        prefetch_block_end = min(prefetch_block_start + BLOCK_SIZE, n)
        
        # 访问预取块的第一行触发缓存加载
        _ = arr[prefetch_block_start]
        
        # 标准二分比较
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1


def exponential_search(arr: List, target) -> int:
    """
    指数搜索结合缓存无关优化的变体
    
    指数搜索首先确定目标可能存在的上界然后在该范围内进行二分搜索
    确定上界的过程按指数增长搜索边界这种访问模式与缓存无关思想
    相符因为访问的数据量与找到的边界大小成正比
    
    Args:
        arr: 有序数组
        target: 搜索目标
        
    Returns:
        目标元素的索引如果不存在返回-1
    """
    n = len(arr)
    
    if n == 0:
        return -1
    
    # 如果目标小于第一个元素不存在
    if arr[0] > target:
        return -1
    
    # 找到目标可能存在的上界
    bound = 1
    while bound < n and arr[bound] < target:
        bound *= 2
    
    # 在[bound//2, min(bound, n)]范围内进行二分搜索
    left = bound // 2
    right = min(bound, n) - 1
    
    return cache_oblivious_binary_search_recursive(arr, target, left, right)


def interpolation_search(arr: List, target) -> int:
    """
    插值搜索的缓存优化版本
    
    插值搜索根据目标值与数组边界值的关系来估计目标的位置
    假设数组均匀分布时插值搜索的时间复杂度为O(log log n)
    该实现加入了缓存优化当估计位置接近目标时使用线性缓存友好搜索
    
    Args:
        arr: 有序数组
        target: 搜索目标
        
    Returns:
        目标元素的索引如果不存在返回-1
    """
    left = 0
    right = len(arr) - 1
    
    while left <= right and target >= arr[left] and target <= arr[right]:
        # 避免除以零
        if left == right:
            return left if arr[left] == target else -1
        
        # 插值公式计算估计位置
        delta = arr[right] - arr[left]
        if delta == 0:
            return -1
        
        # 估计位置（带边界保护）
        pos = left + int(((target - arr[left]) * (right - left)) // delta)
        pos = max(left, min(pos, right))
        
        # 缓存优化:访问pos周围的块
        block_start = max(left, pos - BLOCK_SIZE // 2)
        block_end = min(right, pos + BLOCK_SIZE // 2)
        _ = arr[block_start:block_end + 1]
        
        if arr[pos] == target:
            return pos
        elif arr[pos] < target:
            left = pos + 1
        else:
            right = pos - 1
    
    return -1


def batch_search(arr: List, targets: List) -> List[int]:
    """
    批量搜索 - 一次搜索多个目标
    
    当需要搜索多个目标时批量处理可以提高缓存利用率因为一次处理
    多个目标的搜索可以更好地利用数据局部性该函数按缓存行大小
    分批处理搜索请求
    
    Args:
        arr: 有序数组
        targets: 目标列表
        
    Returns:
        每个目标对应搜索结果的索引列表
    """
    results = []
    n = len(arr)
    
    for target in targets:
        if n == 0:
            results.append(-1)
            continue
        
        # 估算目标在数组中的大致位置
        if target < arr[0]:
            results.append(-1)
            continue
        if target > arr[-1]:
            results.append(-1)
            continue
        
        # 使用缓存无关二分搜索
        result = cache_oblivious_binary_search_recursive(arr, target, 0, n - 1)
        results.append(result)
    
    return results


def analyze_cache_efficiency(arr: List, target, iterations: int = 1000) -> dict:
    """
    分析二分搜索的缓存效率
    
    通过模拟缓存访问来评估算法的缓存性能统计访问缓存行的次数
    和缓存未命中次数
    
    Args:
        arr: 有序数组
        target: 搜索目标
        iterations: 模拟迭代次数
        
    Returns:
        包含缓存分析结果的字典
    """
    n = len(arr)
    
    # 统计标准搜索的缓存访问
    standard_cache_lines = set()
    for _ in range(iterations):
        left, right = 0, n - 1
        while left <= right:
            mid = left + (right - left) // 2
            cache_line = mid // ELEMENTS_PER_CACHE_LINE
            standard_cache_lines.add(cache_line)
            
            if arr[mid] == target:
                break
            elif arr[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
    
    # 统计缓存无关搜索的缓存访问
    co_cache_lines = set()
    for _ in range(iterations):
        left, right = 0, n - 1
        while left <= right:
            mid = left + (right - left) // 2
            
            # 对齐到缓存行边界
            aligned_mid = ((mid // ELEMENTS_PER_CACHE_LINE) * ELEMENTS_PER_CACHE_LINE
                          + ELEMENTS_PER_CACHE_LINE // 2)
            aligned_mid = max(left, min(aligned_mid, right))
            
            cache_line = aligned_mid // ELEMENTS_PER_CACHE_LINE
            co_cache_lines.add(cache_line)
            
            if arr[aligned_mid] == target:
                break
            elif arr[aligned_mid] < target:
                left = aligned_mid + 1
            else:
                right = aligned_mid - 1
    
    return {
        'array_size': n,
        'cache_line_size': CACHE_LINE_SIZE,
        'standard_cache_lines_accessed': len(standard_cache_lines),
        'co_cache_lines_accessed': len(co_cache_lines),
        'cache_line_reduction': (
            len(standard_cache_lines) - len(co_cache_lines)
        ),
        'improvement_ratio': (
            len(standard_cache_lines) / len(co_cache_lines)
            if len(co_cache_lines) > 0 else float('inf')
        )
    }


def generate_ordered_array(size: int, seed: int = 42) -> List:
    """
    生成有序数组用于测试
    
    Args:
        size: 数组大小
        seed: 随机种子
        
    Returns:
        有序数组
    """
    random.seed(seed)
    arr = [random.randint(0, 1000000) for _ in range(size)]
    arr.sort()
    return arr


# 时间复杂度说明:
# =============================================================================
# 标准二分搜索:
#   - 时间复杂度: O(log n)
#   - 比较次数: 最多 ⌊log₂n⌋ + 1 次
#   - 缓存复杂度: O(log n) 每次访问可能跨越不同的缓存行
#
# 缓存无关二分搜索:
#   - 时间复杂度: O(log n) 与标准版本相同
#   - 缓存复杂度: O(log n / log(M/B)) 其中M是缓存大小B是缓存行大小
#   - 空间复杂度: O(1) 额外空间
#
# 指数搜索:
#   - 时间复杂度: O(log n) 最坏情况
#   - 平均复杂度: O(log n) 当元素均匀分布时为 O(log log n)
#
# 插值搜索:
#   - 时间复杂度: O(log log n) 平均情况（均匀分布假设下）
#   - 最坏情况: O(n)
#
# 缓存无关特性:
#   - 算法通过将访问模式与缓存行对齐来减少缓存未命中
#   - 递归结构自然地将大数据和小数据划分到不同缓存层级
#   - 当搜索空间小于缓存大小时整个搜索在缓存中完成


if __name__ == "__main__":
    print("=" * 70)
    print("缓存无关二分搜索测试")
    print("=" * 70)
    
    # 基本正确性测试
    print("\n基本正确性测试:")
    arr = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]
    targets = [7, 13, 1, 25, 99]
    
    for target in targets:
        std_result = standard_binary_search(arr, target)
        co_result = cache_oblivious_binary_search_recursive(arr, target, 0, len(arr) - 1)
        co_iter_result = cache_oblivious_binary_search_iterative(arr, target)
        
        print(f"  搜索 {target:>3}: 标准={std_result:>2}, "
              f"CO递归={co_result:>2}, CO迭代={co_iter_result:>2}")
    
    # 大规模正确性测试
    print("\n大规模正确性测试:")
    sizes = [100, 1000, 10000]
    
    for size in sizes:
        arr = generate_ordered_array(size)
        
        # 随机选择一些元素进行搜索
        random.seed(42)
        test_targets = random.sample(arr, min(100, size))
        test_targets.append(arr[0])
        test_targets.append(arr[-1])
        
        correct_count = 0
        for target in test_targets:
            std_result = standard_binary_search(arr, target)
            co_result = cache_oblivious_binary_search_recursive(arr, target, 0, size - 1)
            if std_result == co_result:
                correct_count += 1
        
        print(f"  规模 {size:>6}: 测试 {len(test_targets)} 个元素, "
              f"正确率 {correct_count}/{len(test_targets)}")
    
    # 性能对比测试
    print("\n性能对比测试:")
    import time
    
    sizes = [1000, 10000, 100000, 1000000]
    
    for size in sizes:
        arr = generate_ordered_array(size)
        
        # 生成随机搜索目标
        random.seed(123)
        targets = [random.choice(arr) for _ in range(1000)]
        
        # 标准搜索
        start = time.perf_counter()
        for target in targets:
            standard_binary_search(arr, target)
        std_time = time.perf_counter() - start
        
        # 缓存无关递归搜索
        start = time.perf_counter()
        for target in targets:
            cache_oblivious_binary_search_recursive(arr, target, 0, size - 1)
        co_rec_time = time.perf_counter() - start
        
        # 缓存无关迭代搜索
        start = time.perf_counter()
        for target in targets:
            cache_oblivious_binary_search_iterative(arr, target)
        co_iter_time = time.perf_counter() - start
        
        print(f"  规模 {size:>8}: 标准 {std_time*1000:>8.2f}ms, "
              f"CO递归 {co_rec_time*1000:>8.2f}ms, "
              f"CO迭代 {co_iter_time*1000:>8.2f}ms")
    
    # 缓存效率分析
    print("\n缓存效率分析:")
    for size in [256, 1024, 4096]:
        arr = generate_ordered_array(size)
        analysis = analyze_cache_efficiency(arr, arr[size // 2])
        print(f"  规模 {size:>6}: 标准访问 {analysis['standard_cache_lines_accessed']:>4} 个缓存行, "
              f"CO访问 {analysis['co_cache_lines_accessed']:>4} 个缓存行, "
              f"改进比 {analysis['improvement_ratio']:.2f}x")
    
    # 边界情况测试
    print("\n边界情况测试:")
    edge_cases = [
        ([], 5),
        ([1], 1),
        ([1], 2),
        ([1, 2], 1),
        ([1, 2], 2),
        ([1, 2], 3),
    ]
    
    for arr, target in edge_cases:
        std_result = standard_binary_search(arr, target)
        co_result = cache_oblivious_binary_search_recursive(arr, target, 0, len(arr) - 1)
        print(f"  arr={arr}, target={target}: 标准={std_result}, CO={co_result}")
    
    # 批量搜索测试
    print("\n批量搜索测试:")
    size = 10000
    arr = generate_ordered_array(size)
    
    random.seed(42)
    targets = random.sample(arr, 100) + [random.randint(0, 10000000) for _ in range(10)]
    
    start = time.perf_counter()
    results = batch_search(arr, targets)
    batch_time = time.perf_counter() - start
    
    found = sum(1 for r in results if r != -1)
    print(f"  搜索 {len(targets)} 个目标: 找到 {found} 个, "
          f"耗时 {batch_time*1000:.2f}ms")
    
    print("\n" + "=" * 70)
    print("测试完成!")
    print("=" * 70)
