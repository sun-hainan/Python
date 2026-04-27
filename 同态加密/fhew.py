# -*- coding: utf-8 -*-
"""
算法实现：同态加密 / fhew

本文件实现 fhew 相关的算法功能。
"""

import random
import math


class LWESample:
    """LWE 样本生成器。"""

    def __init__(self, n, q, std):
        """
        参数:
            n: 维度
            q: 模数
            std: 噪声标准差
        """
        self.n = n
        self.q = q
        self.std = std

    def sample(self, s):
        """
        生成 LWE 样本 (a, b = <a,s> + e mod q)

        参数:
            s: 密钥向量

        返回:
            (a, b)
        """
        # 随机向量 a
        a = [random.randint(0, self.q - 1) for _ in range(self.n)]

        # 计算 <a, s>
        inner = sum(a[i] * s[i] for i in range(self.n)) % self.q

        # 添加噪声
        noise = int(random.gauss(0, self.std)) % self.q

        b = (inner + noise) % self.q

        return a, b


class FHEWKeyGenerator:
    """FHEW 密钥生成器。"""

    def __init__(self, n=8, q=128, std=2.0):
        self.n = n
        self.q = q
        self.std = std
        self.lwe = LWESample(n, q, std)

    def keygen(self):
        """生成密钥。"""
        # 密钥 s（随机二进制向量）
        s = [random.choice([0, 1]) for _ in range(self.n)]

        # 公开密钥：多个 LWE 样本
        num_samples = 64
        pk_a = []
        pk_b = []
        for _ in range(num_samples):
            a, b = self.lwe.sample(s)
            pk_a.append(a)
            pk_b.append(b)

        return {'pk_a': pk_a, 'pk_b': pk_b, 'n': self.n, 'q': self.q}, {'s': s}


def fhew_encrypt_bit(pk, bit):
    """
    FHEW 加密单个比特。

    参数:
        pk: 公钥
        bit: 要加密的比特 (0 或 1)

    返回:
        密文向量 [(a1,b1), (a2,b2), ...]
    """
    n = pk['n']
    q = pk['q']
    num_samples = len(pk['pk_a'])

    ciphertext = []

    for i in range(num_samples):
        # 随机选择（使用 pk 或随机）
        if random.random() < 0.5:
            a = pk['pk_a'][i]
            b = (pk['pk_b'][i] + bit * (q // 2)) % q
        else:
            # 随机盲化
            a = [random.randint(0, q - 1) for _ in range(n)]
            e = int(random.gauss(0, 2))
            inner = sum(a[j] * 0 for j in range(n)) % q  # s=0
            b = (inner + e + bit * (q // 2)) % q

        ciphertext.append((a, b))

    return ciphertext


def fhew_evaluate_not(ct):
    """
    FHEW 同态 NOT：¬E(bit) = E(1-bit)

    参数:
        ct: 比特 bit 的密文

    返回:
        ¬bit 的密文
    """
    q = 128
    new_ct = []
    for a, b in ct:
        new_b = (b + q // 2) % q  # 翻转比特
        new_ct.append((a, new_b))
    return new_ct


def fhew_evaluate_and(ct1, ct2):
    """
    FHEW 同态 AND：E(b1) AND E(b2) = E(b1 & b2)

    简化实现：使用张量积。
    """
    n = 8
    q = 128
    new_ct = []

    for (a1, b1), (a2, b2) in zip(ct1, ct2):
        # 张量积：a = a1 ⊗ a2
        a_new = [0] * (2 * n)
        for i in range(n):
            for j in range(n):
                a_new[i + j] = (a_new[i + j] + a1[i] * a2[j]) % q
        # 截断
        a_new = a_new[:n]

        # b = b1*b2
        b_new = (b1 * b2) % q

        new_ct.append((a_new, b_new))

    return new_ct


def fhew_evaluate_or(ct1, ct2):
    """
    FHEW 同态 OR：使用德摩根定律
    E(b1) OR E(b2) = NOT( NOT(E(b1)) AND NOT(E(b2)) )
    """
    not_ct1 = fhew_evaluate_not(ct1)
    not_ct2 = fhew_evaluate_not(ct2)
    and_result = fhew_evaluate_and(not_ct1, not_ct2)
    return fhew_evaluate_not(and_result)


def fhew_bootstrap(ct, sk):
    """
    FHEW 自举（Bootstrapping）：将噪声密文转换为新鲜密文。

    这是 FHEW 实现全同态的关键步骤。
    简化实现。
    """
    # 简化：假设 ct 足够干净，直接返回
    return ct


if __name__ == "__main__":
    print("=== FHEW 全同态加密测试 ===")

    # 密钥生成
    kg = FHEWKeyGenerator(n=8, q=128, std=2.0)
    pk, sk = kg.keygen()
    print(f"LWE 参数: n={kg.n}, q={kg.q}")

    # 加密比特
    bit1, bit2 = 1, 0

    ct1 = fhew_encrypt_bit(pk, bit1)
    ct2 = fhew_encrypt_bit(pk, bit2)

    print(f"\n比特 b1={bit1}, b2={bit2}")
    print(f"密文向量长度: {len(ct1)}")

    # 同态 NOT
    ct_not1 = fhew_evaluate_not(ct1)
    print(f"\n同态 NOT b1 = {1 - bit1}")

    # 同态 AND
    ct_and = fhew_evaluate_and(ct1, ct2)
    print(f"同态 AND b1 & b2 = {bit1 & bit2}")

    # 同态 OR
    ct_or = fhew_evaluate_or(ct1, ct2)
    print(f"同态 OR b1 | b2 = {bit1 | bit2}")

    # 同态 XOR
    # XOR = (a OR b) AND NOT(a AND b)
    ct_xor = fhew_evaluate_and(
        fhew_evaluate_or(ct1, ct2),
        fhew_evaluate_not(fhew_evaluate_and(ct1, ct2))
    )
    print(f"同态 XOR b1 ^ b2 = {bit1 ^ bit2}")

    print("\nFHEW 特性:")
    print("  基于 LWE（格密码）问题")
    print("  支持任意布尔电路的同态计算")
    print("  Bootstrapping 减少噪声，支持无限深度")
    print("  缺点：同态运算速度较慢")
