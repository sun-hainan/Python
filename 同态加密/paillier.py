# -*- coding: utf-8 -*-
"""
算法实现：同态加密 / paillier

本文件实现 paillier 相关的算法功能。
"""

import random


def generate_prime(bits=8):
    """生成一个小素数（实际应用中需要大素数）。"""
    while True:
        p = random.randrange(2**bits, 2**(bits+1), 2)
        if _is_prime(p):
            return p


def _is_prime(n):
    """Miller-Rabin 素性测试（简化）。"""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    # 简单的试除
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True


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
    if g != 1:
        return None
    return x % m


def generate_keypair(bits=8):
    """
    生成 Paillier 密钥对。

    参数:
        bits: 密钥位数（仅用于演示）

    返回:
        (public_key, private_key)
    """
    # 生成两个大素数
    p = generate_prime(bits)
    q = generate_prime(bits)
    while p == q:
        q = generate_prime(bits)

    n = p * q
    # λ = lcm(p-1, q-1)
    lambda_n = (p - 1) * (q - 1) // 2  # p,q 为奇素数时

    # 选择生成元 g
    # 对于 Paillier，g = n + 1 通常有效
    g = n + 1

    # μ = (L(g^λ mod n^2))^{-1} mod n
    n_sq = n * n
    lambda_mod = pow(g, lambda_n, n_sq)
    # L(x) = (x - 1) / n
    L = (lambda_mod - 1) // n
    mu = modinv(L, n)

    pk = {'n': n, 'g': g, 'n_sq': n_sq}
    sk = {'lambda': lambda_n, 'mu': mu, 'p': p, 'q': q}

    return pk, sk


def paillier_encrypt(pk, m):
    """
    Paillier 加密。

    参数:
        pk: 公钥
        m: 明文消息 (0 <= m < n)

    返回:
        密文
    """
    n = pk['n']
    g = pk['g']
    n_sq = pk['n_sq']

    # 随机选择 r，0 < r < n 且 gcd(r, n) = 1
    while True:
        r = random.randint(2, n - 1)
        if egcd(r, n)[0] == 1:
            break

    # c = g^m * r^n mod n^2
    c1 = pow(g, m, n_sq)
    c2 = pow(r, n, n_sq)
    c = (c1 * c2) % n_sq

    return c


def paillier_decrypt(sk, pk, c):
    """
    Paillier 解密。

    参数:
        sk: 私钥
        pk: 公钥
        c: 密文

    返回:
        明文消息
    """
    n = pk['n']
    n_sq = pk['n_sq']
    lam = sk['lambda']
    mu = sk['mu']

    # 计算 L(c^λ mod n^2)
    c_lambda = pow(c, lam, n_sq)
    L = (c_lambda - 1) // n
    # m = L * μ mod n
    m = (L * mu) % n

    return m


def add_ciphertexts(pk, c1, c2):
    """
    同态加法：E(m1) * E(m2) = E(m1 + m2)
    """
    return (c1 * c2) % pk['n_sq']


def multiply_ciphertext(pk, c, k):
    """
    同态标量乘法：E(m)^k = E(k*m)
    """
    return pow(c, k, pk['n_sq'])


if __name__ == "__main__":
    print("=== Paillier 同态加密测试 ===")

    # 生成密钥对
    pk, sk = generate_keypair(bits=8)
    print(f"公钥 n: {pk['n']}")
    print(f"私钥 λ: {sk['lambda']}")

    # 加密消息
    m1, m2 = 15, 27
    c1 = paillier_encrypt(pk, m1)
    c2 = paillier_encrypt(pk, m2)
    print(f"\n明文 m1={m1}, m2={m2}")
    print(f"密文 c1={c1}, c2={c2}")

    # 解密验证
    d1 = paillier_decrypt(sk, pk, c1)
    d2 = paillier_decrypt(sk, pk, c2)
    print(f"解密: d1={d1}, d2={d2}")

    # 同态加法
    c_sum = add_ciphertexts(pk, c1, c2)
    d_sum = paillier_decrypt(sk, pk, c_sum)
    print(f"\n同态加法:")
    print(f"  E(m1) * E(m2) = E({m1 + m2})?")
    print(f"  解密结果: {d_sum} (期望 {m1 + m2})")

    # 同态标量乘法
    k = 3
    c_mul = multiply_ciphertext(pk, c1, k)
    d_mul = paillier_decrypt(sk, pk, c_mul)
    print(f"\n同态标量乘法:")
    print(f"  E(m1)^{k} = E({m1 * k})?")
    print(f"  解密结果: {d_mul} (期望 {m1 * k})")

    # 组合运算
    c_combined = multiply_ciphertext(pk, c_sum, 2)
    d_combined = paillier_decrypt(sk, pk, c_combined)
    print(f"\n组合运算:")
    print(f"  2 * E(m1+m2) = E({2*(m1+m2)})?")
    print(f"  解密结果: {d_combined} (期望 {2*(m1+m2)})")

    print("\nPaillier 同态特性:")
    print("  支持加法同态：E(m1)*E(m2) = E(m1+m2)")
    print("  支持标量乘法：E(m)^k = E(k*m)")
    print("  不支持普通乘法：E(m1)*E(m2) ≠ E(m1*m2)")
