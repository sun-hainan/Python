# -*- coding: utf-8 -*-
"""
算法实现：安全多方计算 / private_set_intersection

本文件实现 private_set_intersection 相关的算法功能。
"""

import random
import hashlib
from typing import List, Set


class PrivateSetIntersection:
    """隐私集合交集"""

    def __init__(self, security_bits: int = 256):
        """
        参数：
            security_bits: 安全参数
        """
        self.security = security_bits

    def rsa_psi(self, set_a: List[str], set_b: List[str]) -> int:
        """
        基于RSA的PSI

        参数：
            set_a: 集合A
            set_b: 集合B

        返回：交集大小
        """
        # 简化：用哈希
        hash_a = set(hashlib.sha256(x.encode()).digest() for x in set_a)
        hash_b = set(hashlib.sha256(x.encode()).digest() for x in set_b)

        return len(hash_a & hash_b)

    def encrypted_psi(self, set_a: List[str], set_b: List[str]) -> List[str]:
        """
        加密PSI（返回交集元素）

        参数：
            set_a: 集合A
            set_b: 集合B

        返回：交集元素
        """
        # 两方PSI简化版本
        # 实际需要复杂的多方计算

        # 简单方法：交换哈希
        hash_a = {x: hashlib.sha256(x.encode()).hexdigest() for x in set_a}

        intersection = []
        for x in set_b:
            h_x = hashlib.sha256(x.encode()).hexdigest()
            if h_x in hash_a.values():
                intersection.append(x)

        return intersection

    def bloom_filter_psi(self, set_a: List[str], set_b: List[str],
                        bloom_size: int = 1000) -> int:
        """
        基于Bloom Filter的PSI

        参数：
            set_a: 集合A
            set_b: 集合B
            bloom_size: Bloom过滤器大小

        返回：估计的交集大小
        """
        # 构建A的Bloom过滤器
        bloom = [0] * bloom_size

        for x in set_a:
            h1 = int(hashlib.md5(x.encode()).hexdigest(), 16) % bloom_size
            h2 = int(hashlib.sha1(x.encode()).hexdigest(), 16) % bloom_size

            bloom[h1] = 1
            bloom[h2] = 1

        # 检查B中的元素
        matches = 0
        for x in set_b:
            h1 = int(hashlib.md5(x.encode()).hexdigest(), 16) % bloom_size
            h2 = int(hashlib.sha1(x.encode()).hexdigest(), 16) % bloom_size

            if bloom[h1] and bloom[h2]:
                matches += 1

        return matches


def psi_applications():
    """PSI应用"""
    print("=== PSI应用 ===")
    print()
    print("1. 联系人发现")
    print("   - 发现两个服务间共同联系人")
    print("   - 不暴露其他联系人")
    print()
    print("2. 隐私广告")
    print("   - 确定两个集合的交集")
    print("   - 用于定向广告")
    print()
    print("3. 联邦学习")
    print("   - 找到数据相似的客户端")
    print("   - 保护隐私")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 隐私集合交集测试 ===\n")

    psi = PrivateSetIntersection()

    # 集合
    set_a = ["alice@example.com", "bob@example.com", "charlie@example.com",
             "dave@example.com", "eve@example.com"]
    set_b = ["bob@example.com", "charlie@example.com",
             "frank@example.com", "grace@example.com"]

    print(f"集合A: {len(set_a)} 个元素")
    print(f"集合B: {len(set_b)} 个元素")
    print()

    # RSA PSI
    size = psi.rsa_psi(set_a, set_b)
    print(f"RSA PSI: 交集大小 = {size}")
    print(f"真实交集: {len(set(set_a) & set(set_b))}")
    print()

    # 加密PSI
    intersection = psi.encrypted_psi(set_a, set_b)
    print(f"加密PSI: {intersection}")

    # Bloom Filter PSI
    bf_size = psi.bloom_filter_psi(set_a, set_b, bloom_size=100)
    print(f"\nBloom Filter PSI: 估计交集 = {bf_size}")

    print()
    psi_applications()

    print()
    print("说明：")
    print("  - PSI用于安全计算集合交集")
    print("  - 应用于联系人发现、联邦学习")
    print("  - 多种实现方式各有权衡")
