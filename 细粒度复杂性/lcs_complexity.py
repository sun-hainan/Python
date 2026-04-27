# -*- coding: utf-8 -*-
"""
算法实现：细粒度复杂性 / lcs_complexity

本文件实现 lcs_complexity 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple


def classic_lcs(X: str, Y: str) -> int:
    """
    经典动态规划 LCS

    复杂度：O(n*m)
    空间：O(n*m)
    """
    n, m = len(X), len(Y)

    dp = np.zeros((n + 1, m + 1), dtype=int)

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if X[i - 1] == Y[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    return dp[n][m]


def space_optimized_lcs(X: str, Y: str) -> int:
    """
    空间优化版本

    复杂度：O(n*m) 时间，O(min(n,m)) 空间
    """
    if len(X) < len(Y):
        X, Y = Y, X

    n, m = len(X), len(Y)
    prev = np.zeros(m + 1, dtype=int)
    curr = np.zeros(m + 1, dtype=int)

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if X[i - 1] == Y[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev, curr = curr.copy(), np.zeros(m + 1)

    return prev[m]


def hirschberg_lcs(X: str, Y: str) -> Tuple[int, str]:
    """
    Hirschberg算法（空间最优且返回路径）

    复杂度：O(n*m) 时间，O(min(n,m)) 空间
    """
    n, m = len(X), len(Y)

    if n == 0:
        return 0, ""
    if m == 0:
        return 0, ""
    if n == 1:
        if X[0] in Y:
            return 1, X[0]
        else:
            return 0, ""

    mid = n // 2

    # 计算左半部分
    score_left = np.zeros(m + 1, dtype=int)
    for j in range(1, m + 1):
        score_left[j] = score_left[j - 1] + 1 if X[mid - 1] == Y[j - 1] else score_left[j - 1]

    # 计算右半部分（从右到左）
    score_right = np.zeros(m + 1, dtype=int)
    for j in range(m - 1, -1, -1):
        if X[mid] == Y[j]:
            score_right[j] = score_right[j + 1] + 1
        else:
            score_right[j] = max(score_right[j + 1] if j + 1 <= m else 0,
                               score_left[j] if j < len(score_left) else 0)

    # 找到最优分割点
    max_score = -1
    split_j = 0
    for j in range(m + 1):
        score = score_left[j] + score_right[j]
        if score > max_score:
            max_score = score
            split_j = j

    # 递归
    len1, seq1 = hirschberg_lcs(X[:mid], Y[:split_j])
    len2, seq2 = hirschberg_lcs(X[mid:], Y[split_j:])

    return len1 + len2, seq1 + seq2


def lcs_vs_edit_distance():
    """LCS与编辑距离的关系"""
    print("=== LCS vs 编辑距离 ===")
    print()
    print("关系：编辑距离 = |X| + |Y| - 2 * LCS")
    print("  - 删除所有不同字符")
    print("  - 剩余的就是公共子序列")
    print()
    print("下界联系：")
    print("  - LCS下界 ≈ 编辑距离下界")
    print("  - 都是 SETH-hard 问题")
    print()
    print("算法差异：")
    print("  - LCS通常用动态规划")
    print("  - 编辑距离可用加权编辑操作")


def fine_grained_lower():
    """细粒度下界"""
    print()
    print("=== LCS细粒度下界 ===")
    print()
    print("假设：LCS需要 Ω(n²) 时间")
    print()
    print("证明归约：")
    print("  - 从OV（正交向量）问题归约")
    print("  - OV是SETH-hard的")
    print()
    print("实际意义：")
    print("  - 很难有渐近改进")
    print("  - 当前最好仍是 O(n² / log n)")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== LCS测试 ===\n")

    test_cases = [
        ("ABCD", "AEBD"),
        ("AGTACG", "ACATAG"),
        ("ABCDGH", "AEDFHR"),
    ]

    for X, Y in test_cases:
        len_classic = classic_lcs(X, Y)
        len_space = space_optimized_lcs(X, Y)

        print(f"X = '{X}', Y = '{Y}'")
        print(f"  LCS长度: {len_classic}")
        print(f"  空间优化: {len_space}")
        print()

    print("复杂度分析：")
    print("  经典DP: O(nm) 时间, O(nm) 空间")
    print("  空间优化: O(nm) 时间, O(min(n,m)) 空间")
    print("  Hirschberg: O(nm) 时间, O(min(n,m)) 空间, 返回路径")

    lcs_vs_edit_distance()
    fine_grained_lower()

    print()
    print("应用：")
    print("  - 文件比较（diff）")
    print("  - 生物信息学（序列比对）")
    print("  - 抄袭检测")
