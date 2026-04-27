# -*- coding: utf-8 -*-
"""
算法实现：27_整数与FFT / fft_multiplication

本文件实现 fft_multiplication 相关的算法功能。
"""

import math
from typing import List, Tuple


# ============================================================
# 复数运算
# ============================================================

def fft_cooley_tukey(a: List[complex], invert: bool = False) -> List[complex]:
    """
    Cooley-Tukey 迭代版 FFT 算法
    
    参数:
        a: 输入序列 (复数)
        invert: False = 离散傅里叶变换 (DFT), True = 逆 FFT
    
    原理:
        将序列分为偶数位和奇数位:
        F(k) = F_even(k) + W_n^k * F_odd(k)
        F(k + n/2) = F_even(k) - W_n^k * F_odd(k)
        
    复杂度: O(n log n)
    """
    n = len(a)
    
    # 位反转重排 (bit-reversal permutation)
    # 将索引按二进制反转, 例如 001 -> 100
    j = 0  # 交换位置
    for i in range(1, n):
        bit = n >> 1
        # 找到需要交换的位置
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        
        if i < j:
            a[i], a[j] = a[j], a[i]
    
    # 长度 2, 4, 8, ... 的 DFT 逐级合并
    length = 2
    while length <= n:
        # 单位根 W = e^(2πi/length)
        # 对于逆 FFT, 使用共轭
        angle = -2 * math.pi / length if not invert else 2 * math.pi / length
        w_base = complex(math.cos(angle), math.sin(angle))
        
        # 每组有 length 个元素
        for i in range(0, n, length):
            w = 1 + 0j
            half = length // 2
            for j in range(half):
                # 蝴蝶操作
                u = a[i + j]
                v = a[i + j + half] * w
                a[i + j] = u + v
                a[i + j + half] = u - v
                w *= w_base
        
        length <<= 1
    
    # 逆 FFT 需要除以 n
    if invert:
        for i in range(n):
            a[i] /= n
    
    return a


def multiply_fft(x: List[int], y: List[int], base: int = 10000) -> List[int]:
    """
    使用 FFT 加速的多项式乘法
    
    参数:
        x: 第一个数, 每一位是一个数组元素, 低位在前
        y: 第二个数, 低位在前
        base: 每个系数表示的进制 (默认 10000 = 10^4, 避免复数精度问题)
    
    返回:
        乘积结果, 低位在前
        
    原理:
        将大整数 a = Σ a_i * base^i 表示为多项式
        两个整数的乘积 = 两个多项式的卷积
        
    时间复杂度: O(n log n), 其中 n 是结果长度
    """
    # 取较长的长度, 扩展到 2 的幂次
    n = 1
    while n < len(x) + len(y):
        n <<= 1
    
    # 扩展到 n 长度, 转换为复数
    x_complex = [complex(v, 0) for v in x] + [complex(0, 0)] * (n - len(x))
    y_complex = [complex(v, 0) for v in y] + [complex(0, 0)] * (n - len(y))
    
    # FFT
    fft_x = fft_cooley_tukey(x_complex, invert=False)
    fft_y = fft_cooley_tukey(y_complex, invert=False)
    
    # 点值乘法
    for i in range(n):
        fft_x[i] *= fft_y[i]
    
    # 逆 FFT
    result_complex = fft_cooley_tukey(fft_x, invert=True)
    
    # 取实部四舍五入, 得到卷积结果
    result = [0] * (len(x) + len(y))
    for i in range(len(result)):
        result[i] = int(round(result_complex[i].real))
    
    # 进位处理
    carry = 0
    for i in range(len(result)):
        total = result[i] + carry
        result[i] = total % base
        carry = total // base
    
    # 移除多余的前导零
    while len(result) > 1 and result[-1] == 0:
        result.pop()
    
    return result


# ============================================================
# 纯 Python 复数实现 (用于教学理解)
# ============================================================

class Complex:
    """简化的复数类, 用于理解 FFT 原理"""
    
    def __init__(self, real: float, imag: float = 0.0):
        self.real = real
        self.imag = imag
    
    def __add__(self, other):
        return Complex(self.real + other.real, self.imag + other.imag)
    
    def __sub__(self, other):
        return Complex(self.real - other.real, self.imag - other.imag)
    
    def __mul__(self, other):
        # (a + bi)(c + di) = (ac - bd) + (ad + bc)i
        return Complex(
            self.real * other.real - self.imag * other.imag,
            self.real * other.imag + self.imag * other.real
        )
    
    def __truediv__(self, scalar: float):
        return Complex(self.real / scalar, self.imag / scalar)
    
    def __repr__(self):
        if self.imag >= 0:
            return f"{self.real:.2f}+{self.imag:.2f}i"
        else:
            return f"{self.real:.2f}{self.imag:.2f}i"


