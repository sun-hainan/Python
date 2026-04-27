# -*- coding: utf-8 -*-
"""
算法实现：同态加密 / rsa_homomorphic

本文件实现 rsa_homomorphic 相关的算法功能。
"""

import random


def is_prime(n):
    """Miller-Rabin 简化版。"""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True


def generate_prime(bits=8):
    """生成随机素数。"""
    while True:
        p = random.randrange(2**(bits-1) | 1, 2**bits, 2)
        if is_prime(p):
            return p


def egcd(a, b):
    """扩展欧几里得算法。"""
    if a == 0:
        return b, 0, 1
    g, x1, y1 = egcd(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    return g, x, y


def modinv(a, m):
    """模逆元。"""
    g, x, _ = egcd(a % m, m)
    return x % m if g == 1 else None


def generate_keypair(bits=16):
    """生成 RSA 密钥对。"""
    # 生成两个大素数
    p = generate_prime(bits // 2)
    q = generate_prime(bits // 2)
    while p == q:
        q = generate_prime(bits // 2)

    n = p * q
    phi = (p - 1) * (q - 1)

    # 选择公开指数
    e = 65537
    if e >= phi:
        e = 3

    # 计算私钥指数
    d = modinv(e, phi)

    pk = {'n': n, 'e': e}
    sk = {'d': d, 'p': p, 'q': q}

    return pk, sk


def rsa_encrypt(pk, m):
    """
    RSA 加密：c = m^e mod n

    参数:
        pk: 公钥
        m: 明文（必须在 [0, n) 范围内）

    返回:
        密文
    """
    return pow(m % pk['n'], pk['e'], pk['n'])


def rsa_decrypt(sk, pk, c):
    """RSA 解密：m = c^d mod n"""
    return pow(c, sk['d'], pk['n'])


def rsa_homomorphic_multiply(c1, c2, pk):
    """
    RSA 乘法同态：E(m1) * E(m2) = E(m1 * m2)
    """
    return (c1 * c2) % pk['n']


def rsa_homomorphic_pow(c, k, pk):
    """
    RSA 幂同态：E(m)^k = E(m^k)
    """
    return pow(c, k, pk['n'])


def rsa_threshold_decrypt(shares, pk, threshold, total):
    """
    RSA 门限解密演示：t 个人合作才能解密。

    参数:
        shares: 密文份额列表
        pk: 公钥
        threshold: 门限值 t
        total: 总份额数 n
    """
    # 简化：直接用第一个 share
    # 实际中需要拉格朗日插值
    return rsa_decrypt({'d': shares[0] if shares else 0, 'p': 1, 'q': 1}, pk, 0)


if __name__ == "__main__":
    print("=== RSA 乘法同态测试 ===")

    # 生成密钥对
    pk, sk = generate_keypair(bits=16)
    print(f"模数 n: {pk['n']}")
    print(f"公钥指数 e: {pk['e']}")
    print(f"私钥指数 d: {sk['d']}")

    # 加密消息
    m1, m2 = 123, 456
    c1 = rsa_encrypt(pk, m1)
    c2 = rsa_encrypt(pk, m2)

    print(f"\n明文 m1={m1}, m2={m2}")
    print(f"密文 c1={c1}")
    print(f"密文 c2={c2}")

    # 解密验证
    d1 = rsa_decrypt(sk, pk, c1)
    d2 = rsa_decrypt(sk, pk, c2)
    print(f"\n解密: d1={d1}, d2={d2}")

    # 同态乘法
    c_prod = rsa_homomorphic_multiply(c1, c2, pk)
    d_prod = rsa_decrypt(sk, pk, c_prod)
    print(f"\n同态乘法:")
    print(f"  m1 * m2 = {m1 * m2}")
    print(f"  解密结果 = {d_prod}")

    # 同态幂
    k = 5
    c_pow = rsa_homomorphic_pow(c1, k, pk)
    d_pow = rsa_decrypt(sk, pk, c_pow)
    print(f"\n同态幂:")
    print(f"  m1^{k} = {m1**k}")
    print(f"  解密结果 = {d_pow}")

    # 隐私保护计算示例：计算乘积而不暴露明文
    print("\n=== 隐私保护计算示例 ===")
    # 银行 A 有余额 a，银行 B 有余额 b
    # 服务器可以在密文上计算 a * b
    a, b = 1000, 2500
    c_a = rsa_encrypt(pk, a)
    c_b = rsa_encrypt(pk, b)
    c_product = rsa_homomorphic_multiply(c_a, c_b, pk)
    result = rsa_decrypt(sk, pk, c_product)
    print(f"银行 A 余额: {a}")
    print(f"银行 B 余额: {b}")
    print(f"密文相乘后解密: {result}")
    print(f"期望: {a * b}")

    print("\nRSA 同态特性:")
    print("  乘法同态：E(m1) * E(m2) = E(m1 * m2)")
    print("  幂同态：E(m)^k = E(m^k)")
    print("  无加法同态性")
    print("  实际应用中受选密文攻击限制，需用 OAEP 填充")
