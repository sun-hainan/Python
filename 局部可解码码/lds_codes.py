# -*- coding: utf-8 -*-
"""
算法实现：局部可解码码 / lds_codes

本文件实现 lds_codes 相关的算法功能。
"""

import random
from typing import List, Tuple


class LDPCCode:
    """LDPC码"""

    def __init__(self, n: int, k: int):
        """
        参数：
            n: 码字长度
            k: 信息位长度
        """
        self.n = n
        self.k = k
        self.m = n - k  # 校验位数

        # 生成校验矩阵（简化）
        self.H = self._generate_parity_check_matrix()

    def _generate_parity_check_matrix(self) -> List[List[int]]:
        """生成校验矩阵"""
        # 简化：随机生成稀疏矩阵
        H = []

        for i in range(self.m):
            row = [0] * self.n
            # 每行大约3个1
            for _ in range(3):
                j = random.randint(0, self.n - 1)
                row[j] = 1
            H.append(row)

        return H

    def encode(self, message: List[int]) -> List[int]:
        """
        编码

        参数：
            message: k位信息

        返回：n位码字
        """
        # 简化：信息位 + 校验位
        codeword = message + [0] * self.m

        # 计算校验位（简化）
        for i in range(self.m):
            parity = 0
            for j in range(self.n):
                if self.H[i][j] == 1:
                    parity ^= codeword[j]
            codeword[self.k + i] = parity

        return codeword

    def decode_belief_propagation(self, received: List[int],
                                 max_iter: int = 50) -> List[int]:
        """
        置信传播译码

        参数：
            received: 接收向量（0或1）
            max_iter: 最大迭代次数

        返回：译码后的消息
        """
        # 初始化消息
        messages = [[0.5] * self.n for _ in range(self.m)]

        for iteration in range(max_iter):
            decoded = []

            # 硬判决
            for j in range(self.n):
                prob_1 = 0.5
                for i in range(self.m):
                    if self.H[i][j] == 1:
                        prob_1 *= messages[i][j]
                decoded.append(0 if prob_1 < 0.5 else 1)

            # 检查是否满足校验
            all_satisfied = True
            for i in range(self.m):
                parity = 0
                for j in range(self.n):
                    if self.H[i][j] == 1:
                        parity ^= decoded[j]
                if parity != 0:
                    all_satisfied = False
                    break

            if all_satisfied:
                return decoded

            # 更新消息（简化）
            for i in range(self.m):
                for j in range(self.n):
                    if self.H[i][j] == 1:
                        # 翻转概率
                        messages[i][j] = 1.0 - messages[i][j]

        return decoded


def ldpc_capacity():
    """LDPC容量"""
    print("=== LDPC码容量 ===")
    print()
    print("香农极限：")
    print("  - 信道容量 C")
    print("  - 存在码可以接近 C")
    print()
    print("LDPC表现：")
    print("  - 可以非常接近香农极限")
    print("  - 码率 1/2 时，离极限只有0.0045 dB")
    print()
    print("译码算法：")
    print("  - 置信传播（BP）")
    print("  - 硬判决翻转")
    print("  - 雪崩译码")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== LDPC码测试 ===\n")

    random.seed(42)

    # 创建LDPC码
    n = 20  # 码字长度
    k = 10  # 信息长度

    ldpc = LDPCCode(n, k)

    print(f"LDPC码: ({n}, {k})")
    print(f"码率: {k/n}")
    print()

    # 编码
    message = [1, 0, 1, 1, 0, 1, 0, 1, 0, 1]
    codeword = ldpc.encode(message)

    print(f"信息: {message}")
    print(f"码字: {codeword}")

    # 模拟噪声
    noisy = codeword.copy()
    error_positions = [3, 7]  # 引入错误
    for pos in error_positions:
        noisy[pos] ^= 1

    print(f"带噪声: {noisy}")

    # 译码
    decoded = ldpc.decode_belief_propagation(noisy)

    print(f"译码结果: {decoded}")
    print(f"正确: {'✅' if decoded[:k] == message else '❌'}")

    print()
    ldpc_capacity()

    print()
    print("说明：")
    print("  - LDPC用于WiFi、5G、卫星通信")
    print("  - 接近香农极限的纠错能力")
    print("  - 置信传播是标准译码算法")
