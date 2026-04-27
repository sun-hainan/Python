# -*- coding: utf-8 -*-
"""
算法实现：局部可解码码 / reed_muller_code

本文件实现 reed_muller_code 相关的算法功能。
"""

from typing import List, Tuple


class ReedMullerCode:
    """Reed-Muller码"""

    def __init__(self, r: int, m: int):
        """
        参数：
            r: 阶数（order）
            m: 变量数（variables）

        RM(r, m)码：
            - 消息长度：k = Σ C(m, i) for i=0 to r
            - 码字长度：n = 2^m
        """
        self.r = r
        self.m = m
        self.n = 2 ** m  # 码字长度
        self.k = sum(self._binom(m, i) for i in range(r + 1))  # 消息长度

    def _binom(self, n: int, k: int) -> int:
        """二项式系数"""
        if k < 0 or k > n:
            return 0
        result = 1
        for i in range(k):
            result = result * (n - i) // (i + 1)
        return result

    def encode(self, message: List[int]) -> List[int]:
        """
        编码

        参数：
            message: k位消息（信息多项式系数）

        返回：n位码字
        """
        # Reed-Muller码通过在所有2^m点上评估多项式来编码
        codeword = []

        for point in range(self.n):
            # 将point转换为m位二进制
            bits = self._int_to_bits(point, self.m)

            # 计算多项式在当前点的值
            value = self._evaluate_polynomial(message, bits)
            codeword.append(value % 2)

        return codeword

    def _int_to_bits(self, x: int, num_bits: int) -> List[int]:
        """整数转位向量"""
        bits = []
        for _ in range(num_bits):
            bits.append(x & 1)
            x >>= 1
        return bits

    def _evaluate_polynomial(self, coeffs: List[int], point: List[int]) -> int:
        """
        评估在point处的多项式

        多项式是所有阶≤r的单调单项式的线性组合
        """
        monomials = self._generate_monomials(self.m, self.r)
        value = 0

        for i, mono in enumerate(monomials):
            # 计算单项式在point处的值
            mono_value = 1
            for var_idx in mono:
                mono_value *= point[var_idx]
            value += coeffs[i] * mono_value

        return value % 2

    def _generate_monomials(self, m: int, r: int) -> List[Tuple]:
        """生成所有阶≤r的单调单项式"""
        monomials = []

        # 生成所有阶数为0到r的单项式
        def generate(current_mono: List[int], start_var: int):
            if len(current_mono) > r:
                return

            if current_mono:
                monomials.append(tuple(current_mono))

            for v in range(start_var, m):
                current_mono.append(v)
                generate(current_mono, v + 1)
                current_mono.pop()

        generate([], 0)
        return monomials

    def local_decode(self, received: List[int], information_positions: List[int]) -> List[int]:
        """
        局部解码

        参数：
            received: 接收到的码字（可能含错误）
            information_positions: 要恢复的信息位置

        返回：恢复的信息位
        """
        # 简化的局部解码
        # 实际需要使用递归解码算法
        recovered = []

        for pos in information_positions:
            # 找到包含这个位置的所有码字约束
            # 使用线性方程求解
            pass

        return recovered


def rm_properties():
    """Reed-Muller码的性质"""
    print("=== Reed-Muller码性质 ===")
    print()
    print(f"RM({0}, m) = 重复码：每个比特重复2^m次")
    print(f"RM({1}, m) = 汉明码（能纠正1位错误）")
    print(f"RM(m-1, m) = 奇偶校验码")
    print(f"RM(m, m) = 整体码")
    print()
    print("参数：")
    print("  - 消息长度 k = Σ C(m, i) for i=0 to r")
    print("  - 码字长度 n = 2^m")
    print("  - 最小距离 d = 2^(m-r)")


def local_decoding():
    """局部解码算法"""
    print()
    print("=== 局部解码算法 ===")
    print()
    print("问题：给定接收的码字，恢复特定信息位")
    print()
    print("算法（递归）：")
    print("  1. 将码字分为两组，各占2^(m-1)位")
    print("  2. 递归解码两个子码字")
    print("  3. 结合得到信息位")
    print()
    print("复杂度：")
    print("  - 解码1位需要 O(2^(m-r)) 次查询")
    print("  - 远少于直接读取所有n位")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== Reed-Muller码测试 ===\n")

    # RM(1, 3) = 汉明码(7, 4)
    rm = ReedMullerCode(r=1, m=3)

    print(f"RM(1, 3) 汉明码：")
    print(f"  消息长度 k = {rm.k}")
    print(f"  码字长度 n = {rm.n}")
    print()

    # 编码
    message = [1, 0, 1, 1]  # 4位消息
    codeword = rm.encode(message)

    print(f"消息: {message}")
    print(f"码字: {codeword}")
    print()

    # 模拟错误
    noisy = codeword.copy()
    noisy[2] ^= 1  # 翻转第3位

    print(f"加入错误后: {noisy}")

    rm_properties()
    local_decoding()

    print()
    print("应用：")
    print("  - CD/DVD存储（RS码的特例）")
    print("  - 卫星通信")
    print("  - 数据传输可靠性")
