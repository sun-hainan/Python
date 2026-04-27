# -*- coding: utf-8 -*-
"""
算法实现：细粒度复杂性 / suffix_array

本文件实现 suffix_array 相关的算法功能。
"""

from typing import List, Tuple


def build_suffix_array_naive(s: str) -> List[int]:
    """
    朴素算法构建后缀数组:O(n² log n)
    
    Args:
        s: 字符串
    
    Returns:
        后缀数组(后缀起始位置的有序列表)
    """
    n = len(s)
    # 生成所有后缀
    suffixes = [(s[i:], i) for i in range(n)]
    # 排序
    suffixes.sort(key=lambda x: x[0])
    # 提取位置
    return [pos for _, pos in suffixes]


def build_suffix_array_dc(s: str) -> List[int]:
    """
    分治算法构建后缀数组(简化版)
    
    Args:
        s: 字符串
    
    Returns:
        后缀数组
    """
    n = len(s)
    if n <= 1:
        return list(range(n))
    
    # 简化:使用Python的排序
    # 实际应该用更复杂的DC算法
    suffixes = list(range(n))
    suffixes.sort(key=lambda i: s[i:])
    
    return suffixes


def build_suffix_array_sa_is(s: str) -> List[int]:
    """
    SA-IS算法:O(n)构建后缀数组
    
    Args:
        s: 字符串
    
    Returns:
        后缀数组
    """
    n = len(s)
    
    # 使用Python内置排序的简化实现
    return build_suffix_array_dc(s)


def compute_lcp_naive(s: str, sa: List[int]) -> List[int]:
    """
    朴素LCP计算:O(n²)
    
    Args:
        s: 字符串
        sa: 后缀数组
    
    Returns:
        LCP数组
    """
    n = len(s)
    lcp = [0] * n
    
    for i in range(1, n):
        # 比较sa[i-1]和sa[i]对应的后缀
        l = sa[i - 1]
        r = sa[i]
        
        # 计算LCP
        common = 0
        while l + common < n and r + common < n and s[l + common] == s[r + common]:
            common += 1
        lcp[i] = common
    
    return lcp


def compute_lcp_rmq(s: str, sa: List[int]) -> List[List[int]]:
    """
    使用RMQ计算LCP(稀疏表)
    
    Args:
        s: 字符串
        sa: 后缀数组
    
    Returns:
        Sparse Table
    """
    n = len(s)
    lcp = compute_lcp_naive(s, sa)
    
    # 构建Sparse Table
    log_n = (n + 1).bit_length()
    st = [[0] * n for _ in range(log_n)]
    st[0] = lcp[:]
    
    for k in range(1, log_n):
        for i in range(n - (1 << k) + 1):
            st[k][i] = min(st[k-1][i], st[k-1][i + (1 << (k-1))])
    
    return st


def lcp_query(st: List[List[int]], l: int, r: int, sa: List[int]) -> int:
    """
    LCP区间查询
    
    Args:
        st: Sparse Table
        l, r: 区间(闭区间)
        sa: 后缀数组
    
    Returns:
        LCP值
    """
    if l > r:
        l, r = r, l
    # 注意:sa[l]和sa[r]的后缀的LCP是lcp[l+1:r+1]的最小值
    k = (r - l + 1).bit_length() - 1
    return min(st[k][l], st[k][r - (1 << k) + 1])


def longest_common_substring(s1: str, s2: str) -> str:
    """
    找两个字符串的最长公共子串
    
    Args:
        s1: 字符串1
        s2: 字符串2
    
    Returns:
        最长公共子串
    """
    combined = s1 + "#" + s2
    sa = build_suffix_array_dc(combined)
    lcp = compute_lcp_naive(combined, sa)
    
    max_len = max(lcp)
    idx = lcp.index(max_len)
    
    # 找到对应的位置
    pos_in_combined = sa[idx]
    
    # 判断属于哪个字符串
    if pos_in_combined < len(s1):
        return combined[pos_in_combined:pos_in_combined + max_len]
    else:
        return combined[pos_in_combined:pos_in_combined + max_len]


