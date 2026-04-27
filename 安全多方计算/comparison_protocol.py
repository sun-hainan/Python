# -*- coding: utf-8 -*-
"""
算法实现：安全多方计算 / comparison_protocol

本文件实现 comparison_protocol 相关的算法功能。
"""

import random
from typing import Tuple


class SecureComparison:
    """安全比较协议"""

    def __init__(self, security_bits: int = 40):
        """
        参数：
            security_bits: 安全参数
        """
        self.security_bits = security_bits

    def compare(self, a: int, b: int, Alice_key: int, Bob_key: int) -> int:
        """
        安全比较 a 和 b

        返回：1 如果 a > b，否则 0
        """
        # 使用随机化
        r = random.getrandbits(self.security_bits)

        # 计算差值
        diff = a - b

        #  Yao的乱码电路方法（简化版）
        result = self._yao_compare(a, b, r)

        return result

    def _yao_compare(self, a: int, b: int, random_bit: int) -> int:
        """
        简化的Yao比较

        实际需要混淆电路，这里是概念演示
        """
        # 比较a和b
        if a > b:
            return 1
        elif a < b:
            return 0
        else:
            return random_bit % 2


class ComparisonByBits:
    """按位比较协议"""

    def __init__(self, bit_length: int = 32):
        self.bit_length = bit_length

    def secure_compare(self, a: int, b: int,
                     alice_secret: int, bob_secret: int) -> int:
        """
        安全比较（简化）

        参数：
            a, b: 要比较的两个数
            alice_secret, bob_secret: 各方密钥

        返回：1 如果 a > b
        """
        # 按位比较
        for i in range(self.bit_length - 1, -1, -1):
            ai = (a >> i) & 1
            bi = (b >> i) & 1

            # 如果当前位不同，则确定结果
            if ai != bi:
                return ai

        # 相等
        return 0

    def reveal_winner(self, winner: int, alice_secret: int,
                     bob_secret: int) -> int:
        """
        揭示胜者但保护输家信息

        返回：胜者ID
        """
        # 简化的揭示协议
        return winner


def garbled_circuits_compare():
    """基于混淆电路的比较"""
    print("=== 混淆电路安全比较 ===")
    print()
    print("Yao协议步骤：")
    print("  1. Alice构建比较电路")
    print("  2. 混淆电路（加密真值表）")
    print("  3. Bob评估电路（不知道电路逻辑）")
    print("  4. 获得混淆输出，解密得到结果")
    print()
    print("安全性：")
    print("  - Bob只知道比较结果，不知道Alice的输入")
    print("  - Alice不知道Bob的具体评估（除了输出）")


def goldreich_micali():
    """GMW协议"""
    print()
    print("=== GMW多方计算 ===")
    print()
    print("基于混淆电路，但使用秘密共享：")
    print("  - 每个输入被分成多个份额")
    print("  - 多方协同评估电路")
    print("  - 最后重构结果")
    print()
    print("优点：")
    print("  - 比Yao更高效（对于多个参与者）")
    print("  - 可以预处理电路")
    print()
    print("缺点：")
    print("  - 需要所有参与者在线")
    print("  - 通信复杂度高")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 安全比较协议测试 ===\n")

    sc = SecureComparison()

    # 测试用例
    test_cases = [
        (10, 5),
        (5, 10),
        (7, 7),
        (100, 50),
        (0, 1),
    ]

    print("安全比较测试：")
    for a, b in test_cases:
        # 使用两位随机密钥（简化）
        result = sc.compare(a, b, alice_secret=123, bob_secret=456)
        expected = 1 if a > b else 0
        status = "✅" if result == expected else "❌"
        print(f"  a={a}, b={b}: a>b = {result} {status}")

    print()

    # 按位比较
    print("按位比较：")
    bc = ComparisonByBits()

    for a, b in [(15, 10), (5, 20), (100, 100)]:
        result = bc.secure_compare(a, b, 0, 0)
        print(f"  {a} vs {b}: {'a>b' if result else 'a<=b'}")

    print()
    garbled_circuits_compare()
    goldreich_micali()

    print()
    print("说明：")
    print("  - 安全比较是安全多方计算的基本组件")
    print("  - 用于拍卖、投票、隐私保护查询")
    print("  - Yao的混淆电路是最著名的解决方案")
