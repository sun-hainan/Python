# -*- coding: utf-8 -*-

"""

算法实现：同态加密 / elgamal_cipher



本文件实现 elgamal_cipher 相关的算法功能。

"""



import random

from math import gcd





class ElGamalCrypto:

    """ElGamal加密系统"""



    def __init__(self, key_size: int = 256):

        """

        参数：

            key_size: 密钥位数

        """

        self.key_size = key_size



        # 生成大素数

        self.p = self._generate_prime(key_size)

        self.g = self._find_generator()



        # 私钥

        self.x = random.randint(2, self.p - 2)



        # 公钥

        self.y = pow(self.g, self.x, self.p)



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

        small_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]

        for p in small_primes:

            if n % p == 0:

                return n == p



        d = n - 1

        s = 0

        while d % 2 == 0:

            d //= 2

            s += 1



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



    def _find_generator(self) -> int:

        """找到原根（生成元）"""

        phi = self.p - 1

        factors = self._factorize(phi)



        while True:

            g = random.randint(2, self.p - 2)

            is_gen = True



            for q in factors:

                if pow(g, phi // q, self.p) == 1:

                    is_gen = False

                    break



            if is_gen:

                return g



    def _factorize(self, n: int) -> list:

        """分解素数"""

        factors = []

        d = 2

        while d * d <= n:

            if n % d == 0:

                factors.append(d)

                while n % d == 0:

                    n //= d

            d += 1

        if n > 1:

            factors.append(n)

        return factors



    def encrypt(self, m: int) -> Tuple[int, int]:

        """

        加密：c = (c1, c2)



        c1 = g^k mod p

        c2 = m * y^k mod p



        参数：

            m: 明文（0 < m < p）



        返回：(c1, c2)

        """

        k = random.randint(2, self.p - 2)

        while gcd(k, self.p - 1) != 1:

            k = random.randint(2, self.p - 2)



        c1 = pow(self.g, k, self.p)

        c2 = (m * pow(self.y, k, self.p)) % self.p



        return (c1, c2)



    def decrypt(self, c1: int, c2: int) -> int:

        """

        解密：m = c2 * c1^(-x) mod p



        参数：

            c1, c2: 密文



        返回：明文

        """

        s = pow(c1, self.x, self.p)

        s_inv = pow(s, -1, self.p)  # 模逆元

        m = (c2 * s_inv) % self.p



        return m



    def homomorphic_multiply(self, c1: int, c2: int,

                           d1: int, d2: int) -> Tuple[int, int]:

        """

        同态乘法：E(m1) * E(m2) = E(m1 * m2)



        参数：

            c1, c2: 第一个密文

            d1, d2: 第二个密文



        返回：乘积的密文

        """

        return ((c1 * d1) % self.p, (c2 * d2) % self.p)





def elgamal_homomorphic_example():

    """ElGamal同态示例"""

    print("=== ElGamal乘法同态示例 ===\n")



    # 创建ElGamal实例

    elgamal = ElGamalCrypto(key_size=256)



    print(f"素数位数: ~{len(bin(elgamal.p)) - 2}")

    print()



    # 同态乘法示例

    m1, m2 = 7, 5

    expected_product = m1 * m2



    print(f"明文: m1={m1}, m2={m2}")

    print(f"期望乘积: {expected_product}")

    print()



    # 加密

    c1 = elgamal.encrypt(m1)

    c2 = elgamal.encrypt(m2)



    print(f"密文1: {c1}")

    print(f"密文2: {c2}")



    # 同态乘法

    c_product = elgamal.homomorphic_multiply(c1[0], c1[1], c2[0], c2[1])

    print(f"同态乘积密文: {c_product}")



    # 解密验证

    decrypted_product = elgamal.decrypt(c_product[0], c_product[1])

    print(f"解密结果: {decrypted_product}")

    print(f"验证: {'✅ 正确' if decrypted_product == expected_product else '❌ 错误'}")





def semantic_security():

    """语义安全"""

    print()

    print("=== ElGamal语义安全 ===")

    print()

    print("ElGamal是语义安全的，因为：")

    print("  - 每次加密使用随机k")

    print("  - 相同的明文会产生不同的密文")

    print("  - 攻击者无法区分两个密文对应的明文")

    print()

    print("对比RSA：")

    print("  - RSA基本版本不是语义安全的")

    print("  - 需要填充才能达到语义安全")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== ElGamal加密测试 ===\n")



    elgamal_homomorphic_example()

    semantic_security()



    print()

    print("总结：")

    print("  - ElGamal有自然的乘法同态性")

    print("  - 是语义安全的概率加密")

    print("  - 常用于秘密共享和多方计算")

    print("  - 与RSA互补（基于离散对数而非大整数分解）")

