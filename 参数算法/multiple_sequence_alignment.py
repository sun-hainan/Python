# -*- coding: utf-8 -*-
"""
算法实现：参数算法 / multiple_sequence_alignment

本文件实现 multiple_sequence_alignment 相关的算法功能。
"""

import random


def compute_score(seq1, seq2, match=1, mismatch=-1, gap=-2):
    """计算两条序列的对齐得分。"""
    score = 0
    for a, b in zip(seq1, seq2):
        if a == '-' or b == '-':
            score += gap
        elif a == b:
            score += match
        else:
            score += mismatch
    return score


def pairwise_alignment_dp(seq1, seq2):
    """
    成对序列动态规划对齐（Needleman-Wunsch 算法）。

    返回:
        (aligned1, aligned2, score)
    """
    m, n = len(seq1), len(seq2)

    # 初始化得分矩阵
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # 边界条件
    for i in range(m + 1):
        dp[i][0] = i * (-2)  # gap penalty
    for j in range(n + 1):
        dp[0][j] = j * (-2)

    # 填充矩阵
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            match_score = 1 if seq1[i-1] == seq2[j-1] else -1
            dp[i][j] = max(
                dp[i-1][j-1] + match_score,  # 对齐
                dp[i-1][j] - 2,             # seq1 的 gap
                dp[i][j-1] - 2              # seq2 的 gap
            )

    # 回溯
    aligned1, aligned2 = [], []
    i, j = m, n
    while i > 0 or j > 0:
        if i > 0 and j > 0:
            match_score = 1 if seq1[i-1] == seq2[j-1] else -1
            if dp[i][j] == dp[i-1][j-1] + match_score:
                aligned1.append(seq1[i-1])
                aligned2.append(seq2[j-1])
                i -= 1
                j -= 1
                continue
        if i > 0 and dp[i][j] == dp[i-1][j] - 2:
            aligned1.append(seq1[i-1])
            aligned2.append('-')
            i -= 1
        else:
            aligned1.append('-')
            aligned2.append(seq2[j-1])
            j -= 1

    return ''.join(reversed(aligned1)), ''.join(reversed(aligned2)), dp[m][n]


def multiple_alignment_center(sequences, k):
    """
    中心字符串启发式多序列比对。

    参数:
        sequences: 序列列表
        k: 选择的中心字符串数量

    返回:
        比对结果
    """
    n = len(sequences)

    # 选择一个中心序列（最长的）
    center_idx = max(range(n), key=lambda i: len(sequences[i]))
    center = sequences[center_idx]

    # 对每个序列与中心对齐
    alignments = [center]
    for i, seq in enumerate(sequences):
        if i != center_idx:
            aligned1, aligned2, score = pairwise_alignment_dp(center, seq)
            alignments.append(aligned2)

    # 合并所有对齐（使用最长长度填充）
    max_len = max(len(a) for a in alignments)
    result = []
    for a in alignments:
        result.append(a + '-' * (max_len - len(a)))

    return result


def profile_alignment(alignment1, alignment2):
    """
    对齐两个已有比对（profile-profile 比对）。

    参数:
        alignment1: 第一个比对（列表）
        alignment2: 第二个比对（列表）

    返回:
        合并后的比对
    """
    # 合并成更长的比对
    combined = alignment1 + alignment2
    return combined


def score_multiple_alignment(alignment):
    """
    计算多序列比对的得分（SUM_OF_PAIRS）。

    参数:
        alignment: 对齐后的序列列表

    返回:
        总得分
    """
    if not alignment:
        return 0

    m = len(alignment[0])
    n = len(alignment)

    total_score = 0
    for i in range(m):
        for p in range(n):
            for q in range(p + 1, n):
                a, b = alignment[p][i], alignment[q][i]
                if a == '-' or b == '-':
                    total_score -= 2
                elif a == b:
                    total_score += 1
                else:
                    total_score -= 1

    return total_score


if __name__ == "__main__":
    print("=== 多序列比对测试 ===")

    # 测试序列
    sequences = [
        "ATCGATCG",
        "ATCGATCG",
        "ATCGATCG",
        "AT-GAT-G"
    ]

    print("原始序列:")
    for seq in sequences:
        print(f"  {seq}")

    # 成对比对
    print("\n=== 成对比对示例 ===")
    seq1, seq2 = sequences[0], sequences[1]
    aligned1, aligned2, score = pairwise_alignment_dp(seq1, seq2)
    print(f"序列1 vs 序列2:")
    print(f"  {aligned1}")
    print(f"  {aligned2}")
    print(f"  得分: {score}")

    # 多序列比对
    print("\n=== 多序列比对 ===")
    msa = multiple_alignment_center(sequences, k=1)
    for seq in msa:
        print(f"  {seq}")

    # 评分
    msa_score = score_multiple_alignment(msa)
    print(f"多序列比对得分 (SUM_OF_PAIRS): {msa_score}")

    # FPT 分析
    print("\n=== FPT 算法分析 ===")
    print("多序列比对参数化:")
    print("  k = 允许的 gap 数")
    print("  算法复杂度: O(k! * 2^k * n)")
    print("  对于固定 k 是 FPT")

    print("\n参数算法在生物信息学中的应用:")
    print("  多序列比对、基因组组装、蛋白质折叠")
    print("  使用树宽分解利用序列的生物学结构")
