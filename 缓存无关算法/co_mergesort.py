# -*- coding: utf-8 -*-
"""
算法实现：缓存无关算法 / co_mergesort

本文件实现 co_mergesort 相关的算法功能。
"""

import math
import random
from typing import List, Optional, Callable


# 算法参数配置
# =============================================================================
# CUTOFF_THRESHOLD: 小规模排序切换阈值当数组规模小于此值时切换到插入排序
# 插入排序对小规模数据有良好的缓存局部性
CUTOFF_THRESHOLD = 16

# CACHE_LINE_SIZE: 模拟的缓存行大小用于分析缓存效率
CACHE_LINE_SIZE = 64

# MIN_MERGE_SIZE: 最小合并规模用于控制合并操作的粒度
MIN_MERGE_SIZE = 4


def cache_oblivious_merge(arr: List, left: int, mid: int, right: int, 
                         temp: Optional[List] = None) -> List:
    """
    缓存无关的两路合并操作
    
    合并两个相邻的有序子数组[left, mid]和[mid+1, right]
    缓存无关特性体现在合并过程按照数据在内存中的自然布局进行
    避免了夸缓存行边界的随机访问
    
    Args:
        arr: 输入数组包含两个相邻的有序子数组
        left: 第一个子数组的起始索引
        mid: 两个子数组的分界索引
        right: 第二个子数组的结束索引
        temp: 可选的辅助缓冲区用于合并操作
        
    Returns:
        合并后的有序数组（如果temp为None则返回新数组否则返回arr）
    """
    # 计算两个子数组的长度
    left_len = mid - left + 1     # 第一个子数组长度
    right_len = right - mid      # 第二个子数组长度
    
    # 如果规模很小使用简单的缓存感知合并
    if right - left + 1 <= MIN_MERGE_SIZE:
        return simple_cache_aware_merge(arr, left, mid, right, temp)
    
    # 创建临时数组存储合并结果
    if temp is None:
        result = [0] * (left_len + right_len)
        temp_buffer = result
    else:
        result = temp
        temp_buffer = temp
    
    # 初始化合并指针
    left_ptr = left              # 指向第一个子数组当前元素
    right_ptr = mid + 1         # 指向第二个子数组当前元素
    result_ptr = 0               # 指向结果数组当前写入位置
    
    # 两路合并选择较小元素放入结果数组
    while left_ptr <= mid and right_ptr <= right:
        if arr[left_ptr] <= arr[right_ptr]:
            temp_buffer[result_ptr] = arr[left_ptr]
            left_ptr += 1
        else:
            temp_buffer[result_ptr] = arr[right_ptr]
            right_ptr += 1
        result_ptr += 1
    
    # 处理剩余元素
    # 如果第一个子数组有剩余元素全部复制到结果
    while left_ptr <= mid:
        temp_buffer[result_ptr] = arr[left_ptr]
        left_ptr += 1
        result_ptr += 1
    
    # 如果第二个子数组有剩余元素全部复制到结果
    while right_ptr <= right:
        temp_buffer[result_ptr] = arr[right_ptr]
        right_ptr += 1
        result_ptr += 1
    
    # 将结果复制回原数组
    for i in range(left_len + right_len):
        arr[left + i] = temp_buffer[i]
    
    return arr


def simple_cache_aware_merge(arr: List, left: int, mid: int, right: int,
                            temp: Optional[List] = None) -> List:
    """
    简单的缓存感知合并实现
    
    适用于小规模数据的合并操作该实现针对缓存行对齐进行了优化
    减少夸缓存行边界的访问次数
    
    Args:
        arr: 输入数组
        left: 第一个子数组起始索引
        mid: 分界索引
        right: 第二个子数组结束索引
        temp: 辅助缓冲区
        
    Returns:
        合并后的数组
    """
    left_len = mid - left + 1
    right_len = right - mid
    
    # 分配临时空间
    if temp is None:
        left_copy = arr[left:left + left_len]
        right_copy = arr[mid + 1:mid + 1 + right_len]
    else:
        left_copy = temp[left:left + left_len]
        right_copy = temp[mid + 1:mid + 1 + right_len]
        for i in range(left_len):
            left_copy[i] = arr[left + i]
        for i in range(right_len):
            right_copy[i] = arr[mid + 1 + i]
    
    # 初始化指针
    left_idx = 0
    right_idx = 0
    arr_idx = left
    
    # 合并两个有序数组
    while left_idx < left_len and right_idx < right_len:
        if left_copy[left_idx] <= right_copy[right_idx]:
            arr[arr_idx] = left_copy[left_idx]
            left_idx += 1
        else:
            arr[arr_idx] = right_copy[right_idx]
            right_idx += 1
        arr_idx += 1
    
    # 复制剩余元素
    while left_idx < left_len:
        arr[arr_idx] = left_copy[left_idx]
        left_idx += 1
        arr_idx += 1
    
    while right_idx < right_len:
        arr[arr_idx] = right_copy[right_idx]
        right_idx += 1
        arr_idx += 1
    
    return arr


