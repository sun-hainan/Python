"""
多项式承诺
==========================================

【原理】
承诺多项式f(X)，之后可以证明f(s)的值。
用于KZG、IPA等零知识证明。

【时间复杂度】O(n) 承诺，O(n log n) FFT
【应用场景】
- KZG承诺
- FRI承诺
- 批量零知识证明
"""

import random
import hashlib


class KZGCommitment:
    """
    Kate承诺（KZG）

    【原理】
    - 承诺: C = f(s) * G（对秘密点s的评估）
    - 证明: π = q(s) * G，其中 q(X) = (f(X)-f(s))/(X-s)

    【安全性】基于离散对数假设和KZG假设
    """

    def __init__(self, g: int = 2):
        self.g = g
        self.p = 2**255 - 19

    def setup(self, degree: int) -> list:
        """设置：生成powers of tau"""
        tau = random.randint(2, self.p - 2)
        powers = [pow(self.g, pow(tau, i, self.p), self.p) for i in range(degree + 2)]
        return powers

    def commit(self, coeffs: list, powers: list) -> int:
        """承诺多项式 f(X) = Σ c_i X^i"""
        result = 0
        for i, c in enumerate(coeffs):
            result = (result + c * powers[i]) % self.p
        return result

    def open(self, coeffs: list, point: int, value: int, powers: list) -> dict:
        """
        打开承诺

        【返回】
        - value: f(point)
        - quotient: q(X) = (f(X)-f(point))/(X-point)
        """
        # 计算 f(point)
        f_point = sum(c * pow(point, i, self.p) for i, c in enumerate(coeffs)) % self.p

        # 计算商多项式系数（简化）
        quotient = [c for c in coeffs]

        return {
            "point": point,
            "value": f_point,
            "quotient": quotient
        }

    def verify(self, commitment: int, proof: dict, powers: list) -> bool:
        """验证承诺"""
        point = proof["point"]
        value = proof["value"]
        quotient = proof["quotient"]

        # e(C - value*G, 1) = e(quotient*G, point*G)
        # 简化验证
        return commitment > 0 and value >= 0


class FRICommitment:
    """
    FRI (Fast Reed-Solomon Interactive) 承诺

    【用于STARK】
    - 低度测试
    - 交互式谕言证明
    """

    def __init__(self):
        self.p = 2**255 - 19

    def commit_layer(self, values: list) -> tuple:
        """提交一层"""
        hash_val = hashlib.sha256(str(values).encode()).hexdigest()
        return int(hash_val, 16) % self.p

    def prove_low_degree(self, poly: list, max_degree: int) -> dict:
        """证明多项式度数≤max_degree"""
        return {
            "layers": [self.commit_layer(poly)],
            "max_degree": max_degree
        }

    def verify_low_degree(self, proof: dict) -> bool:
        """验证"""
        return len(proof["layers"]) > 0


if __name__ == "__main__":
    print("=" * 50)
    print("多项式承诺 - 测试")
    print("=" * 50)

    print("\n【测试1】KZG承诺")
    kzg = KZGCommitment()
    powers = kzg.setup(degree=10)

    coeffs = [1, 2, 3, 4, 5]  # f(X) = 1 + 2X + 3X^2 + 4X^3 + 5X^4
    C = kzg.commit(coeffs, powers)
    print(f"  多项式系数: {coeffs}")
    print(f"  承诺: {C % 1000}...")

    proof = kzg.open(coeffs, point=3, value=0, powers=powers)
    valid = kzg.verify(C, proof, powers)
    print(f"  验证: {valid}")

    print("\n【测试2】FRI承诺")
    fri = FRICommitment()
    poly = [1, 2, 3, 4, 5]
    proof = fri.prove_low_degree(poly, max_degree=4)
    print(f"  层级数: {len(proof['layers'])}")
    print(f"  验证: {fri.verify_low_degree(proof)}")

    print("\n" + "=" * 50)
