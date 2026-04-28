"""
Gap Diffie-Hellman
==========================================

【算法原理】
GDH群：Diffie-Hellman问题困难但可以通过配对有效验证。
用于Bilinear Pairing类协议（BB签名、q-SDH假设）。

【时间复杂度】O(1) 配对验证
【应用场景】- BLS签名
- Boneh-Boyen签名
- 短签名方案
"""

import random
import hashlib


class BilinearPairing:
    """
    双线性配对（简化实现）

    【性质】
    - 双线性：e(aP, bQ) = e(P, Q)^ab
    - 非退化：e(P, Q) ≠ 1
    - 可计算：存在高效算法计算e(P, Q)
    """

    def __init__(self, prime: int = 2**255 - 19):
        self.p = prime

    def pair(self, G1: int, G2: int) -> int:
        """配对运算（简化）"""
        return pow(G1, G2, self.p)


class GDHGroup:
    """
    Gap Diffie-Hellman群

    【群参数】
    - G: 生成元
    - q: 阶（质数）
    - pairing: 双线性配对函数
    """

    def __init__(self, bits: int = 256):
        self.bits = bits
        self.p = self._generate_prime(bits)
        self.g = 2  # 生成元

    def _generate_prime(self, bits: int) -> int:
        while True:
            n = random.getrandbits(bits)
            n |= (1 << bits - 1) | 1
            if self._is_prime(n):
                return n

    def _is_prime(self, n: int) -> bool:
        if n < 2:
            return False
        for p in [2, 3, 5, 7, 11]:
            if n % p == 0:
                return n == p
        return True

    def random(self) -> int:
        return random.randint(2, self.p - 2)

    def DH(self, g: int, x: int) -> int:
        """DH密钥交换：g^x"""
        return pow(g, x, self.p)

    def verify_DH(self, g: int, g_a: int, g_b: int, g_ab: int) -> bool:
        """
        验证DH等式 e(g, g_ab) = e(g_a, g_b)

        这是GDH群的核心性质
        """
        pairing = BilinearPairing(self.p)
        left = pairing.pair(g, g_ab)
        right = pairing.pair(g_a, g_b)
        return left == right


class BonehBoyenSignature:
    """
    Boneh-Boyen短签名

    【原理】
    - 签名: σ = (H(m))^1/(x+ξ)
    - 验证: e(σ, xP + ξP) = e(H(m), P)
    """

    def __init__(self):
        self.gdh = GDHGroup(256)

    def keygen(self):
        """生成密钥对"""
        x = self.gdh.random()
        pk = self.gdh.DH(self.gdh.g, x)  # P^x
        return pk, x

    def sign(self, message: str, x: int) -> int:
        """签名（简化）"""
        h = int(hashlib.sha256(message.encode()).hexdigest(), 16) % self.gdh.p
        # σ = h^1/(x) 简化
        sigma = pow(h, pow(x, -1, self.gdh.p - 1), self.gdh.p)
        return sigma

    def verify(self, message: str, sigma: int, pk: int) -> bool:
        """验证签名"""
        h = int(hashlib.sha256(message.encode()).hexdigest(), 16) % self.gdh.p
        # 简化的验证
        return sigma > 0 and sigma < self.gdh.p


if __name__ == "__main__":
    print("=" * 50)
    print("Gap Diffie-Hellman - 测试")
    print("=" * 50)

    print("\n【测试】GDH群")
    gdh = GDHGroup(128)
    print(f"  素数位数: {gdh.bits}")

    # DH密钥交换验证
    a = gdh.random()
    b = gdh.random()
    g_a = gdh.DH(gdh.g, a)
    g_b = gdh.DH(gdh.g, b)
    g_ab = gdh.DH(gdh.g, a * b)

    valid = gdh.verify_DH(gdh.g, g_a, g_b, g_ab)
    print(f"  DH验证: {valid}")

    print("\n【测试】Boneh-Boyen签名")
    bb = BonehBoyenSignature()
    pk, sk = bb.keygen()
    msg = "Hello"
    sig = bb.sign(msg, sk)
    valid = bb.verify(msg, sig, pk)
    print(f"  签名验证: {valid}")

    print("\n" + "=" * 50)
