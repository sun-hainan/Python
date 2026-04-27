# -*- coding: utf-8 -*-

"""

算法实现：同态加密 / rsa_cipher



本文件实现 rsa_cipher 相关的算法功能。

"""



import random

from math import gcd





class RSACrypto:

    """RSA加密系统"""



    def __init__(self, key_size: int = 512):

        """

        参数：

            key_size: 密钥位数

        """

        self.key_size = key_size



        # 生成大素数

        self.p = self._generate_prime(key_size // 2)

        self.q = self._generate_prime(key_size // 2)



        # 模数

        self.n = self.p * self.q



        # 欧拉函数

        phi = (self.p - 1) * (self.q - 1)



        # 选公钥指数

        self.e = 65537  # 常用值

        if self.e >= phi:

            self.e = 3



        # 私钥指数

        self.d = self._mod_inverse(self.e, phi)



    def _generate_prime(self, bits: int) -> int:

        """生成随机素数"""

        while True:

            n = random.getrandbits(bits)

            n |= (1 << bits - 1) | 1

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



        # 分解 n-1

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



    def _mod_inverse(self, a: int, m: int) -> int:

        """扩展欧几里得求逆元"""

        if m == 1:

            return 0



        y0, y1 = 0, 1

        while m > 1:

            q = a // m

            a, m = m, a - q * m

            y0, y1 = y1, y0 - q * y1



        return y0 if y0 > 0 else y0 + m



    def encrypt(self, plaintext: int) -> int:

        """

        加密：c = m^e mod n

        """

        return pow(plaintext, self.e, self.n)



    def decrypt(self, ciphertext: int) -> int:

        """

        解密：m = c^d mod n

        """

        return pow(ciphertext, self.d, self.n)



    def homomorphic_multiply(self, c1: int, c2: int) -> int:

        """

        同态乘法：E(m1) × E(m2) = E(m1 × m2)



        参数：

            c1, c2: 两个密文



        返回：加密 m1 × m2 的密文

        """

        return (c1 * c2) % self.n



    def get_public_key(self) -> Tuple[int, int]:

        """获取公钥"""

        return (self.e, self.n)



    def get_private_key(self) -> Tuple[int, int]:

        """获取私钥"""

        return (self.d, self.n)





def rsa_homomorphic_example():

    """RSA同态示例"""

    print("=== RSA乘法同态示例 ===\n")



    # 创建RSA实例

    rsa = RSACrypto(key_size=256)



    print(f"密钥生成完成")

    print(f"  n 位数: {len(bin(rsa.n)) - 2}")

    print()



    # 同态乘法示例

    m1, m2 = 7, 5

    expected_product = m1 * m2



    print(f"明文: m1={m1}, m2={m2}")

    print(f"期望乘积: {expected_product}")

    print()



    # 加密

    c1 = rsa.encrypt(m1)

    c2 = rsa.encrypt(m2)

    print(f"密文1: {c1}")

    print(f"密文2: {c2}")



    # 同态乘法

    c_product = rsa.homomorphic_multiply(c1, c2)

    print(f"同态乘积密文: {c_product}")



    # 解密验证

    decrypted_product = rsa.decrypt(c_product)

    print(f"解密结果: {decrypted_product}")

    print(f"验证: {'✅ 正确' if decrypted_product == expected_product else '❌ 错误'}")





def homomorphic_limitations():

    """同态限制"""

    print()

    print("=== RSA同态的限制 ===")

    print()

    print("1. 选择明文攻击（CPA）")

    print("   - 攻击者可以加密任意消息")

    print("   - 选择适当的密文可能获取私钥信息")

    print()

    print("2. 填充必要")

    print("   - 真实RSA必须使用OAEP或PKCS#1填充")

    print("   - 纯RSA乘法同态不安全")

    print()

    print("3. 只能乘法")

    print("   - 加法需要不同的方案（如Paillier）")

    print("   - 全同态需要两者结合")





def paillier_comparison():

    """与Paillier对比"""

    print()

    print("=== RSA vs Paillier ===")

    print()

    print("RSA（乘法同态）：")

    print("  - E(m1) × E(m2) = E(m1 × m2)")

    print("  - 需要私钥解密")

    print("  - 应用：加密乘法投票、秘密乘积")

    print()

    print("Paillier（加法同态）：")

    print("  - E(m1) × E(m2) = E(m1 + m2)")

    print("  - 适合求和类应用")

    print("  - 更多细节见同态加密/paillier_crypto.py")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== RSA加密测试 ===\n")



    rsa_homomorphic_example()

    homomorphic_limitations()

    paillier_comparison()



    print()

    print("总结：")

    print("  - RSA有自然的乘法同态性")

    print("  - 但实际使用需要填充保证安全")

    print("  - 与Paillier互补（一个乘法一个加法）")

    print("  - 两者结合可实现有限的全同态")

