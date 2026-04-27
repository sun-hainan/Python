# -*- coding: utf-8 -*-
"""
算法实现：同态加密 / bgn_cipher

本文件实现 bgn_cipher 相关的算法功能。
"""

import random
from typing import Tuple


class BGNEncryption:
    """BGN加密方案（简化）"""

    def __init__(self, security_bits: int = 256):
        """
        参数：
            security_bits: 安全参数
        """
        self.security_bits = security_bits
        # 简化：使用小素数模拟
        self.p = 17
        self.q = 19
        self.n = self.p * self.q

    def keygen(self) -> Tuple[int, int]:
        """
        密钥生成

        返回：(公钥, 私钥)
        """
        # 简化：公钥=随机数，私钥=简单乘积
        pk = random.randint(100, 1000)
        sk = self.n
        return pk, sk

    def encrypt(self, message: int, public_key: int) -> int:
        """
        加密

        参数：
            message: 明文（0或1）
            public_key: 公钥

        返回：密文
        """
        # 简化：随机掩码
        r = random.randint(1, self.n)
        return message + r * public_key

    def decrypt(self, ciphertext: int, private_key: int) -> int:
        """
        解密

        返回：明文
        """
        return ciphertext % private_key % 2

    def add(self, c1: int, c2: int) -> int:
        """
        密文加法

        返回：c1 + c2
        """
        return c1 + c2

    def multiply(self, c1: int, c2: int) -> int:
        """
        密文乘法（简化）

        注意：实际BGN使用双线性对

        返回：c1 × c2
        """
        return c1 * c2


def bgn_properties():
    """BGN性质"""
    print("=== BGN性质 ===")
    print()
    print("加密方案：")
    print("  - 公钥加密")
    print("  - 安全性基于Diffie-Hellman假设")
    print()
    print("同态性质：")
    print("  - 加法：任意次数")
    print("  - 乘法：只支持一次")
    print()
    print("应用：")
    print("  - 投票系统")
    print("  - 隐私计算")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== BGN加密测试 ===\n")

    bgn = BGNEncryption()

    # 密钥生成
    pk, sk = bgn.keygen()
    print(f"公钥: {pk}")
    print(f"私钥: {sk}")
    print()

    # 加密消息
    m1, m2 = 1, 0

    c1 = bgn.encrypt(m1, pk)
    c2 = bgn.encrypt(m2, pk)

    print(f"消息: {m1}, {m2}")
    print(f"加密: {c1}, {c2}")
    print()

    # 同态加法
    c_sum = bgn.add(c1, c2)
    decrypted_sum = bgn.decrypt(c_sum, sk)
    print(f"加法结果: {decrypted_sum}")

    # 同态乘法
    c_prod = bgn.multiply(c1, c2)
    decrypted_prod = bgn.decrypt(c_prod, sk)
    print(f"乘法结果: {decrypted_prod}")

    print()
    bgn_properties()

    print()
    print("说明：")
    print("  - BGN支持一次乘法")
    print("  - 多次加法无限制")
    print("  - 是SWHE的经典例子")
