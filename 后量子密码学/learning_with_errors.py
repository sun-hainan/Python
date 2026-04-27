# -*- coding: utf-8 -*-
"""
算法实现：后量子密码学 / learning_with_errors

本文件实现 learning_with_errors 相关的算法功能。
"""

import random
from typing import List, Tuple


class LWESample:
    """LWE样本"""

    def __init__(self, a: List[int], b: int, secret: List[int], modulus: int, error_std: float):
        self.a = a
        self.b = b
        self.secret = secret
        self.q = modulus
        self.error_std = error_std

    def create(self) -> Tuple[List[int], int]:
        """
        创建LWE样本

        b = <a, s> + e mod q
        其中e是小误差

        返回：(a, b)
        """
        import numpy as np

        # 计算内积
        inner = sum(ai * si for ai, si in zip(self.a, self.secret)) % self.q

        # 添加小误差
        error = int(np.random.normal(0, self.error_std))
        error = max(-self.q//4, min(self.q//4, error))  # 限制误差范围

        b = (inner + error) % self.q

        return self.a, b


class LWEPuzzle:
    """LWE谜题（简化版）"""

    def __init__(self, n: int, modulus: int, error_std: float):
        """
        参数：
            n: 向量维度
            modulus: 模数q
            error_std: 误差标准差
        """
        self.n = n
        self.q = modulus
        self.error_std = error_std

        # 秘密向量
        self.secret = [random.randint(0, modulus - 1) for _ in range(n)]

    def create_samples(self, m: int) -> Tuple[List[List[int]], List[int]]:
        """
        创建m个LWE样本

        返回：(A矩阵, b向量)
        """
        A = []
        b = []

        for _ in range(m):
            a = [random.randint(0, self.q - 1) for _ in range(self.n)]

            import numpy as np
            error = int(np.random.normal(0, self.error_std))
            error = max(-self.q//4, min(self.q//4, error))

            inner = sum(ai * si for ai, si in zip(a, self.secret)) % self.q
            b_i = (inner + error) % self.q

            A.append(a)
            b.append(b_i)

        return A, b

    def recover_secret(self, A: List[List[int]], b: List[int]) -> List[int]:
        """
        尝试恢复秘密（使用高斯消去）

        实际中应该使用格基约简
        """
        n = self.n
        q = self.q

        # 构造增广矩阵 [A|b]
        M = [A[i] + [b[i]] for i in range(len(A))]

        # 高斯消去（模q）
        for col in range(n):
            # 找到主元
            pivot = -1
            for row in range(col, len(M)):
                if M[row][col] != 0:
                    pivot = row
                    break

            if pivot == -1:
                continue

            # 交换行
            M[col], M[pivot] = M[pivot], M[col]

            # 归一化
            pivot_val = M[col][col]
            inv = pow(pivot_val, -1, q)  # 模逆元
            for j in range(col, n + 1):
                M[col][j] = (M[col][j] * inv) % q

            # 消去
            for row in range(len(M)):
                if row != col and M[row][col] != 0:
                    factor = M[row][col]
                    for j in range(col, n + 1):
                        M[row][j] = (M[row][j] - factor * M[col][j]) % q

        # 提取解
        solution = [0] * n
        for row in M[:n]:
            if len(row) == n + 1:
                solution[row.index(row) if row[col] != 0 else 0] = row[-1]

        return solution


def lwe_security():
    """LWE安全性分析"""
    print("=== LWE安全性 ===")
    print()
    print("困难性假设：")
    print("  - 没有已知的多项式时间算法")
    print("  - 即使量子算法也没有有效解")
    print()
    print("安全性来源：")
    print("  - 基于格的最坏情况困难性")
    print("  - GapSVP / SIVP / LWE")
    print()
    print("参数选择：")
    print("  - n = 256-1024（维度）")
    print("  - q = poly(n)（模数）")
    print("  - 误差分布：离散高斯，σ = ω(√log n)")


def lwe_cryptosystems():
    """基于LWE的密码系统"""
    print()
    print("=== 基于LWE的密码系统 ===")
    print()
    print("1. Regev (2005) - 基础加密方案")
    print("   - 公钥加密，安全性基于LWE")
    print("   - 密钥尺寸较大")
    print()
    print("2. Ring-LWE - 效率优化")
    print("   - 在多项式环上定义LWE")
    print("   - 密钥尺寸更小")
    print("   - 用于Kyber（KEM）、Dilithium（签名）")
    print()
    print("3. Field Guide")
    print("   - 实际参数选择指南")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== LWE问题测试 ===\n")

    np = __import__('numpy')
    np.random.seed(42)

    # 创建LWE谜题
    n = 10      # 维度
    q = 1024    # 模数
    error_std = 3.0

    lwe = LWEPuzzle(n, q, error_std)

    # 创建样本
    m = 50  # 样本数
    A, b = lwe.create_samples(m)

    print(f"LWE参数：")
    print(f"  维度 n = {n}")
    print(f"  模数 q = {q}")
    print(f"  样本数 m = {m}")
    print()

    # 恢复尝试
    recovered = lwe.recover_secret(A, b)

    print(f"真实秘密: {lwe.secret[:5]}...")
    print(f"恢复秘密: {recovered[:5]}...")

    # 检查
    matches = sum(1 for i in range(n) if lwe.secret[i] == recovered[i])
    print(f"匹配: {matches}/{n}")

    print()
    lwe_security()
    lwe_cryptosystems()

    print()
    print("说明：")
    print("  - LWE是后量子密码的基石")
    print("  - 实际系统使用Ring-LWE减少尺寸")
    print("  - Kyber/Dilithium已标准化")
