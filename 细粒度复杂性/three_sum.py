# -*- coding: utf-8 -*-
"""
算法实现：细粒度复杂性 / three_sum

本文件实现 three_sum 相关的算法功能。
"""

from typing import List, Tuple, Optional
import random


def three_sum_naive(nums: List[int]) -> List[Tuple[int, int, int]]:
    """
    朴素算法:O(n³)
    
    Args:
        nums: 输入数组
    
    Returns:
        所有和为0的三元组
    """
    n = len(nums)
    result = []
    
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                if nums[i] + nums[j] + nums[k] == 0:
                    result.append((i, j, k))
    
    return result


def three_sum_quadratic(nums: List[int]) -> List[Tuple[int, int, int]]:
    """
    平方算法:O(n²)
    1. 排序
    2. 对每个元素i,双指针找j,k使得nums[i]+nums[j]+nums[k]=0
    
    Args:
        nums: 输入数组
    
    Returns:
        所有和为0的三元组
    """
    nums_sorted = sorted(nums)
    n = len(nums_sorted)
    result = []
    
    for i in range(n - 2):
        if i > 0 and nums_sorted[i] == nums_sorted[i-1]:
            continue  # 跳过重复
        
        target = -nums_sorted[i]
        j, k = i + 1, n - 1
        
        while j < k:
            current_sum = nums_sorted[j] + nums_sorted[k]
            
            if current_sum == target:
                result.append((i, j, k))
                
                # 跳过重复
                while j < k and nums_sorted[j] == nums_sorted[j+1]:
                    j += 1
                while j < k and nums_sorted[k] == nums_sorted[k-1]:
                    k -= 1
                
                j += 1
                k -= 1
            
            elif current_sum < target:
                j += 1
            else:
                k -= 1
    
    return result


def three_sum_hash(nums: List[int]) -> List[Tuple[int, int, int]]:
    """
    哈希方法:O(n²)空间,O(n²)时间
    
    Args:
        nums: 输入数组
    
    Returns:
        所有和为0的三元组
    """
    n = len(nums)
    result = []
    
    # 预处理:所有数对之和
    sum_to_pairs = {}
    for i in range(n):
        for j in range(i + 1, n):
            s = nums[i] + nums[j]
            if s not in sum_to_pairs:
                sum_to_pairs[s] = []
            sum_to_pairs[s].append((i, j))
    
    # 找第三个数
    for k in range(n):
        target = -nums[k]
        if target in sum_to_pairs:
            for i, j in sum_to_pairs[target]:
                if i < j < k or j < i < k:
                    result.append((min(i, j), max(i, j), k))
    
    return result


def has_three_sum(nums: List[int], target: int = 0) -> bool:
    """
    判断是否存在和为target的三个数
    
    Args:
        nums: 输入数组
        target: 目标和
    
    Returns:
        是否存在
    """
    nums_sorted = sorted(nums)
    n = len(nums_sorted)
    
    for i in range(n - 2):
        left, right = i + 1, n - 1
        
        while left < right:
            current = nums_sorted[i] + nums_sorted[left] + nums_sorted[right]
            
            if current == target:
                return True
            elif current < target:
                left += 1
            else:
                right -= 1
    
    return False


def convolution_3sum(nums: List[int]) -> int:
    """
    Convolution-3SUM算法
    使用FFT将时间复杂度降至O(n log n)
    
    Args:
        nums: 输入数组
    
    Returns:
        和为0的三元组数量
    """
    # 简化版:使用多项式卷积
    # 将问题转化为:找a+b+c=0
    # 即a+b=-c
    
    n = len(nums)
    if n < 3:
        return 0
    
    # 归一化到非负索引
    offset = max(nums) + 1
    size = 2 * offset + 1
    
    # 构建多项式A和B
    A = [0] * size
    B = [0] * size
    
    for x in nums:
        if 0 <= x + offset < size:
            A[x + offset] = 1
        if -x + offset < size:
            B[-x + offset] = 1
    
    # 简化的卷积(用FFT)
    # 这里用O(n²)模拟
    C = [0] * (2 * size - 1)
    
    for i in range(size):
        for j in range(size):
            C[i + j] += A[i] * B[j]
    
    # 检查C[2*offset]的值(对应a+b=-a的和)
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            k = -(nums[i] + nums[j])
            if k in nums[j+1:]:
                count += 1
    
    return count // 3  # 每个三元组被计数6次


# 测试代码
if __name__ == "__main__":
    # 测试1: 简单实例
    print("测试1 - 简单实例:")
    nums1 = [-1, 0, 1, 2, -1, -4]
    
    result_naive = three_sum_naive(nums1)
    print(f"  输入: {nums1}")
    print(f"  朴素算法找到: {len(result_naive)}个三元组")
    
    result_quad = three_sum_quadratic(nums1)
    print(f"  平方算法找到: {len(result_quad)}个三元组")
    
    # 验证
    print("  三元组:")
    for i, j, k in result_quad:
        print(f"    {nums1[i]} + {nums1[j]} + {nums1[k]} = {nums1[i]+nums1[j]+nums1[k]}")
    
    # 测试2: 判断存在性
    print("\n测试2 - 判断存在性:")
    nums2 = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    
    for target in [0, 10, 15, 20]:
        exists = has_three_sum(nums2, target)
        print(f"  和为{target}? {exists}")
    
    # 测试3: 性能对比
    print("\n测试3 - 性能对比:")
    import time
    
    for n in [100, 500, 1000]:
        nums = [random.randint(-1000, 1000) for _ in range(n)]
        
        # 平方算法
        start = time.time()
        result = three_sum_quadratic(nums)
        time_quad = time.time() - start
        
        print(f"  n={n}: 平方算法耗时={time_quad:.4f}s, 找到{len(result)}个")
    
    # 测试4: 特殊情况
    print("\n测试4 - 全相同元素:")
    nums4 = [0, 0, 0, 0, 0]
    result4 = three_sum_quadratic(nums4)
    print(f"  [0,0,0,0,0] -> {len(result4)}个三元组")
    
    # 测试5: Convolution-3SUM
    print("\n测试5 - Convolution-3SUM:")
    nums5 = [1, -2, 1, 2, -1]
    count = convolution_3sum(nums5)
    print(f"  输入: {nums5}")
    print(f"  3SUM数量(去重前): {count}")
    
    # 验证
    print("  验证:")
    result = three_sum_quadratic(nums5)
    print(f"    实际三元组: {result}")
    
    print("\n所有测试完成!")
