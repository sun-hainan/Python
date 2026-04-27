# -*- coding: utf-8 -*-
"""
算法实现：代数算法 / integer_multiplication

本文件实现 integer_multiplication 相关的算法功能。
"""

import numpy as np
from typing import Tuple


class IntegerMultiplier:
    """整数乘法器"""

    def __init__(self, method: str = "fft"):
        """
        参数：
            method: 方法 "naive", "karatsuba", "fft"
        """
        self.method = method

    def multiply(self, a: int, b: int) -> int:
        """
        乘法

        参数：
            a, b: 非负整数

        返回：a × b
        """
        if self.method == "naive":
            return self._naive_multiply(a, b)
        elif self.method == "karatsuba":
            return self._karatsuba(a, b)
        elif self.method == "fft":
            return self._fft_multiply(a, b)
        else:
            return a * b

    def _naive_multiply(self, a: int, b: int) -> int:
        """朴素乘法 O(n²)"""
        result = 0
        a_str = str(a)
        b_str = str(b)

        for i, digit_a in enumerate(reversed(a_str)):
            carry = 0
            row = []

            for digit_b in reversed(b_str):
                product = (ord(digit_a) - 48) * (ord(digit_b) - 48) + carry
                row.append(product % 10)
                carry = product // 10

            if carry:
                row.append(carry)

            # 处理移位
            for _ in range(i):
                row.insert(0, 0)

            # 加到结果
            result += int(''.join(map(str, row[::-1])))

        return result

    def _karatsuba(self, a: int, b: int) -> int:
        """Karatsuba算法 O(n^{log2(3)})"""
        a_str = str(a)
        b_str = str(b)

        n = max(len(a_str), len(b_str))

        # 小数字直接乘
        if n <= 4:
            return a * b

        # 分成两半
        m = n // 2

        a_high = a // (10 ** m)
        a_low = a % (10 ** m)
        b_high = b // (10 ** m)
        b_low = b % (10 ** m)

        # 三个乘法
        z0 = self._karatsuba(a_low, b_low)
        z2 = self._karatsuba(a_high, b_high)

        # z1 = (a_low + a_high)(b_low + b_high) - z2 - z0
        z1_mid = self._karatsuba(a_low + a_high, b_low + b_high)
        z1 = z1_mid - z2 - z0

        return z2 * (10 ** (2 * m)) + z1 * (10 ** m) + z0

    def _fft_multiply(self, a: int, b: int) -> int:
        """FFT乘法 O(n log n)"""
        if a == 0 or b == 0:
            return 0

        # 转换为数字数组
        a_digits = [int(d) for d in str(a)]
        b_digits = [int(d) for d in str(b)]

        # 反转
        a_digits = a_digits[::-1]
        b_digits = b_digits[::-1]

        # 找到合适的长度
        n = 1
        while n < len(a_digits) + len(b_digits):
            n *= 2

        # 补零
        a_digits += [0] * (n - len(a_digits))
        b_digits += [0] * (n - len(b_digits))

        # FFT（简化版本）
        a_fft = np.fft.fft(a_digits)
        b_fft = np.fft.fft(b_digits)

        # 乘积
        c_fft = a_fft * b_fft

        # 逆FFT
        c = np.fft.ifft(c_fft).real.round().astype(int)

        # 进位处理
        result = 0
        carry = 0
        for i in range(len(c)):
            total = int(c[i]) + carry
            result += (total % 10) * (10 ** i)
            carry = total // 10

        while carry > 0:
            result += (carry % 10) * (10 ** len(c))
            carry //= 10

        return result


def multiplication_complexity():
    """乘法复杂度"""
    print("=== 整数乘法复杂度 ===")
    print()
    print("方法对比：")
    print("  朴素: O(n²)")
    print("  Karatsuba: O(n^{1.585})")
    print("  FFT: O(n log n)")
    print()
    print("历史：")
    print("  1960: Karatsuba 发现")
    print("  1968: Schönhage-Strassen")
    print("  2019: 进一步改进")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 整数乘法测试 ===\n")

    multiplier = IntegerMultiplier()

    test_cases = [
        (123, 456),
        (123456789, 987654321),
        (111111111, 111111111),
    ]

    for a, b in test_cases:
        print(f"{a} × {b}")

        # 参考值
        expected = a * b

        # Karatsuba
        karatsuba_result = multiplier._karatsuba(a, b)
        print(f"  Karatsuba: {karatsuba_result}")

        # FFT
        fft_result = multiplier._fft_multiply(a, b)
        print(f"  FFT: {fft_result}")
        print(f"  正确: {'✅' if fft_result == expected else '❌'}")
        print()

    multiplication_complexity()

    print()
    print("说明：")
    print("  - FFT适合大数相乘")
    print("  - Python内置int已经很快")
    print("  - 学习目的理解算法思想")
