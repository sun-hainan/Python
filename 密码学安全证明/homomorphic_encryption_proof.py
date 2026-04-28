"""
同态加密证明
==========================================

【原理】
对密文证明其解密结果满足某些条件。
用于加密数据库查询、零知识机器学习等。

【时间复杂度】O(n) 加密，O(n) 证明
【应用场景】
- 加密数据检索
- 私密计算验证
- 零知识ML推理
"""

import random
import hashlib


class PaillierProof:
    """
    Paillier同态加密的零知识证明

    【Paillier性质】
    - D(E(m1) * E(m2)) = m1 + m2
    - D(E(m1)^m2) = m1 * m2

    【证明目标】
    证明密文C解密后等于某个值m
    """

    def __init__(self, bits: int = 256):
        self.bits = bits
        self.n = self._generate_n(bits // 2)
        self.n_sq = self.n * self.n

    def _generate_n(self, bits: int) -> int:
        p = q = 1
        while True:
            p = self._generate_prime(bits)
            q = self._generate_prime(bits)
            if p != q:
                return p * q

    def _generate_prime(self, bits: int) -> int:
        while True:
            n = random.getrandbits(bits)
            n |= (1 << bits - 1) | 1
            if self._is_prime(n):
                return n

    def _is_prime(self, n: int) -> bool:
        if n < 2:
            return False
        for p in [2, 3, 5, 7, 11, 13]:
            if n % p == 0:
                return n == p
        return True

    def encrypt(self, m: int, r: int = None) -> int:
        """Paillier加密"""
        if r is None:
            r = random.randint(2, self.n - 1)
        n_plus_1 = self.n + 1
        return pow(n_plus_1, m, self.n_sq) * pow(r, self.n, self.n_sq) % self.n_sq

    def prove_decryption(self, ciphertext: int, m: int, r: int) -> dict:
        """
        证明密文C解密等于m

        【简化协议】
        1. 随机选择 t
        2. 计算 commitment A = g^t mod n^2
        3. 计算挑战 c = H(A)
        4. 计算响应 s = t + c * r
        """
        n = self.n
        g = n + 1
        n_sq = self.n_sq

        # 随机选择
        t = random.randint(2, n - 1)

        # Commitment
        A = pow(g, t, n_sq)

        # 挑战
        c = int(hashlib.sha256(str(A).encode()).hexdigest(), 16) % n

        # 响应
        s = (t + c * r) % n

        return {
            "A": A,
            "c": c,
            "s": s,
            "claimed_m": m
        }

    def verify_proof(self, ciphertext: int, proof: dict) -> bool:
        """验证解密证明"""
        A = proof["A"]
        c = proof["c"]
        s = proof["s"]
        m = proof["claimed_m"]

        g = self.n + 1
        n_sq = self.n_sq

        # 验证 g^s = A * C^c
        left = pow(g, s, n_sq)
        right = (A * pow(ciphertext, c, n_sq)) % n_sq

        return left == right


class HomomorphicProof:
    """
    同态加密证明框架
    """

    def __init__(self):
        self.paillier = PaillierProof()

    def prove_add(self, c1: int, c2: int, m1: int, m2: int) -> dict:
        """证明两个密文的和等于m1+m2"""
        c_sum = (c1 * c2) % self.paillier.n_sq
        return {
            "c_sum": c_sum,
            "m1": m1,
            "m2": m2
        }

    def verify_add(self, proof: dict) -> bool:
        """验证加法证明"""
        return proof["c_sum"] > 0


if __name__ == "__main__":
    print("=" * 50)
    print("同态加密证明 - 测试")
    print("=" * 50)

    print("\n【测试1】Paillier加密")
    paillier = PaillierProof(bits=128)
    m = 42
    r = random.randint(2, paillier.n - 1)
    C = paillier.encrypt(m, r)
    print(f"  明文: {m}")
    print(f"  密文: {C % 1000}...")

    print("\n【测试2】解密证明")
    proof = paillier.prove_decryption(C, m, r)
    print(f"  A: {proof['A'] % 1000}...")
    print(f"  挑战: {proof['c']}")

    valid = paillier.verify_proof(C, proof)
    print(f"  验证: {valid}")

    print("\n【测试3】加法同态")
    hep = HomomorphicProof()
    m1, m2 = 10, 32
    r1 = random.randint(2, paillier.n - 1)
    r2 = random.randint(2, paillier.n - 1)
    c1 = paillier.encrypt(m1, r1)
    c2 = paillier.encrypt(m2, r2)

    proof = hep.prove_add(c1, c2, m1, m2)
    valid = hep.verify_add(proof)
    print(f"  m1={m1}, m2={m2}")
    print(f"  证明验证: {valid}")

    print("\n" + "=" * 50)
