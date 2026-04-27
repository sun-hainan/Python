# -*- coding: utf-8 -*-
"""
算法实现：12_密码学与安全 / keccak_hash

本文件实现 keccak_hash 相关的算法功能。
"""

from typing import List


class KeccakHash:
    """Keccak哈希（简化）"""

    def __init__(self, rate: int = 1600, capacity: int = 512):
        """
        参数：
            rate: 比特率
            capacity: 容量
        """
        self.rate = rate
        self.capacity = capacity
        self.state_size = rate // 8  # 字节数

    def initialize_state(self) -> bytearray:
        """初始化状态"""
        return bytearray(self.state_size)

    def xor_bytes(self, state: bytearray, data: bytes) -> bytearray:
        """XOR操作"""
        result = state.copy()
        for i, b in enumerate(data):
            if i < len(result):
                result[i] ^= b
        return result

    def keccak_f(self, state: bytearray) -> bytearray:
        """
        Keccak函数

        返回：更新后的状态
        """
        # 简化：循环几轮
        for round in range(24):
            # 简化轮函数
            for i in range(len(state)):
                state[i] = (state[i] + round + i) & 0xFF

                # 简化置换
                state[i] = ((state[i] << 1) | (state[i] >> 7)) & 0xFF

        return state

    def hash(self, message: bytes) -> bytes:
        """
        哈希

        返回：哈希值
        """
        # 初始化
        state = self.initialize_state()

        # 填充
        padded = message + b'\x01'
        while len(padded) % self.state_size != 0:
            padded += b'\x00'
        padded += b'\x80'

        # 吸收
        for block in [padded[i:i+self.state_size] for i in range(0, len(padded), self.state_size)]:
            state = self.xor_bytes(state, block)
            state = self.keccak_f(state)

        return bytes(state[:32])  # 返回256位（简化）


def sha3_variants():
    """SHA-3变体"""
    print("=== SHA-3变体 ===")
    print()
    print("SHA-3-224:")
    print("  - 输出224位")
    print("  - 用于受限环境")
    print()
    print("SHA-3-256:")
    print("  - 输出256位")
    print("  - 通用目的")
    print()
    print("SHA-3-384/512:")
    print("  - 高安全性需求")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== Keccak哈希测试 ===\n")

    keccak = KeccakHash()

    # 测试消息
    messages = [
        b"",
        b"abc",
        b"Hello, Keccak!"
    ]

    print("Keccak-256哈希：")
    for msg in messages:
        h = keccak.hash(msg)
        msg_display = msg.decode() if len(msg) < 50 else 'long message'
        print(f"  '{msg_display}'")
        print(f"  -> {h.hex()[:64]}...")
        print()

    print("说明：")
    print("  - Keccak是SHA-3的基础")
    print("  - 使用海绵结构")
    print("  - 抗量子攻击")
