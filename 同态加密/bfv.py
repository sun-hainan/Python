# -*- coding: utf-8 -*-
"""
算法实现：同态加密 / bfv

本文件实现 bfv 相关的算法功能。
"""

import random


class BFVKeyGenerator:
    """BFV 密钥生成器。"""

    def __init__(self, poly_degree=8, plain_modulus=16, cipher_modulus=1024):
        self.poly_degree = poly_degree       # 多项式次数
        self.t = plain_modulus               # 明文模数
        self.q = cipher_modulus              # 密文模数
        self.polynomial_ring = self._create_polynomial_ring()

    def _create_polynomial_ring(self):
        """创建多项式环 Z_q[X]/(X^n + 1)。"""
        # 简化：使用整数多项式模拟
        return {
            'degree': self.poly_degree,
            'modulus': self.q,
            'poly_modulus': 'X^8 + 1'
        }

    def generate_keys(self):
        """
        生成 BFV 密钥对。

        - s: 私钥（随机小多项式）
        - a: 公钥一部分（随机多项式）
        - b = -a*s + e (噪声项)
        """
        n = self.poly_degree

        # 私钥 s：随机小系数（-1, 0, 1）
        s = [random.choice([-1, 0, 1]) for _ in range(n)]

        # 公钥：(a, b) 其中 b = -a*s + e
        a = [random.randint(0, self.q - 1) for _ in range(n)]
        e = [random.choice([0, 1, -1]) for _ in range(n)]  # 小噪声

        # 计算 -a*s（循环卷积）
        b = self._poly_mul_neg(a, s)
        # 加上噪声
        b = [(b[i] + e[i]) % self.q for i in range(n)]

        pk = {'a': a, 'b': b, 'q': self.q, 't': self.t}
        sk = {'s': s}

        return pk, sk

    def _poly_mul_neg(self, a, s):
        """计算 -a * s mod (X^n + 1, q)。"""
        n = self.poly_degree
        q = self.q
        # 循环卷积
        result = [0] * n
        for i in range(n):
            for j in range(n):
                idx = (i + j) % n
                result[idx] = (result[idx] - a[i] * s[j]) % q
        return result

    def _poly_mul(self, a, b):
        """计算 a * b mod (X^n + 1, q)。"""
        n = self.poly_degree
        result = [0] * n
        for i in range(n):
            for j in range(n):
                idx = (i + j) % n
                result[idx] = (result[idx] + a[i] * b[j]) % self.q
        return result


class BFVCiphertext:
    """BFV 密文对象。"""

    def __init__(self, c0, c1, pk):
        self.c0 = c0   # 密文第一部分
        self.c1 = c1   # 密文第二部分
        self.pk = pk


def bfv_encrypt(pk, plaintext_poly):
    """
    BFV 加密消息多项式。

    参数:
        pk: 公钥
        plaintext_poly: 明文多项式系数列表

    返回:
        BFVCiphertext 对象
    """
    n = len(plaintext_poly)
    q = pk['q']
    t = pk['t']

    # 将明文多项式编码到密文中
    # 缩放：m' = round(t * m)
    scaled = [(m * t) % q for m in plaintext_poly]

    # 生成随机掩码多项式 u
    u = [random.choice([0, 1]) for _ in range(n)]

    # 计算 u * pk.a 和 u * pk.b
    c0 = _poly_add_scaled(scaled, _poly_mul(pk['a'], u, q), q)
    c1 = _poly_mul(pk['b'], u, q)

    return BFVCiphertext(c0, c1, pk)


def _poly_mul(a, b, q):
    """多项式乘法 mod q（循环卷积）。"""
    n = len(a)
    result = [0] * n
    for i in range(n):
        for j in range(n):
            idx = (i + j) % n
            result[idx] = (result[idx] + a[i] * b[j]) % q
    return result


def _poly_add_scaled(a, b, q):
    """多项式加法。"""
    return [(a[i] + b[i]) % q for i in range(len(a))]


def bfv_decrypt(sk, ciphertext):
    """
    BFV 解密。

    参数:
        sk: 私钥
        ciphertext: BFVCiphertext

    返回:
        明文多项式
    """
    pk = ciphertext.pk
    q = pk['q']
    t = pk['t']

    # 计算 c0 + c1 * s
    c1_s = _poly_mul(ciphertext.c1, sk['s'], q)
    message = _poly_add_scaled(ciphertext.c0, c1_s, q)

    # 解码：除以 t 并取整
    decoded = [((m + q // 2) % q) // t % 2 for m in message]

    return decoded


def bfv_add(ct1, ct2):
    """
    BFV 密文加法：E(m1) + E(m2) = E(m1 + m2)
    """
    c0 = [(ct1.c0[i] + ct2.c0[i]) % ct1.pk['q'] for i in range(len(ct1.c0))]
    c1 = [(ct1.c1[i] + ct2.c1[i]) % ct1.pk['q'] for i in range(len(ct1.c1))]
    return BFVCiphertext(c0, c1, ct1.pk)


def bfv_multiply(ct1, ct2):
    """
    BFV 密文乘法：E(m1) * E(m2) = E(m1 * m2)

    这是重线性化过程，简化为密文对相乘。
    """
    q = ct1.pk['q']
    n = len(ct1.c0)

    # c_new = c1 * c2
    c0_new = _poly_mul(ct1.c0, ct2.c0, q)
    c1_new = _poly_mul(ct1.c0, ct2.c1, q)
    c2_new = _poly_mul(ct1.c1, ct2.c0, q)
    c3_new = _poly_mul(ct1.c1, ct2.c1, q)

    # 简化：只保留 c0 和 c1
    c0_final = [(c0_new[i] + c3_new[i]) % q for i in range(n)]
    c1_final = [(c1_new[i] + c2_new[i]) % q for i in range(n)]

    return BFVCiphertext(c0_final, c1_final, ct1.pk)


if __name__ == "__main__":
    print("=== BFV 同态加密测试 ===")

    # 生成密钥
    kg = BFVKeyGenerator(poly_degree=8, plain_modulus=16, cipher_modulus=1024)
    pk, sk = kg.generate_keys()
    print(f"多项式次数 n = {kg.poly_degree}")
    print(f"明文模数 t = {kg.t}")
    print(f"密文模数 q = {kg.q}")

    # 加密消息
    m1 = [1, 0, 1, 0, 1, 0, 0, 0]  # 二进制消息
    m2 = [1, 1, 0, 0, 0, 0, 0, 0]

    ct1 = bfv_encrypt(pk, m1)
    ct2 = bfv_encrypt(pk, m2)
    print(f"\n消息 m1: {m1}")
    print(f"消息 m2: {m2}")

    # 解密验证
    d1 = bfv_decrypt(sk, ct1)
    d2 = bfv_decrypt(sk, ct2)
    print(f"解密 m1: {d1}")
    print(f"解密 m2: {d2}")

    # 同态加法
    ct_sum = bfv_add(ct1, ct2)
    d_sum = bfv_decrypt(sk, ct_sum)
    print(f"\n同态加法 m1+m2: {d_sum}")

    # 同态乘法
    ct_prod = bfv_multiply(ct1, ct2)
    d_prod = bfv_decrypt(sk, ct_prod)
    print(f"同态乘法 m1*m2: {d_prod}")

    print("\nBFV 特性:")
    print("  基于 RLWE 问题（格密码）")
    print("  支持密文加法和密文乘法")
    print("  乘法后需要重线性化来控制噪声增长")
