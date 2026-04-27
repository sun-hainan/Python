# -*- coding: utf-8 -*-
"""
算法实现：密码学与安全 / password_security

本文件实现 password_security 相关的算法功能。
"""

import hashlib
import os
import time
from typing import List, Tuple, Dict, Set
from collections import defaultdict


class PasswordCracker:
    """密码破解器（用于教育和理解）"""

    def __init__(self):
        """初始化破解器"""
        self.common_passwords = self._load_common_passwords()

    def _load_common_passwords(self) -> List[str]:
        """
        加载常见密码列表

        返回：密码列表
        """
        # 简化的常见密码
        return [
            "123456", "password", "12345678", "qwerty", "abc123",
            "monkey", "1234567", "letmein", "trustno1", "dragon",
            "baseball", "iloveyou", "master", "sunshine", "ashley",
            "bailey", "passw0rd", "shadow", "123123", "654321",
            "superman", "qazwsx", "michael", "football", "password1",
            "password123", "welcome", "welcome1", "admin", "login",
            "hello", "charlie", "donald", "qwerty123", "password12",
            "1234", "abcd", "12345", "0000", "1111",
            "letmein1", "abc", "123456789", "1234567890", "pass",
            "test", "guest", "master123", "root", "toor",
            "p@ssw0rd", "p@ssword", "pass123", "pass1234"
        ]

    def brute_force(self, target_hash: str, charset: str, max_len: int,
                   hash_func: str = "md5") -> Tuple[bool, str, int]:
        """
        暴力破解

        参数：
            target_hash: 目标哈希
            charset: 字符集
            max_len: 最大长度
            hash_func: 哈希函数

        返回：(是否找到, 找到的密码, 尝试次数)
        """
        attempts = 0

        def generate_all(charset: str, length: int, prefix: str = ""):
            if length == 0:
                return [prefix]
            result = []
            for c in charset:
                result.extend(generate_all(charset, length - 1, prefix + c))
            return result

        for length in range(1, max_len + 1):
            for password in generate_all(charset, length):
                attempts += 1
                h = hashlib.new(hash_func, password.encode()).hexdigest()
                if h == target_hash:
                    return True, password, attempts

        return False, "", attempts

    def dictionary_attack(self, target_hash: str, hash_func: str = "md5") -> Tuple[bool, str, int]:
        """
        字典攻击

        参数：
            target_hash: 目标哈希
            hash_func: 哈希函数

        返回：(是否找到, 找到的密码, 尝试次数)
        """
        attempts = 0

        for password in self.common_passwords:
            attempts += 1
            h = hashlib.new(hash_func, password.encode()).hexdigest()
            if h == target_hash:
                return True, password, attempts

            # 常见变体
            for variant in [password + "123", password + "!", password.upper()]:
                attempts += 1
                h = hashlib.new(hash_func, variant.encode()).hexdigest()
                if h == target_hash:
                    return True, variant, attempts

        return False, "", attempts

    def rainbow_table_attack(self, target_hash: str, rainbow_table: Dict[str, str]) -> Tuple[bool, str]:
        """
        彩虹表攻击

        参数：
            target_hash: 目标哈希
            rainbow_table: 彩虹表

        返回：(是否找到, 找到的密码)
        """
        return target_hash in rainbow_table, rainbow_table.get(target_hash, "")

    def probabilistic_attack(self, password: str, hash_func: str = "md5") -> Tuple[bool, str, int]:
        """
        概率密码破解（基于字符频率）

        参数：
            password: 目标密码
            hash_func: 哈希函数

        返回：(是否找到, 找到的密码, 尝试次数)
        """
        # 简化：按常见程度排序字符
        char_freq = "etaoinsrhldcumfpgwybvkxjqz0123456789!@#$%^&*"
        attempts = 0

        # 生成按频率排序的密码
        def generate_by_freq(charset: str, length: int) -> str:
            if length == 0:
                return ""
            return charset[0] + generate_by_freq(charset, length - 1)

        target_hash = hashlib.new(hash_func, password.encode()).hexdigest()

        for length in range(1, len(password) + 1):
            guess = generate_by_freq(char_freq[:15], length)
            attempts += 1
            h = hashlib.new(hash_func, guess.encode()).hexdigest()
            if h == target_hash:
                return True, guess, attempts

        return False, "", attempts


