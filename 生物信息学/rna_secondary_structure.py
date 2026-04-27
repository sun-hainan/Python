# -*- coding: utf-8 -*-
"""
算法实现：生物信息学 / rna_secondary_structure

本文件实现 rna_secondary_structure 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Optional, Dict
import math


def complementarity_check(base1: str, base2: str) -> bool:
    """检查两个碱基是否互补"""
    pairs = {('A', 'U'), ('U', 'A'), ('G', 'C'), ('C', 'G'), ('G', 'U'), ('U', 'G')}
    return (base1, base2) in pairs


def nussinov_algorithm(sequence: str) -> Tuple[np.ndarray, List[Tuple[int, int]]]:
    """
    Nussinov动态规划算法

    目标：最大化碱基配对数

    递归关系：
    dp[i][j] = max {
        dp[i+1][j],                           # 不配对i
        dp[i][j-1],                           # 不配对j
        dp[i+1][j-1] + 1,                     # i和j配对
        max_{i<k<j} dp[i][k] + dp[k+1][j]    # 分裂
    }

    参数:
        sequence: RNA序列（如 "ACGU"）

    返回:
        (dp_matrix, base_pairs)
    """
    n = len(sequence)
    dp = np.zeros((n, n), dtype=int)

    # 填充dp矩阵
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1

            # 初始化：dp[i][j] = dp[i+1][j] 或 dp[i][j-1]
            dp[i][j] = dp[i + 1][j] if i + 1 <= j else 0
            dp[i][j] = max(dp[i][j], dp[i][j - 1] if i <= j - 1 else 0)

            # 如果i和j可以配对
            if complementarity_check(sequence[i], sequence[j]):
                pair_score = 1
                if i + 1 <= j - 1:
                    pair_score = max(pair_score, dp[i + 1][j - 1] + 1)
                dp[i][j] = max(dp[i][j], pair_score)

            # 分裂
            for k in range(i + 1, j):
                score = dp[i][k] + dp[k + 1][j]
                dp[i][j] = max(dp[i][j], score)

    # 回溯找配对
    pairs = []
    def traceback(i, j):
        if i >= j:
            return
        if dp[i][j] == dp[i + 1][j]:
            traceback(i + 1, j)
        elif dp[i][j] == dp[i][j - 1]:
            traceback(i, j - 1)
        elif complementarity_check(sequence[i], sequence[j]) and              (i + 1 > j - 1 or dp[i][j] == dp[i + 1][j - 1] + 1):
            pairs.append((i, j))
            traceback(i + 1, j - 1)
        else:
            for k in range(i + 1, j):
                if dp[i][j] == dp[i][k] + dp[k + 1][j]:
                    traceback(i, k)
                    traceback(k + 1, j)
                    break

    traceback(0, n - 1)
    return dp, pairs


def zuker_algorithm(sequence: str) -> Tuple[float, List[Tuple[int, int]]]:
    """
    Zuker算法 - 自由能最小化

    能量参数（简化）：
    - GC配对：-3 kcal/mol
    - AU配对：-2 kcal/mol
    - GU配对：-1 kcal/mol
    - 内环/凸起：+4 kcal/mol

    参数:
        sequence: RNA序列

    返回:
        (min_energy, base_pairs)
    """
    n = len(sequence)
    INF = float('inf')

    # 能量参数
    pair_energy = {
        ('G', 'C'): -3.0, ('C', 'G'): -3.0,
        ('A', 'U'): -2.0, ('U', 'A'): -2.0,
        ('G', 'U'): -1.0, ('U', 'G'): -1.0,
    }

    def pair_e(i, j):
        return pair_energy.get((sequence[i], sequence[j]), INF)

    # dp[i][j]: 从i到j的最小自由能
    dp = np.full((n, n), INF)
    trace = np.full((n, n), -1, dtype=int)

    # 初始化：单碱基不能形成配对
    for i in range(n):
        dp[i][i] = 0
        if i + 1 < n:
            dp[i][i + 1] = 0

    # 填充
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1

            # 情况1：不形成茎（分裂）
            for k in range(i, j):
                if dp[i][k] + dp[k + 1][j] < dp[i][j]:
                    dp[i][j] = dp[i][k] + dp[k + 1][j]
                    trace[i][j] = k  # 分裂点

            # 情况2：i和j配对
            if pair_e(i, j) != INF:
                # 配对形成茎
                if i + 1 <= j - 1 and dp[i + 1][j - 1] + pair_e(i, j) < dp[i][j]:
                    dp[i][j] = dp[i + 1][j - 1] + pair_e(i, j)
                    trace[i][j] = -2  # 配对标记

    # 回溯
    pairs = []
    def traceback(i, j):
        if i >= j:
            return
        if trace[i][j] == -1:
            pass  # 已有最优
        elif trace[i][j] == -2:
            pairs.append((i, j))
            traceback(i + 1, j - 1)
        else:
            k = trace[i][j]
            traceback(i, k)
            traceback(k + 1, j)

    traceback(0, n - 1)
    return dp[0][n - 1], pairs


def visualize_structure(sequence: str, pairs: List[Tuple[int, int]]) -> str:
    """
    可视化RNA二级结构（点括号表示法）

    参数:
        sequence: RNA序列
        pairs: 配对列表

    返回:
        可视化字符串
    """
    n = len(sequence)
    structure = ['.'] * n
    pair_dict = {i: j for i, j in pairs}

    for i, j in pairs:
        structure[i] = '('
        structure[j] = ')'

    return ''.join(structure)


def dot_bracket_to_pairs(dot_bracket: str) -> List[Tuple[int, int]]:
    """点括号表示法转配对列表"""
    stack = []
    pairs = []
    for i, c in enumerate(dot_bracket):
        if c == '(':
            stack.append(i)
        elif c == ')':
            if stack:
                j = stack.pop()
                pairs.append((j, i))
    return pairs


if __name__ == '__main__':
    print('=== RNA二级结构预测测试 ===')

    sequences = ['ACGU', 'GGCC', 'ACGUACGU', 'ACGUCCGGAAU']
    for seq in sequences:
        print(f'\n序列: {seq}')

        # Nussinov
        dp, pairs = nussinov_algorithm(seq)
        structure = visualize_structure(seq, pairs)
        print(f'  Nussinov: 配对数={dp[0][len(seq)-1]}, 结构={structure}')
        print(f'  配对: {pairs}')

        # Zuker
        energy, pairs_z = zuker_algorithm(seq)
        structure_z = visualize_structure(seq, pairs_z)
        print(f'  Zuker: 自由能={energy:.1f} kcal/mol, 结构={structure_z}')
        print(f'  配对: {pairs_z}')

    # 验证点括号
    print('\n--- 验证点括号转换 ---')
    test = '..((..))..((..))..'
    pairs_test = dot_bracket_to_pairs(test)
    print(f'点括号: {test}')
    print(f'配对: {pairs_test}')