def cache_oblivious_merge_sort(arr: List, left: int, right: int,
                              aux_buffer: Optional[List] = None) -> List:
    """
    缓存无关归并排序的主实现
    
    该函数递归地将数组分成两半分别排序然后合并
    递归的深度为O(log n)每次合并操作都充分利用数据的空间局部性
    
    缓存无关特性分析:
    - 当数组规模大于缓存大小时递归分割自然地将数据分布到各级缓存
    - 当数组规模小于缓存大小时整个数组可以放入缓存操作变得高效
    - 合并操作按照内存顺序进行充分利用预取机制
    
    Args:
        arr: 待排序数组
        left: 排序起始索引
        right: 排序结束索引
        aux_buffer: 辅助缓冲区用于合并操作
        
    Returns:
        排序后的数组
    """
    # 计算当前子数组的长度
    length = right - left + 1
    
    # 小规模数据使用插入排序利用其良好的缓存局部性
    if length <= CUTOFF_THRESHOLD:
        insertion_sort(arr, left, right)
        return arr
    
    # 计算中点进行二分递归
    mid = left + (right - left) // 2
    
    # 递归排序左半部分
    cache_oblivious_merge_sort(arr, left, mid, aux_buffer)
    
    # 递归排序右半部分
    cache_oblivious_merge_sort(arr, mid + 1, right, aux_buffer)
    
    # 合并两个有序子数组
    # 分配或复用辅助缓冲区
    if aux_buffer is None:
        temp = [0] * length
    else:
        temp = aux_buffer
    
    cache_oblivious_merge(arr, left, mid, right, temp)
    
    return arr


def insertion_sort(arr: List, left: int, right: int) -> List:
    """
    插入排序实现用于小规模数据排序
    
    插入排序对于小规模几乎有序的数据有很好的性能
    而且其缓存访问模式非常规则有利于缓存预取
    
    Args:
        arr: 输入数组
        left: 排序起始索引
        right: 排序结束索引
        
    Returns:
        排序后的数组
    """
    for i in range(left + 1, right + 1):
        key = arr[i]
        j = i - 1
        while j >= left and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr


def analyze_cache_behavior(arr: List, left: int, right: int) -> dict:
    """
    分析排序过程中的缓存行为
    
    该函数通过模拟缓存访问来评估算法的缓存效率
    统计缓存未命中次数和缓存行占用情况
    
    Args:
        arr: 输入数组
        left: 分析起始索引
        right: 分析结束索引
        
    Returns:
        包含缓存行为统计信息的字典
    """
    cache_misses = 0
    cache_hits = 0
    cache_lines_used = set()
    total_accesses = 0
    
    length = right - left + 1
    
    # 模拟缓存访问
    for i in range(left, right + 1):
        # 计算元素所属的缓存行
        cache_line = i // CACHE_LINE_SIZE
        cache_lines_used.add(cache_line)
        total_accesses += 1
        
        # 简化模型新缓存行产生缓存未命中
        if cache_line not in cache_lines_used or \
           i % CACHE_LINE_SIZE == 0:
            cache_misses += 1
        else:
            cache_hits += 1
    
    return {
        'cache_misses': cache_misses,
        'cache_hits': cache_hits,
        'cache_lines_used': len(cache_lines_used),
        'total_accesses': total_accesses,
        'miss_rate': cache_misses / total_accesses if total_accesses > 0 else 0
    }


def calculate_memory_access_complexity(n: int, cache_size: int) -> dict:
    """
    计算缓存无关归并排序的内存访问复杂度
    
    缓存无关算法的一个重要特性是其内存访问模式与缓存大小无关
    但实际性能会受缓存影响该函数计算不同缓存大小假设下的预期缓存未命中次数
    
    Args:
        n: 输入数组大小
        cache_size: 缓存大小（以元素个数为单位）
        
    Returns:
        包含复杂度分析的字典
    """
    # 归并排序的缓存复杂度分析基于递归深度和每层合并成本
    # 详细的缓存无关分析请参考 Prokop 的原始论文
    
    # 计算理想缓存下的缓存未命中次数（由 Frath 和 Sebot 的结果）
    # 对于归并排序理想缓存复杂度为 O(n/B + n/B * log_{M/B}(n/B))
    # 其中 B 是缓存行大小 M 是缓存大小
    
    # 简化模型使用主定理分析
    cache_line_size = CACHE_LINE_SIZE
    memory_levels = int(math.log2(cache_size)) if cache_size > 1 else 1
    
    # 理论缓存未命中次数下界
    cache_misses_lower = n / cache_line_size
    cache_misses_upper = (n / cache_line_size) * memory_levels
    
    return {
        'array_size': n,
        'assumed_cache_size': cache_size,
        'memory_levels': memory_levels,
        'optimal_cache_misses': cache_misses_lower,
        'worst_cache_misses': cache_misses_upper,
        'analysis': '归并排序的缓存无关复杂度为 O(n/B + n/B * log_{M/B}(n/B))'
    }