class RainbowTable:
    """彩虹表生成"""

    def __init__(self, reduction_func: callable = None):
        """
        初始化彩虹表

        参数：
            reduction_func: 简化函数（哈希->候选密码）
        """
        self.chain_starts = {}
        self.chain_length = 100
        self.num_chains = 1000

        if reduction_func is None:
            self.reduction_func = self._default_reduction
        else:
            self.reduction_func = reduction_func

    def _default_reduction(self, hash_str: str, step: int) -> str:
        """
        默认简化函数

        参数：
            hash_str: 哈希字符串
            step: 链中的步骤

        返回：简化后的候选密码
        """
        charset = "abcdefghijklmnopqrstuvwxyz0123456789"
        result = ""
        for i in range(6):  # 生成6字符密码
            idx = (int(hash_str[i * 4:(i + 1) * 4], 16) + step) % len(charset)
            result += charset[idx]
        return result

    def _hash(self, password: str) -> str:
        """密码哈希"""
        return hashlib.md5(password.encode()).hexdigest()

    def generate_chain(self, start_password: str) -> Tuple[str, str]:
        """
        生成单条彩虹链

        参数：
            start_password: 起始密码

        返回：(起始密码, 终点哈希)
        """
        current = start_password
        for step in range(self.chain_length):
            h = self._hash(current)
            current = self.reduction_func(h, step)
        return start_password, self._hash(current)

    def generate_table(self) -> Dict[str, str]:
        """
        生成完整的彩虹表

        返回：终点哈希->起始密码的映射
        """
        table = {}

        for i in range(self.num_chains):
            start = f"start{i:04d}"  # 简化的起始点
            _, end_hash = self.generate_chain(start)
            table[end_hash] = start

        return table


class SaltedPasswordStorage:
    """盐值密码存储"""

    def __init__(self, hash_func: str = "sha256"):
        """
        初始化存储

       参数：
            hash_func: 哈希函数
        """
        self.hash_func = hash_func
        self.users = {}  # username -> {salt, hash}

    def hash_password(self, password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
        """
        哈希密码（带盐）

        参数：
            password: 明文密码
            salt: 盐值（如果为None则生成）

        返回：(盐值, 哈希值)
        """
        if salt is None:
            salt = os.urandom(16)

        salted = salt + password.encode()
        h = hashlib.new(self.hash_func, salted).digest()

        return salt, h

    def register_user(self, username: str, password: str) -> bool:
        """
        注册用户

        参数：
            username: 用户名
            password: 密码

        返回：是否成功
        """
        if username in self.users:
            return False

        salt, h = self.hash_password(password)
        self.users[username] = {
            'salt': salt.hex(),
            'hash': h.hex()
        }
        return True

    def verify_user(self, username: str, password: str) -> bool:
        """
        验证用户

        参数：
            username: 用户名
            password: 密码

        返回：验证结果
        """
        if username not in self.users:
            return False

        user = self.users[username]
        salt = bytes.fromhex(user['salt'])
        _, expected_hash = self.hash_password(password, salt)

        return expected_hash.hex() == user['hash']


def password_strength_rules():
    """密码强度规则"""
    print("=== 密码强度评估规则 ===")
    print()
    print("1. 长度评分")
    print("   - 8字符以下：弱")
    print("   - 12字符以上：强")
    print()
    print("2. 字符多样性")
    print("   - 大小写字母")
    print("   - 数字")
    print("   - 特殊字符")
    print()
    print("3. 禁止规则")
    print("   - 禁用常见密码")
    print("   - 禁用字典词")
    print("   - 禁用个人信息")
    print()
    print("4. 推荐方案")
    print("   - 密码短语（如 correct horse battery staple）")
    print("   - 或使用密码管理器")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 密码破解与防御测试 ===\n")

    # 创建破解器
    cracker = PasswordCracker()

    # 测试密码
    test_password = "password123"

    print(f"测试密码: {test_password}")
    print()

    # 字典攻击
    target_hash = hashlib.md5(test_password.encode()).hexdigest()
    print(f"MD5哈希: {target_hash}")

    found, cracked, attempts = cracker.dictionary_attack(target_hash, "md5")

    print()
    print("字典攻击：")
    print(f"  是否找到: {'是' if found else '否'}")
    if found:
        print(f"  破解的密码: {cracked}")
    print(f"  尝试次数: {attempts}")
    print()

    # 彩虹表攻击
    print("彩虹表攻击演示：")
    rainbow = RainbowTable()
    table = rainbow.generate_table()

    found_rt, cracked_rt = cracker.rainbow_table_attack(target_hash, table)
    print(f"  彩虹表大小: {len(table)} 条")
    print(f"  是否找到: {'是' if found_rt else '否'}")
    print()

    # 盐值保护演示
    print("盐值保护演示：")
    storage = SaltedPasswordStorage("sha256")

    # 注册用户
    storage.register_user("alice", "password123")
    storage.register_user("bob", "password123")  # 相同密码

    alice_data = storage.users["alice"]
    bob_data = storage.users["bob"]

    print(f"  Alice盐值: {alice_data['salt'][:16]}...")
    print(f"  Bob盐值:   {bob_data['salt'][:16]}...")
    print(f"  相同密码的哈希相同: {'是' if alice_data['hash'] == bob_data['hash'] else '否'}")
    print()

    # 验证
    print("用户验证：")
    print(f"  Alice正确密码: {'通过' if storage.verify_user('alice', 'password123') else '失败'}")
    print(f"  Alice错误密码: {'通过' if not storage.verify_user('alice', 'wrongpass') else '失败'}")
    print()

    # 密码强度
    password_strength_rules()

    print()
    print("说明：")
    print("  - 字典攻击效率最高（大多数密码很弱）")
    print("  - 彩虹表攻击利用预计算")
    print("  - 盐值使彩虹表失效")
    print("  - 慢哈希（bcrypt/argon2）增加攻击成本")
