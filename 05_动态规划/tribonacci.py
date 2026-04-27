# -*- coding: utf-8 -*-
"""
算法实现：05_动态规划 / tribonacci

本文件实现 tribonacci 相关的算法功能。
"""

from typing import List


def trinonacci_recursive(n: int) -> int:
    """
    递归版本

    参数：
        n: 第n项（从0开始）

    返回：T(n)

    复杂度：时间O(3^n)，空间O(n)递归栈
    """
    if n == 0:
        return 0
    if n == 1:
        return 0
    if n == 2:
        return 1

    return (trinonacci_recursive(n - 1) +
            trinonacci_recursive(n - 2) +
            trinonacci_recursive(n - 3))


def trinonacci_memoized(n: int, memo: List[int] = None) -> int:
    """
    记忆化递归（动态规划）

    参数：
        n: 第n项
        memo: 记忆化表

    返回：T(n)

    复杂度：时间O(n)，空间O(n)
    """
    if memo is None:
        memo = [-1] * (n + 1)

    if n == 0:
        return 0
    if n == 1:
        return 0
    if n == 2:
        return 1

    if memo[n] != -1:
        return memo[n]

    memo[n] = (trinonacci_memoized(n - 1, memo) +
               trinonacci_memoized(n - 2, memo) +
               trinonacci_memoized(n - 3, memo))

    return memo[n]


def trinonacci_iterative(n: int) -> int:
    """
    迭代版本（空间优化）

    参数：
        n: 第n项

    返回：T(n)

    复杂度：时间O(n)，空间O(1)
    """
    if n == 0:
        return 0
    if n == 1:
        return 0
    if n == 2:
        return 1

    a, b, c = 0, 0, 1  # T(0), T(1), T(2)

    for i in range(3, n + 1):
        next_val = a + b + c
        a, b, c = b, c, next_val

    return c


def trinonacci_matrix(n: int) -> int:
    """
    矩阵快速幂版本

    |T(n)  |   |1 1 1|^(n-2) |T(2)|
    |T(n-1)| = |1 0 0|       |T(1)|
    |T(n-2)|   |0 1 0|       |T(0)|

    参数：
        n: 第n项

    返回：T(n)

    复杂度：时间O(log n)，空间O(1)
    """
    if n == 0:
        return 0
    if n == 1:
        return 0
    if n == 2:
        return 1

    # 基础矩阵
    base = [[1, 1, 1],
            [1, 0, 0],
            [0, 1, 0]]

    # 快速幂
    result = [[1, 0, 0],
              [0, 1, 0],
              [0, 0, 1]]

    power = n - 2

    while power > 0:
        if power % 2 == 1:
            result = matrix_multiply(result, base)
        base = matrix_multiply(base, base)
        power //= 2

    # 乘以初始向量 [T(2), T(1), T(0)]^T = [1, 0, 0]^T
    return result[0][0]


def matrix_multiply(A: List[List[int]], B: List[List[int]]) -> List[List[int]]:
    """矩阵乘法"""
    n = len(A)
    C = [[0] * n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            for k in range(n):
                C[i][j] += A[i][k] * B[k][j]

    return C


def generate_trinonacci_sequence(n: int) -> List[int]:
    """
    生成前n项Trinonacci数列

    参数：
        n: 项数

    返回：Trinonacci数列列表
    """
    if n <= 0:
        return []

    seq = [0, 0, 1]  # T(0), T(1), T(2)

    for i in range(3, n):
        seq.append(seq[-1] + seq[-2] + seq[-3])

    return seq[:n]


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== Trinonacci数列测试 ===\n")

    n = 10

    print(f"前{n}项Trinonacci数列:")
    seq = generate_trinonacci_sequence(n)
    for i, val in enumerate(seq):
        print(f"  T({i}) = {val}")

    print()

    # 比较三种方法
    test_n = [5, 10, 20, 30]

    print("方法对比:")
    for n in test_n:
        rec = trinonacci_recursive(n)
        iter_result = trinonacci_iterative(n)
        mat = trinonacci_matrix(n)
        print(f"  T({n}): 递归={rec}, 迭代={iter_result}, 矩阵={mat}")

    print()

    print("复杂度对比:")
    print("  递归:   O(3^n) 时间, O(n) 空间")
    print("  记忆化: O(n) 时间, O(n) 空间")
    print("  迭代:   O(n) 时间, O(1) 空间")
    print("  矩阵:   O(log n) 时间, O(1) 空间")

    print()
    print("与斐波那契对比:")
    print("  Trinonacci增长率 ≈ 1.839^n（黄金比例≈1.618）")
    print("  增长更快，因为更多项求和")
