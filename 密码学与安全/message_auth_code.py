# -*- coding: utf-8 -*-
"""
算法实现：密码学与安全 / message_auth_code

本文件实现 message_auth_code 相关的算法功能。
"""

import hmac
import hashlib
from typing import Union


class HMACImplementation:
    """HMAC实现"""

    def __init__(self, hash_func: str = "sha256"):
        """
        初始化HMAC

        参数：
            hash_func: 哈希函数（md5/sha1/sha256/sha512）
        """
        self.hash_func = hash_func
        self.block_sizes = {
            'md5': 64,
            'sha1': 64,
            'sha256': 64,
            'sha512': 128
        }
        self.hash_len = hashlib.new(hash_func).digest_size

    def _pad_key(self, key: bytes) -> bytes:
        """
        填充或扩展密钥到块大小

        参数：
            key: 原始密钥

        返回：填充后的密钥
        """
        block_size = self.block_sizes[self.hash_func]

        if len(key) > block_size:
            # 密钥太长：先哈希
            key = hashlib.new(self.hash_func, key).digest()

        if len(key) < block_size:
            # 密钥太短：填充0
            key = key + b'\x00' * (block_size - len(key))

        return key

    def compute(self, key: bytes, message: bytes) -> bytes:
        """
        计算HMAC

        公式：HMAC(K, m) = H((K' ⊕ opad) || H((K' ⊕ ipad) || m))

        参数：
            key: 认证密钥
            message: 待认证消息

        返回：HMAC值
        """
        block_size = self.block_sizes[self.hash_func]

        # 填充密钥
        k = self._pad_key(key)

        # 内部填充（ipad = 0x36）
        ipad = b'\x36' * block_size
        k_ipad = bytes(k[i] ^ ipad[i] for i in range(block_size))

        # 外部填充（opad = 0x5c）
        opad = b'\x5c' * block_size
        k_opad = bytes(k[i] ^ opad[i] for i in range(block_size))

        # 内层哈希
        inner_hash = hashlib.new(self.hash_func, k_ipad + message).digest()

        # 外层哈希
        outer_hash = hashlib.new(self.hash_func, k_opad + inner_hash).digest()

        return outer_hash

    def verify(self, key: bytes, message: bytes, mac: bytes) -> bool:
        """
        验证HMAC

        参数：
            key: 认证密钥
            message: 待验证消息
            mac: 期望的MAC值

        返回：验证结果
        """
        computed_mac = self.compute(key, message)
        return hmac.compare_digest(computed_mac, mac)


class CMACImplementation:
    """CMAC（CBC-MAC变体）实现"""

    def __init__(self, key: bytes):
        """
        初始化CMAC

        参数：
            key: AES密钥（16/24/32字节）
        """
        if len(key) not in (16, 24, 32):
            raise ValueError("AES密钥长度必须是16/24/32字节")

        self.key = key
        self.block_size = 16  # AES块大小

    def _aes_encrypt(self, block: bytes) -> bytes:
        """
        AES加密单个块（简化实现）

        参数：
            block: 16字节明文块

        返回：16字节密文块
        """
        # 简化：使用密文的CBC模式
        # 实际使用AES加密
        import os
        # 这里用XOR模拟，实际需要AES实现
        return bytes(block[i] ^ self.key[i] ^ os.urandom(1)[0] for i in range(16))

    def _xor_bytes(self, a: bytes, b: bytes) -> bytes:
        """
        字节异或

        参数：
            a: 第一个字节串
            b: 第二个字节串

        返回：异或结果
        """
        return bytes(a[i] ^ b[i] for i in range(len(a)))

    def _pad_message(self, message: bytes) -> list:
        """
        PKCS7填充

        参数：
            message: 原始消息

        返回：填充后的块列表
        """
        # 消息分块
        blocks = []
        for i in range(0, len(message), self.block_size):
            block = message[i:i + self.block_size]

            if len(block) == self.block_size:
                blocks.append(block)
            else:
                # 需要填充
                padded = block + b'\x80' + b'\x00' * (self.block_size - len(block) - 1)
                blocks.append(padded)

        return blocks

    def compute(self, message: bytes) -> bytes:
        """
        计算CMAC

        参数：
            message: 待认证消息

        返回：CMAC值（最后一个密文块）
        """
        blocks = self._pad_message(message)

        prev_ct = b'\x00' * self.block_size  # 初始向量

        for i, block in enumerate(blocks):
            is_last = (i == len(blocks) - 1)

            if is_last:
                # 最后一个块：与子密钥K1异或
                # 简化：直接处理
                block = self._xor_bytes(block, b'\x00' * self.block_size)

            # CBC模式：明文与前一个密文异或后再加密
            xored = self._xor_bytes(prev_ct, block)
            # 简化：用XOR模拟加密
            ct = self._xor_bytes(xored, self.key)
            prev_ct = ct

        return prev_ct

    def verify(self, message: bytes, expected_mac: bytes) -> bool:
        """
        验证CMAC

        参数：
            message: 待验证消息
            expected_mac: 期望的MAC值

        返回：验证结果
        """
        computed_mac = self.compute(message)
        return hmac.compare_digest(computed_mac, expected_mac)


def mac_comparison():
    """MAC算法比较"""
    print("=== MAC算法比较 ===")
    print()
    print("HMAC：")
    print("  - 基于哈希函数（MD5/SHA系列）")
    print("  - 实现简单，依赖广泛")
    print("  - 适合任何哈希函数")
    print()
    print("CMAC：")
    print("  - 基于块密码（AES）")
    print("  - 更紧凑的输出")
    print("  - 需要块密码实现")
    print()
    print("GMAC（Galois/Counter Mode）：")
    print("  - 基于认证加密")
    print("  - 支持加密和认证")
    print("  - 如AES-GCM")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 消息认证码测试 ===\n")

    message = b"Hello, this is a secret message for authentication!"

    # HMAC测试
    hmac_impl = HMACImplementation("sha256")
    key = b'super_secret_key_1234567890'

    hmac_value = hmac_impl.compute(key, message)

    print("HMAC测试：")
    print(f"  消息: {message}")
    print(f"  HMAC: {hmac_value.hex()}")
    print(f"  验证: {'通过' if hmac_impl.verify(key, message, hmac_value) else '失败'}")
    print()

    # 使用标准hmac库验证
    std_hmac = hmac.new(key, message, hashlib.sha256).digest()
    print(f"标准库HMAC: {std_hmac.hex()}")
    print(f"实现一致: {'是' if hmac_value == std_hmac else '否'}")
    print()

    # CMAC测试
    aes_key = b'AES16bytekey123!'  # 16字节
    cmac_impl = CMACImplementation(aes_key)

    cmac_value = cmac_impl.compute(message)

    print("CMAC测试：")
    print(f"  消息: {message}")
    print(f"  CMAC: {cmac_value.hex()}")
    print(f"  验证: {'通过' if cmac_impl.verify(message, cmac_value) else '失败'}")
    print()

    # 篡改检测
    tampered = message + b'X'
    hmac_tampered = hmac_impl.compute(key, tampered)
    print("篡改检测：")
    print(f"  原始消息验证: {'通过' if hmac_impl.verify(key, message, hmac_value) else '失败'}")
    print(f"  篡改消息验证: {'通过' if hmac_impl.verify(key, tampered, hmac_value) else '失败'}")
    print()

    # 比较
    mac_comparison()

    print()
    print("说明：")
    print("  - MAC确保消息完整性和认证")
    print("  - 不能提供机密性（加密）")
    print("  - 配合加密使用时，如AES-GCM")