def verify_sort_correctness(arr: List) -> bool:
    """
    验证排序结果的正确性
    
    Args:
        arr: 排序后的数组
        
    Returns:
        如果数组有序返回True否则返回False
    """
    for i in range(1, len(arr)):
        if arr[i - 1] > arr[i]:
            return False
    return True


# 时间复杂度说明:
# =============================================================================
# 缓存无关归并排序的时间复杂度:
#   - 比较次数: O(n log n) 与标准归并排序相同
#   - 缓存复杂度（理想缓存）: O(n/B + (n/B) * log_{M/B}(n/B))
#   - 其中 B 是缓存行大小 M 是缓存大小
#
# 空间复杂度:
#   - 工作空间: O(n) 用于合并操作的辅助缓冲区
#   - 递归栈空间: O(log n)
#
# 缓存无关特性:
#   - 算法自动适应任何缓存大小不需要参数调优
#   - 递归结构使得大数据在小缓存中分段处理大缓存在大缓存中高效处理
#   - 合并操作按照内存顺序进行利用预取机制减少缓存未命中
#   - 当 n >> M 时算法工作集大小与问题规模匹配实现最优缓存利用


if __name__ == "__main__":
    # 测试缓存无关归并排序
    print("=" * 70)
    print("缓存无关归并排序测试")
    print("=" * 70)
    
    # 基本功能测试
    print("\n基本功能测试:")
    test_cases = [
        [38, 27, 43, 3, 9, 82, 10, 56],
        [5, 2, 4, 6, 1, 3, 2, 8],
        [1],
        [2, 1],
        list(range(20, 0, -1)),
    ]
    
    for i, test_arr in enumerate(test_cases):
        original = test_arr.copy()
        result = cache_oblivious_merge_sort(test_arr.copy(), 0, len(test_arr) - 1)
        is_correct = verify_sort_correctness(result)
        status = "通过" if is_correct else "失败"
        print(f"  测试用例 {i + 1}: {' '.join(map(str, original[:5]))}... -> {status}")
    
    # 性能对比测试
    print("\n性能对比测试 (与Python内置排序):")
    sizes = [100, 1000, 5000, 10000]
    
    for size in sizes:
        # 生成随机测试数据
        random.seed(42)
        test_arr = [random.randint(0, 100000) for _ in range(size)]
        
        # 复制数据确保使用相同输入
        co_arr = test_arr.copy()
        py_arr = test_arr.copy()
        
        # 缓存无关归并排序
        import time
        start = time.perf_counter()
        cache_oblivious_merge_sort(co_arr, 0, len(co_arr) - 1)
        co_time = time.perf_counter() - start
        
        # Python内置排序
        start = time.perf_counter()
        py_arr.sort()
        py_time = time.perf_counter() - start
        
        print(f"  规模 {size:>6}: 缓存无关排序 {co_time*1000:>8.2f}ms, "
              f"内置排序 {py_time*1000:>8.2f}ms, "
              f"比率 {co_time/py_time:>6.2f}x")
    
    # 缓存行为分析
    print("\n缓存行为分析:")
    for size in [1000, 5000, 10000]:
        random.seed(42)
        test_arr = [random.randint(0, 100000) for _ in range(size)]
        
        # 创建辅助缓冲区
        aux = [0] * size
        
        # 排序并分析
        cache_oblivious_merge_sort(test_arr, 0, len(test_arr) - 1, aux)
        cache_stats = analyze_cache_behavior(test_arr, 0, len(test_arr) - 1)
        
        print(f"  规模 {size:>6}: 缓存未命中 {cache_stats['cache_misses']:>6}, "
              f"缓存命中 {cache_stats['cache_hits']:>6}, "
              f"未命中率 {cache_stats['miss_rate']*100:>6.2f}%")
    
    # 复杂度分析
    print("\n理论复杂度分析:")
    for cache_size in [64, 256, 1024, 4096]:
        for n in [1000, 10000, 100000]:
            complexity = calculate_memory_access_complexity(n, cache_size)
            print(f"  n={n:>7}, 缓存={cache_size:>5}: "
                  f"最优 {complexity['optimal_cache_misses']:>10.1f}, "
                  f"最坏 {complexity['worst_cache_misses']:>10.1f}")
    
    # 大规模测试
    print("\n大规模测试:")
    random.seed(42)
    large_arr = [random.randint(0, 1000000) for _ in range(50000)]
    original_sum = sum(large_arr)
    
    print(f"  生成 {len(large_arr)} 个随机数")
    print(f"  原数组和: {original_sum}")
    
    import time
    start = time.perf_counter()
    cache_oblivious_merge_sort(large_arr, 0, len(large_arr) - 1)
    elapsed = time.perf_counter() - start
    
    print(f"  排序耗时: {elapsed*1000:.2f}ms")
    print(f"  排序后首元素: {large_arr[0]}, 末元素: {large_arr[-1]}")
    print(f"  结果正确性: {'通过' if verify_sort_correctness(large_arr) else '失败'}")
    
    print("\n" + "=" * 70)
    print("测试完成!")
    print("=" * 70)
