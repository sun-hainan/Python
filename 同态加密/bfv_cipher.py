# -*- coding: utf-8 -*-

"""

算法实现：同态加密 / bfv_cipher



本文件实现 bfv_cipher 相关的算法功能。

"""



import random

from typing import Tuple





class BFVCipher:

    """BFV同态加密方案"""



    def __init__(self, poly_degree: int = 4096, plaintext_mod: int = 1 << 16):

        """

        参数：

            poly_degree: 多项式阶数

            plaintext_mod: 明文模数

        """

        self.n = poly_degree

        self.t = plaintext_mod

        self.q = self.t * 32  # 密文模数



    def keygen(self) -> Tuple[dict, dict]:

        """

        密钥生成



        返回：(公钥, 私钥)

        """

        # 简化密钥生成

        sk = random.randint(1, self.q // 2)

        pk = sk * 3 % self.q



        return {'pk': pk}, {'sk': sk}



    def encrypt(self, message: int, public_key: dict) -> Tuple[int, int]:

        """

        加密



        参数：

            message: 明文消息

            public_key: 公钥



        返回：密文对 (c0, c1)

        """

        pk = public_key['pk']



        # 随机掩码

        r = random.randint(0, self.q)



        # 密文

        c0 = (message + r * pk) % self.q

        c1 = r % self.q



        return (c0, c1)



    def decrypt(self, ciphertext: Tuple[int, int], private_key: dict) -> int:

        """

        解密



        参数：

            ciphertext: 密文

            private_key: 私钥



        返回：明文

        """

        c0, c1 = ciphertext

        sk = private_key['sk']



        # m = c0 - c1 * sk (mod q) (mod t)

        m = (c0 - c1 * sk) % self.q

        m = m % self.t



        return m



    def add(self, c1: Tuple[int, int], c2: Tuple[int, int]) -> Tuple[int, int]:

        """

        密文加法



        返回：c1 + c2

        """

        return ((c1[0] + c2[0]) % self.q,

                (c1[1] + c2[1]) % self.q)



    def multiply(self, c1: Tuple[int, int], c2: Tuple[int, int]) -> Tuple[int, int]:

        """

        密文乘法



        返回：c1 × c2

        """

        # 简化的乘法

        # 实际需要更复杂的处理

        return ((c1[0] * c2[0]) % self.q,

                (c1[1] * c2[1]) % self.q)





def bfv_properties():

    """BFV性质"""

    print("=== BFV方案性质 ===")

    print()

    print("参数：")

    print(f"  - 多项式阶数: {self.n}")

    print(f"  - 明文模数: {self.t}")

    print(f"  - 密文模数: {self.q}")

    print()

    print("同态操作：")

    print("  - 加法: 密文直接相加")

    print("  - 乘法: 密文相乘（更复杂）")

    print()

    print("应用：")

    print("  - 数值数据加密")

    print("  - 机器学习推理")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== BFV同态加密测试 ===\n")



    bfev = BFVCipher(poly_degree=1024)



    print(f"多项式阶数: {bfev.n}")

    print(f"明文模数: {bfev.t}")

    print(f"密文模数: {bfev.q}")

    print()



    # 密钥生成

    pk, sk = bfev.keygen()



    # 加密消息

    m1 = 42

    m2 = 17



    c1 = bfev.encrypt(m1, pk)

    c2 = bfev.encrypt(m2, pk)



    print(f"消息1: {m1}")

    print(f"消息2: {m2}")

    print(f"密文1: {c1}")

    print(f"密文2: {c2}")

    print()



    # 同态加法

    c_add = bfev.add(c1, c2)

    m_add = bfev.decrypt(c_add, sk)

    print(f"加法结果: {m_add} (应该是 {m1 + m2})")



    # 同态乘法

    c_mul = bfev.multiply(c1, c2)

    m_mul = bfev.decrypt(c_mul, sk)

    print(f"乘法结果: {m_mul} (简化计算)")



    print()

    print("说明：")

    print("  - BFV是整数上的同态加密")

    print("  - 支持加法和乘法")

    print("  - 微软SEAL库实现")

