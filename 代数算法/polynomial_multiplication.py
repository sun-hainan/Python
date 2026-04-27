# -*- coding: utf-8 -*-
"""
算法实现：代数算法 / polynomial_multiplication

本文件实现 polynomial_multiplication 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple


def naive_polynomial_multiply(a: List[float], b: List[float]) -> List[float]:
    """
    朴素多项式乘法

    复杂度：O(n²)
    """
    n = len(a) + len(b) - 1
    result = [0.0] * n

    for i, ai in enumerate(a):
        for j, bj in enumerate(b):
            result[i + j] += ai * bj

    return result


def fft_recursive(x: List[complex], inverse: bool = False) -> List[complex]:
    """
    递归FFT

    复杂度：O(n log n)
    """
    n = len(x)

    if n <= 1:
        return x

    # 分治：偶数和奇数
    even = fft_recursive(x[0::2], inverse)
    odd = fft_recursive(x[1::2], inverse)

    # 合并
    result = [0j] * n
    for k in range(n // 2):
        if not inverse:
            t = np.exp(2j * np.pi * k / n) * odd[k]
        else:
            t = np.exp(-2j * np.pi * k / n) * odd[k]

        result[k] = even[k] + t
        result[k + n // 2] = even[k] - t

    return result


def fft_iterative(x: List[complex], inverse: bool = False) -> List[complex]:
    """
    迭代FFT（更高效）

    使用位反转重排
    """
    n = len(x)

    # 位反转重排
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit

        if i < j:
            x[i], x[j] = x[j], x[i]

    # FFT蝴蝶操作
    length = 2
    while length <= n:
        angle = -2j * np.pi / length if not inverse else 2j * np.pi / length
        wlen = np.exp(angle)

        for i in range(0, n, length):
            w = 1j + 0
            for j in range(i, i + length // 2):
                u = x[j]
                v = x[j + length // 2] * w
                x[j] = u + v
                x[j + length // 2] = u - v
                w *= wlen

        length <<= 1

    if inverse:
        for i in range(n):
            x[i] /= n

    return x


def polynomial_multiply_fft(a: List[float], b: List[float]) -> List[float]:
    """
    使用FFT的多项式乘法

    参数：
        a, b: 系数向量

    返回：乘积的系数向量
    """
    # 确定合适的长度（2的幂）
    n = 1
    while n < len(a) + len(b) - 1:
        n <<= 1

    # 填充
    a_complex = np.array(a + [0] * (n - len(a)), dtype=complex)
    b_complex = np.array(b + [0] * (n - len(b)), dtype=complex)

    # FFT
    a_fft = fft_iterative(list(a_complex), inverse=False)
    b_fft = fft_iterative(list(b_complex), inverse=False)

    # 点乘
    c_fft = [a * b for a, b in zip(a_fft, b_fft)]

    # 逆FFT
    c = fft_iterative(c_fft, inverse=True)

    # 取实部（四舍五入到整数）
    result = [int(round(x.real)) for x in c[:len(a) + len(b) - 1]]

    return result


def polynomial_coefficients():
    """多项式系数表示"""
    print("=== 多项式乘法 ===")
    print()
    print("系数表示 vs 点值表示")
    print()
    print("系数表示：")
    print("  a(x) = a0 + a1*x + a2*x² + ...")
    print("  乘法需要 O(n²)")
    print()
    print("点值表示：")
    print("  在n个点求值 (x_i, y_i)")
    print("  乘法变成点乘 O(n)")
    print()
    print("FFT桥接两者：")
    print("  系数 -> 点值 (FFT) O(n log n)")
    print("  点乘 O(n)")
    print("  点值 -> 系数 (逆FFT) O(n log n)")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== FFT多项式乘法测试 ===\n")

    # 测试
    a = [1, 2, 3]  # 1 + 2x + 3x²
    b = [4, 5]      # 4 + 5x

    print(f"a = {a}")
    print(f"b = {b}")
    print()

    # 朴素方法
    result_naive = naive_polynomial_multiply(a, b)
    print(f"朴素乘法: {result_naive}")

    # FFT方法
    result_fft = polynomial_multiply_fft(a, b)
    print(f"FFT乘法: {result_fft}")

    # 验证
    print()
    print("验证：(1+2x+3x²)(4+5x)")
    print("  = 4 + 5x + 8x + 10x² + 12x² + 15x³")
    print("  = 4 + 13x + 22x² + 15x³")
    expected = [4, 13, 22, 15]
    print(f"  期望: {expected}")
    print(f"  匹配: {'✅' if result_fft == expected else '❌'}")

    print()
    polynomial_coefficients()

    print()
    print("应用：")
    print("  - 大整数乘法（Karatsuba的改进）")
    print("  - 信号卷积")
    print("  - 图像处理中的滤镜")
