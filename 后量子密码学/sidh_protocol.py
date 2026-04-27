# -*- coding: utf-8 -*-
"""
算法实现：后量子密码学 / sidh_protocol

本文件实现 sidh_protocol 相关的算法功能。
"""

import random
from typing import Tuple


class SIDHKeyExchange:
    """SIDH密钥交换"""

    def __init__(self, p_bits: int = 256):
        """
        参数：
            p_bits: 安全参数
        """
        self.p_bits = p_bits

    def keygen(self) -> Tuple[dict, dict]:
        """
        密钥生成

        返回：(公钥, 私钥)
        """
        # 简化：生成随机私钥
        sk = random.randint(1, 2**self.p_bits)

        # 模拟公钥（实际需要复杂的椭圆曲线运算）
        pk = {
            'E': f"curve_{self.p_bits}",  # 椭圆曲线
            'P': random.randint(0, 2**self.p_bits),
            'Q': random.randint(0, 2**self.p_bits)
        }

        return pk, {'sk': sk, 'E': pk['E']}

    def shared_secret(self, pk: dict, sk: dict) -> int:
        """
        计算共享密钥

        返回：共享密钥
        """
        # 简化：混合生成
        return pk['P'] ^ pk['Q'] ^ sk['sk']


def sidh_vs_lattice():
    """SIDH vs 格密码"""
    print("=== SIDH vs 格密码 ===")
    print()
    print("SIDH：")
    print("  - 基于椭圆曲线同源")
    print("  - 密钥小")
    print("  - 已被SIKE攻击破解")
    print()
    print("格密码（Kyber等）：")
    print("  - 基于格困难问题")
    print("  - 被NIST标准化")
    print("  - 目前安全")
    print()
    print("结论：")
    print("  - SIDH不再推荐使用")
    print("  - 推荐使用后量子格密码")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== SIDH密钥交换测试 ===\n")

    sidh = SIDHKeyExchange(p_bits=256)

    # Alice密钥
    pk_alice, sk_alice = sidh.keygen()
    print(f"Alice公钥: P={pk_alice['P']}, Q={pk_alice['Q']}")

    # Bob密钥
    pk_bob, sk_bob = sidh.keygen()
    print(f"Bob公钥: P={pk_bob['P']}, Q={pk_bob['Q']}")
    print()

    # 计算共享密钥
    ss_alice = sidh.shared_secret(pk_bob, sk_alice)
    ss_bob = sidh.shared_secret(pk_alice, sk_bob)

    print(f"Alice计算共享密钥: {ss_alice}")
    print(f"Bob计算共享密钥: {ss_bob}")
    print(f"匹配: {'是' if ss_alice == ss_bob else '否'}")

    print()
    sidh_vs_lattice()

    print()
    print("说明：")
    print("  - SIDH曾是后量子密码的候选")
    print("  - 2022年被攻击，不再安全")
    print("  - Kyber等是更好的选择")
