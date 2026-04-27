# -*- coding: utf-8 -*-
"""
算法实现：软件工程算法 / longest_common_subsequence

本文件实现 longest_common_subsequence 相关的算法功能。
"""

from typing import List, Tuple, Optional


def lcs_length(s: str, t: str) -> int:
    """
    计算两个字符串的 LCS 长度

    Args:
        s: 第一个字符串
        t: 第二个字符串

    Returns:
        LCS 的长度
    """
    n = len(s)
    m = len(t)

    # ---- DP 数组（滚动数组优化到 2 行）----
    prev_row = [0] * (m + 1)

    for i in range(1, n + 1):
        curr_row = [0] * (m + 1)
        for j in range(1, m + 1):
            if s[i - 1] == t[j - 1]:
                curr_row[j] = prev_row[j - 1] + 1
            else:
                curr_row[j] = max(prev_row[j], curr_row[j - 1])
        prev_row = curr_row

    return prev_row[m]


def lcs_with_backtrack(s: str, t: str) -> Tuple[int, str]:
    """
    计算 LCS 长度并回溯得到具体 LCS 字符串

    Returns:
        (lcs_length, lcs_string)
    """
    n = len(s)
    m = len(t)

    # dp[i][j] = LCS(s[:i], t[:j]) 的长度
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if s[i - 1] == t[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    # ---- 回溯得到 LCS ----
    lcs_chars: List[str] = []
    i, j = n, m
    while i > 0 and j > 0:
        if s[i - 1] == t[j - 1]:
            lcs_chars.append(s[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1

    lcs_chars.reverse()
    return dp[n][m], "".join(lcs_chars)


def lcs_diff_indices(s: str, t: str) -> List[Tuple[str, int, int]]:
    """
    计算 LCS 并返回各字符的对应关系

    Returns:
        List of (char, index_in_s, index_in_t)
        若 char 不在 LCS 中，则对应 index 为 -1
    """
    n = len(s)
    m = len(t)

    # ---- DP 表 ----
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if s[i - 1] == t[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    # ---- 回溯 ----
    result: List[Tuple[str, int, int]] = []
    i, j = n, m
    while i > 0 and j > 0:
        if s[i - 1] == t[j - 1]:
            result.append((s[i - 1], i - 1, j - 1))
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1

    result.reverse()

    # ---- 合并：包含所有字符在各自序列中的位置 ----
    s_idx_map = {idx: idx_t for _, idx, idx_t in result}
    t_idx_map = {idx_t: idx for _, idx, idx_t in result}

    full_result = []
    si = 0
    ti = 0
    for char, si_orig, ti_orig in result:
        # 加入 LCS 之前的非 LCS 字符
        while si < si_orig:
            full_result.append((s[si], si, -1))
            si += 1
        while ti < ti_orig:
            full_result.append((t[ti], -1, ti))
            ti += 1
        # LCS 字符
        full_result.append((char, si_orig, ti_orig))
        si += 1
        ti += 1

    while si < n:
        full_result.append((s[si], si, -1))
        si += 1
    while ti < m:
        full_result.append((t[ti], -1, ti))
        ti += 1

    return full_result


def hirschberg_lcs(s: str, t: str) -> str:
    """
    Hirschberg 算法：在 O(N*M) 时间和 O(min(N,M)) 空间内计算 LCS

    适用于超长序列（如基因组数据），避免 O(N*M) 空间开销。

    Args:
        s, t: 输入字符串

    Returns:
        LCS 字符串
    """
    n = len(s)
    m = len(t)

    if n == 0:
        return ""
    elif n == 1:
        return s if s in t else ""
    else:
        # ---- 分治 ----
        mid = n // 2

        # 计算左半部分 LCS 长度（从左到右）
        left_scores = _n_w_len(s[:mid], t)
        # 计算右半部分 LCS 长度（从右到左）
        right_scores = _n_w_len(s[mid:][::-1], t[::-1])

        # 找到最佳分割点
        max_score = -1
        split_j = 0
        for j in range(m + 1):
            score = left_scores[j] + right_scores[m - j]
            if score > max_score:
                max_score = score
                split_j = j

        # 递归分治
        lcs_left = hirschberg_lcs(s[:mid], t[:split_j])
        lcs_right = hirschberg_lcs(s[mid:], t[split_j:])

        return lcs_left + lcs_right


def _n_w_len(a: str, b: str) -> List[int]:
    """
    计算 LCS 长度（只保留最后一行 DP）
    用于 Hirschberg 的分割点查找
    """
    n = len(a)
    m = len(b)
    prev_row = [0] * (m + 1)

    for i in range(1, n + 1):
        curr_row = [0] * (m + 1)
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                curr_row[j] = prev_row[j - 1] + 1
            else:
                curr_row[j] = max(prev_row[j], curr_row[j - 1])
        prev_row = curr_row

    return prev_row


if __name__ == "__main__":
    print("=" * 50)
    print("最长公共子序列（LCS）- 单元测试")
    print("=" * 50)

    test_cases = [
        ("ABCDGH", "AEDFHR"),    # LCS: "ADH", 长度 3
        ("AGGTAB", "GXTXAYB"),   # LCS: "GTAB", 长度 4
        ("ABCBDAB", "BDCAB"),    # LCS: "BCAB" 或 "BDAB", 长度 4
        ("ABCD", "ABCD"),       # LCS: "ABCD", 长度 4
        ("ABCD", "EFGH"),       # LCS: "", 长度 0
        ("AGTACG", "ACATAG"),   # LCS: 长度?
    ]

    print("\n测试用例:")
    all_passed = True
    for s, t in test_cases:
        length, lcs_str = lcs_with_backtrack(s, t)
        calc_len = lcs_length(s, t)
        status = "✓" if length == calc_len else "✗"
        print(f"  {status} LCS('{s}', '{t}') = '{lcs_str}' (长度={length})")

    # Hirschberg 测试
    print("\nHirschberg 算法（O(min(N,M)) 空间）:")
    for s, t in test_cases[:4]:
        h_result = hirschberg_lcs(s, t)
        expected_len, expected_str = lcs_with_backtrack(s, t)
        status = "✓" if h_result == expected_str else "✗"
        print(f"  {status} Hirschberg: '{h_result}' (期望: '{expected_str}')")

    # LCS 对应关系可视化
    print("\nLCS 对应关系（diff 风格）:")
    s, t = "ABCBDAB", "BDCAB"
    diff = lcs_diff_indices(s, t)
    print(f"  s='{s}'")
    print(f"  t='{t}'")
    print("  diff:")
    for char, si, ti in diff:
        marker = ""
        if si >= 0 and ti >= 0:
            marker = "│"  # LCS 字符
        elif si >= 0:
            marker = "←"  # 仅在 s 中
        else:
            marker = "→"  # 仅在 t 中
        print(f"    {marker} s:{si:2d}={s[si] if si >= 0 else ' '}  t:{ti:2d}={t[ti] if ti >= 0 else ' '}")

    print(f"\n复杂度: O(N * M) 时间，O(N * M) 空间（标准版），O(min(N,M)) 空间（Hirschberg）")
    print("算法完成。")
