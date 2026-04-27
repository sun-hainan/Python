# -*- coding: utf-8 -*-

"""

算法实现：密码学与安全 / post_quantum_crypto



本文件实现 post_quantum_crypto 相关的算法功能。

"""



import random

import hashlib

import numpy as np

from typing import Tuple, List





class RingLWE:

    """基于环上学习错误的密钥交换协议（简化版）"""



    def __init__(self, n: int = 8, q: int = 97):

        """

        初始化Ring-LWE



        参数：

            n: 多项式阶数

            q: 模数

        """

        self.n = n

        self.q = q



    def _random_poly(self) -> List[int]:

        """

        生成随机多项式系数



        返回：n个[-q/2, q/2)范围内的系数

        """

        return [random.randint(-self.q//2, self.q//2) for _ in range(self.n)]



    def _poly_mult(self, a: List[int], b: List[int]) -> List[int]:

        """

        多项式乘法（模q）



        参数：

            a, b: 两个多项式



        返回：乘积（模q，模x^n+1）

        """

        # 简化：普通多项式乘法

        result = [0] * (2 * self.n - 1)

        for i in range(self.n):

            for j in range(self.n):

                result[i + j] += a[i] * b[j]



        # 模q，模x^n+1（即 x^n = -1）

        for i in range(self.n, 2 * self.n - 1):

            result[i - self.n] = (result[i - self.n] - result[i]) % self.q



        return [result[i] % self.q for i in range(self.n)]



    def _poly_add(self, a: List[int], b: List[int]) -> List[int]:

        """

        多项式加法



        参数：

            a, b: 两个多项式



        返回：和（模q）

        """

        return [(a[i] + b[i]) % self.q for i in range(self.n)]



    def _poly_sub(self, a: List[int], b: List[int]) -> List[int]:

        """

        多项式减法



        参数：

            a, b: 两个多项式



        返回：差（模q）

        """

        return [(a[i] - b[i]) % self.q for i in range(self.n)]



    def generate_keys(self) -> Tuple[Tuple[List[int], List[int]], List[int]]:

        """

        生成密钥对



        返回：(公钥, 私钥)

        """

        # 生成秘密多项式s（私钥）

        s = self._random_poly()



        # 生成随机多项式a（公开参数）

        a = [random.randint(0, self.q - 1) for _ in range(self.n)]



        # 生成错误多项式e

        e = self._random_poly()

        # 错误项通常更小

        e = [x // 10 for x in e]



        # 计算 b = a * s + e mod q（公钥）

        a_s = self._poly_mult(a, s)

        b = self._poly_add(a_s, e)



        # 公钥：(a, b)

        pk = (a, b)

        sk = s



        return pk, sk



    def alice_send(self, pk: Tuple[List[int], List[int]]) -> Tuple[List[int], List[int]]:

        """

        Alice发送



        参数：

            pk: Alice的公钥



        返回：Alice的消息

        """

        a, b = pk



        # Alice选择随机多项式s'和错误e'

        s_prime = self._random_poly()

        e_prime = self._random_poly()

        e_prime = [x // 10 for x in e_prime]



        # 计算 u = a * s' + e' mod q

        u = self._poly_add(self._poly_mult(a, s_prime), e_prime)



        # 计算 v = b * s' + e'' mod q（v'）

        e_double_prime = self._random_poly()

        e_double_prime = [x // 10 for x in e_double_prime]

        v = self._poly_add(self._poly_mult(b, s_prime), e_double_prime)



        return u, v



    def bob_compute(self, pk: Tuple[List[int], List[int]]) -> List[int]:

        """

        Bob计算共享秘密



        参数：

            pk: Alice的公钥



        返回：Bob的共享秘密

        """

        a, b = pk



        # Bob选择随机s''和e'''

        s_double_prime = self._random_poly()

        e_triple_prime = self._random_poly()

        e_triple_prime = [x // 10 for x in e_triple_prime]



        # 计算 u' = a * s'' + e'''

        u_prime = self._poly_add(self._poly_mult(a, s_double_prime), e_triple_prime)



        # 计算 v' = b * s'' mod q（忽略更小的错误）

        v_prime = self._poly_mult(b, s_double_prime)



        # Bob的共享秘密近似于 a * s * s''

        # 注意：简化实现中，精确的密钥协商需要更多步骤



        return v_prime



    def alice_compute(self, sk: List[int], bob_message: Tuple[List[int], List[int]]) -> List[int]:

        """

        Alice计算共享秘密



        参数：

            sk: Alice的私钥

            bob_message: Bob的消息



        返回：Alice的共享秘密

        """

        u, v = bob_message



        # Alice计算 v - u * s（简化）

        u_s = self._poly_mult(u, sk)

        shared = self._poly_sub(v, u_s)



        return shared



    def compress_poly(self, poly: List[int]) -> bytes:

        """

        将多项式压缩为哈希（用于生成会话密钥）



        参数：

            poly: 多项式



        返回：哈希值

        """

        return hashlib.sha256(str(poly).encode()).digest()





class McElieceSimplified:

    """简化的McEliece公钥密码系统"""



    def __init__(self, n: int = 8, k: int = 4):

        """

        初始化McEliece



        参数：

            n: 码字长度

            k: 消息长度

        """

        self.n = n

        self.k = k



    def generate_matrix(self, rows: int, cols: int) -> List[List[int]]:

        """

        生成随机二进制矩阵



        参数：

            rows: 行数

            cols: 列数



        返回：二进制矩阵

        """

        return [[random.randint(0, 1) for _ in range(cols)] for _ in range(rows)]



    def matrix_mult(self, A: List[List[int]], B: List[List[int]]) -> List[List[int]]:

        """

        矩阵乘法（模2）



        参数：

            A, B: 二进制矩阵



        返回：A * B mod 2

        """

        n = len(A)

        m = len(B[0])

        p = len(B)



        result = [[0] * m for _ in range(n)]

        for i in range(n):

            for j in range(m):

                for k_idx in range(p):

                    result[i][j] ^= (A[i][k_idx] & B[k_idx][j])

        return result



    def encode(self, message: List[int], G: List[List[int]]) -> List[int]:

        """

        线性码编码



        参数：

            message: k位消息

            G: k×n 生成矩阵



        返回：n位码字

        """

        codeword = [0] * len(G[0])

        for i in range(len(G)):

            for j in range(len(G[0])):

                codeword[j] ^= (message[i] & G[i][j])

        return codeword



    def add_noise(self, codeword: List[int], t: int) -> List[int]:

        """

        添加最多t个错误



        参数：

            codeword: 码字

            t: 错误数量



        返回：带噪声的码字

        """

        result = codeword.copy()

        error_positions = random.sample(range(len(codeword)), min(t, len(codeword)))

        for pos in error_positions:

            result[pos] ^= 1

        return result



    def syndrome_decode(self, received: List[int], H: List[List[int]]) -> List[int]:

        """

        简化的伴随式译码



        参数：

            received: 接收向量

            H: n×(n-k) 校验矩阵



        返回：估计的错误向量

        """

        # 简化：只返回全零向量

        return [0] * len(received)





def post_quantum_comparison():

    """后量子算法比较"""

    print("=== 后量子密码算法比较 ===")

    print()

    print("1. Ring-LWE / NTRU")

    print("   - 基于格困难问题")

    print("   - 密钥小、速度快")

    print("   - 密钥交换和加密")

    print()

    print("2. McEliece")

    print("   - 基于纠错码困难问题")

    print("   - 公钥很大，但历史最稳定")

    print("   - 签名和加密")

    print()

    print("3. 哈希签名（SPHINCS+）")

    print("   - 基于哈希函数安全性")

    print("   - 只用于签名")

    print("   - 公钥/签名很大")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 后量子密码学测试 ===\n")



    # Ring-LWE密钥交换演示

    print("Ring-LWE密钥交换：")

    lwe = RingLWE(n=8, q=97)



    # Alice生成密钥

    pk, sk = lwe.generate_keys()



    print(f"  n={lwe.n}, q={lwe.q}")

    print(f"  私钥s: {sk}")

    print(f"  公钥a: {pk[0]}")

    print(f"  公钥b: {pk[1]}")

    print()



    # Bob计算

    bob_shared = lwe.bob_compute(pk)

    print(f"  Bob共享秘密: {lwe.compress_poly(bob_shared).hex()[:16]}...")

    print()



    # Alice接收Bob消息并计算

    bob_msg = lwe.alice_send(pk)

    alice_shared = lwe.alice_compute(sk, bob_msg)

    print(f"  Alice共享秘密: {lwe.compress_poly(alice_shared).hex()[:16]}...")

    print()



    # 密钥不完全匹配演示（简化实现）

    print("注意：简化实现中密钥不完全相等")

    print("实际协议需要额外的错误纠正步骤")

    print()



    # McEliece演示

    print("McEliece编码演示：")

    mceliece = McElieceSimplified(n=8, k=4)



    # 生成生成矩阵

    G = mceliece.generate_matrix(4, 8)



    # 消息

    message = [1, 0, 1, 1]



    # 编码

    codeword = mceliece.encode(message, G)



    print(f"  消息: {message}")

    print(f"  生成矩阵G: {G}")

    print(f"  码字: {codeword}")

    print()



    # 添加噪声

    noisy = mceliece.add_noise(codeword, t=1)



    print(f"  添加1个错误后: {noisy}")

    print()



    # 后量子算法比较

    post_quantum_comparison()



    print()

    print("说明：")

    print("  - 量子计算机威胁RSA/ECC")

    print("  - 后量子密码学已准备就绪")

    print("  - NIST已在标准化进程中")

