# -*- coding: utf-8 -*-
"""
算法实现：局部可解码码 / list_decoding

本文件实现 list_decoding 相关的算法功能。
"""

import random
from typing import List, Tuple


class ListDecoder:
    """列表译码器基类"""

    def __init__(self, radius: float = 0.5):
        """
        参数：
            radius: 译码半径
        """
        self.radius = radius

    def decode_list(self, received: str, codewords: List[str]) -> List[str]:
        """
        列表译码

        参数：
            received: 接收到的码字
            codewords: 所有可能的码字列表

        返回：距离在radius内的所有码字
        """
        candidates = []

        for cw in codewords:
            distance = self._hamming_distance(received, cw)
            if distance <= self.radius * len(received):
                candidates.append((cw, distance))

        # 按距离排序
        candidates.sort(key=lambda x: x[1])

        return [cw for cw, _ in candidates]

    def _hamming_distance(self, s1: str, s2: str) -> int:
        """计算汉明距离"""
        return sum(c1 != c2 for c1, c2 in zip(s1, s2))


class ReedSolomonListDecoder(ListDecoder):
    """Reed-Solomon码的列表译码"""

    def __init__(self, n: int, k: int, field_size: int):
        """
        参数：
            n: 码字长度
            k: 消息长度
            field_size: 有限域大小
        """
        super().__init__()
        self.n = n
        self.k = k
        self.q = field_size

    def welch_berlekamp_decode(self, received: List[int],
                              error_locator: List[int]) -> Tuple[List[int], int]:
        """
        Welch-Berlekamp算法

        参数：
            received: 接收到的值
            error_locator: 错误定位多项式

        返回：(解码消息, 错误数)
        """
        # 简化实现
        # 实际使用Berlekamp-Massey + Forney算法

        n_errors = sum(error_locator)

        # 尝试恢复消息
        decoded = []
        for i, val in enumerate(received):
            if i not in error_locator:
                decoded.append(val)

        return decoded, n_errors


def sudan_algorithm():
    """Sudan列表译码算法"""
    print("=== Sudan算法 ===")
    print()
    print("用于Reed-Solomon码的列表译码：")
    print("  - 可以超过黑Products半径译码")
    print("  - 复杂度 O(n^2)")
    print()
    print("与Welch-Berlekamp对比：")
    print("  - WB：唯一译码，最大半径 (n-k)/2")
    print("  - Sudan：列表译码，半径可达 n-√(2nk)")


def guruswami_sudan():
    """Guruswami-Sudan算法"""
    print()
    print("=== Guruswami-Sudan改进 ===")
    print()
    print("改进点：")
    print("  1. 使用插值多项式")
    print("  2. 因子分解代替根搜索")
    print("  3. 可以达到最优的列表大小")
    print()
    print("复杂度：")
    print("  O(n^(l-1)) 其中l是参数（列表大小）")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 列表译码测试 ===\n")

    # 简单汉明码列表译码
    codewords = ['000', '011', '101', '110']

    decoder = ListDecoder(radius=0.5)

    print(f"码本: {codewords}")
    print()

    # 测试
    test_received = ['001', '010', '111', '000']

    for received in test_received:
        candidates = decoder.decode_list(received, codewords)
        print(f"接收: {received} -> 候选: {candidates}")

    print()
    sudan_algorithm()
    guruswami_sudan()

    print()
    print("说明：")
    print("  - 列表译码在有噪声时更鲁棒")
    print("  - Reed-Solomon列表译码用于CD/DVD")
    print("  - 在互联网上也有应用（如删除了纠错码）")