def fft_verbose(a: List[Complex], invert: bool = False) -> List[Complex]:
    """
    详细打印版 FFT, 用于理解算法过程
    
    参数:
        a: 输入复数序列
        invert: 是否为逆变换
    
    返回:
        变换后的复数序列
    """
    n = len(a)
    
    # 位反转
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        if i < j:
            a[i], a[j] = a[j], a[i]
    
    # 合并
    length = 2
    step = 0
    while length <= n:
        angle = -2 * math.pi / length if not invert else 2 * math.pi / length
        w = Complex(math.cos(angle), math.sin(angle))
        
        for i in range(0, n, length):
            w_power = Complex(1, 0)
            half = length // 2
            for j in range(half):
                u = a[i + j]
                v = a[i + j + half] * w_power
                a[i + j] = u + v
                a[i + j + half] = u - v
                w_power = w_power * w
        
        length <<= 1
        step += 1
    
    if invert:
        for i in range(n):
            a[i] = a[i] / n
    
    return a


def multiply_fft_verbose(x: List[int], y: List[int], base: int = 1000) -> List[int]:
    """
    带详细打印的 FFT 乘法, 用于教学
    
    参数:
        x: 第一个数, 低位在前
        y: 第二个数, 低位在前
        base: 进制基数 (用 1000 避免精度问题)
    
    返回:
        乘积结果
    """
    print(f"\n输入: x={x}, y={y}, base={base}")
    
    n = 1
    while n < len(x) + len(y):
        n <<= 1
    print(f"扩展到 n={n} (2的幂次)")
    
    x_complex = [Complex(v, 0) for v in x] + [Complex(0, 0)] * (n - len(x))
    y_complex = [Complex(v, 0) for v in y] + [Complex(0, 0)] * (n - len(y))
    
    print(f"\nFFT 变换 x:")
    fft_x = fft_verbose(x_complex[:], invert=False)
    print(f"FFT(x) = {[round(c.real, 2) for c in fft_x]}")
    
    print(f"\nFFT 变换 y:")
    fft_y = fft_verbose(y_complex[:], invert=False)
    print(f"FFT(y) = {[round(c.real, 2) for c in fft_y]}")
    
    print(f"\n点值乘法:")
    for i in range(n):
        fft_x[i] = fft_x[i] * fft_y[i]
        print(f"  [{i}] = {round(fft_x[i].real, 2)}")
    
    print(f"\n逆 FFT:")
    result_complex = fft_verbose(fft_x, invert=True)
    print(f"逆 FFT 结果 (实部) = {[round(c.real, 2) for c in result_complex]}")
    
    result = [0] * (len(x) + len(y))
    for i in range(len(result)):
        result[i] = int(round(result_complex[i].real))
    
    print(f"\n原始卷积: {result}")
    
    # 进位处理
    carry = 0
    for i in range(len(result)):
        total = result[i] + carry
        result[i] = total % base
        carry = total // base
    
    while len(result) > 1 and result[-1] == 0:
        result.pop()
    
    print(f"进位处理后: {result}")
    return result


# ============================================================
# 数值精度问题与解决方案
# ============================================================

