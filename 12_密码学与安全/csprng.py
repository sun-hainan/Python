# -*- coding: utf-8 -*-
"""
算法实现：12_密码学与安全 / csprng

本文件实现 csprng 相关的算法功能。
"""

import os
import hashlib
import random
from typing import List


class CSPRNG:
    """密码学安全的PRNG"""

    def __init__(self, seed: bytes = None):
        """
        参数：
            seed: 种子（如果为None，使用系统熵）
        """
        if seed is None:
            seed = os.urandom(32)  # 256位系统熵

        self.state = seed
        self.counter = 0

    def _update_state(self) -> None:
        """更新内部状态"""
        self.counter += 1
        # 使用SHA-256哈希更新
        self.state = hashlib.sha256(self.state + bytes([self.counter])).digest()

    def random_bytes(self, n: int) -> bytes:
        """
        生成随机字节

        参数：
            n: 字节数

        返回：随机字节
        """
        result = bytearray()

        while len(result) < n:
            self._update_state()
            result.extend(self.state)

        return bytes(result[:n])

    def random_int(self, low: int, high: int) -> int:
        """
        生成指定范围内的随机整数

        返回：随机整数
        """
        range_size = high - low
        n_bytes = (range_size.bit_length() + 7) // 8

        while True:
            bytes_val = self.random_bytes(n_bytes)
            val = int.from_bytes(bytes_val, 'big')

            if val < (1 << (n_bytes * 8)) - (1 << (n_bytes * 8)) % range_size:
                return low + (val % range_size)

    def shuffle(self, data: List) -> List:
        """
        密码学安全的洗牌

        返回：洗牌后的列表
        """
        result = data.copy()

        for i in range(len(result) - 1, 0, -1):
            j = self.random_int(0, i + 1)
            result[i], result[j] = result[j], result[i]

        return result


def prng_vs_csprng():
    """PRNG vs CSPRNG"""
    print("=== PRNG vs CSPRNG ===")
    print()
    print("PRNG（伪随机）：")
    print("  - 基于确定性算法")
    print("  - 可预测")
    print("  - 用于模拟、游戏")
    print()
    print("CSPRNG（密码学安全）：")
    print("  - 基于密码学原语")
    print("  - 不可预测")
    print("  - 用于安全应用")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== CSPRNG测试 ===\n")

    # 创建CSPRNG
    rng = CSPRNG()

    # 生成随机字节
    random_bytes = rng.random_bytes(16)
    print(f"随机字节: {random_bytes.hex()}")

    # 生成随机整数
    random_int = rng.random_int(1, 100)
    print(f"随机整数 [1,100): {random_int}")
    print()

    # 洗牌
    data = list(range(10))
    shuffled = rng.shuffle(data)

    print(f"原始: {data}")
    print(f"洗牌: {shuffled}")

    print()
    prng_vs_csprng()

    print()
    print("说明：")
    print("  - CSPRNG用于安全应用")
    print("  - 加密密钥生成")
    print("  - 区块链随机数")
