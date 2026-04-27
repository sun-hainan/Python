# -*- coding: utf-8 -*-

"""

算法实现：同态加密 / paillier_crypto



本文件实现 paillier_crypto 相关的算法功能。

"""



import random

from math import gcd





class PaillierCrypto:

    """Paillier加密系统"""



    def __init__(self, key_size: int = 512):

        """

        参数：

            key_size: 密钥位数（安全参数）

        """

        self.key_size = key_size



        # 生成大素数

        self.p = self._generate_prime(key_size // 2)

        self.q = self._generate_prime(key_size // 2)



        # n = p * q

        self.n = self.p * self.q



        # λ = lcm(p-1, q-1)

        self.lambda_n = self._lcm(self.p - 1, self.q - 1)



        # μ = λ^(-1) mod n

        self.mu = self._mod_inverse(self.lambda_n, self.n)



        # 生成元g

        self.g = self.n + 1  # 通常选择 n + 1



        # n^2（用于加密）

        self.n_squared = self.n * self.n



    def _generate_prime(self, bits: int) -> int:

        """生成随机素数"""

        while True:

            n = random.getrandbits(bits)

            n |= (1 << bits - 1) | 1  # 确保是奇数且有足够位数



            if self._is_prime(n):

                return n



    def _is_prime(self, n: int, k: int = 10) -> bool:

        """Miller-Rabin素性测试"""

        if n < 2:

            return False

        if n == 2 or n == 3:

            return True

        if n % 2 == 0:

            return False



        # 分解 n-1 = d * 2^s

        d = n - 1

        s = 0

        while d % 2 == 0:

            d //= 2

            s += 1



        # 测试

        for _ in range(k):

            a = random.randrange(2, n - 2)

            x = pow(a, d, n)



            if x == 1 or x == n - 1:

                continue



            for _ in range(s - 1):

                x = (x * x) % n

                if x == n - 1:

                    break

            else:

                return False



        return True



    def _lcm(self, a: int, b: int) -> int:

        """最小公倍数"""

        return a * b // gcd(a, b)



    def _mod_inverse(self, a: int, m: int) -> int:

        """模逆元（扩展欧几里得）"""

        g, x, _ = self._extended_gcd(a, m)

        if g != 1:

            raise ValueError("模逆元不存在")

        return x % m



    def _extended_gcd(self, a: int, b: int) -> tuple:

        """扩展欧几里得算法"""

        if a == 0:

            return b, 0, 1

        gcd, x1, y1 = self._extended_gcd(b % a, a)

        x = y1 - (b // a) * x1

        y = x1

        return gcd, x, y



    def _L_function(self, x: int) -> int:

        """L函数：L(x) = (x - 1) / n"""

        return (x - 1) // self.n



    def encrypt(self, plaintext: int) -> int:

        """

        加密



        参数：

            plaintext: 明文（0 到 n-1 之间）



        返回：密文

        """

        if plaintext < 0 or plaintext >= self.n:

            raise ValueError(f"明文必须在0到{self.n-1}之间")



        # 选择随机数 r，0 < r < n 且 gcd(r, n) = 1

        r = random.randrange(1, self.n)

        while gcd(r, self.n) != 1:

            r = random.randrange(1, self.n)



        # c = g^m * r^n mod n^2

        n_plus_1_pow = pow(self.g, plaintext, self.n_squared)

        r_pow_n = pow(r, self.n, self.n_squared)



        ciphertext = (n_plus_1_pow * r_pow_n) % self.n_squared



        return ciphertext



    def decrypt(self, ciphertext: int) -> int:

        """

        解密



        参数：

            ciphertext: 密文



        返回：明文

        """

        # L(c^λ mod n^2)

        c_pow = pow(ciphertext, self.lambda_n, self.n_squared)

        L_result = self._L_function(c_pow)



        # m = L(c^λ) * μ mod n

        plaintext = (L_result * self.mu) % self.n



        return plaintext



    def add(self, ciphertext1: int, ciphertext2: int) -> int:

        """

        同态加法：E(m1) ⊕ E(m2) = E(m1 + m2)



        参数：

            ciphertext1: 密文1

            ciphertext2: 密文2



        返回：加密 m1 + m2 的密文

        """

        return (ciphertext1 * ciphertext2) % self.n_squared



    def scalar_multiply(self, ciphertext: int, scalar: int) -> int:

        """

        标量乘法：E(m) ^ k = E(k * m)



        参数：

            ciphertext: 密文

            scalar: 标量k



        返回：加密 k*m 的密文

        """

        return pow(ciphertext, scalar, self.n_squared)





def voting_example():

    """投票示例"""

    print("=== Paillier投票示例 ===\n")



    # 创建加密系统

    paillier = PaillierCrypto(key_size=256)



    # 3个候选人：Alice, Bob, Charlie

    votes = [0, 0, 0]  # 实际投票

    encrypted_votes = [0, 0, 0]  # 加密投票



    print("投票过程：")

    print("  1. 每个选民加密自己的选择")

    print("  2. 所有加密投票可以同态相加")

    print()



    # 模拟投票

    vote_sequence = [0, 1, 2, 0, 1, 1, 2, 0, 0, 1]



    for voter_id, vote in enumerate(vote_sequence):

        # 加密投票

        encrypted_vote = paillier.encrypt(1)  # 投1票

        if vote == 0:

            encrypted_votes[0] = paillier.add(encrypted_votes[0], encrypted_vote)

        elif vote == 1:

            encrypted_votes[1] = paillier.add(encrypted_votes[1], encrypted_vote)

        else:

            encrypted_votes[2] = paillier.add(encrypted_votes[2], encrypted_vote)



    print(f"投票数: Alice={vote_sequence.count(0)}, Bob={vote_sequence.count(1)}, Charlie={vote_sequence.count(2)}")

    print()



    # 解密结果

    print("解密结果：")

    for i, encrypted_vote in enumerate(encrypted_votes):

        count = paillier.decrypt(encrypted_vote)

        name = ["Alice", "Bob", "Charlie"][i]

        print(f"  {name}: {count}票")





def secure_computation():

    """安全多方计算示例"""

    print()

    print("=== Paillier安全计算 ===")

    print()

    print("场景：计算总和但不知道各方数值")

    print()

    print("Alice有数值a，Bob有数值b")

    print()

    print("步骤：")

    print("  1. Alice加密a，发送给Bob")

    print("  2. Bob计算 E(a) ⊕ E(b) = E(a+b)")

    print("  3. Bob（或第三方）解密得到 a+b")

    print()

    print("关键：Bob只知道 a+b，不知道a或b的具体值")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== Paillier加密测试 ===\n")



    # 创建加密系统（使用小密钥用于测试）

    paillier = PaillierCrypto(key_size=256)



    # 测试加密/解密

    messages = [0, 1, 5, 42, 100]



    print("加密/解密测试：")

    for m in messages:

        c = paillier.encrypt(m)

        d = paillier.decrypt(c)

        status = "✅" if d == m else "❌"

        print(f"  {m} -> 密文 -> {d} {status}")



    print()



    # 测试同态加法

    print("同态加法测试：")

    m1, m2 = 10, 20

    c1 = paillier.encrypt(m1)

    c2 = paillier.encrypt(m2)



    c_sum = paillier.add(c1, c2)

    m_sum = paillier.decrypt(c_sum)



    print(f"  E({m1}) ⊕ E({m2}) = E({m1 + m2})")

    print(f"  解密结果: {m_sum} {'✅' if m_sum == m1 + m2 else '❌'}")



    print()



    # 测试标量乘法

    print("标量乘法测试：")

    m = 5

    k = 3

    c = paillier.encrypt(m)

    c_k = paillier.scalar_multiply(c, k)

    result = paillier.decrypt(c_k)



    print(f"  E({m})^{k} = E({m * k})")

    print(f"  解密结果: {result} {'✅' if result == m * k else '❌'}")



    print()

    voting_example()

    secure_computation()



    print()

    print("说明：")

    print("  - Paillier是概率加密（同一明文多次加密结果不同）")

    print("  - 加法同态适合投票、求和等应用")

    print("  - 需要大整数支持（Python默认支持）")

