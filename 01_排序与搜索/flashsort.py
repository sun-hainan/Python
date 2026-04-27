# -*- coding: utf-8 -*-
"""
算法实现：01_排序与搜索 / flashsort

本文件实现 flashsort 相关的算法功能。
"""

def flash_sort(arr: list) -> list:
    """
    FlashSort 主函数
    
    Args:
        arr: 待排序数组
    
    Returns:
        排序后的数组（原地修改）
    
    示例:
        >>> flash_sort([64, 25, 12, 22, 11, 90, 38])
        [11, 12, 22, 25, 38, 64, 90]
    """
    n = len(arr)
    
    # 空数组或单元素直接返回
    if n <= 1:
        return arr
    
    # 第一步：找到最小值和最大值
    min_val = min(arr)           # 数组最小值
    max_val = max(arr)           # 数组最大值
    
    # 如果所有元素相同，无需排序
    if min_val == max_val:
        return arr
    
    # 第二步：计算桶数量，m 取 n*0.45 的平方根，最优经验值
    m = int(0.45 * n * n)        # 桶数量
    if m < 1:
        m = 1
    
    # 创建桶索引数组，存储每个元素的目标桶位置
    bucket_index = [0] * n
    
    # 计算常数 c = (m - 1) / (max_val - min_val)，用于线性映射
    c = (m - 1) / (max_val - min_val)
    
    # 第三步：计算每个元素的桶索引
    for i in range(n):
        # 元素映射到 [0, m-1] 区间
        bucket_index[i] = int(c * (arr[i] - min_val))
    
    # 第四步：计算每个桶内元素数量（用于排列）
    # 这里同时完成了循环移位，将元素移动到正确位置
    move_count = 0               # 已移动的元素计数
    j = 0                        # 当前扫描位置
    
    # 核心循环：将每个元素移动到其目标桶位置
    # 利用桶索引找到目标位置，通过循环移位依次填入
    while move_count < n - 1:
        # 跳过已在正确桶的元素
        while bucket_index[j] != j:
            # 计算当前元素应该去的目标位置
            target_pos = bucket_index[j]
            
            # 如果目标位置就是当前位置，说明计算有误
            # 这种情况下，使用传统插入排序作为后备
            if target_pos == j:
                break
            
            # 交换元素：arr[j] <-> arr[target_pos]
            arr[j], arr[target_pos] = arr[target_pos], arr[j]
            
            # 同时更新目标位置的桶索引，标记为已就位
            bucket_index[target_pos] = target_pos
            
            # 记录移动次数
            move_count += 1
        
        j += 1
    
    # 第五步：对每个桶内部进行插入排序
    # 由于元素已大致按桶分布，每个桶内元素数量较少
    # 插入排序对部分有序的小数组效率很高
    for i in range(1, n):
        key = arr[i]             # 待插入元素
        j = i - 1
        
        # 插入到已排序部分
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        
        arr[j + 1] = key
    
    return arr


def flash_sort_classic(arr: list) -> list:
    """
    FlashSort 经典实现（使用额外桶数组）
    更直观但使用 O(m) 额外空间
    
    Args:
        arr: 待排序数组
    
    Returns:
        排序后的数组
    """
    n = len(arr)
    
    if n <= 1:
        return arr
    
    # 找到极值
    min_val = min(arr)
    max_val = max(arr)
    
    if min_val == max_val:
        return arr
    
    # 计算桶数量
    m = int(0.45 * n * n)
    if m < 1:
        m = 1
    
    # 创建桶（每个桶是一个列表）
    buckets = [[] for _ in range(m)]
    
    # 线性映射常数
    c = (m - 1) / (max_val - min_val)
    
    # 将元素分配到桶中
    for val in arr:
        bucket_id = int(c * (val - min_val))
        buckets[bucket_id].append(val)
    
    # 收集所有桶
    idx = 0
    for bucket in buckets:
        for val in sorted(bucket):  # 每个桶内部排序（可用其他排序）
            arr[idx] = val
            idx += 1
    
    return arr


if __name__ == "__main__":
    # 基本功能测试
    test_cases = [
        [64, 25, 12, 22, 11, 90, 38],
        [5, 3, 8, 3, 9, 1, 5, 7],
        [1],
        [],
        [3, 3, 3, 1, 1, 2, 2],
        list(range(20, 0, -1)),
    ]
    
    print("FlashSort 测试:")
    for i, arr in enumerate(test_cases):
        original = arr.copy()
        flash_sort(arr)
        status = "✓" if arr == sorted(original) else "✗"
        print(f"  测试 {i+1}: {status}")
        print(f"    原始: {original}")
        print(f"    结果: {arr}")
    
    # 性能测试
    import random
    import time
    
    sizes = [1000, 5000, 10000]
    print("\n性能测试 (均匀分布数据):")
    for size in sizes:
        test_arr = [random.uniform(0, 1000) for _ in range(size)]
        start = time.time()
        flash_sort(test_arr.copy())
        elapsed = time.time() - start
        print(f"  n={size}: {elapsed:.4f}秒")
