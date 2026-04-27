# -*- coding: utf-8 -*-
"""
算法实现：生物信息学 / needleman_wunsch

本文件实现 needleman_wunsch 相关的算法功能。
"""

from typing import Tuple


def needleman_wunsch(seq1: str, seq2: str, match: int = 1, mismatch: int = -1, gap: int = -1) -> Tuple[int, str, str]:
    """
    全局序列比对（Needleman-Wunsch算法）

    参数：
        seq1: 序列1
        seq2: 序列2
        match: 匹配得分
        mismatch: 不匹配惩罚
        gap: 空位惩罚

    返回：(得分, 对齐后的seq1, 对齐后的seq2)
    """
    m, n = len(seq1), len(seq2)

    # DP表初始化
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # 初始化第一行和第一列
    for i in range(m + 1):
        dp[i][0] = i * gap
    for j in range(n + 1):
        dp[0][j] = j * gap

    # 填表
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if seq1[i-1] == seq2[j-1]:
                diag = dp[i-1][j-1] + match
            else:
                diag = dp[i-1][j-1] + mismatch

            up = dp[i-1][j] + gap
            left = dp[i][j-1] + gap

            dp[i][j] = max(diag, up, left)

    # 回溯
    align1, align2 = [], []
    i, j = m, n

    while i > 0 or j > 0:
        if i > 0 and j > 0:
            if seq1[i-1] == seq2[j-1]:
                score = match
            else:
                score = mismatch

            if dp[i][j] == dp[i-1][j-1] + score:
                align1.append(seq1[i-1])
                align2.append(seq2[j-1])
                i -= 1
                j -= 1
            elif i > 0 and dp[i][j] == dp[i-1][j] + gap:
                align1.append(seq1[i-1])
                align2.append('-')
                i -= 1
            else:
                align1.append('-')
                align2.append(seq2[j-1])
                j -= 1
        elif i > 0:
            align1.append(seq1[i-1])
            align2.append('-')
            i -= 1
        else:
            align1.append('-')
            align2.append(seq2[j-1])
            j -= 1

    return dp[m][n], ''.join(reversed(align1)), ''.join(reversed(align2))


def blosum62_matrix() -> dict:
    """BLOSUM62替换矩阵（简化的氨基酸替换得分）"""
    # 简化的得分矩阵（实际BLOSUM62是20x20）
    same = {'A': 'A', 'T': 'T', 'G': 'G', 'C': 'C',
            'R': 'R', 'Y': 'Y', 'S': 'S', 'W': 'W', 'K': 'K', 'M': 'M',
            'B': 'B', 'D': 'D', 'H': 'H', 'V': 'V', 'N': 'N'}
    return same


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 全局序列比对测试 ===\n")

    # DNA序列
    seq1 = "GATTACA"
    seq2 = "GCATGCU"

    score, align1, align2 = needleman_wunsch(seq1, seq2, match=1, mismatch=-1, gap=-2)

    print(f"序列1: {seq1}")
    print(f"序列2: {seq2}")
    print(f"比对得分: {score}")
    print(f"对齐结果:")
    print(f"  {align1}")
    print(f"  {align2}")

    # 蛋白质序列示例
    print("\n--- 蛋白质序列比对 ---")
    prot1 = "PAWHEAE"
    prot2 = "HEAGAWGHEE"

    score2, a1, a2 = needleman_wunsch(prot1, prot2, match=1, mismatch=-1, gap=-2)
    print(f"蛋白1: {prot1}")
    print(f"蛋白2: {prot2}")
    print(f"比对得分: {score2}")
    print(f"对齐:")
    print(f"  {a1}")
    print(f"  {a2}")

    print("\n说明：")
    print("  - 全局比对：两条序列从头到尾完整比对")
    print("  - 局部比对：用Smith-Waterman（单独文件）")
    print("  - 生物信息学中用于DNA、RNA、蛋白质序列分析")
