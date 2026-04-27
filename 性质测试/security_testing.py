# -*- coding: utf-8 -*-
"""
算法实现：性质测试 / security_testing

本文件实现 security_testing 相关的算法功能。
"""

import random
from typing import List, Tuple


class SecurityTester:
    """安全性测试器"""

    def __init__(self, crypto_system):
        """
        参数：
            crypto_system: 密码系统
        """
        self.crypto = crypto_system

    def brute_force_attack(self, ciphertext: bytes,
                          max_key: int = 1000000) -> Tuple[bool, int]:
        """
        暴力攻击

        返回：(是否成功, 密钥)
        """
        for key in range(max_key):
            try:
                plaintext = self.crypto.decrypt(ciphertext, key)
                # 检查是否有意义（简化）
                if self._is_sensible(plaintext):
                    return True, key
            except:
                pass

        return False, -1

    def _is_sensible(self, plaintext: bytes) -> bool:
        """检查明文是否有意义"""
        if not plaintext:
            return False

        # 简化：检查可打印字符比例
        printable = sum(1 for b in plaintext if 32 <= b <= 126)
        return printable / len(plaintext) > 0.8

    def known_plaintext_attack(self, plaintext: bytes,
                              ciphertext: bytes) -> List[int]:
        """
        已知明文攻击

        返回：可能的密钥列表
        """
        possible_keys = []

        # 简化：假设密钥是简单的XOR
        if len(plaintext) == len(ciphertext):
            key = bytes(p ^ c for p, c in zip(plaintext, ciphertext))
            possible_keys.append(key)

        return possible_keys


def chosen_plaintext_attack():
    """选择明文攻击"""
    print("=== 选择明文攻击 ===")
    print()
    print("CPA模型：")
    print("  - 攻击者可以获取任意明文的密文")
    print("  - 判断是否语义安全")
    print()
    print("IND-CPA安全：")
    print("  - 即使攻击者选择明文")
    print("  - 也无法区分两个消息的密文")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 安全性测试 ===\n")

    class SimpleXOR:
        def __init__(self, key):
            self.key = key

        def encrypt(self, plaintext: bytes, key=None) -> bytes:
            k = key if key else self.key
            return bytes(b ^ (k >> (i % 8) & 1) for i, b in enumerate(plaintext))

        def decrypt(self, ciphertext: bytes, key=None) -> bytes:
            return self.encrypt(ciphertext, key)

    # 创建密码系统
    key = 42
    crypto = SimpleXOR(key)

    # 加密
    plaintext = b"Hello, World!"
    ciphertext = crypto.encrypt(plaintext)

    print(f"明文: {plaintext}")
    print(f"密文: {ciphertext}")
    print()

    # 安全性测试
    tester = SecurityTester(crypto)

    success, found_key = tester.brute_force_attack(ciphertext, max_key=100)
    print(f"暴力攻击: {'成功' if success else '失败'}")
    print(f"找到密钥: {found_key}")

    print()
    chosen_plaintext_attack()

    print()
    print("说明：")
    print("  - 安全性测试评估密码系统强度")
    print("  - 现代密码学基于计算安全")
    print("  - 需要抵抗已知攻击类型")
