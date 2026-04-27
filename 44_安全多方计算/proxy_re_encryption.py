# -*- coding: utf-8 -*-

"""

算法实现：安全多方计算 / proxy_re_encryption



本文件实现 proxy_re_encryption 相关的算法功能。

"""



import random

from typing import Tuple





class ProxyReEncryption:

    """代理重加密"""



    def __init__(self, security_bits: int = 256):

        """

        参数：

            security_bits: 安全参数

        """

        self.security_bits = security_bits



    def keygen(self, user_id: int) -> Tuple[int, int]:

        """

        用户密钥生成



        参数：

            user_id: 用户ID



        返回：(公钥, 私钥)

        """

        sk = random.randint(2**(security_bits-1), 2**security_bits)

        pk = sk * 3  # 简化的关系

        return pk, sk



    def encrypt(self, message: int, public_key: int) -> int:

        """

        加密



        返回：密文

        """

        return message + public_key



    def decrypt(self, ciphertext: int, private_key: int) -> int:

        """

        解密



        返回：明文

        """

        return ciphertext - private_key



    def generate_re_encryption_key(self, sk_a: int, pk_b: int) -> int:

        """

        生成重加密密钥



        参数：

            sk_a: 用户A的私钥

            pk_b: 用户B的公钥



        返回：重加密密钥

        """

        # 简化：rk_A→B = sk_A * pk_B

        return sk_a * pk_b



    def re_encrypt(self, ciphertext: int, rk: int) -> int:

        """

        重加密



        参数：

            ciphertext: A的密文

            rk: 重加密密钥



        返回：B可以解密的密文

        """

        # 简化：转换

        return ciphertext + rk



    def decrypt_final(self, ciphertext: int, sk_b: int) -> int:

        """

        B解密重加密后的密文



        返回：明文

        """

        return (ciphertext - sk_b) // 3





def pre_applications():

    """PRE应用"""

    print("=== 代理重加密应用 ===")

    print()

    print("1. 云存储")

    print("   - 数据从A迁移到B")

    print("   - 不需要解密再加密")

    print()

    print("2. 邮件转发")

    print("   - 第三方可以转发加密邮件")

    print("   - 不暴露内容")

    print()

    print("3. 区块链")

    print("   - 跨链资产转移")

    print("   - 安全的密文转换")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 代理重加密测试 ===\n")



    pre = ProxyReEncryption(security_bits=64)



    # 用户A和B

    pk_a, sk_a = pre.keygen(1)

    pk_b, sk_b = pre.keygen(2)



    print(f"用户A: pk={pk_a}, sk={sk_a}")

    print(f"用户B: pk={pk_b}, sk={sk_b}")

    print()



    # A加密消息

    message = 42

    c_a = pre.encrypt(message, pk_a)



    print(f"消息: {message}")

    print(f"A的密文: {c_a}")



    # 生成重加密密钥

    rk_a_to_b = pre.generate_re_encryption_key(sk_a, pk_b)



    print(f"重加密密钥: {rk_a_to_b}")

    print()



    # 代理重加密

    c_b = pre.re_encrypt(c_a, rk_a_to_b)



    print(f"重加密后: {c_b}")



    # B解密

    decrypted = pre.decrypt_final(c_b, sk_b)



    print(f"B解密结果: {decrypted}")

    print(f"正确: {'✅' if decrypted == message else '❌'}")



    print()

    pre_applications()



    print()

    print("说明：")

    print("  - 代理重加密用于安全数据迁移")

    print("  - 云存储和邮件系统有应用")

    print("  - 需要防止滥用攻击")

