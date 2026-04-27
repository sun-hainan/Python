# -*- coding: utf-8 -*-
"""
算法实现：12_密码学与安全 / djb2

本文件实现 djb2 相关的算法功能。
"""

def djb2(s: str) -> int:
    """
    计算字符串的 DJB2 哈希值。
    
    Args:
        s: 输入字符串
    
    Returns:
        32 位哈希值
    
    示例:
        >>> djb2('Algorithms')
        3782405311
        >>> djb2('scramble bits')
        1609059040
    """
    hash_value = 5381  # 初始魔数
    for x in s:
        # hash = hash * 33 + ord(c)
        hash_value = ((hash_value << 5) + hash_value) + ord(x)
    return hash_value & 0xFFFFFFFF  # 取低 32 位


# ==========================================================
# 测试代码
# ==========================================================
if __name__ == "__main__":
    test_strings = ["Algorithms", "scramble bits", "hello", "world"]
    for s in test_strings:
        print(f"djb2('{s}') = {djb2(s)}")
