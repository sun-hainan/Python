# -*- coding: utf-8 -*-
"""
算法实现：密码学协议 / oblivious_transfer

本文件实现 oblivious_transfer 相关的算法功能。
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


class OTReceiver:
    """OT 接收方。"""

    def __init__(self, p):
        self.p = p

    def choose(self, messages, choice_bit):
        """
        选择消息。

        参数:
            messages: 两条消息 [m0, m1]
            choice_bit: 选择位 (0 或 1)

        返回:
            选中的消息
        """
        # 生成随机数
        self.k = random.randint(2, self.p - 2)

        # 计算 v
        self.v = pow(self.k, -1, self.p - 1)  # k^{-1} mod (p-1)

        # 选择消息
        return messages[choice_bit]


class OTSender:
    """OT 发送方。"""

    def __init__(self, p, messages):
        """
        初始化发送方。

        参数:
            p: 大素数
            messages: 两条消息 [m0, m1]
        """
        self.p = p
        self.messages = messages

    def send(self, v):
        """
        发送消息给接收方。

        参数:
            v: 接收方传来的值

        返回:
            加密的消息
        """
        # 生成 RSA 密钥对
        q = generate_prime(12)
        n = self.p * q
        e = 65537
        phi = (self.p - 1) * (q - 1)
        d = modinv(e, phi)

        # 加密消息
        k_int = v % n
        enc_messages = []
        for m in self.messages:
            m_int = int(hashlib.sha256(str(m).encode()).hexdigest(), 16) % n
            enc_m = pow(m_int, e, n)
            enc_messages.append(enc_m)

        return enc_messages, d, n


def simple_ot(messages, choice_bit):
    """
    简化的一次选择 OT 协议。

    基于 Diffie-Hellman 的 OT 协议。
    """
    print("=== 不经意传输协议 ===")

    # 公共参数
    p = generate_prime(16)
    g = 2

    # 发送方
    sender_secret = random.randint(2, p - 2)
    sender_public = pow(g, sender_secret, p)

    # 接收方
    receiver_random = random.randint(2, p - 2)
    receiver_public = pow(g, receiver_random, p)

    # 接收方根据选择位混淆公钥
    if choice_bit == 0:
        PK = receiver_public
    else:
        PK = (receiver_public * modinv(sender_public, p)) % p

    # 发送方计算共享密钥
    shared_secret = pow(PK, sender_secret, p)

    # 双方推导出会话密钥
    K = int(hashlib.sha256(str(shared_secret).encode()).hexdigest(), 16) % p

    # 加密消息
    encrypted = []
    for m in messages:
        m_int = int(hashlib.sha256(str(m).encode()).hexdigest(), 16) % p
        enc_m = (m_int * K) % p
        encrypted.append(enc_m)

    # 接收方用随机数恢复正确的消息
    receiver_shared = pow(receiver_random, sender_secret, p)
    K_receiver = int(hashlib.sha256(str(receiver_shared).encode()).hexdigest(), 16) % p

    if choice_bit == 0:
        chosen = encrypted[0]
    else:
        chosen = encrypted[1]

    # 解密
    decrypted = (chosen * modinv(K_receiver, p)) % p

    return decrypted


class OTExtension:
    """
    OT 扩展协议：将少量 base OT 扩展到大量 OT。

    使用二叉树结构实现。
    """

    def __init__(self, num_ot, security_lambda=128):
        self.num_ot = num_ot
        self.security_lambda = security_lambda

    def base_ot(self):
        """
        执行少量基础 OT（这里简化）。

        返回:
            base_keys: 基础密钥
        """
        p = generate_prime(16)
        base_keys = []

        for i in range(self.security_lambda):
            # 每 bit 执行一次 OT
            k0 = random.randint(2, p - 2)
            k1 = random.randint(2, p - 2)
            base_keys.append((k0, k1))

        return base_keys

    def extend_ot(self, messages, choices):
        """
        扩展 OT：从少量基础 OT 构造大量 OT。

        参数:
            messages: 2 x num_ot 的消息列表
            choices: 选择位列表

        返回:
            选中的消息列表
        """
        base_keys = self.base_ot()
        results = []

        # 简化的扩展：用 base keys 派生所有 OT 的密钥
        for i in range(self.num_ot):
            choice = choices[i] if i < len(choices) else 0

            # 派生密钥（简化）
            key = base_keys[i % len(base_keys)][choice]
            K = int(hashlib.sha256(str(key).encode()).hexdigest(), 16) % (2**32)

            # 加密消息
            m0_int = int(hashlib.sha256(str(messages[0][i]).encode()).hexdigest(), 16)
            m1_int = int(hashlib.sha256(str(messages[1][i]).encode()).hexdigest(), 16)

            enc0 = m0_int ^ K
            enc1 = m1_int ^ K

            # 接收方解密
            result = enc0 if choice == 0 else enc1
            results.append(result)

        return results


if __name__ == "__main__":
    print("=== 不经意传输测试 ===")

    # 测试简单 OT
    messages = ["Hello, this is message 0", "Hello, this is message 1"]
    choice = 1

    result = simple_ot(messages, choice)
    print(f"消息: {messages}")
    print(f"选择位: {choice}")
    print(f"收到的消息（解密后）: {result}")

    # OT 扩展测试
    print("\n=== OT 扩展测试 ===")
    num_ot = 8
    ext = OTExtension(num_ot)

    messages = [
        [f"msg_{i}_0" for i in range(num_ot)],
        [f"msg_{i}_1" for i in range(num_ot)]
    ]
    choices = [random.choice([0, 1]) for _ in range(num_ot)]

    results = ext.extend_ot(messages, choices)
    print(f"执行了 {num_ot} 次 OT")
    for i in range(num_ot):
        expected = hashlib.sha256(str(messages[choices[i]][i]).encode()).hexdigest()
        print(f"  选择 {choices[i]}: 收到 {results[i]}")

    print("\n不经意传输特性:")
    print("  接收方隐私：发送方不知道哪条消息被选中")
    print("  发送方隐私：接收方只能获得一条消息")
    print("  应用：安全多方计算、隐私信息检索（PIR）")
    print("  OT 扩展：从少量基础 OT 构造大量 OT")
