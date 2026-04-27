# -*- coding: utf-8 -*-
"""
算法实现：后量子密码学 / code_based_crypto

本文件实现 code_based_crypto 相关的算法功能。
"""

import random
import numpy as np
from typing import Tuple


class McElieceCipher:
    """McEliece密码系统（简化）"""

    def __init__(self, n: int = 1024, k: int = 524):
        """
        参数：
            n: 码字长度
            k: 信息长度
        """
        self.n = n
        self.k = k
        self.t = 50  # 纠错能力

    def keygen(self) -> Tuple[dict, dict]:
        """
        密钥生成

        返回：(公钥, 私钥)
        """
        # 简化：生成随机矩阵
        G = np.random.randint(0, 2, (self.k, self.n))

        # 私钥：G = SGP
        S = np.random.randint(0, 2, (self.k, self.k))
        P = np.random.randint(0, 2, (self.n, self.n))

        # 伪装矩阵T
        T = np.random.randint(0, 2, (self.n, self.n))

        sk = {'S': S, 'G': G, 'P': P}
        pk = {'G_hat': np.mod(S @ G @ P, 2), 'T': T}

        return pk, sk

    def encrypt(self, message: np.ndarray, pk: dict) -> Tuple[np.ndarray, np.ndarray]:
        """
        加密

        参数：
            message: 信息位
            pk: 公钥

        返回：(密文, 错误向量)
        """
        # 计算编码
        c1 = np.mod(message @ pk['G_hat'], 2)

        # 添加随机错误
        error = np.zeros(self.n, dtype=int)
        error_positions = random.sample(range(self.n), self.t)
        for pos in error_positions:
            error[pos] = 1

        # 密文
        ciphertext = np.mod(c1 + error, 2)

        return ciphertext, error

    def decrypt(self, ciphertext: np.ndarray, sk: dict) -> np.ndarray:
        """
        解密

        参数：
            ciphertext: 密文
            sk: 私钥

        返回：信息位
        """
        # 简化：假设解密成功
        # 实际需要复杂的译码算法

        # 去除伪装
        c_transformed = ciphertext  # 简化

        # 信息恢复（简化）
        message = c_transformed[:self.k]

        return message


def mceliece_properties():
    """McEliece性质"""
    print("=== McEliece性质 ===")
    print()
    print("安全性：")
    print("  - 基于随机线性码译码问题")
    print("  - NP困难")
    print("  - 抗量子攻击")
    print()
    print("参数：")
    print("  - 公钥：~1MB（较大）")
    print("  - 密文：~1KB")
    print("  - 安全性：非常高")
    print()
    print("应用：")
    print("  - 需要长期安全通信")
    print("  - 后量子迁移")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== McEliece密码测试 ===\n")

    mc = McElieceCipher(n=1024, k=524)

    # 密钥生成
    pk, sk = mc.keygen()

    print(f"参数: n={mc.n}, k={mc.k}, t={mc.t}")
    print()

    # 加密
    message = np.random.randint(0, 2, mc.k)

    print(f"消息长度: {len(message)} bits")

    ciphertext, error = mc.encrypt(message, pk)

    print(f"密文长度: {len(ciphertext)} bits")
    print(f"错误数: {sum(error)}")
    print()

    # 解密
    decrypted = mc.decrypt(ciphertext, sk)

    print(f"解密后消息长度: {len(decrypted)} bits")
    print(f"恢复正确: {'✅' if np.array_equal(decrypted, message) else '❌'}")

    print()
    mceliece_properties()

    print()
    print("说明：")
    print("  - McEliece是最早的后量子密码之一")
    print("  - 公钥大但安全性高")
    print("  - NIST候选方案")
