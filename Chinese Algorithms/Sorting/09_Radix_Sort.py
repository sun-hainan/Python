"""
Radix Sort - 基数排序
==========================================

【算法原理】
按位数进行排序，从低位到高位，
每次按当前位分配到0-9共10个桶中，然后收集，再进行下一位。

【时间复杂度】O(n * k)
【空间复杂度】O(n + k)
【稳定性】稳定

【应用场景】
- 学号排序（固定长度字符串/数字）
- 身份证号排序
- 银行卡号排序
- 日期排序

【何时使用】
- 数据有固定格式（位数相同）
- 数据范围极大（无法用计数排序）
- 字符串排序（按字符排序）
- 正整数排序

【实际案例】
# 快递单号排序（固定18位）
tracking_numbers = ["SF123456789012345", "YT987654321098765", "ZTO246801357924680"]
radix_sort(tracking_numbers)  # 按单号排序

# 身份证号排序（固定18位）
id_cards = ["110101199001011234", "310101198505051234", "440101200010101234"]
radix_sort(id_cards)  # 按身份证号排序
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
