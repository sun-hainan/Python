# -*- coding: utf-8 -*-
"""
算法实现：并行算法 / parallel_merge

本文件实现 parallel_merge 相关的算法功能。
"""

from typing import List, Callable, Tuple
import math
import threading


def sequential_merge(list_a: List, list_b: List, 
                   key: Callable = None, reverse: bool = False) -> List:
    """
    顺序两路合并
    
    参数:
        list_a: 第一个已排序数组
        list_b: 第二个已排序数组
        key: 排序关键字
        reverse: 是否降序
    
    返回:
        合并后的排序数组
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
            take_a = a_cmp >= b_cmp
        else:
            take_a = a_cmp <= b_cmp
        
        if take_a:
            result.append(a_val)
            i += 1
        else:
            result.append(b_val)
            j += 1
    
    result.extend(list_a[i:])
    result.extend(list_b[j:])
    
    return result


def parallel_merge_two_way(list_a: List, list_b: List,
                           num_threads: int = 2,
                           key: Callable = None,
                           reverse: bool = False) -> List:
    """
    并行两路合并
    
    参数:
        list_a: 第一个已排序数组
        list_b: 第二个已排序数组
        num_threads: 可用线程数
        key: 排序关键字
        reverse: 是否降序
    
    返回:
        合并后的排序数组
    """
    total_len = len(list_a) + len(list_b)
    
    if total_len <= 1000 or num_threads <= 1:
        return sequential_merge(list_a, list_b, key, reverse)
    
    # 在list_a中找到分割点，使得list_a[0:split]和list_b可以合并
    # 使用二分搜索找到分割位置
    
    def find_split_pos():
        """找到将合并结果分成的两部分的分割点"""
        total_left = total_len // 2
        
        # 在list_a中找到分割位置
        low = max(0, total_left - len(list_b))
        high = min(len(list_a), total_left)
        
        while low < high:
            mid = (low + high) // 2
            a_count = mid
            b_count = total_left - mid
            
            if b_count < 0:
                high = mid - 1
                continue
            if b_count > len(list_b):
                low = mid + 1
                continue
            
            a_val = list_a[mid - 1] if mid > 0 else None
            b_val = list_b[b_count - 1] if b_count > 0 else None
            
            # 比较
            if key:
                a_cmp = key(a_val) if a_val is not None else (float('-inf') if not reverse else float('inf'))
                b_cmp = key(b_val) if b_val is not None else (float('-inf') if not reverse else float('inf'))
            else:
                a_cmp = a_val if a_val is not None else (float('-inf') if not reverse else float('inf'))
                b_cmp = b_val if b_val is not None else (float('-inf') if not reverse else float('inf'))
            
            if reverse:
                cond = a_cmp >= b_cmp
            else:
                cond = a_cmp <= b_cmp
            
            if cond:
                low = mid + 1
            else:
                high = mid
        
        return low
    
    split = find_split_pos()
    split = max(0, min(len(list_a), split))
    
    left_a = list_a[:split]
    right_a = list_a[split:]
    left_b_count = total_len // 2 - split
    left_b_count = max(0, min(len(list_b), left_b_count))
    left_b = list_b[:left_b_count]
    right_b = list_b[left_b_count:]
    
    # 并行合并左右两部分
    if num_threads >= 2:
        left_result = [None]
        right_result = [None]
        threads = []
        
        def merge_left():
            left_result[0] = sequential_merge(left_a, left_b, key, reverse)
        
        def merge_right():
            right_result[0] = sequential_merge(right_a, right_b, key, reverse)
        
        t1 = threading.Thread(target=merge_left)
        t2 = threading.Thread(target=merge_right)
        
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
        
        return left_result[0] + right_result[0]
    else:
        left = sequential_merge(left_a, left_b, key, reverse)
        right = sequential_merge(right_a, right_b, key, reverse)
        return left + right


def k_way_merge(sorted_lists: List[List], 
                key: Callable = None, 
                reverse: bool = False) -> List:
    """
    K路合并 - 合并多个已排序数组
    
    参数:
        sorted_lists: 已排序数组的列表
        key: 排序关键字
        reverse: 是否降序
    
    返回:
        合并后的排序数组
    """
    if not sorted_lists:
        return []
    
    # 过滤空列表
    non_empty = [lst for lst in sorted_lists if lst]
    if not non_empty:
        return []
    
    if len(non_empty) == 1:
        return non_empty[0]
    
    # 使用最小堆进行K路合并
    import heapq
    
    result = []
    
    # 初始化堆，每个元素包含(值, 列表索引, 元素索引)
    heap = []
    
    for i, lst in enumerate(non_empty):
        if lst:
            val = lst[0]
            if key:
                cmp_val = key(val)
            else:
                cmp_val = val
            
            if reverse:
                cmp_val = -cmp_val
            
            heapq.heappush(heap, (cmp_val, i, 0, val))
    
    while heap:
        cmp_val, list_idx, elem_idx, val = heapq.heappop(heap)
        result.append(val)
        
        # 如果该列表还有更多元素，推入下一个
        if elem_idx + 1 < len(non_empty[list_idx]):
            next_val = non_empty[list_idx][elem_idx + 1]
            if key:
                next_cmp = key(next_val)
            else:
                next_cmp = next_val
            
            if reverse:
                next_cmp = -next_cmp
            
            heapq.heappush(heap, (next_cmp, list_idx, elem_idx + 1, next_val))
    
    return result


def parallel_k_way_merge(sorted_lists: List[List],
                         num_threads: int = 4,
                         key: Callable = None,
                         reverse: bool = False) -> List:
    """
    并行K路合并
    
    参数:
        sorted_lists: 已排序数组的列表
        num_threads: 线程数
        key: 排序关键字
        reverse: 是否降序
    
    返回:
        合并后的排序数组
    """
    if not sorted_lists:
        return []
    
    non_empty = [lst for lst in sorted_lists if lst]
    if not non_empty:
        return []
    
    if len(non_empty) <= num_threads:
        return k_way_merge(non_empty, key, reverse)
    
    # 分组并行合并
    chunk_size = max(1, len(non_empty) // num_threads)
    chunks = []
    
    for i in range(num_threads):
        start = i * chunk_size
        end = min(start + chunk_size, len(non_empty))
        if start < len(non_empty):
            chunks.append(non_empty[start:end])
    
    # 并行合并每组
    results = [None] * len(chunks)
    threads = []
    
    def merge_chunk(chunk, idx):
        results[idx] = k_way_merge(chunk, key, reverse)
    
    for idx, chunk in enumerate(chunks):
        if chunk:
            thread = threading.Thread(target=merge_chunk, args=(chunk, idx))
            thread.start()
            threads.append(thread)
    
    for thread in threads:
        thread.join()
    
    # 合并中间结果
    valid_results = [r for r in results if r is not None]
    return k_way_merge(valid_results, key, reverse)


def bitonic_merge(data: List, ascending: bool = True,
                 key: Callable = None) -> List:
    """
    双调合并 - 用于双调排序中的合并步骤
    
    参数:
        data: 输入数据（应为双调序列）
        ascending: 是否升序
        key: 排序关键字
    
    返回:
        完全排序的数组
    """
    n = len(data)
    if n <= 1:
        return list(data)
    
    # 双调序列：先增后减（或反过来）
    # 需要将其转换为完全有序
    
    # 找到分割点
    mid = n // 2
    
    # 找到转折点
    asc = True
    for i in range(1, n):
        curr = key(data[i]) if key else data[i]
        prev = key(data[i-1]) if key else data[i-1]
        
        if curr < prev:
            asc = False
            break
    
    # 如果已经是完全有序，直接返回
    if asc == ascending:
        return sorted(data, key=key, reverse=not ascending)
    
    # 分成两半递归处理
    first = bitonic_merge(data[:mid], True, key)
    second = bitonic_merge(data[mid:], False, key)
    
    # 合并两个已排序序列
    return sequential_merge(first, second, key, reverse=False)


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 测试用例1：基本两路合并
    print("=" * 50)
    print("测试1: 顺序两路合并")
    print("=" * 50)
    
    list_a = [1, 3, 5, 7, 9]
    list_b = [2, 4, 6, 8, 10]
    
    result = sequential_merge(list_a, list_b)
    print(f"A: {list_a}")
    print(f"B: {list_b}")
    print(f"合并: {result}")
    print(f"正确: {result == [1,2,3,4,5,6,7,8,9,10]}")
    
    # 测试用例2：并行两路合并
    print("\n" + "=" * 50)
    print("测试2: 并行两路合并")
    print("=" * 50)
    
    list_a = [1, 4, 7, 10]
    list_b = [2, 5, 8, 11]
    
    result = parallel_merge_two_way(list_a, list_b, num_threads=2)
    print(f"A: {list_a}")
    print(f"B: {list_b}")
    print(f"合并: {result}")
    
    # 测试用例3：K路合并
    print("\n" + "=" * 50)
    print("测试3: K路合并")
    print("=" * 50)
    
    lists = [
        [1, 5, 9],
        [2, 6, 10],
        [3, 7, 11],
        [4, 8, 12]
    ]
    
    result = k_way_merge(lists)
    print(f"4个已排序列表合并:")
    print(f"结果: {result}")
    print(f"正确: {result == [1,2,3,4,5,6,7,8,9,10,11,12]}")
    
    # 测试用例4：并行K路合并
    print("\n" + "=" * 50)
    print("测试4: 并行K路合并")
    print("=" * 50)
    
    import random
    
    lists = []
    for i in range(8):
        lst = sorted([random.randint(1, 100) for _ in range(10)])
        lists.append(lst)
    
    print(f"8个列表，每个10个元素")
    
    result = parallel_k_way_merge(lists, num_threads=4)
    expected_len = 8 * 10
    print(f"结果长度: {len(result)} (预期 {expected_len})")
    is_sorted = all(result[i] <= result[i+1] for i in range(len(result)-1))
    print(f"正确排序: {is_sorted}")
    
    # 测试用例5：带key的合并
    print("\n" + "=" * 50)
    print("测试5: 带key的合并")
    print("=" * 50)
    
    list_a = [('a', 3), ('b', 7), ('c', 9)]
    list_b = [('d', 2), ('e', 5), ('f', 8)]
    
    result = sequential_merge(list_a, list_b, key=lambda x: x[1])
    print("按第二元素排序:")
    for item in result:
        print(f"  {item}")
    
    # 测试用例6：性能测试
    print("\n" + "=" * 50)
    print("测试6: 性能测试")
    print("=" * 50)
    
    import time
    
    for size in [1000, 10000]:
        list_a = sorted([random.randint(1, 100000) for _ in range(size)])
        list_b = sorted([random.randint(1, 100000) for _ in range(size)])
        
        start = time.time()
        result = sequential_merge(list_a, list_b)
        seq_time = time.time() - start
        
        start = time.time()
        result = parallel_merge_two_way(list_a, list_b, num_threads=4)
        par_time = time.time() - start
        
        print(f"\n大小 {size}x2:")
        print(f"  顺序: {seq_time*1000:.2f}ms")
        print(f"  并行: {par_time*1000:.2f}ms")
