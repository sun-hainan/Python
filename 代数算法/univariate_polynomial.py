# -*- coding: utf-8 -*-
"""
算法实现：代数算法 / univariate_polynomial

本文件实现 univariate_polynomial 相关的算法功能。
"""

from typing import List, Tuple


class Polynomial:
    """一元多项式"""

    def __init__(self, coeffs: List[float]):
        """
        参数：
            coeffs: 系数列表，从常数项开始
        """
        self.coeffs = coeffs
        self.degree = len(coeffs) - 1

    def __add__(self, other: 'Polynomial') -> 'Polynomial':
        """多项式加法"""
        max_len = max(len(self.coeffs), len(other.coeffs))
        result = [0.0] * max_len

        for i in range(len(self.coeffs)):
            result[i] += self.coeffs[i]
        for i in range(len(other.coeffs)):
            result[i] += other.coeffs[i]

        return Polynomial(result)

    def __mul__(self, other: 'Polynomial') -> 'Polynomial':
        """多项式乘法（卷积）"""
        result = [0.0] * (len(self.coeffs) + len(other.coeffs) - 1)

        for i in range(len(self.coeffs)):
            for j in range(len(other.coeffs)):
                result[i + j] += self.coeffs[i] * other.coeffs[j]

        return Polynomial(result)

    def evaluate(self, x: float) -> float:
        """
        Horner法则求值

        参数：
            x: 变量值

        返回：p(x)
        """
        result = 0.0
        for coeff in reversed(self.coeffs):
            result = result * x + coeff
        return result

    def divide(self, other: 'Polynomial') -> Tuple['Polynomial', 'Polynomial']:
        """
        多项式除法

        参数：
            other: 除数

        返回：(商, 余数)
        """
        if self.degree < other.degree:
            return Polynomial([0.0]), Polynomial(self.coeffs.copy())

        # 长除法
        quotient = [0.0] * (self.degree - other.degree + 1)
        remainder = self.coeffs.copy()

        for i in range(len(quotient) - 1, -1, -1):
            quotient[i] = remainder[i + other.degree] / other.coeffs[-1]

            for j in range(len(other.coeffs)):
                remainder[i + j] -= quotient[i] * other.coeffs[j]

        return Polynomial(quotient), Polynomial(remainder)

    def derivative(self) -> 'Polynomial':
        """求导"""
        if self.degree == 0:
            return Polynomial([0.0])

        deriv_coeffs = [c * i for i, c in enumerate(self.coeffs[1:], start=1)]
        return Polynomial(deriv_coeffs)

    def integral(self, constant: float = 0.0) -> 'Polynomial':
        """积分"""
        int_coeffs = [constant]
        int_coeffs.extend([c / i for i, c in enumerate(self.coeffs, start=1)])
        return Polynomial(int_coeffs)


def polynomial_gcd(p: 'Polynomial', q: 'Polynomial') -> 'Polynomial':
    """
    多项式gcd（欧几里得算法）

    参数：
        p, q: 多项式

    返回：gcd(p, q)
    """
    while q.degree > 0 or any(abs(c) > 1e-10 for c in q.coeffs):
        _, r = p.divide(q)
        if r.degree == 0 and all(abs(c) < 1e-10 for c in r.coeffs):
            break
        p, q = q, r

    # 归一化
    if q.degree >= 0:
        leading_coeff = q.coeffs[-1]
        if abs(leading_coeff) > 1e-10:
            normalized = [c / leading_coeff for c in q.coeffs]
            return Polynomial(normalized)

    return Polynomial([1.0])


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 一元多项式运算测试 ===\n")

    # 创建多项式
    p = Polynomial([1.0, -3.0, 2.0])  # x² - 3x + 2
    q = Polynomial([1.0, -1.0])       # x - 1

    print(f"p(x) = {p.coeffs[0]} + {p.coeffs[1]}x + {p.coeffs[2]}x²")
    print(f"q(x) = {q.coeffs[0]} + {q.coeffs[1]}x")
    print()

    # 加法
    p_add_q = p + q
    print(f"p + q = {[f'{c:.1f}' for c in p_add_q.coeffs]}")

    # 乘法
    p_mul_q = p * q
    print(f"p × q = {[f'{c:.1f}' for c in p_mul_q.coeffs]}")
    print(f"验证: (x²-3x+2)(x-1) = x³-4x²+5x-2")

    # 求值
    x = 2.0
    val = p.evaluate(x)
    print(f"p(2) = {val}")

    # 除法
    quotient, remainder = p_mul_q.divide(q)
    print(f"\n除法: (p×q) ÷ q")
    print(f"  商: {[f'{c:.1f}' for c in quotient.coeffs]}")
    print(f"  余: {[f'{c:.1f}' for c in remainder.coeffs]}")

    # 求导
    deriv = p.derivative()
    print(f"\n导数: p'(x) = {[f'{c:.1f}' for c in deriv.coeffs]}")

    # GCD
    gcd_pq = polynomial_gcd(p, q)
    print(f"\nGCD: gcd(p, q) = {[f'{c:.1f}' for c in gcd_pq.coeffs]}")

    print()
    print("说明：")
    print("  - 多项式运算是代数算法的基础")
    print("  - 用于符号计算、编码理论")
    print("  - Horner法则高效求值")
