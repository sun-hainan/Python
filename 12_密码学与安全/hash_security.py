# -*- coding: utf-8 -*-
"""
算法实现：12_密码学与安全 / hash_security

本文件实现 hash_security 相关的算法功能。
"""

import hashlib
import random


class HashSecurityAnalyzer:
    """Hash安全分析器"""

    def __init__(self, hash_func: str = "sha256"):
        """
        参数：
            hash_func: Hash函数名称
        """
        self.hash_func = hash_func

    def compute_hash(self, data: bytes) -> str:
        """
        计算哈希

        返回：十六进制哈希值
        """
        if self.hash_func == "sha256":
            return hashlib.sha256(data).hexdigest()
        elif self.hash_func == "sha3":
            return hashlib.sha3_256(data).hexdigest()
        elif self.hash_func == "md5":
            return hashlib.md5(data).hexdigest()
        else:
            return hashlib.sha256(data).hexdigest()

    def preimage_attack(self, target_hash: str, search_space: List[bytes]) -> tuple:
        """
        原像攻击测试

        参数：
            target_hash: 目标哈希
            search_space: 搜索空间

        返回：(是否找到, 找到的输入)
        """
        for data in search_space:
            if self.compute_hash(data) == target_hash:
                return True, data

        return False, None

    def collision_search(self, n_samples: int = 10000) -> float:
        """
        碰撞搜索

        参数：
            n_samples: 样本数

        返回：找到的碰撞对数
        """
        hashes = {}
        collisions = 0

        for _ in range(n_samples):
            data = random.randbytes(32)
            h = self.compute_hash(data)

            if h in hashes:
                collisions += 1
            else:
                hashes[h] = data

        return collisions

    def evaluate_security(self) -> dict:
        """
        评估安全性

        返回：安全评估报告
        """
        # 简化安全评估
        bits = {
            'sha256': 256,
            'sha3_256': 256,
            'md5': 128,
            'sha1': 160
        }.get(self.hash_func, 256)

        return {
            'hash_function': self.hash_func,
            'output_bits': bits,
            'preimage_resistance': '强' if bits >= 128 else '中',
            'second_preimage_resistance': '强' if bits >= 128 else '中',
            'collision_resistance': '强' if bits >= 256 else '中'
        }


def hash_attack_methods():
    """Hash攻击方法"""
    print("=== Hash攻击方法 ===")
    print()
    print("1. 暴力攻击")
    print("   - 尝试所有可能的输入")
    print("   - 复杂度 2^n")
    print()
    print("2. 生日攻击")
    print("   - 利用生日悖论")
    print("   - 复杂度 O(2^{n/2})")
    print()
    print("3. 彩虹表")
    print("   - 预计算哈希表")
    print("   - 空间换时间")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== Hash安全分析 ===\n")

    analyzer = HashSecurityAnalyzer("sha256")

    # 计算哈希
    data = b"Hello, Hash Function!"
    h = analyzer.compute_hash(data)

    print(f"数据: {data}")
    print(f"哈希: {h}")
    print()

    # 安全评估
    report = analyzer.evaluate_security()

    print("SHA-256安全评估：")
    for key, value in report.items():
        print(f"  {key}: {value}")

    print()

    # 碰撞搜索
    n_collisions = analyzer.collision_search(10000)

    print(f"碰撞搜索（10000样本）：找到 {n_collisions} 个碰撞")
    print(f"理论期望：~0.02（如果输出足够大）")

    print()
    hash_attack_methods()

    print()
    print("说明：")
    print("  - SHA-256目前是安全的")
    print("  - MD5和SHA-1已有已知攻击")
    print("  - 选择合适的哈希函数很重要")
