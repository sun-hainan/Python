"""
Radix Sort - 基数排序
==========================================

【算法原理】
按位数排序，从低位到高位，逐位分配到桶中收集。

【时间复杂度】O(n * k)
【空间复杂度】O(n + k)
【稳定性】稳定

【应用场景】
- 快递单号排序（固定18位）
- 身份证号排序（固定18位）
- 手机号排序（固定11位）
- 日期时间戳排序

【何时使用】
- 数据有固定格式/长度
- 数据是整数
- 数据范围极大（计数排序放不下）
"""

def radix_sort(arr):
    """
    基数排序
    """
    RADIX = 10
    max_val = max(arr)
    exp = 1
    while max_val // exp > 0:
        buckets = [[] for _ in range(RADIX)]
        for num in arr:
            digit = (num // exp) % RADIX
            buckets[digit].append(num)
        arr = []
        for bucket in buckets:
            arr.extend(bucket)
        exp *= RADIX
    return arr
