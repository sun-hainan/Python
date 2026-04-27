# -*- coding: utf-8 -*-

"""

算法实现：后量子密码学 / kyber



本文件实现 kyber 相关的算法功能。

"""



import random

from math import sqrt, log2





class KyberKEM:

    """Kyber简化实现"""



    def __init__(self, k: int = 4, n: int = 256, q: int = 3329):

        """

        参数：

            k: 模块度

            n: 多项式阶数（2的幂）

            q: 模数

        """

        self.k = k

        self.n = n

        self.q = q



        # 生成密钥

        self.public_key = self._generate_key()

        self.private_key = self._generate_key()



    def _generate_key(self) -> list:

        """生成密钥"""

        return [[random.randint(0, self.q - 1) for _ in range(self.n)]

                for _ in range(self.k)]



    def _sample_poly(self) -> list:

        """从二项分布采样多项式系数"""

        return [random.randint(0, 3) - 1 for _ in range(self.n)]



    def encapsulate(self, public_key: list) -> Tuple[list, list]:

        """

        封装：生成共享密钥



        参数：

            public_key: 公钥



        返回：(密文, 共享密钥)

        """

        # 生成随机多项式

        m = [self._sample_poly() for _ in range(self.k)]



        # 计算 u = A^T * m + e1 (简化)

        u = public_key  # 简化



        # 计算 v = <m, t> + e2 + shared_secret

        v = m  # 简化



        shared_secret = self._sample_poly()



        return (u, v), shared_secret



    def decapsulate(self, private_key: list, ciphertext: Tuple[list, list]) -> list:

        """

        解封装：恢复共享密钥



        参数：

            private_key: 私钥

            ciphertext: 密文



        返回：共享密钥

        """

        u, v = ciphertext



        # 简化：直接返回v

        return v





def kyber_parameters():

    """Kyber参数"""

    print("=== Kyber参数 ===")

    print()

    print("Kyber-512:")

    print("  - k = 2, n = 256")

    print("  - 公钥大小: 800 bytes")

    print("  - 密文大小: 768 bytes")

    print()

    print("Kyber-768:")

    print("  - k = 3, n = 256")

    print("  - 公钥大小: 1184 bytes")

    print("  - 密文大小: 1088 bytes")

    print()

    print("Kyber-1024:")

    print("  - k = 4, n = 256")

    print("  - 公钥大小: 1568 bytes")

    print("  - 密文大小: 1568 bytes")





def security_analysis():

    """安全性分析"""

    print()

    print("=== Kyber安全性 ===")

    print()

    print("基于困难问题：")

    print("  - Module-LWE（格的特殊变体）")

    print("  - 被认为对量子计算机也困难")

    print()

    print("与RSA/ECC对比：")

    print("  - RSA-2048：容易被量子算法破解（Shor）")

    print("  - Kyber-512：量子计算机也需要指数时间")

    print()

    print("性能：")

    print("  - 公钥/密文更大")

    print("  - 但在量子威胁下是必要的")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== Kyber KEM测试 ===\n")



    kyber = KyberKEM(k=2)



    print(f"Kyber参数: k={kyber.k}, n={kyber.n}, q={kyber.q}")

    print()



    # 封装

    ciphertext, shared_secret = kyber.encapsulate(kyber.public_key)



    print(f"生成的共享密钥长度: {len(shared_secret) if isinstance(shared_secret, list) else 1}")

    print(f"密文: {len(ciphertext) if isinstance(ciphertext, list) else 2} parts")



    # 解封装

    recovered = kyber.decapsulate(kyber.private_key, ciphertext)



    print(f"验证: {'✅ 成功' if recovered == shared_secret else '❌ 失败'}")



    print()

    kyber_parameters()

    security_analysis()



    print()

    print("说明：")

    print("  - Kyber是NIST后量子标准之一")

    print("  - 用于密钥交换，保护TLS等协议")

    print("  - 已经被多个公司和项目采用")

