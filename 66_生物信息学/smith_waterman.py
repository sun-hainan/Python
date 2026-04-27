# -*- coding: utf-8 -*-

"""

算法实现：生物信息学 / smith_waterman



本文件实现 smith_waterman 相关的算法功能。

"""



from typing import Tuple





def smith_waterman(seq1: str, seq2: str, match: int = 1, mismatch: int = -1, gap: int = -1) -> Tuple[int, str, str]:

    """

    局部序列比对（Smith-Waterman算法）



    返回：(最佳得分, 对齐后的seq1, 对齐后的seq2)

    """

    m, n = len(seq1), len(seq2)



    # DP表

    dp = [[0] * (n + 1) for _ in range(m + 1)]



    max_score = 0

    max_i, max_j = 0, 0



    # 填表

    for i in range(1, m + 1):

        for j in range(1, n + 1):

            if seq1[i-1] == seq2[j-1]:

                diag = dp[i-1][j-1] + match

            else:

                diag = dp[i-1][j-1] + mismatch



            up = dp[i-1][j] + gap

            left = dp[i][j-1] + gap



            # 关键区别：不允许负分，截断到0

            dp[i][j] = max(0, diag, up, left)



            if dp[i][j] > max_score:

                max_score = dp[i][j]

                max_i, max_j = i, j



    # 从最高分位置回溯

    align1, align2 = [], []

    i, j = max_i, max_j



    while i > 0 and j > 0:

        if dp[i][j] == 0:

            break



        if seq1[i-1] == seq2[j-1]:

            score = match

        else:

            score = mismatch



        if dp[i][j] == dp[i-1][j-1] + score:

            align1.append(seq1[i-1])

            align2.append(seq2[j-1])

            i -= 1

            j -= 1

        elif dp[i][j] == dp[i-1][j] + gap:

            align1.append(seq1[i-1])

            align2.append('-')

            i -= 1

        else:

            align1.append('-')

            align2.append(seq2[j-1])

            j -= 1



    return max_score, ''.join(reversed(align1)), ''.join(reversed(align2))





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== Smith-Waterman 测试 ===\n")



    seq1 = "GATTACA"

    seq2 = "GCATGCU"



    score, align1, align2 = smith_waterman(seq1, seq2)



    print(f"序列1: {seq1}")

    print(f"序列2: {seq2}")

    print(f"最佳局部得分: {score}")

    print(f"局部对齐:")

    print(f"  {align1}")

    print(f"  {align2}")



    print("\n与全局比对对比（Needleman-Wunsch）：")

    from needleman_wunsch import needleman_wunsch

    score_global, g1, g2 = needleman_wunsch(seq1, seq2)

    print(f"全局得分: {score_global}")

    print(f"  {g1}")

    print(f"  {g2}")



    print("\n说明：")

    print("  - 局部比对找出最高相似的子区域")

    print("  - 全局比对从头到尾完整比对")

    print("  - BLAST基于Smith-Waterman的启发式加速")

