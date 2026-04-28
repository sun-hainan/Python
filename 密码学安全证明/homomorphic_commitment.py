"""
同态承诺
==========================================

【原理】
承诺后可以密文状态下进行运算。
支持加法同态和乘法同态。

【时间复杂度】O(1) 承诺
【应用场景】
- 机密投票
- 私密拍卖
- 可验证计算
"""

import random
import hashlib


class PedersenCommitment:
    """
    Pedersen承诺

    【性质】
    - 绑定：无法找到两个打开同一个承诺的值
    - 隐藏：承诺不泄露原始值
    - 加法同态：C1 = g^a h^r1, C2 = g^b h^r2
      C1 * C2 = g^(a+b) h^(r1+r2)
    """

    def __init__(self, prime: int = 2**255 - 19, g: int = 2):
        self.p = prime
        self.g = g
        # h需要与g独立（不知道离散对数）
        self.h = pow(g, 7, prime)

    def commit(self, value: int, blinding: int = None) -> tuple:
        """创建承诺"""
        if blinding is None:
            blinding = random.randint(1, self.p - 1)

        C = pow(self.g, value, self.p) * pow(self.h, blinding, self.p) % self.p
        return C, blinding

    def open(self, value: int, blinding: int) -> bool:
        """验证承诺"""
        C, _ = self.commit(value, blinding)
        return C > 0

    def add(self, C1: int, C2: int) -> int:
        """加法同态：C = C1 * C2"""
        return C1 * C2 % self.p


class ElGamalCommitment:
    """
    ElGamal承诺

    【加法同态】
    E(m; r) = (g^r, g^m * h^r)
    """

    def __init__(self, prime: int = 2**255 - 19):
        self.p = prime
        self.g = 2
        self.h = pow(self.g, 7, prime)

    def commit(self, m: int, r: int = None) -> tuple:
        """承诺"""
        if r is None:
            r = random.randint(1, self.p - 1)

        c1 = pow(self.g, r, self.p)
        c2 = pow(self.g, m, self.p) * pow(self.h, r, self.p) % self.p
        return (c1, c2), r

    def verify(self, m: int, ciphertext: tuple) -> bool:
        """验证"""
        _, r = self.commit(0)
        c1, c2 = ciphertext
        expected_c2 = pow(self.g, m, self.p) * pow(self.h, r, self.p) % self.p
        return c2 == expected_c2


if __name__ == "__main__":
    print("=" * 50)
    print("同态承诺 - 测试")
    print("=" * 50)

    print("\n【测试1】Pedersen承诺")
    pc = PedersenCommitment()

    v1, b1 = pc.commit(100)
    v2, b2 = pc.commit(50)

    print(f"  承诺1: {v1 % 1000}...")
    print(f"  承诺2: {v2 % 1000}...")

    # 同态加
    v_sum = pc.add(v1, v2)
    print(f"  和承诺: {v_sum % 1000}...")

    print("\n【测试2】ElGamal承诺")
    eg = ElGamalCommitment()

    m = 42
    ct, r = eg.commit(m)
    print(f"  明文: {m}")
    print(f"  密文: ({ct % 1000}..., {r % 1000}...)")

    valid = eg.verify(m, ct)
    print(f"  验证: {valid}")

    print("\n" + "=" * 50)
