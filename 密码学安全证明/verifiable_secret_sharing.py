"""
可验证秘密分享
==========================================

【算法原理】
在Shamir秘密分享基础上增加验证功能。
每个份额持有者可以验证自己收到的份额是正确的，
且所有份额来自同一个秘密。

【时间复杂度】O(n) 分享和验证
【应用场景】- 分布式账本
- 多方密钥管理
- VSS用于门限签名
"""

import random
import hashlib
from typing import List, Tuple


class FeldmanVSS:
    """
    Feldman可验证秘密分享 (VSS)

    【原理】
    承诺者公布 g^f(i) 而非 f(i)
    份额持有者可以验证：
    g^y_i = Π_j (g^a_j)^i^j

    【安全性】
    - 隐藏性：给定承诺无法得知秘密（离散对数难题）
    - 绑定性：承诺者必须使用同一个多项式
    """

    def __init__(self, prime: int = 2**127 - 1, generator: int = 2):
        self.p = prime
        self.g = generator

    def share(self, secret: int, t: int, n: int) -> Tuple[List[Tuple[int, int]], List[int]]:
        """
        分享秘密

        【返回】
        - shares: n个秘密份额
        - commitments: 多项式系数的承诺
        """
        # 创建t-1次多项式，f(0) = secret
        coeffs = [secret] + [random.randint(1, self.p - 2) for _ in range(t - 1)]

        # 计算承诺 C_i = g^a_i
        commitments = [pow(self.g, coeff, self.p) for coeff in coeffs]

        # 计算份额
        shares = []
        for x in range(1, n + 1):
            # Horner计算 f(x)
            y = 0
            for coeff in reversed(coeffs):
                y = (y * x + coeff) % self.p
            shares.append((x, y))

        return shares, commitments

    def verify_share(self, share: Tuple[int, int], commitments: List[int], t: int) -> bool:
        """验证份额"""
        x, y = share

        # 检查 g^y = Π C_i^x^i
        left = pow(self.g, y, self.p)
        right = 1
        for i, C_i in enumerate(commitments):
            right = (right * pow(C_i, pow(x, i, self.p), self.p)) % self.p

        return left == right


class PedersenVSS:
    """
    Pedersen可验证秘密分享

    【与Feldman的区别】
    - Feldman承诺暴露了秘密的离散对数
    - Pedersen使用两个承诺，一个绑定一个隐藏

    【原理】
    C_i = g^a_i * h^b_i
    其中 h 是另一个生成元
    """

    def __init__(self, prime: int = 2**127 - 1):
        self.p = prime
        self.g = 2
        # h需要知道离散对数才知道
        self.h = pow(2, 7, prime)  # 选取某个h

    def share(self, secret: int, t: int, n: int) -> Tuple[List[Tuple[int, int]], Tuple[List[int], List[int]]]:
        """分享秘密"""
        # 两个多项式
        coeffs_f = [secret] + [random.randint(1, self.p - 2) for _ in range(t - 1)]
        coeffs_r = [0] + [random.randint(1, self.p - 2) for _ in range(t - 1)]

        # 计算两组承诺
        commitments_f = [pow(self.g, c, self.p) for c in coeffs_f]
        commitments_r = [pow(self.h, c, self.p) for c in coeffs_r]

        # 计算份额
        shares = []
        for x in range(1, n + 1):
            y_f = self._eval(coeffs_f, x)
            y_r = self._eval(coeffs_r, x)
            shares.append((x, (y_f, y_r)))

        return shares, (commitments_f, commitments_r)

    def _eval(self, coeffs: List[int], x: int) -> int:
        """Horner求值"""
        result = 0
        for coeff in reversed(coeffs):
            result = (result * x + coeff) % self.p
        return result

    def verify_share(self, share: Tuple[int, int],
                    commitments: Tuple[List[int], List[int]], t: int) -> bool:
        """验证份额"""
        x, (y_f, y_r) = share
        C_f, C_r = commitments

        # 验证两个承诺
        left1 = pow(self.g, y_f, self.p)
        right1 = 1
        for i, C in enumerate(C_f):
            right1 = (right1 * pow(C, pow(x, i, self.p), self.p)) % self.p

        left2 = pow(self.h, y_r, self.p)
        right2 = 1
        for i, C in enumerate(C_r):
            right2 = (right2 * pow(C, pow(x, i, self.p), self.p)) % self.p

        return left1 == right1 and left2 == right2


# ========================================
# 测试
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("可验证秘密分享 - 测试")
    print("=" * 50)

    # Feldman VSS
    print("\n【测试1】Feldman VSS")
    feldman = FeldmanVSS()
    secret = 12345
    t, n = 3, 5
    shares, commitments = feldman.share(secret, t, n)
    print(f"  秘密: {secret}")
    print(f"  承诺数: {len(commitments)}")

    for i in [0, 2, 4]:
        x, y = shares[i]
        valid = feldman.verify_share(shares[i], commitments, t)
        print(f"  份额{x}: 验证={valid}")

    # Pedersen VSS
    print("\n【测试2】Pedersen VSS")
    pedersen = PedersenVSS()
    shares2, (C_f, C_r) = pedersen.share(secret, t, n)
    print(f"  承诺F数: {len(C_f)}, 承诺R数: {len(C_r)}")

    for i in [0, 2, 4]:
        valid = pedersen.verify_share(shares2[i], (C_f, C_r), t)
        print(f"  份额{shares2[i][0]}: 验证={valid}")

    print("\n" + "=" * 50)
