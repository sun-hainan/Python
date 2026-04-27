# -*- coding: utf-8 -*-
"""
算法实现：局部可解码码 / bch_list_decode

本文件实现 bch_list_decode 相关的算法功能。
"""

import random


def gcd(a, b):
    """最大公约数。"""
    while b:
        a, b = b, a % b
    return a


def extended_gcd(a, b):
    """扩展欧几里得算法。"""
    if a == 0:
        return b, 0, 1
    g, x1, y1 = extended_gcd(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    return g, x, y


def modinv(a, m):
    """模逆元。"""
    g, x, _ = extended_gcd(a % m, m)
    if g != 1:
        return None
    return x % m


def generate_finite_field(p, n=1):
    """
    生成 GF(p^n) 的不可约多项式。

    简化：使用 GF(2^8) 的 AES 多项式 x^8 + x^4 + x^3 + x + 1
    """
    # 不可约多项式 x^8 + x^4 + x^3 + x + 1 = 0x11D
    return 0x11D


class BCHCode:
    """简化 BCH 码实现。"""

    def __init__(self, m=4, r=3):
        """
        初始化 BCH 码。

        参数:
            m: 域参数（GF(2^m)）
            r: 设计距离

        码参数:
            n = 2^m - 1
            k = n - m * r
            d >= 2r + 1
        """
        self.m = m
        self.n = 2 ** m - 1
        self.r = r
        self.k = self.n - m * r

    def encode(self, message):
        """
        BCH 编码（简化：使用线性编码矩阵）。

        参数:
            message: k 比特消息

        返回:
            n 比特码字
        """
        k = self.k
        n = self.n

        # 简化：使用循环码结构
        # 实际需要生成多项式 g(x)
        codeword = list(message) + [0] * (n - k)

        # 简化的编码：填充后返回
        # 实际应用中需要除以生成多项式
        return codeword

    def syndrome_decode(self, received):
        """
        计算伴随式。

        参数:
            received: 接收向量

        返回:
            伴随式向量
        """
        n = self.n
        r = self.r
        syndromes = []

        for i in range(1, r + 1):
            # 计算 S_i = r(alpha^i)
            s = 0
            for j in range(n):
                s ^= received[j] * (self._power_alpha(j, i))
            syndromes.append(s)

        return syndromes

    def _power_alpha(self, exponent, power):
        """计算 alpha^{exponent * power}。"""
        # 简化实现
        return pow(2, (exponent * power) % self.n, self.n + 1)

    def list_decode(self, received, radius):
        """
        列表解码：返回所有在汉明距离 radius 内的码字。

        参数:
            received: 接收向量
            radius: 搜索半径

        返回:
            候选码字列表
        """
        n = self.n
        candidates = []

        # 暴力搜索（仅用于演示）
        # 实际使用 Berlekamp-Welch 算法
        if n <= 16:
            from itertools import combinations
            for error_positions in combinations(range(n), min(radius, 4)):
                # 假设这些位置有错误，尝试纠正
                corrected = received[:]
                for pos in error_positions:
                    corrected[pos] ^= 1

                # 检查是否接近有效码字
                if self._is_valid_codeword(corrected):
                    candidates.append(corrected)

        return candidates[:5]  # 限制返回数量

    def _is_valid_codeword(self, word):
        """检查是否为有效码字（简化）。"""
        # 简化：只检查 Syndrome 是否为零
        syndromes = self.syndrome_decode(word)
        return all(s == 0 for s in syndromes)

    def decode(self, received):
        """
        标准解码（纠错）。

        返回:
            解码后的码字
        """
        syndromes = self.syndrome_decode(received)

        # 如果所有伴随式为零，无错误
        if all(s == 0 for s in syndromes):
            return received

        # 否则尝试纠错（简化）
        return received


class BCHListDecoder:
    """BCH 列表解码器。"""

    def __init__(self, bch_code):
        self.bch = bch_code

    def decode_with_list(self, received):
        """
        列表解码：返回所有可能的解码结果。

        参数:
            received: 接收向量

        返回:
            候选列表
        """
        n = self.bch.n
        r = self.bch.r

        # Guruswami-Sudan 列表解码算法（简化版）
        # 实际实现非常复杂，这里用简化版本

        candidates = []

        # 尝试纠正最多 r 个错误
        for num_errors in range(r + 1):
            # 生成所有可能的错误模式
            from itertools import combinations

            for error_pos in combinations(range(n), num_errors):
                # 应用错误
                corrected = received[:]
                for pos in error_pos:
                    corrected[pos] ^= 1

                # 检查是否为有效码字
                if self._check_codeword(corrected):
                    candidates.append(corrected)

        return candidates

    def _check_codeword(self, word):
        """检查是否为码字。"""
        syndromes = self.bch.syndrome_decode(word)
        return all(s == 0 for s in syndromes)


if __name__ == "__main__":
    print("=== BCH 码列表解码测试 ===")

    # 创建 BCH 码
    m = 4
    bch = BCHCode(m=m, r=3)

    print(f"BCH({m}, {bch.r}) 码:")
    print(f"  码字长度 n = {bch.n}")
    print(f"  消息长度 k = {bch.k}")
    print(f"  设计距离 >= {2*bch.r + 1}")

    # 构造一个简单的码字
    message = [1, 0, 1, 1, 0, 0, 0, 0]  # k=8 比特
    codeword = bch.encode(message)
    print(f"\n原始消息: {message[:bch.k]}")
    print(f"码字: {codeword}")

    # 注入错误
    noisy = codeword[:]
    error_positions = [2, 5, 7]
    for pos in error_positions:
        noisy[pos] ^= 1

    print(f"\n注入错误后: {noisy}")
    print(f"错误位置: {error_positions}")

    # 列表解码
    print("\n=== 列表解码 ===")
    decoder = BCHListDecoder(bch)
    candidates = decoder.decode_with_list(noisy)

    print(f"找到 {len(candidates)} 个候选:")
    for i, cand in enumerate(candidates):
        matches_original = cand == codeword
        print(f"  候选 {i+1}: {cand[:12]}... {'(正确)' if matches_original else ''}")

    print("\nBCH 列表解码特性:")
    print("  列表解码可以在超过半距离时工作")
    print("  返回多个可能的解码结果")
    print("  应用：信道条件差时的可靠通信")
    print("  Guruswami-Sudan 算法：O(n^{O(sqrt(d))}) 复杂度")
