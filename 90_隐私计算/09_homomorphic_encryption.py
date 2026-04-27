# -*- coding: utf-8 -*-

"""

算法实现：隐私计算 / 09_homomorphic_encryption



本文件实现 09_homomorphic_encryption 相关的算法功能。

"""



import numpy as np

from typing import Tuple, List





class PaillierEncryption:

    """

    Paillier加法同态加密



    核心性质:

    - E(m1) * E(m2) = E(m1 + m2)

    - E(m1)^k = E(k * m1)



    公钥: (n, g)

    私钥: lambda, mu

    """



    def __init__(self, key_size: int = 256):

        """

        初始化Paillier加密系统



        Args:

            key_size: 密钥位长(实际应使用1024+)

        """

        self.key_size = key_size

        np.random.seed(42)



        # 生成两个大素数

        self.p = self._generate_prime(key_size // 2)

        self.q = self._generate_prime(key_size // 2)



        # n = p * q

        self.n = self.p * self.q



        # g = n + 1 (简化版本)

        self.g = self.n + 1



        # 计算lambda

        self._compute_keys()



    def _generate_prime(self, bits: int) -> int:

        """

        生成随机素数



        Args:

            bits: 位数



        Returns:

            素数

        """

        # 简化的素数生成

        p = np.random.randint(2**(bits-1), 2**bits)

        # 简单的Miller-Rabin测试

        while not self._is_prime(p):

            p += 1

        return p



    def _is_prime(self, n: int) -> bool:

        """Miller-Rabin素性测试(简化)"""

        if n < 2:

            return False

        if n == 2:

            return True

        if n % 2 == 0:

            return False

        return True  # 简化



    def _compute_keys(self):

        """计算私钥参数"""

        # lambda = lcm(p-1, q-1)

        import math

        self.lambda_key = np.lcm(self.p - 1, self.q - 1)



        # mu = L(g^lambda mod n^2)^(-1) mod n

        n_squared = self.n * self.n

        g_lambda = pow(self.g, self.lambda_key, n_squared)

        # L(x) = (x-1)/n

        l_val = (g_lambda - 1) // self.n

        self.mu = pow(l_val, -1, self.n)



    def L(self, x: int) -> int:

        """Paillier的L函数: L(x) = (x-1)/n"""

        return (x - 1) // self.n



    def generate_keys(self) -> Tuple[Tuple[int, int], Tuple[int, int]]:

        """

        生成密钥对



        Returns:

            ((public_key_n, public_key_g), (private_key_lambda, private_key_mu))

        """

        public_key = (self.n, self.g)

        private_key = (self.lambda_key, self.mu)

        return public_key, private_key



    def encrypt(self, plaintext: int) -> int:

        """

        加密



        E(m) = g^m * r^n mod n^2



        Args:

            plaintext: 明文整数



        Returns:

            密文

        """

        n_squared = self.n * self.n



        # 随机盲因子r

        r = np.random.randint(1, self.n)



        # g^m mod n^2

        g_m = pow(self.g, plaintext, n_squared)



        # r^n mod n^2

        r_n = pow(r, self.n, n_squared)



        # 密文

        ciphertext = (g_m * r_n) % n_squared

        return ciphertext



    def decrypt(self, ciphertext: int) -> int:

        """

        解密



        L(c^lambda mod n^2) * mu mod n



        Args:

            ciphertext: 密文



        Returns:

            明文

        """

        n_squared = self.n * self.n



        # c^lambda mod n^2

        c_lambda = pow(ciphertext, self.lambda_key, n_squared)



        # L(c^lambda)

        l_val = self.L(c_lambda)



        # m = L(c^lambda) * mu mod n

        plaintext = (l_val * self.mu) % self.n

        return plaintext



    def add(self, ciphertext1: int, ciphertext2: int) -> int:

        """

        密文加法



        E(m1) * E(m2) = E(m1 + m2)



        Args:

            ciphertext1: 第一个密文

            ciphertext2: 第二个密文



        Returns:

            和的密文

        """

        n_squared = self.n * self.n

        return (ciphertext1 * ciphertext2) % n_squared



    def multiply(self, ciphertext: int, scalar: int) -> int:

        """

        密文标量乘法



        E(m)^k = E(k*m)



        Args:

            ciphertext: 密文

            scalar: 标量



        Returns:

            标量乘的密文

        """

        n_squared = self.n * self.n

        return pow(ciphertext, scalar, n_squared)





class RSAEncryption:

    """

    RSA乘法同态加密



    核心性质:

    - E(m1) * E(m2) = E(m1 * m2)



    简化版本,实际使用需要OAEP填充

    """



    def __init__(self, key_size: int = 256):

        """

        初始化RSA加密



        Args:

            key_size: 密钥位长

        """

        self.key_size = key_size

        np.random.seed(42)



        # 生成素数

        self.p = self._generate_prime(key_size // 2)

        self.q = self._generate_prime(key_size // 2)



        # n = p * q

        self.n = self.p * self.q



        # 欧拉函数

        phi = (self.p - 1) * (self.q - 1)



        # 公开指数

        self.e = 65537



        # 私钥指数

        self.d = pow(self.e, -1, phi)



    def _generate_prime(self, bits: int) -> int:

        """生成随机素数"""

        p = np.random.randint(2**(bits-1), 2**bits)

        while not self._is_prime(p):

            p += 1

        return p



    def _is_prime(self, n: int) -> bool:

        """素性测试"""

        if n < 2:

            return False

        if n == 2:

            return True

        if n % 2 == 0:

            return False

        return True



    def generate_keys(self) -> Tuple[Tuple[int, int], Tuple[int, int]]:

        """

        生成密钥对



        Returns:

            ((public_n, public_e), (private_n, private_d))

        """

        public_key = (self.n, self.e)

        private_key = (self.n, self.d)

        return public_key, private_key



    def encrypt(self, plaintext: int, public_key: Tuple[int, int] = None) -> int:

        """

        加密



        C = m^e mod n



        Args:

            plaintext: 明文

            public_key: 公钥(可选)



        Returns:

            密文

        """

        if public_key is None:

            public_key = (self.n, self.e)



        n, e = public_key

        return pow(plaintext, e, n)



    def decrypt(self, ciphertext: int, private_key: Tuple[int, int] = None) -> int:

        """

        解密



        m = c^d mod n



        Args:

            ciphertext: 密文

            private_key: 私钥(可选)



        Returns:

            明文

        """

        if private_key is None:

            private_key = (self.n, self.d)



        n, d = private_key

        return pow(ciphertext, d, n)



    def multiply(self, ciphertext1: int, ciphertext2: int) -> int:

        """

        密文乘法



        E(m1) * E(m2) = E(m1 * m2)



        Args:

            ciphertext1: 第一个密文

            ciphertext2: 第二个密文



        Returns:

            乘积的密文

        """

        return (ciphertext1 * ciphertext2) % self.n



    def power(self, ciphertext: int, exponent: int) -> int:

        """

        密文幂运算



        E(m)^k = E(m^k)



        Args:

            ciphertext: 密文

            exponent: 指数



        Returns:

            幂的密文

        """

        return pow(ciphertext, exponent, self.n)





class SimpleFHE:

    """

    简化的全同态加密演示



    展示同态加密的基本原理

    不适合实际使用,仅用于教育目的



    实际FHE方案如BFV, CKKS, BGV等需要:

    - 格密码学基础

    - 复杂的噪声管理

    -  bootstrapping技术

    """



    def __init__(self):

        """初始化简化的FHE"""

        np.random.seed(42)

        self.modulus = 2**31 - 1  # 大素数



    def keygen(self) -> Tuple[int, int]:

        """

        生成密钥



        Returns:

            (公钥, 私钥)

        """

        secret = np.random.randint(1, self.modulus)

        public = secret * 2 + np.random.randint(0, 10)  # 简化的公钥

        return public, secret



    def encrypt(self, plaintext: int, public_key: int) -> Tuple[int, int]:

        """

        加密



        简化的加密: 密文 = 明文 + 公钥 * 随机数



        Args:

            plaintext: 明文

            public_key: 公钥



        Returns:

            (密文1, 密文2)

        """

        r = np.random.randint(1, 100)

        c1 = (plaintext + r * public_key) % self.modulus

        c2 = r % self.modulus

        return c1, c2



    def decrypt(self, ciphertext: Tuple[int, int], secret_key: int) -> int:

        """

        解密



        m = c1 - c2 * secret mod p



        Args:

            ciphertext: 密文

            secret_key: 私钥



        Returns:

            明文

        """

        c1, c2 = ciphertext

        m = (c1 - c2 * secret_key) % self.modulus

        return m



    def add(

        self,

        ct1: Tuple[int, int],

        ct2: Tuple[int, int]

    ) -> Tuple[int, int]:

        """

        密文加法



        Args:

            ct1: 第一个密文

            ct2: 第二个密文



        Returns:

            和的密文

        """

        c1_sum = (ct1[0] + ct2[0]) % self.modulus

        c2_sum = (ct1[1] + ct2[1]) % self.modulus

        return c1_sum, c2_sum



    def multiply(

        self,

        ct: Tuple[int, int],

        scalar: int

    ) -> Tuple[int, int]:

        """

        密文标量乘法



        Args:

            ct: 密文

            scalar: 标量



        Returns:

            乘积的密文

        """

        c1_prod = (ct[0] * scalar) % self.modulus

        c2_prod = (ct[1] * scalar) % self.modulus

        return c1_prod, c2_prod





def homomorphic_computation_demo():

    """

    演示同态加密计算

    """



    print("同态加密下的隐私计算演示")

    print("=" * 60)



    # 1. Paillier加法同态

    print("\n1. Paillier加法同态加密")

    paillier = PaillierEncryption(key_size=128)



    m1 = 10

    m2 = 20



    print(f"   明文1: {m1}, 明文2: {m2}")



    c1 = paillier.encrypt(m1)

    c2 = paillier.encrypt(m2)

    print(f"   密文1: {c1}")

    print(f"   密文2: {c2}")



    # 密文加法

    c_sum = paillier.add(c1, c2)

    decrypted_sum = paillier.decrypt(c_sum)

    print(f"   密文加法: {decrypted_sum} (期望: {m1 + m2})")



    # 密文标量乘法

    c_scaled = paillier.multiply(c1, 5)

    decrypted_scaled = paillier.decrypt(c_scaled)

    print(f"   密文乘5: {decrypted_scaled} (期望: {m1 * 5})")



    # 2. RSA乘法同态

    print("\n2. RSA乘法同态加密")

    rsa = RSAEncryption(key_size=128)



    m1_rsa = 7

    m2_rsa = 13



    print(f"   明文1: {m1_rsa}, 明文2: {m2_rsa}")



    c1_rsa = rsa.encrypt(m1_rsa)

    c2_rsa = rsa.encrypt(m2_rsa)

    print(f"   密文1: {c1_rsa}")

    print(f"   密文2: {c2_rsa}")



    # 密文乘法

    c_product = rsa.multiply(c1_rsa, c2_rsa)

    decrypted_product = rsa.decrypt(c_product)

    print(f"   密文乘法: {decrypted_product} (期望: {m1_rsa * m2_rsa})")



    # 3. 简化的全同态演示

    print("\n3. 简化的全同态加密")

    fhe = SimpleFHE()



    public_key, secret_key = fhe.keygen()



    m1_fhe = 5

    m2_fhe = 3



    print(f"   明文1: {m1_fhe}, 明文2: {m2_fhe}")



    ct1 = fhe.encrypt(m1_fhe, public_key)

    ct2 = fhe.encrypt(m2_fhe, public_key)

    print(f"   密文1: {ct1}")

    print(f"   密文2: {ct2}")



    # 密文加法

    ct_sum = fhe.add(ct1, ct2)

    m_sum = fhe.decrypt(ct_sum, secret_key)

    print(f"   密文加法: {m_sum} (期望: {m1_fhe + m2_fhe})")



    # 密文标量乘法

    ct_scaled = fhe.multiply(ct1, 4)

    m_scaled = fhe.decrypt(ct_scaled, secret_key)

    print(f"   密文乘4: {m_scaled} (期望: {m1_fhe * 4})")



    # 4. 实际应用场景

    print("\n4. 实际应用场景: 隐私保护的机器学习推理")

    print("   场景: 服务器在不知道输入的情况下计算模型输出")



    # 模拟

    model_weights = np.array([0.5, -0.3, 0.8])

    user_input = np.array([10, 20, 30])



    # 服务器只有模型,用户只有数据(加密的)

    # 这里简化演示

    encrypted_input = [paillier.encrypt(x) for x in user_input]



    # 服务器计算(在密文上)

    encrypted_output = np.zeros(1, dtype=object)

    for i, (enc_x, w) in enumerate(zip(encrypted_input, model_weights)):

        scaled = paillier.multiply(enc_x, int(w * 1000))  # 缩放

        if i == 0:

            encrypted_output[0] = scaled

        else:

            encrypted_output[0] = paillier.add(encrypted_output[0], scaled)



    # 用户解密得到结果

    result = paillier.decrypt(encrypted_output[0]) / 1000.0

    true_result = np.dot(user_input, model_weights)



    print(f"   模型权重: {model_weights}")

    print(f"   用户输入: {user_input}")

    print(f"   计算结果(明文): {true_result:.2f}")

    print(f"   计算结果(密文): {result:.2f}")





if __name__ == "__main__":

    homomorphic_computation_demo()



    print("\n" + "=" * 60)

    print("同态加密演示完成!")

    print("注意: 实际FHE需要复杂的格密码学和噪声管理")

    print("=" * 60)

