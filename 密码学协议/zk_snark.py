# -*- coding: utf-8 -*-
"""
算法实现：密码学协议 / zk_snark

本文件实现 zk_snark 相关的算法功能。
"""

import random
import hashlib


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


def find_generator(p):
    """找到素数 p 的原根。"""
    phi = p - 1
    factors = []
    temp = phi
    for i in range(2, int(temp**0.5) + 1):
        if temp % i == 0:
            factors.append(i)
            while temp % i == 0:
                temp //= i
    if temp > 1:
        factors.append(temp)

    for g in range(2, p):
        valid = True
        for q in factors:
            if pow(g, phi // q, p) == 1:
                valid = False
                break
        if valid:
            return g
    return None


class ZKProver:
    """零知识证明的证明者。"""

    def __init__(self, p, g, secret):
        self.p = p
        self.g = g
        self.x = secret  # 私钥：离散对数
        self.y = pow(g, secret, p)  # 公钥

    def first_message(self):
        """
        第一步：证明者发送初始承诺。

        选择随机数 k，计算 R = g^k mod p
        """
        self.k = random.randint(2, self.p - 2)
        R = pow(self.g, self.k, self.p)
        return R

    def second_message(self, challenge):
        """
        第二步：证明者根据挑战计算响应。

        s = k - challenge * x mod (p-1)
        """
        p_minus_1 = self.p - 1
        s = (self.k - challenge * self.x) % p_minus_1
        return s

    def get_public_key(self):
        """获取公钥。"""
        return self.y


class ZKVerifier:
    """零知识证明的验证者。"""

    def __init__(self, p, g, public_key):
        self.p = p
        self.g = g
        self.y = public_key  # 证明者的公钥

    def generate_challenge(self, R):
        """
        第二步：验证者生成挑战。

        实际使用 Fiat-Shamir 变换使其非交互式。
        """
        # 挑战 = H(g, y, R)
        data = f"{self.g}{self.y}{R}".encode()
        challenge = int(hashlib.sha256(data).hexdigest(), 16) % (self.p - 1)
        return challenge

    def verify(self, R, s):
        """
        第三步：验证者验证证明。

        检查 g^s * y^challenge ≡ R mod p
        """
        p = self.p
        g = self.g
        y = self.y

        # 左边：g^s * y^challenge mod p
        left = (pow(g, s, p) * pow(y, self.challenge, p)) % p

        return left == R % p

    def set_challenge(self, c):
        """设置挑战（用于验证）。"""
        self.challenge = c


def simulate_zk_proof():
    """模拟完整的零知识证明交互。"""
    print("=== Schnorr 零知识证明模拟 ===")

    # 公共参数
    p = generate_prime(16)
    g = find_generator(p)

    # 秘密值
    secret = random.randint(2, p - 2)
    print(f"素数 p: {p}")
    print(f"生成元 g: {g}")
    print(f"证明者知道私钥 x = {secret}")
    print(f"公钥 y = g^x mod p = {pow(g, secret, p)}")

    # 证明者
    prover = ZKProver(p, g, secret)

    # 验证者
    verifier = ZKVerifier(p, g, prover.get_public_key())

    # 第一步：承诺
    R = prover.first_message()
    print(f"\n第一步：承诺")
    print(f"  证明者计算 R = g^k mod p = {R}")
    print(f"  发送 R 给验证者")

    # 第二步：挑战
    challenge = verifier.generate_challenge(R)
    verifier.set_challenge(challenge)
    print(f"\n第二步：挑战")
    print(f"  验证者计算 challenge = H(g, y, R) = {challenge}")
    print(f"  发送挑战给证明者")

    # 第三步：响应
    s = prover.second_message(challenge)
    print(f"\n第三步：响应")
    print(f"  证明者计算 s = k - challenge * x mod (p-1) = {s}")
    print(f"  发送 s 给验证者")

    # 第四步：验证
    valid = verifier.verify(R, s)
    print(f"\n第四步：验证")
    print(f"  验证者检查 g^s * y^challenge ≡ R mod p")
    print(f"  验证结果: {valid}")

    # 伪造证明测试（失败）
    print("\n=== 伪造证明测试 ===")
    fake_prover = ZKProver(p, g, 0)  # 不知道真正的 x
    fake_R = fake_prover.first_message()
    fake_challenge = verifier.generate_challenge(fake_R)
    verifier.set_challenge(fake_challenge)
    fake_s = fake_prover.second_message(fake_challenge)
    fake_valid = verifier.verify(fake_R, fake_s)
    print(f"不知道 x 的证明者验证结果: {fake_valid}")

    return valid


def fiat_shamir_noninteractive():
    """Fiat-Shamir 变换：将交互式证明转为非交互式。"""
    print("\n=== Fiat-Shamir 非交互式证明 ===")

    p = generate_prime(16)
    g = find_generator(p)
    secret = random.randint(2, p - 2)
    y = pow(g, secret, p)

    # 证明者（非交互式）
    k = random.randint(2, p - 2)
    R = pow(g, k, p)

    # 挑战 = H(g, y, R)
    challenge = int(hashlib.sha256(f"{g}{y}{R}".encode()).hexdigest(), 16) % (p - 1)

    # 响应
    s = (k - challenge * secret) % (p - 1)

    # 验证
    left = (pow(g, s, p) * pow(y, challenge, p)) % p
    valid = left == R

    print(f"公共输入 (g, y): ({g}, {y})")
    print(f"证明 π = (R, s): ({R}, {s})")
    print(f"验证结果: {valid}")

    print("\n零知识证明特性:")
    print("  完备性：如果证明者知道 witness，验证者一定接受")
    print("  可靠性：如果证明者不知道 witness，验证者几乎一定拒绝")
    print("  零知识：验证者无法获知 witness 的值")

if __name__ == "__main__":
    # 基础功能测试
    # 测试函数: is_prime, generate_prime, find_generator, simulate_zk_proof, fiat_shamir_noninteractive
    # is_prime()
    # generate_prime()
    # find_generator()
    pass