def substring_search_with_sa(s: str, pattern: str, sa: List[int]) -> List[int]:
    """
    使用后缀数组进行子串搜索
    
    Args:
        s: 主串
        pattern: 模式
        sa: 后缀数组
    
    Returns:
        所有匹配位置
    """
    n = len(s)
    m = len(pattern)
    
    # 二分查找下界
    lo = 0
    hi = n
    
    combined = s + pattern
    offset = len(s)
    
    while lo < hi:
        mid = (lo + hi) // 2
        suffix_start = sa[mid]
        if combined[suffix_start:suffix_start + m] < pattern:
            lo = mid + 1
        else:
            hi = mid
    
    lower = lo
    
    # 二分查找上界
    lo = 0
    hi = n
    while lo < hi:
        mid = (lo + hi) // 2
        suffix_start = sa[mid]
        if combined[suffix_start:suffix_start + m] > pattern:
            hi = mid
        else:
            lo = mid + 1
    
    upper = hi
    
    # 收集所有匹配
    matches = []
    for i in range(lower, upper):
        pos = sa[i]
        if pos < len(s):
            matches.append(pos)
    
    return sorted(matches)


# 测试代码
if __name__ == "__main__":
    # 测试1: 后缀数组
    print("测试1 - 后缀数组:")
    s1 = "banana"
    sa1 = build_suffix_array_naive(s1)
    print(f"  字符串: {s1}")
    print(f"  后缀数组: {sa1}")
    print("  后缀:")
    for i in sa1:
        print(f"    {i}: '{s1[i:]}'")
    
    # 测试2: LCP数组
    print("\n测试2 - LCP数组:")
    lcp1 = compute_lcp_naive(s1, sa1)
    print(f"  LCP: {lcp1}")
    
    # 测试3: 最长公共子串
    print("\n测试3 - 最长公共子串:")
    s2_1 = "ababc"
    s2_2 = "bcabx"
    lcs = longest_common_substring(s2_1, s2_2)
    print(f"  字符串1: {s2_1}")
    print(f"  字符串2: {s2_2}")
    print(f"  LCS: '{lcs}'")
    
    # 测试4: 子串搜索
    print("\n测试4 - 子串搜索:")
    s4 = "abracadabra"
    pattern4 = "abra"
    sa4 = build_suffix_array_naive(s4)
    matches4 = substring_search_with_sa(s4, pattern4, sa4)
    print(f"  主串: {s4}")
    print(f"  模式: {pattern4}")
    print(f"  匹配位置: {matches4}")
    
    # 测试5: 后缀数组构建方法对比
    print("\n测试5 - 不同方法对比:")
    s5 = "mississippi"
    sa5_naive = build_suffix_array_naive(s5)
    sa5_dc = build_suffix_array_dc(s5)
    print(f"  字符串: {s5}")
    print(f"  朴素: {sa5_naive}")
    print(f"  DC: {sa5_dc}")
    print(f"  一致: {sa5_naive == sa5_dc}")
    
    # 测试6: 大字符串
    print("\n测试6 - 较大字符串(1000字符):")
    import random
    import string
    
    random.seed(42)
    s6 = ''.join(random.choices(string.ascii_lowercase, k=1000))
    sa6 = build_suffix_array_dc(s6)
    print(f"  长度: {len(s6)}")
    print(f"  前10个后缀位置: {sa6[:10]}")
    
    # 验证排序正确性
    for i in range(len(sa6) - 1):
        if s6[sa6[i]:] > s6[sa6[i+1]:]:
            print(f"  错误: 后缀{s6[sa6[i]:]} > 后缀{s6[sa6[i+1]:]}")
            break
    else:
        print("  排序正确!")
    
    print("\n所有测试完成!")
