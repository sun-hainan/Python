# -*- coding: utf-8 -*-
"""
算法实现：08_位运算 / chudnovsky_multiplication

本文件实现 chudnovsky_multiplication 相关的算法功能。
"""

import math
from typing import Generator

# 预计算常数（Chudnovsky系数）
CHUDNOVSKY_A = 13591409  # 分子常数项
CHUDNOVSKY_B = 545140134  # 分子系数
CHUDNOVSKY_C = 13591409  # 初始值
CHUDNOVSKY_SCALING = 426880 * int(math.sqrt(10005))  # 全局缩放因子

# 大数乘法基础参数（Karatsuba阈值）
KARATSUBA_THRESHOLD = 32  # 超过此位数启用Karatsuba


def chudnovsky_term(k: int) -> tuple[int, int]:
    """
    计算Chudnovsky级数第k项的分子和分母
    返回 (numerator, denominator)
    """
    # 分子：C_k * (6k)!
    C_k = CHUDNOVSKY_B * k + CHUDNOVSKY_A
    six_k_fact = math.prod(range(1, 6 * k + 1))  # (6k)!
    numerator = C_k * six_k_fact

    # 分母：k!³ × 3^k
    k_fact = math.factorial(k)
    denominator = k_fact ** 3 * (3 ** k)

    return numerator, denominator


def chudnovsky_series(n_terms: int) -> Generator[tuple[int, int, float], None, None]:
    """迭代生成Chudnovsky级数项"""
    for k in range(n_terms):
        num, den = chudnovsky_term(k)
        ratio = num / den
        yield num, den, ratio


def compute_pi_digits(n_terms: int) -> float:
    """使用Chudnovsky算法近似计算π"""
    total = 0
    for k in range(n_terms):
        num, den = chudnovsky_term(k)
        if k % 2 == 0:
            total += num / den
        else:
            total -= num / den

    pi_approx = CHUDNOVSKY_SCALING / total
    return pi_approx


def karatsuba_mult(x: int, y: int) -> int:
    """Karatsuba快速乘法：O(n^log2(3)) ≈ O(n^1.585)"""
    if x < 10 or y < 10:
        return x * y

    n = max(x.bit_length(), y.bit_length())
    half = (n + 1) // 2

    # 拆分
    a, b = divmod(x, 1 << half)  # x = a*2^half + b
    c, d = divmod(y, 1 << half)  # y = c*2^half + d

    # 递归计算三个中间量
    ac = karatsuba_mult(a, c)
    bd = karatsuba_mult(b, d)
    ad_bc = karatsuba_mult(a + b, c + d) - ac - bd

    # 合并结果：ac * 2^(2*half) + (ad+bc) * 2^half + bd
    return (ac << (2 * half)) + (ad_bc << half) + bd


if __name__ == "__main__":
    import time

    print("=== Chudnovsky算法计算π ===")

    # 测试不同项数
    for terms in [1, 5, 10, 20, 50]:
        start = time.perf_counter()
        pi_approx = compute_pi_digits(terms)
        elapsed = time.perf_counter() - start
        error = abs(pi_approx - math.pi)
        print(f"项数={terms:3d}: π≈{pi_approx:.15f} | 误差={error:.2e} | 耗时={elapsed:.4f}s")

    print(f"\n参考值: {math.pi:.15f}")

    # Karatsuba乘法演示
    print("\n=== Karatsuba乘法测试 ===")
    test_pairs = [
        (123456789012345678901234567890, 987654321098765432109876543210),
        (99999999999999999999, 111111111111111111111),
        (31415926535897932384, 23846264338327950288),
    ]

    for x, y in test_pairs:
        result = karatsuba_mult(x, y)
        expected = x * y
        status = "✓" if result == expected else "✗"
        print(f"{status} {str(x)[:20]}... × {str(y)[:20]}...")
        print(f"    结果位数: {result.bit_length()}")
        print(f"    验证: {result == expected}")
