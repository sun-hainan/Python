"""
Radix Sort - 基数排序
==========================================

【算法原理】
按位数进行排序，从低位到高位，
每次按当前位分配到0-9共10个桶中，然后收集，再进行下一位。

【时间复杂度】O(n * k)
【空间复杂度】O(n + k)
【稳定性】稳定
"""

def radix_sort(arr):
    """
    基数排序(LSD)
    
    Args:
        arr: 待排序正整数列表
        
    Returns:
        排序后的新列表
    """
    RADIX = 10
    max_val = max(arr)
    exp = 1  # 当前位数
    
    while max_val // exp > 0:
        # 按当前位分配到桶中
        buckets = [[] for _ in range(RADIX)]
        for num in arr:
            digit = (num // exp) % RADIX
            buckets[digit].append(num)
        
        # 从桶中收集
        arr = []
        for bucket in buckets:
            arr.extend(bucket)
        
        exp *= RADIX
    
    return arr


# ---------- Fibonacci ----------
FILES['Chinese Algorithms/DP/01_Fibonacci.py'] = 
Fibonacci - 斐波那契数列
==========================================

【数列定义】
F(0) = 0, F(1) = 1
F(n) = F(n-1) + F(n-2)

【应用场景】
- 递归可视化
- 动态规划入门
- 黄金分割比例
