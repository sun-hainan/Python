# -*- coding: utf-8 -*-
"""
算法实现：密码学与安全 / lightweight_simon_speck

本文件实现 lightweight_simon_speck 相关的算法功能。
"""

import binascii
from typing import Tuple


class SIMON:
    """SIMON轻量级块密码"""

    # 循环左移量
    R_1 = 1
    R_2 = 8
    R_3 = 2

    def __init__(self, key: bytes):
        """
        初始化SIMON

        参数：
            key: 密钥（12字节=96位，或16字节=128位）
        """
        key_len = len(key)
        if key_len not in (12, 16):
            raise ValueError("SIMON密钥必须是96位(12字节)或128位(16字节)")

        self.key = key
        self.key_len = key_len * 8  # 位数
        self.round_keys = self._key_expansion()

    def _rot_left(self, x: int, n: int, bits: int = 16) -> int:
        """
        循环左移

        参数：
            x: 输入值
            n: 移位量
            bits: 位宽

        返回：循环左移后的值
        """
        x = x & ((1 << bits) - 1)
        return ((x << n) | (x >> (bits - n))) & ((1 << bits) - 1)

    def _f(self, x: int) -> int:
        """
        SIMON的F函数：x << 1 | x >> 8

        参数：
            x: 16位输入

        返回：F(x)
        """
        # 循环左移1和8位，然后异或
        return self._rot_left(x, self.R_1) ^ self._rot_left(x, self.R_2)

    def _key_expansion(self) -> list:
        """
        密钥扩展

        返回：轮密钥列表
        """
        k = []
        if self.key_len == 96:
            # 96位密钥：3个字
            for i in range(3):
                k.append(int.from_bytes(self.key[i*4:i*4+4], 'big'))
        else:
            # 128位密钥：4个字
            for i in range(4):
                k.append(int.from_bytes(self.key[i*4:i*4+4], 'big'))

        n = len(k)  # 密钥字数
        r = 42 if self.key_len == 96 else 44  # 64位块的轮数

        for i in range(n, r):
            # k[i] = (k[i-n] + f(k[i-1]) + c + i) mod 2^16
            # 其中c = 0xFFFF...（某个常数）
            k_i = (k[i-n] + self._f(k[i-1]) + 0xFFFF + i) & 0xFFFFFFFF
            k.append(k_i)

        return k[:r]

    def encrypt_block(self, plaintext: int) -> int:
        """
        加密单个64位块

        参数：
            plaintext: 64位明文

        返回：64位密文
        """
        # 分成两个16位字
        x = (plaintext >> 16) & 0xFFFF
        y = plaintext & 0xFFFF

        # 32轮Feistel结构
        for round_num in range(32):
            # x, y = y, x ^ f(y) ^ round_key
            new_x = y
            new_y = x ^ self._f(y) ^ self.round_keys[round_num]
            x, y = new_x, new_y

        # 合并
        return ((x << 16) | y) & 0xFFFFFFFFFFFFFFFF

    def decrypt_block(self, ciphertext: int) -> int:
        """
        解密单个64位块

        参数：
            ciphertext: 64位密文

        返回：64位明文
        """
        # 分成两个16位字
        x = (ciphertext >> 16) & 0xFFFF
        y = ciphertext & 0xFFFF

        # 反向32轮Feistel结构
        for round_num in range(31, -1, -1):
            # x = y_prev, y = x_prev ^ f(y_prev) ^ round_key
            new_y = x
            new_x = y ^ self._f(x) ^ self.round_keys[round_num]
            x, y = new_x, new_y

        return ((x << 16) | y) & 0xFFFFFFFFFFFFFFFF


