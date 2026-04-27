# -*- coding: utf-8 -*-
"""
算法实现：08_位运算 / solinas_reduction

本文件实现 solinas_reduction 相关的算法功能。
"""

import math

# Solinas常数：2^255 - 19（Curve25519的素数模数）
MODULUS = (1 << 255) - 19


def solinas_reduce(w: int, m: int = MODULUS) -> int:
    """
    Solinas约简算法：
    对于大数w，将其表示为 w = q * 2^255 + r
    其中 r = w mod 2^255，然后通过特殊约简规则处理q部分
    核心：对于模数 2^255 - 19，有 2^255 ≡ 19 (mod m)
    所以 w ≡ q * 19 + r (mod m)
    """
    # 提取低255位
    low = w & ((1 << 255) - 1)
    # 提取高位部分（超过255位的部分）
    high = w >> 255

    # 迭代约简：high * 2^255 ≡ high * 19
    result = low + high * 19

    # 如果结果仍然超过模数，递归约简
    if result >= m:
        return solinas_reduce(result, m)
    return result


def montgomery_multiply(a: int, b: int, m: int = MODULUS) -> int:
    """
    Montgomery乘法（配合Solinas约简）：
    计算 a * b mod m
    使用ReDot基表示法避免大数除法
    """
    # 简单的O(n²)乘法用于演示（实际用Karatsuba/Toom-Cook）
    product = a * b
    return solinas_reduce(product, m)


def pow_mod_solinas(base: int, exp: int, m: int = MODULUS) -> int:
    """使用Solinas约简的快速幂模"""
    result = 1
    base = base % m

    while exp > 0:
        if exp & 1:
            result = montgomery_multiply(result, base, m)
        base = montgomery_multiply(base, base, m)
        exp >>= 1

    return result


def validate_solinas() -> bool:
    """验证Solinas约简的正确性"""
    import random
    for _ in range(1000):
        w = random.getrandbits(512)  # 测试512位大数
        expected = w % MODULUS
        actual = solinas_reduce(w, MODULUS)
        if expected != actual:
            return False
    return True


def decode_scalars(hex_str: str) -> list[int]:
    """将十六进制字符串解码为标量数组（用于椭圆曲线）"""
    scalars = []
    for i in range(0, len(hex_str), 8):
        chunk = hex_str[i:i + 8]
        if chunk:
            scalars.append(int(chunk, 16))
    return scalars


if __name__ == "__main__":
    print("=== Solinas模约简测试 ===")
    print(f"模数: 2^255 - 19 = {MODULUS}")

    # 正确性验证
    print(f"\n正确性验证: {'✓ 通过' if validate_solinas() else '✗ 失败'}")

    # 性能测试
    import time

    test_values = [1 << 500, (1 << 600) - 12345, 10 ** 180]

    for i, w in enumerate(test_values):
        start = time.perf_counter()
        for _ in range(1000):
            result = solinas_reduce(w)
        elapsed = time.perf_counter() - start
        print(f"测试{i + 1}: w.bit_length()={w.bit_length()}, 1000次约简耗时={elapsed:.4f}s")

    # Montgomery乘法演示
    print("\n=== Montgomery乘法 ===")
    a, b = 123456789012345678901234567890, 987654321098765432109876543210
    result = montgomery_multiply(a, b)
    expected = (a * b) % MODULUS
    status = "✓" if result == expected else "✗"
    print(f"{status} ({a}... × {b}...) mod M = {result}")

    # 幂模运算
    print("\n=== 幂模运算 ===")
    base, exp = 2, 1000
    result = pow_mod_solinas(base, exp)
    expected = pow(base, exp, MODULUS)
    status = "✓" if result == expected else "✗"
    print(f"{status} {base}^{exp} mod M = {result}")