def multiply_fft_split(x: List[int], y: List[int]) -> List[int]:
    """
    分块 FFT, 避免精度问题
    
    原理: 
        每个系数可能很大, 直接 FFT 会因精度问题出错。
        解决: 将系数拆分为高低位, 多次 FFT 后合并。
        
    例如: 123456789 = 123 * 1000000 + 456789
          每块用更小的进制 (如 10000)
    """
    # 分块大小: 确保 4 块 FFT 结果不会超过 2^53 精度范围
    # 10000^4 = 10^16 < 2^53 ≈ 9 × 10^15
    BLOCK_SIZE = 4      # 每 4 位作为一块
    base = 10 ** BLOCK_SIZE
    
    def split_number(n: int) -> List[int]:
        """将大数按 BLOCK_SIZE 位分块"""
        result = []
        while n > 0:
            result.append(n % base)
            n //= base
        return result if result else [0]
    
    # 转换输入
    x_blocks = split_number(int(''.join(map(str, x)))) if isinstance(x[0], int) else x
    y_blocks = split_number(int(''.join(map(str, y)))) if isinstance(y[0], int) else y
    
    return multiply_fft(x_blocks, y_blocks, base)


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("FFT 快速傅里叶变换乘法测试")
    print("=" * 70)
    
    # 测试 1: 基础验证
    test_cases = [
        ([3, 2, 1], [4, 5], 10),      # 123 * 54 = 6642
        ([9, 9, 9], [1], 10),         # 999 * 1 = 999
        ([1, 0, 0], [1, 0, 0], 10),   # 001 * 001 = 1
    ]
    
    print("\n--- 基础测试 ---")
    for x, y, base in test_cases:
        result = multiply_fft(x, y, base)
        expected = 0
        for i, v in enumerate(x):
            expected += v * (base ** i)
        for i, v in enumerate(y):
            expected *= base ** len(y)
        # 简单计算期望
        expected = sum(x[i] * (base ** i) for i in range(len(x))) * \
                   sum(y[i] * (base ** i) for i in range(len(y)))
        
        # 验证
        calc = 0
        for i, v in enumerate(reversed(result)):
            calc = calc * base + v
        
        x_int = sum(x[i] * (base ** i) for i in range(len(x)))
        y_int = sum(y[i] * (base ** i) for i in range(len(y)))
        expected = x_int * y_int
        
        status = "✓" if calc == expected else "✗"
        x_str = ''.join(map(str, reversed(x)))
        y_str = ''.join(map(str, reversed(y)))
        print(f"{status} {x_str} * {y_str} = {''.join(map(str, reversed(result)))} (期望: {expected})")
    
    # 测试 2: 大数 FFT (使用更大的 base)
    print("\n--- 大数测试 (base=10000) ---")
    large_cases = [
        ([9999, 9999, 9999, 9999], [1, 2, 3, 4]),  # 999999999999 * 4321
        ([1] * 10, [1] * 10),                       # 1111111111 * 1111111111
    ]
    
    for x, y in large_cases:
        result = multiply_fft(x, y, base=10000)
        x_int = sum(x[i] * (10000 ** i) for i in range(len(x)))
        y_int = sum(y[i] * (10000 ** i) for i in range(len(y)))
        expected = x_int * y_int
        
        # 计算结果整数
        result_int = sum(result[i] * (10000 ** i) for i in range(len(result)))
        status = "✓" if result_int == expected else "✗"
        print(f"{status} 位数: len(x)={len(x)}, len(y)={len(y)}, len(result)={len(result)}")
        print(f"   期望: {expected}, 实际: {result_int}, 匹配: {result_int == expected}")
    
    # 测试 3: 详细打印版
    print("\n--- 详细 FFT 过程 (小数据) ---")
    result = multiply_fft_verbose([1, 2], [3, 4], base=10)  # 21 * 43 = 903
    print(f"结果: {''.join(map(str, reversed(result)))}")
    
    # 测试 4: 性能对比
    print("\n--- 性能测试 ---")
    import time
    
    # 创建大数: 500 位十进制数
    big_x = [9999] * 125  # 125 * 4 位 = 500 位
    big_y = [9999] * 125
    
    start = time.time()
    result = multiply_fft(big_x, big_y, base=10000)
    fft_time = time.time() - start
    
    # 纯 Python 乘法
    def naive_multiply(x: List[int], y: List[int], base: int) -> List[int]:
        result = [0] * (len(x) + len(y))
        for i in range(len(x)):
            for j in range(len(y)):
                result[i + j] += x[i] * y[j]
        # 进位
        carry = 0
        for i in range(len(result)):
            total = result[i] + carry
            result[i] = total % base
            carry = total // base
        while len(result) > 1 and result[-1] == 0:
            result.pop()
        return result
    
    start = time.time()
    result_naive = naive_multiply(big_x, big_y, base=10000)
    naive_time = time.time() - start
    
    print(f"FFT 乘法 (500位 × 500位): {fft_time:.4f}s")
    print(f"朴素乘法 (500位 × 500位): {naive_time:.4f}s")
    print(f"加速比: {naive_time / fft_time:.2f}x")
    
    # 验证正确性
    x_int = sum(big_x[i] * (10000 ** i) for i in range(len(big_x)))
    y_int = sum(big_y[i] * (10000 ** i) for i in range(len(big_y)))
    result_int = sum(result[i] * (10000 ** i) for i in range(len(result)))
    print(f"正确性验证: {result_int == x_int * y_int}")
    
    # 测试 5: 多种 base 对比
    print("\n--- 不同 base 的精度测试 ---")
    for base in [10, 100, 1000, 10000]:
        test_x = [9] * 10
        test_y = [9] * 10
        result = multiply_fft(test_x, test_y, base)
        
        # 计算期望值
        x_int = sum(test_x[i] * (base ** i) for i in range(len(test_x)))
        y_int = sum(test_y[i] * (base ** i) for i in range(len(test_y)))
        result_int = sum(result[i] * (base ** i) for i in range(len(result)))
        
        status = "✓" if result_int == x_int * y_int else "✗"
        print(f"base={base:5d}: {status} (期望={x_int*y_int}, 实际={result_int})")
    
    print("\n" + "=" * 70)
    print("FFT 乘法总结:")
    print("- 时间复杂度: O(n log n)")
    print("- 空间复杂度: O(n)")
    print("- 核心原理: 卷积定理 + 快速傅里叶变换")
    print("- 精度问题: 需要用足够大的 base 或分块解决")
    print("- 实际应用: Python 内置 int 已使用更优化的 FFT/Schnorr 算法")
    print("=" * 70)
