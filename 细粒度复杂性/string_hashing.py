# -*- coding: utf-8 -*-
"""
算法实现：细粒度复杂性 / string_hashing

本文件实现 string_hashing 相关的算法功能。
"""

import hashlib
from typing import List


def hash_string(s: str, mod: int = 2**64) -> int:
    """简单字符串哈希"""
    h = 0
    for c in s:
        h = (h * 31 + ord(c)) % mod
    return h


def hash_rolling(s: str, base: int = 31, mod: int = 10**9 + 7) -> List[int]:
    """
    计算字符串所有前缀的哈希值
    
    Args:
        s: 字符串
        base: 进制基数
        mod: 模数
    
    Returns:
        前缀哈希列表
    """
    n = len(s)
    prefix = [0] * (n + 1)
    
    for i in range(n):
        prefix[i+1] = (prefix[i] * base + ord(s[i])) % mod
    
    return prefix


def hash_substring(prefix: List[int], start: int, end: int, 
                   base: int = 31, mod: int = 10**9 + 7) -> int:
    """
    使用前缀哈希计算子串哈希
    
    Args:
        prefix: 前缀哈希列表
        start: 起始位置(包含)
        end: 结束位置(不包含)
        base: 进制基数
        mod: 模数
    
    Returns:
        子串哈希值
    """
    length = end - start
    power = pow(base, length, mod)
    return (prefix[end] - prefix[start] * power) % mod


def hash_double(s: str) -> int:
    """双哈希(使用两个不同的哈希函数)"""
    h1 = hashlib.md5(s.encode()).hexdigest()
    h2 = hashlib.sha256(s.encode()).hexdigest()
    return int(h1[:16], 16) ^ int(h2[:16], 16)


def hash_polynomial_rolling(s: str, coefficients: List[int] = None) -> int:
    """
    多项式滚动哈希
    
    Args:
        s: 字符串
        coefficients: 系数列表(可选)
    
    Returns:
        哈希值
    """
    if coefficients is None:
        coefficients = list(range(1, len(s) + 1))
    
    h = 0
    for i, c in enumerate(s):
        h += ord(c) * coefficients[i % len(coefficients)]
    return h


def rabin_karp_search(text: str, pattern: str) -> List[int]:
    """
    Rabin-Karp字符串匹配
    
    Args:
        text: 文本
        pattern: 模式
    
    Returns:
        所有匹配位置
    """
    n, m = len(text), len(pattern)
    
    if m > n:
        return []
    
    # 计算模式哈希
    pattern_hash = hash_string(pattern)
    
    # 计算文本中所有长度为m的子串哈希
    matches = []
    
    for i in range(n - m + 1):
        substring = text[i:i+m]
        substring_hash = hash_string(substring)
        
        if substring_hash == pattern_hash:
            if substring == pattern:
                matches.append(i)
    
    return matches


def anagram_hash(s: str) -> str:
    """
    生成与顺序无关的哈希(字谜哈希)
    相同字符集的元素会有相同的哈希
    """
    count = [0] * 26
    for c in s.lower():
        if 'a' <= c <= 'z':
            count[ord(c) - ord('a')] += 1
    
    # 转换为字符串
    return ','.join(str(x) for x in count)


# 测试代码
if __name__ == "__main__":
    # 测试1: 基础哈希
    print("测试1 - 基础哈希:")
    test_strings = ["hello", "world", "python", "HELLO"]
    
    for s in test_strings:
        h = hash_string(s)
        print(f"  hash('{s}') = {h}")
    
    # 测试2: 前缀哈希
    print("\n测试2 - 前缀哈希:")
    s = "ababc"
    prefix = hash_rolling(s)
    print(f"  字符串: {s}")
    print(f"  前缀哈希: {prefix}")
    
    # 子串哈希
    print(f"  子串[1:3]='ba': {hash_substring(prefix, 1, 3)}")
    print(f"  子串[2:5]='abc': {hash_substring(prefix, 2, 5)}")
    
    # 测试3: 双哈希
    print("\n测试3 - 双哈希:")
    for s in ["hello", "world", "hlleo"]:
        h = hash_double(s)
        print(f"  hash_double('{s}') = {h}")
    
    # 测试4: Rabin-Karp
    print("\n测试4 - Rabin-Karp搜索:")
    text = "ABABDABACDABABCABAB"
    pattern = "ABAB"
    
    matches = rabin_karp_search(text, pattern)
    print(f"  文本: {text}")
    print(f"  模式: {pattern}")
    print(f"  匹配位置: {matches}")
    
    # 测试5: 字谜哈希
    print("\n测试5 - 字谜哈希:")
    words = ["listen", "silent", "enlist", "hello", "world"]
    hashes = {}
    
    for word in words:
        h = anagram_hash(word)
        if h not in hashes:
            hashes[h] = []
        hashes[h].append(word)
    
    print("  字谜组:")
    for h, group in hashes.items():
        if len(group) > 1:
            print(f"    {group}")
    
    # 测试6: 哈希碰撞测试
    print("\n测试6 - 哈希碰撞:")
    n = 10000
    hashes = set()
    collisions = 0
    
    for i in range(n):
        s = f"string_{i}"
        h = hash_string(s)
        
        if h in hashes:
            collisions += 1
        else:
            hashes.add(h)
    
    print(f"  生成了{n}个字符串的哈希")
    print(f"  碰撞次数: {collisions}")
    
    print("\n所有测试完成!")
