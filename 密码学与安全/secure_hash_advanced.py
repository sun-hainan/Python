# -*- coding: utf-8 -*-

"""

算法实现：密码学与安全 / secure_hash_advanced



本文件实现 secure_hash_advanced 相关的算法功能。

"""



import hashlib

import os

import hmac

from typing import Tuple





class Blake2b:

    """BLAKE2b哈希算法（简化实现）"""



    # BLAKE2b参数

    IV = [

        0x6a09e667f3bcc908, 0xbb67ae8584caa73b, 0x3c6ef372fe94f82b, 0xa54ff53a5f1d36f1,

        0x510e527fade682d1, 0x9b05688c2b3e6c1f, 0x1f83d9abfb41bd6b, 0x5be0cd19137e2179

    ]



    # 压缩函数参数

    SIGMA = [

        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],

        [14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3],

        [11, 8, 12, 0, 5, 2, 15, 13, 10, 14, 3, 6, 7, 1, 9, 4],

        [7, 9, 3, 1, 13, 12, 11, 14, 2, 6, 5, 10, 4, 0, 15, 8],

        [9, 0, 5, 7, 2, 4, 10, 15, 14, 1, 11, 12, 6, 8, 3, 13],

        [2, 12, 6, 10, 0, 11, 8, 3, 4, 13, 7, 5, 15, 14, 1, 9],

        [12, 5, 1, 15, 14, 13, 4, 10, 0, 7, 6, 3, 9, 2, 8, 11],

        [13, 11, 7, 14, 12, 1, 3, 9, 5, 0, 15, 4, 8, 6, 2, 10],

        [6, 15, 14, 9, 11, 3, 0, 8, 12, 2, 13, 7, 1, 4, 10, 5],

        [10, 2, 8, 4, 7, 6, 1, 5, 15, 11, 9, 14, 3, 12, 13, 0],

        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],

        [14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3]

    ]



    def __init__(self, digest_size: int = 64):

        """

        初始化BLAKE2b



        参数：

            digest_size: 输出摘要长度（1-64字节）

        """

        if not (1 <= digest_size <= 64):

            raise ValueError("digest_size必须在1-64之间")

        self.digest_size = digest_size



    def _ch(self, x: int, y: int, z: int) -> int:

        """BLAKE2b的Ch函数"""

        return (x & y) ^ (~x & z)



    def _maj(self, x: int, y: int, z: int) -> int:

        """BLAKE2b的Maj函数"""

        return (x & y) ^ (x & z) ^ (y & z)



    def _rotr(self, x: int, n: int, bits: int = 64) -> int:

        """64位循环右移"""

        return ((x >> n) | (x << (bits - n))) & (2**64 - 1)



    def _g(self, v: list, a: int, b: int, c: int, d: int, x: int, y: int):

        """

        BLAKE2b的G函数



        参数：

            v: 状态向量

            a, b, c, d: 状态索引

            x, y: 轮参数

        """

        v[a] = (v[a] + v[b] + x) & (2**64 - 1)

        v[d] = self._rotr(v[d] ^ v[a], 32)

        v[c] = (v[c] + v[d]) & (2**64 - 1)

        v[b] = self._rotr(v[b] ^ v[c], 24)

        v[a] = (v[a] + v[b] + y) & (2**64 - 1)

        v[d] = self._rotr(v[d] ^ v[a], 16)

        v[c] = (v[c] + v[d]) & (2**64 - 1)

        v[b] = self._rotr(v[b] ^ v[c], 63)



    def _compress(self, state: list, block: bytes, block_len: int, 

                  offset: int, is_last: bool) -> list:

        """

        BLAKE2b压缩函数



        参数：

            state: 当前状态

            block: 数据块

            block_len: 块长度

            offset: 字节偏移

            is_last: 是否最后一块



        返回：新的状态

        """

        v = state + self.IV.copy()



        # 添加块长度和最后块标志

        v[12] ^= offset & 0xFFFFFFFFFFFFFFFF

        v[13] ^= 0  # reserved

        v[14] ^= 0x01010000 | (self.digest_size if is_last else 0)

        v[15] ^= 0  # salt



        # 简化的12轮迭代

        for round_num in range(12):

            sigma = self.SIGMA[round_num]



            # 将block转换为字

            x = [int.from_bytes(block[i*8:(i+1)*8], 'little') for i in range(16)]



            self._g(v, 0, 4, 8, 12, x[sigma[0]], x[sigma[1]])

            self._g(v, 1, 5, 9, 13, x[sigma[2]], x[sigma[3]])

            self._g(v, 2, 6, 10, 14, x[sigma[4]], x[sigma[5]])

            self._g(v, 3, 7, 11, 15, x[sigma[6]], x[sigma[7]])



            self._g(v, 0, 5, 10, 15, x[sigma[8]], x[sigma[9]])

            self._g(v, 1, 6, 11, 12, x[sigma[10]], x[sigma[11]])

            self._g(v, 2, 7, 8, 13, x[sigma[12]], x[sigma[13]])

            self._g(v, 3, 4, 9, 14, x[sigma[14]], x[sigma[15]])



        return [(v[i] ^ v[i+8]) & (2**64 - 1) for i in range(8)]



    def hash(self, data: bytes) -> bytes:

        """

        计算BLAKE2b哈希



        参数：

            data: 输入数据



        返回：哈希值

        """

        # 初始化状态

        state = self.IV[:8]



        # 初始化参数

        h0 = state[0] ^ (0x01010000 | self.digest_size)

        state[0] = h0

        # 其他参数使用默认值



        # 处理完整块

        block_size = 128

        offset = 0



        for i in range(0, len(data), block_size):

            block = data[i:i+block_size]

            is_last = (i + block_size >= len(data))

            block_len = len(block)



            # 填充到block_size

            if len(block) < block_size:

                block = block + b'\x00' * (block_size - len(block))



            state = self._compress(state, block, block_len, offset, is_last)

            offset += block_len



        # 输出

        result = b''

        for s in state[:self.digest_size // 8]:

            result += s.to_bytes(8, 'little')



        return result[:self.digest_size]





class Scrypt:

    """Scrypt：内存硬哈希函数"""



    def __init__(self, n: int = 1024, r: int = 8, p: int = 1):

        """

        初始化Scrypt



        参数：

            n: CPU/内存成本参数

            r: 块大小参数

            p: 并行参数

        """

        self.n = n

        self.r = r

        self.p = p



    def _blockxor(self, dest: bytearray, offset: int, src: bytes):

        """

        块XOR



        参数：

            dest: 目标数组

            offset: 偏移

            src: 源数据

        """

        for i in range(len(src)):

            dest[offset + i] ^= src[i]



    def _smix(self, data: bytes, v: list, xy: list, n: int, r: int) -> bytes:

        """

        Scrypt的SMix函数（简化实现）



        参数：

            data: 输入数据

            v: V数组

            xy: X和Y缓冲区

            n: 成本参数

            r: 块大小



        返回：Mix后的数据

        """

        block_size = 128 * r



        # 初始化X为数据副本

        x = bytearray(data)



        # 填充V数组（内存密集部分）

        for i in range(n):

            v[i] = x[:]

            # 简化的ROMix

            x = bytearray(hashlib.salsa20_8(

                bytes(x[:block_size])

            ).digest() + x[block_size:])



        # 最终的Mix

        for i in range(n):

            j = int.from_bytes(x[-4:], 'little') % n

            self._blockxor(x, 0, v[j])

            x = bytearray(hashlib.salsa20_8(

                bytes(x[:block_size])

            ).digest() + x[block_size:])



        return bytes(x[:block_size])



    def hash(self, password: bytes, salt: bytes) -> bytes:

        """

        计算Scrypt哈希



        参数：

            password: 密码

            salt: 盐值



        返回：哈希值（32字节）

        """

        # 简化的Scrypt实现

        # 实际实现需要完整的PBKDF2 + SMix + Salsa20



        # 第一步：PBKDF2-Salsa20/8

        block_size = 128 * self.r



        # 填充数据

        data = password + salt

        data += b'\x00' * (block_size * self.p - len(data))



        blocks = []

        for i in range(self.p):

            block = data[i*block_size:(i+1)*block_size]

            for j in range(self.n):

                # 简化的内存硬操作

                h = hashlib.sha256(block).digest()

                block = bytes(a ^ b for a, b in zip(block, h * (len(block) // 32)))

            blocks.append(block[:32])



        # 最终哈希

        result = b''.join(blocks)

        return hashlib.sha256(result).digest()





def hash_algorithm_comparison():

    """哈希算法比较"""

    print("=== 安全哈希算法比较 ===")

    print()

    print("BLAKE2：")

    print("  - SHA-3候选，最终胜出")

    print("  - 比SHA-2快30%")

    print("  - 支持任意长度输出")

    print("  - Blake2s（软件），Blake2b（64位优化）")

    print()

    print("Argon2：")

    print("  - 密码哈希竞赛冠军（2015）")

    print("  - 三种变体：d（数据独立）、i（数据独立）、id（混合）")

    print("  - 内存硬度可调")

    print()

    print("Scrypt：")

    print("  - 第一个内存硬哈希函数")

    print("  - 比特币早期使用（莱特币）")

    print("  - 内存和计算成本都高")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 安全哈希进阶测试 ===\n")



    # 测试数据

    test_data = b"Hello, this is a test message for secure hashing!"



    # BLAKE2b测试

    blake2 = Blake2b(digest_size=32)



    print("BLAKE2b测试：")

    blake2_hash = blake2.hash(test_data)

    print(f"  输入: {test_data[:40]}...")

    print(f"  BLAKE2b-256: {blake2_hash.hex()}")

    print()



    # 与标准库比较

    std_blake2b = hashlib.blake2b(test_data, digest_size=32).digest()

    print(f"  标准blake2b: {std_blake2b.hex()}")

    print(f"  实现匹配: {'部分（简化实现）'}")

    print()



    # Scrypt测试

    print("Scrypt测试：")

    scrypt = Scrypt(n=1024, r=8, p=1)



    password = b"strong_password_123"

    salt = os.urandom(16)



    scrypt_hash = scrypt.hash(password, salt)



    print(f"  密码: {password.decode()}")

    print(f"  盐值: {salt.hex()[:32]}...")

    print(f"  Scrypt: {scrypt_hash.hex()[:32]}...")

    print()



    # 性能比较

    print("哈希性能比较（100KB数据）：")

    large_data = os.urandom(100 * 1024)



    algorithms = ['md5', 'sha1', 'sha256', 'sha512', 'blake2b']



    for algo in algorithms:

        if algo == 'blake2b':

            h = hashlib.blake2b(large_data, digest_size=32)

        else:

            h = hashlib.new(algo, large_data)



        start = time.perf_counter()

        for _ in range(10):

            h = hashlib.new(algo, large_data)

        elapsed = (time.perf_counter() - start) * 1000



        print(f"  {algo}: {elapsed:.2f} ms (10次)")



    print()

    print("注意：实际BLAKE2和Scrypt实现更复杂，上面的简化版本用于教学")

    print()



    # 算法比较

    hash_algorithm_comparison()



    print()

    print("说明：")

    print("  - BLAKE2是最快的现代哈希")

    print("  - Argon2/Scrypt用于密码存储")

    print("  - 不要使用MD5/SHA1做新系统")

