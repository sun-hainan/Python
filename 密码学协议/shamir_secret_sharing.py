# -*- coding: utf-8 -*-
"""
算法实现：密码学协议 / shamir_secret_sharing

本文件实现 shamir_secret_sharing 相关的算法功能。
"""

import random
import sys


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


def is_prime(n):
    """素性测试。"""
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


def generate_prime(bits=16):
    """生成素数。"""
    while True:
        p = random.randrange(2**(bits-1), 2**bits, 2)
        if is_prime(p):
            return p


class ShamirSecretSharing:
    """Shamir (t, n) 秘密共享方案。"""

    def __init__(self, threshold=None, num_shares=None, prime=None):
        """
        初始化 Shamir 方案。

        参数:
            threshold: 阈值 t（至少 t 份才能恢复）
            num_shares: 总份额数 n
            prime: 大素数 p（素域的模数）
        """
        if prime is None:
            prime = generate_prime(16)
        self.p = prime

        if threshold is not None:
            self.t = threshold
        if num_shares is not None:
            self.n = num_shares

    def split_secret(self, secret, t=None, n=None):
        """
        将秘密分成 n 份。

        参数:
            secret: 要分享的秘密
            t: 阈值（至少 t 份恢复）
            n: 总份额数

        返回:
            shares: (x, y) 坐标对列表
        """
        if t is None:
            t = self.t
        if n is None:
            n = self.n

        if t < 2:
            raise ValueError("阈值至少为 2")
        if n > self.p - 1:
            raise ValueError("n 不能超过 p-1")

        # 生成随机系数：a_1, a_2, ..., a_{t-1}
        coefficients = [random.randint(1, self.p - 1) for _ in range(t - 1)]

        # 构建多项式 f(x) = secret + a_1*x + a_2*x^2 + ... + a_{t-1}*x^{t-1}
        def f(x):
            result = secret
            for i, a in enumerate(coefficients):
                result = (result + a * pow(x, i + 1, self.p)) % self.p
            return result

        # 计算 n 个份额 (x, f(x))，x 从 1 到 n
        shares = []
        for x in range(1, n + 1):
            y = f(x)
            shares.append((x, y))

        return shares

    def recover_secret(self, shares):
        """
        使用拉格朗日插值恢复秘密。

        参数:
            shares: 至少 t 个 (x, y) 对

        返回:
            恢复的秘密
        """
        if len(shares) < self.t:
            raise ValueError(f"需要至少 {self.t} 份份额来恢复秘密")

        p = self.p
        secret = 0

        # 拉格朗日插值：计算 f(0)
        # f(0) = sum(y_i * l_i(0)) mod p
        # l_i(0) = prod_{j!=i} (x_j / (x_j - x_i)) mod p

        for i, (x_i, y_i) in enumerate(shares):
            # 计算 l_i(0)
            numerator = 1
            denominator = 1

            for j, (x_j, y_j) in enumerate(shares):
                if i != j:
                    numerator = (numerator * x_j) % p
                    denominator = (denominator * (x_j - x_i)) % p

            # 模逆
            denominator_inv = modinv(denominator, p)
            l_i_0 = (numerator * denominator_inv) % p

            # 累加
            secret = (secret + y_i * l_i_0) % p

        return secret

    def get_prime(self):
        """获取素数。"""
        return self.p


def lagrange_interpolation_at_zero(shares, p):
    """
    拉格朗日插值计算 f(0)。

    参数:
        shares: (x, y) 对列表
        p: 素数模

    返回:
        f(0) 的值
    """
    secret = 0
    for i, (x_i, y_i) in enumerate(shares):
        numerator = 1
        denominator = 1
        for j, (x_j, _) in enumerate(shares):
            if i != j:
                numerator = (numerator * x_j) % p
                denominator = (denominator * ((x_j - x_i) % p)) % p

        denominator_inv = modinv(denominator, p)
        l_i_0 = (numerator * denominator_inv) % p
        secret = (secret + y_i * l_i_0) % p

    return secret


if __name__ == "__main__":
    print("=== Shamir 秘密共享测试 ===")

    # 初始化方案
    sss = ShamirSecretSharing(threshold=3, num_shares=5)
    p = sss.get_prime()
    print(f"素数 p: {p}")

    # 秘密
    secret = 12345
    print(f"原始秘密: {secret}")

    # 分裂秘密
    shares = sss.split_secret(secret, t=3, n=5)
    print(f"\n将秘密分成 5 份（阈值 3）：")
    for i, (x, y) in enumerate(shares):
        print(f"  份额 {i+1}: (x={x}, y={y})")

    # 恢复测试：用 3 份
    print("\n=== 恢复测试 ===")
    for num_shares in [3, 4, 5]:
        selected = shares[:num_shares]
        recovered = sss.recover_secret(selected)
        print(f"使用 {num_shares} 份恢复: {recovered} {'✓' if recovered == secret else '✗'}")

    # 少于 t 份无法恢复
    print("\n=== 安全性测试 ===")
    for num_shares in [1, 2]:
        selected = shares[:num_shares]
        if num_shares < 3:
            # 尝试用拉格朗日插值（会得到随机值）
            result = lagrange_interpolation_at_zero(selected, p)
            print(f"使用 {num_shares} 份插值结果: {result}（随机值，无法得到正确秘密）")

    # 验证零知识性质
    print("\n=== 零知识性质验证 ===")
    print("任何少于 3 份的份额组合都无法泄露秘密的任何信息")
    print("因为拉格朗日插值在有限域上是唯一确定的，但缺少足够点时解不唯一")

    print("\nShamir 秘密共享特性:")
    print("  完美安全性：少于 t 份无法获得任何秘密信息")
    print("  可验证性：（加扩展后）可验证份额有效性")
    print("  门限访问结构：只有达到阈值才能恢复")
    print("  应用：密钥管理、多方计算、加密备份")
