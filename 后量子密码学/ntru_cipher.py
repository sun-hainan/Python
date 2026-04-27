# -*- coding: utf-8 -*-
"""
算法实现：后量子密码学 / ntru_cipher

本文件实现 ntru_cipher 相关的算法功能。
"""

from typing import Tuple, List
import random


class NTRUCipher:
    """NTRU密码（简化）"""

    def __init__(self, n: int = 11, q: int = 32):
        """
        参数：
            n: 多项式阶数
            q: 模数
        """
        self.n = n
        self.q = q

    def create_polynomial(self, ones: int) -> List[int]:
        """创建随机多项式（简化：稀疏）"""
        poly = [0] * self.n

        # 随机放一些1和-1
        indices = random.sample(range(self.n), ones)
        for i, idx in enumerate(indices):
            poly[idx] = 1 if i < ones // 2 else -1

        return poly

    def polynomial_mult(self, a: List[int], b: List[int]) -> List[int]:
        """多项式乘法（模q）"""
        result = [0] * self.n

        for i in range(self.n):
            for j in range(self.n):
                result[(i + j) % self.n] = (result[(i + j) % self.n] +
                                           a[i] * b[j]) % self.q

        return result

    def polynomial_add(self, a: List[int], b: List[int]) -> List[int]:
        """多项式加法（模q）"""
        return [(a[i] + b[i]) % self.q for i in range(self.n)]

    def keygen(self) -> Tuple[List[int], List[int]]:
        """
        密钥生成

        返回：(公钥, 私钥)
        """
        # 创建密钥多项式
        f = self.create_polynomial(ones=5)  # 简化的稀疏
        g = self.create_polynomial(ones=3)

        # 公钥 h = g * f^(-1) mod q
        # 简化：使用随机近似
        h = self.create_polynomial(ones=4)

        return h, f

    def encrypt(self, message: List[int], public_key: List[int]) -> List[int]:
        """
        加密

        参数：
            message: 消息多项式
            public_key: 公钥

        返回：密文
        """
        # 随机掩码
        r = self.create_polynomial(ones=3)

        # 密文 e = r * h + m (mod q)
        e = self.polynomial_mult(r, public_key)
        e = self.polynomial_add(e, message)

        return e

    def decrypt(self, ciphertext: List[int], private_key: List[int]) -> List[int]:
        """
        解密

        参数：
            ciphertext: 密文
            private_key: 私钥

        返回：消息
        """
        # 简化：直接返回（实际需要复杂的解密过程）
        return ciphertext[:len(message)] if 'message' in dir() else ciphertext


def ntru_vs_rsa():
    """NTRU vs RSA"""
    print("=== NTRU vs RSA ===")
    print()
    print("RSA：")
    print("  - 基于大数分解")
    print("  - 量子计算机可破解（Shor）")
    print("  - 加密慢，解密快")
    print()
    print("NTRU：")
    print("  - 基于多项式格")
    print("  - 量子计算机也难以破解")
    print("  - 加密解密都快")
    print()
    print("NTRU优势：")
    print("  - 后量子安全")
    print("  - 低延迟")
    print("  - 适合物联网")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== NTRU密码测试 ===\n")

    random.seed(42)

    ntru = NTRUCipher(n=11, q=32)

    # 密钥生成
    pk, sk = ntru.keygen()

    print(f"多项式阶数: {ntru.n}")
    print(f"模数: {ntru.q}")
    print()

    # 消息
    message = [1, 0, 1, 1, 0, 1, 0, 0, 0, 1, 0]
    print(f"消息: {message}")
    print()

    # 加密
    ciphertext = ntru.encrypt(message, pk)
    print(f"密文: {ciphertext}")

    # 解密
    decrypted = ntru.decrypt(ciphertext, sk)
    print(f"解密: {decrypted}")

    print()
    ntru_vs_rsa()

    print()
    print("说明：")
    print("  - NTRU是重要的后量子密码")
    print("  - 已被NIST标准化")
    print("  - 适合资源受限环境")
