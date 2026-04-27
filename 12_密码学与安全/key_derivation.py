# -*- coding: utf-8 -*-

"""

算法实现：密码学与安全 / key_derivation



本文件实现 key_derivation 相关的算法功能。

"""



import hmac

import hashlib

import os

from typing import Tuple





class HKDF:

    """HMAC-based Key Derivation Function"""



    def __init__(self, hash_func: str = "sha256"):

        """

        初始化HKDF



        参数：

            hash_func: 哈希函数（sha256/sha512）

        """

        self.hash_func = hash_func

        self.hash_len = 32 if hash_func == "sha256" else 64



    def _hmac(self, key: bytes, data: bytes) -> bytes:

        """

        计算HMAC



        参数：

            key: HMAC密钥

            data: HMAC数据



        返回：HMAC输出

        """

        return hmac.new(key, data, hashlib.new(self.hash_func)).digest()



    def extract(self, salt: bytes, ikm: bytes) -> bytes:

        """

        HKDF提取：从不完整密钥材料提取伪随机密钥



        参数：

            salt: 盐值（可选，默认为全0）

            ikm: 输入密钥材料



        返回：伪随机密钥(PRK)

        """

        if not salt:

            salt = b'\x00' * self.hash_len



        prk = self._hmac(salt, ikm)

        return prk



    def expand(self, prk: bytes, info: bytes, length: int) -> bytes:

        """

        HKDF扩展：从PRK派生指定长度密钥



        参数：

            prk: 伪随机密钥

            info: 上下文信息

            length: 期望输出长度



        返回：派生的密钥

        """

        n = (length + self.hash_len - 1) // self.hash_len  # 需要的消息块数

        okm = b''



        t = b''

        for i in range(1, n + 1):

            t = self._hmac(prk, t + info + bytes([i]))

            okm += t



        return okm[:length]



    def derive(self, ikm: bytes, salt: bytes, info: bytes, length: int) -> bytes:

        """

        完整的HKDF流程



        参数：

            ikm: 输入密钥材料

            salt: 盐值

            info: 上下文信息

            length: 输出长度



        返回：派生的密钥

        """

        prk = self.extract(salt, ikm)

        okm = self.expand(prk, info, length)

        return okm





class Argon2Simple:

    """简化的Argon2（用于演示）"""



    def __init__(self, time_cost: int = 1, memory_cost: int = 4096, parallelism: int = 1):

        """

        初始化Argon2参数



        参数：

            time_cost: 时间成本（迭代次数）

            memory_cost: 内存成本（KB）

            parallelism: 并行度

        """

        self.time_cost = time_cost

        self.memory_cost = memory_cost

        self.parallelism = parallelism



    def hash(self, password: bytes, salt: bytes) -> bytes:

        """

        简化的Argon2哈希



        参数：

            password: 密码

            salt: 盐值



        返回：哈希值

        """

        # 简化的内存填充和迭代

        block_size = 1024

        memory_blocks = self.memory_cost // block_size



        # 初始化内存块

        blocks = []

        for i in range(memory_blocks):

            initial = hashlib.sha256(salt + password + bytes([i])).digest()

            blocks.append(initial)



        # 时间和内存迭代

        for iteration in range(self.time_cost):

            for i in range(memory_blocks):

                # 简化：依赖于前一个块

                prev = blocks[(i - 1) % memory_blocks]

                current = blocks[i]



                # 混合操作

                mixed = hashlib.sha256(prev + current + bytes([iteration])).digest()



                # 简化：仅更新部分块

                if i % 10 == 0:

                    blocks[i] = mixed



        # 最终哈希

        final_input = b''.join(blocks[:8])  # 取前8块

        return hashlib.sha256(final_input).digest()



    def verify(self, password: bytes, salt: bytes, expected: bytes) -> bool:

        """

        验证Argon2哈希



        参数：

            password: 密码

            salt: 盐值

            expected: 期望的哈希



        返回：是否匹配

        """

        computed = self.hash(password, salt)

        return hmac.compare_digest(computed, expected)





def kdf_usage_scenarios():

    """KDF使用场景"""

    print("=== KDF使用场景 ===")

    print()

    print("1. TLS/SSL密钥交换")

    print("   - 从DH共享秘密派生会话密钥")

    print()

    print("2. 密码存储")

    print("   - Argon2/PBKDF2存储密码哈希")

    print()

    print("3. 密钥分裂")

    print("   - 从主密钥派生多个子密钥")

    print()

    print("4. 密钥更新")

    print("   - 定期更新而不需要重新协商")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 密钥派生函数测试 ===\n")



    # HKDF测试

    hkdf = HKDF("sha256")



    # 模拟DH共享秘密

    shared_secret = os.urandom(32)

    salt = os.urandom(32)

    info = b"session_key_v1"



    # 派生128字节密钥

    derived_key = hkdf.derive(shared_secret, salt, info, 128)



    print("HKDF测试：")

    print(f"  输入密钥材料: {shared_secret.hex()[:32]}...")

    print(f"  派生密钥: {derived_key.hex()[:32]}...")

    print(f"  派生密钥长度: {len(derived_key)} 字节")

    print()



    # Argon2测试

    argon2 = Argon2Simple(time_cost=1, memory_cost=4096)



    password = b"secure_password_123"

    salt = os.urandom(16)



    argon2_hash = argon2.hash(password, salt)



    print("Argon2测试：")

    print(f"  密码: {password.decode()}")

    print(f"  哈希: {argon2_hash.hex()}")

    print()



    # 验证

    valid = argon2.verify(password, salt, argon2_hash)

    print(f"密码验证: {'通过' if valid else '失败'}")

    print()



    # 使用场景

    kdf_usage_scenarios()



    print()

    print("说明：")

    print("  - HKDF适合从熵源派生密钥")

    print("  - Argon2适合密码存储")

    print("  - 两者都是NIST推荐")

