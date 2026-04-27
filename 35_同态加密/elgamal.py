# -*- coding: utf-8 -*-

"""

算法实现：同态加密 / elgamal



本文件实现 elgamal 相关的算法功能。

"""



import random

import hashlib





def is_prime(n):

    """Miller-Rabin 素性测试（简化）。"""

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

    """生成小素数。"""

    while True:

        p = random.randrange(2**(bits-1), 2**bits, 2)

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

    if g != 1:

        return None

    return x % m





def generate_keypair(p):

    """

    生成 ElGamal 密钥对。



    参数:

        p: 大素数（群阶）



    返回:

        (pk, sk)

    """

    # 原根生成（简化：随机选一个）

    g = random.randint(2, p - 2)



    # 私钥：随机选择 x

    x = random.randint(2, p - 2)



    # 公钥：y = g^x mod p

    y = pow(g, x, p)



    pk = {'p': p, 'g': g, 'y': y}

    sk = {'x': x}



    return pk, sk





def elgamal_encrypt(pk, m):

    """

    ElGamal 加密。



    参数:

        pk: 公钥

        m: 消息（必须在 [1, p-1] 范围内）



    返回:

        (c1, c2): 密文对

    """

    p, g, y = pk['p'], pk['g'], pk['y']



    # 选择随机数 k

    k = random.randint(2, p - 2)



    # c1 = g^k mod p

    c1 = pow(g, k, p)



    # c2 = m * y^k mod p

    c2 = (m * pow(y, k, p)) % p



    return (c1, c2)





def elgamal_decrypt(sk, pk, ciphertext):

    """

    ElGamal 解密。



    参数:

        sk: 私钥

        pk: 公钥

        ciphertext: (c1, c2)



    返回:

        明文消息

    """

    p = pk['p']

    x = sk['x']

    c1, c2 = ciphertext



    # s = c1^x mod p

    s = pow(c1, x, p)



    # m = c2 * s^{-1} mod p

    s_inv = modinv(s, p)

    m = (c2 * s_inv) % p



    return m





def elgamal_multiply(ct1, ct2, pk):

    """

    ElGamal 同态乘法：E(m1) * E(m2) = E(m1 * m2)



    两个密文对应分量相乘即可。

    """

    c1 = (ct1[0] * ct2[0]) % pk['p']

    c2 = (ct1[1] * ct2[1]) % pk['p']

    return (c1, c2)





def elgamal_pow(ct, k, pk):

    """

    ElGamal 同态幂：E(m)^k = E(m^k)

    """

    c1 = pow(ct[0], k, pk['p'])

    c2 = pow(ct[1], k, pk['p'])

    return (c1, c2)





if __name__ == "__main__":

    print("=== ElGamal 部分同态加密测试 ===")



    # 生成素数和密钥对

    p = generate_prime(12)  # 小素数便于演示

    pk, sk = generate_keypair(p)



    print(f"素数 p: {p}")

    print(f"原根 g: {pk['g']}")

    print(f"公钥 y: {pk['y']}")



    # 加密消息

    m1, m2 = 7, 5

    ct1 = elgamal_encrypt(pk, m1)

    ct2 = elgamal_encrypt(pk, m2)



    print(f"\n明文 m1={m1}, m2={m2}")

    print(f"密文 ct1={ct1}")

    print(f"密文 ct2={ct2}")



    # 解密验证

    d1 = elgamal_decrypt(sk, pk, ct1)

    d2 = elgamal_decrypt(sk, pk, ct2)

    print(f"\n解密: d1={d1}, d2={d2}")



    # 同态乘法

    ct_prod = elgamal_multiply(ct1, ct2, pk)

    d_prod = elgamal_decrypt(sk, pk, ct_prod)

    print(f"\n同态乘法: m1*m2 = {m1*m2}, 解密结果 = {d_prod}")



    # 同态幂

    k = 3

    ct_pow = elgamal_pow(ct1, k, pk)

    d_pow = elgamal_decrypt(sk, pk, ct_pow)

    print(f"\n同态幂: m1^{k} = {m1**k}, 解密结果 = {d_pow}")



    # 组合：m1^2 * m2

    ct_combined = elgamal_multiply(elgamal_pow(ct1, 2, pk), ct2, pk)

    d_combined = elgamal_decrypt(sk, pk, ct_combined)

    print(f"\n组合: m1^2 * m2 = {m1**2 * m2}, 解密结果 = {d_combined}")



    print("\nElGamal 同态特性:")

    print("  乘法同态：E(m1) * E(m2) = E(m1 * m2)")

    print("  幂同态：E(m)^k = E(m^k)")

    print("  不支持加法同态")