class SPECK:
    """SPECK轻量级块密码"""

    def __init__(self, key: bytes):
        """
        初始化SPECK

        参数：
            key: 密钥（12字节=96位，或16字节=128位）
        """
        key_len = len(key)
        if key_len not in (12, 16):
            raise ValueError("SPECK密钥必须是96位(12字节)或128位(16字节)")

        self.key = key
        self.key_len = key_len * 8
        self.round_keys = self._key_expansion()

    def _rot_right(self, x: int, n: int, bits: int = 16) -> int:
        """
        循环右移

        参数：
            x: 输入值
            n: 移位量
            bits: 位宽

       返回：循环右移后的值
        """
        x = x & ((1 << bits) - 1)
        return ((x >> n) | (x << (bits - n))) & ((1 << bits) - 1)

    def _key_schedule_round(self, l: int, k: int, m: int) -> Tuple[int, int]:
        """
        密钥调度的单轮

        参数：
            l: L数组
            k: K值
            m: 轮数索引

        返回：(新的K, 新的L[m])
        """
        l_next = k
        k_next = (self._rot_right(l, 8) + k) ^ m
        return k_next, l_next

    def _key_expansion(self) -> list:
        """
        密钥扩展

        返回：轮密钥列表
        """
        if self.key_len == 96:
            k_len = 3
        else:
            k_len = 4

        # 初始化L和K
        k = []
        l = []

        for i in range(k_len):
            word = int.from_bytes(self.key[i*4:i*4+4], 'big')
            if i < k_len - 1:
                l.append(word)
            else:
                k.append(word)

        r = 26 if self.key_len == 96 else 27  # 64位块的轮数

        for i in range(r):
            m = i + 1
            k_i, l_i = self._key_schedule_round(l[0] if l else 0, k[0], m)
            k.insert(0, k_i)
            if l:
                l.pop(0)
            l.append(l_i)

        return k[:r]

    def encrypt_block(self, plaintext: int) -> int:
        """
        加密单个64位块

        参数：
            plaintext: 64位明文

        返回：64位密文
        """
        # 分成两个16位字
        x = (plaintext >> 16) & 0xFFFF
        y = plaintext & 0xFFFF

        # Feistel结构（与SIMON相反）
        for round_num in range(26 if self.key_len == 96 else 27):
            # x = (x >> 8 | x << 8) + y ^ round_key
            # y = x (rotate back)
            new_x = (self._rot_right(x, 8) + y) ^ self.round_keys[round_num]
            y = x
            x = new_x

        return ((x << 16) | y) & 0xFFFFFFFFFFFFFFFF


def simon_speck_comparison():
    """SIMON vs SPECK比较"""
    print("=== SIMON vs SPECK比较 ===")
    print()
    print("SIMON：")
    print("  - 硬件优化设计")
    print("  - 门数更少")
    print("  - 适合受限硬件")
    print()
    print("SPECK：")
    print("  - 软件优化设计")
    print("  - 速度更快")
    print("  - 适合微控制器")
    print()
    print("共同特点：")
    print("  - ARX结构（加法、循环移位、异或）")
    print("  - 抗侧信道（无查找表）")
    print("  - NSA设计，有争议")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== SIMON与SPECK轻量级密码测试 ===\n")

    # SIMON测试
    simon_key = b'\x00' * 12  # 96位零密钥
    simon = SIMON(simon_key)

    plaintext = 0x0123456789ABCDEF

    ciphertext = simon.encrypt_block(plaintext)
    decrypted = simon.decrypt_block(ciphertext)

    print("SIMON 64/96测试：")
    print(f"  明文: {hex(plaintext)}")
    print(f"  密文: {hex(ciphertext)}")
    print(f"  解密: {hex(decrypted)}")
    print(f"  往返正确: {'是' if decrypted == plaintext else '否'}")
    print()

    # SPECK测试
    speck_key = b'\x00' * 12  # 96位零密钥
    speck = SPECK(speck_key)

    speck_ct = speck.encrypt_block(plaintext)

    print("SPECK 64/96测试：")
    print(f"  明文: {hex(plaintext)}")
    print(f"  密文: {hex(speck_ct)}")
    print()

    # 比较
    simon_speck_comparison()

    print()
    print("说明：")
    print("  - SIMON/SPECK是NSA的轻量级密码标准")
    print("  - 适合IoT和嵌入式设备")
    print("  - 软件和硬件各有优势")
    print("  - 存在一些关于后门的争议")
