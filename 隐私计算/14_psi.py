# -*- coding: utf-8 -*-
"""
算法实现：隐私计算 / 14_psi

本文件实现 14_psi 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Set, Dict
import hashlib


class SimplePSI:
    """
    简单PSI协议

    使用加密哈希实现,但不提供真正的隐私保护
    (仅用于理解原理)
    """

    def __init__(self):
        """初始化简单PSI"""
        pass

    def hash_set(self, dataset: Set[str]) -> Set[int]:
        """
        哈希集合元素

        Args:
            dataset: 字符串集合

        Returns:
            哈希值集合
        """
        return {self._hash(x) for x in dataset}

    def _hash(self, item: str) -> int:
        """哈希函数"""
        return int(hashlib.sha256(item.encode()).hexdigest()[:16], 16)

    def compute_intersection(self, set1: Set[str], set2: Set[str]) -> Set[str]:
        """
        计算交集

        Args:
            set1: 集合1
            set2: 集合2

        Returns:
            交集
        """
        hash1 = self.hash_set(set1)
        hash2 = self.hash_set(set2)
        common_hashes = hash1.intersection(hash2)

        # 简化: 直接返回哈希(实际需要映射回原值)
        return {f"hash_{h}" for h in common_hashes}


class DHPSI:
    """
    Diffie-Hellman PSI 协议

    基于DH密钥交换的PSI协议

    步骤:
    1. Alice对集合中每个元素计算 g^{H1(x)}
    2. Bob对集合中每个元素计算 g^{H2(x)}
    3. Alice使用私钥转换后发送回Bob
    4. Bob计算最终交集
    """

    def __init__(self, prime: int = None):
        """
        初始化DH-PSI

        Args:
            prime: 大素数
        """
        if prime is None:
            self.prime = (1 << 61) - 1  # Mersenne素数
        else:
            self.prime = prime

        np.random.seed(42)
        # 生成DH参数
        self.generator = 5

    def _hash_to_exponent(self, item: str) -> int:
        """将字符串哈希到指数"""
        h = int(hashlib.sha256(item.encode()).hexdigest(), 16)
        return h % (self.prime - 1) + 1

    def encode_set(self, dataset: Set[str]) -> List[int]:
        """
        编码集合

        Alice/Bob 各自编码自己的集合

        Args:
            dataset: 字符串集合

        Returns:
            编码后的列表
        """
        return [self._hash_to_exponent(x) for x in dataset]

    def alice_encode(self, encoded_set: List[int], private_key: int) -> List[int]:
        """
        Alice的编码

        A_i = (g^{a_i})^private_key mod p

        Args:
            encoded_set: 编码后的集合
            private_key: Alice的私钥

        Returns:
            Alice编码后的集合
        """
        return [pow(self.generator, x * private_key, self.prime) for x in encoded_set]

    def bob_encode(self, encoded_set: List[int], private_key: int) -> List[int]:
        """
        Bob的编码

        B_i = (g^{b_i})^private_key mod p

        Args:
            encoded_set: 编码后的集合
            private_key: Bob的私钥

        Returns:
            Bob编码后的集合
        """
        return [pow(self.generator, x * private_key, self.prime) for x in encoded_set]

    def bob_finalize(
        self,
        alice_encoded: List[int],
        bob_encoded: List[int],
        bob_private_key: int
    ) -> Set[int]:
        """
        Bob计算最终交集

        交集元素: (A_i)^{b} = (B_i)^{a} = g^{ab}

        Args:
            alice_encoded: Alice编码后的集合
            bob_encoded: Bob编码后的集合
            bob_private_key: Bob的私钥

        Returns:
            交集的编码
        """
        intersection = set()
        for a_val, b_val in zip(alice_encoded, bob_encoded):
            # A_i 是 g^{a*H_a}, Bob计算 (A_i)^b = g^{ab*H_a}
            # 需要检查是否匹配
            # 简化: 使用排序后的位置匹配
            pass

        # 简化的实现: 返回编码的交集
        return set([alice_encoded[i] for i in range(len(alice_encoded))
                   if alice_encoded[i] in bob_encoded])


class OBBalancedPSI:
    """
    基于不经意传输(OT)的平衡PSI

    利用OT协议实现更高效的PSI

    协议:
    1. 将元素映射到桶
    2. 使用OT在桶内寻找交集
    """

    def __init__(self, num_buckets: int = 100):
        """
        初始化OT-PSI

        Args:
            num_buckets: 桶数量
        """
        self.num_buckets = num_buckets

    def map_to_buckets(self, dataset: Set[str]) -> Dict[int, List[str]]:
        """
        将元素映射到桶

        Args:
            dataset: 数据集

        Returns:
            桶映射字典
        """
        buckets = {i: [] for i in range(self.num_buckets)}

        for item in dataset:
            bucket_idx = int(hashlib.md5(item.encode()).hexdigest()[:8], 16) % self.num_buckets
            buckets[bucket_idx].append(item)

        return buckets

    def compute_intersection_buckets(
        self,
        buckets1: Dict[int, List[str]],
        buckets2: Dict[int, List[str]]
    ) -> Set[str]:
        """
        计算桶级交集

        Args:
            buckets1: 集合1的桶
            buckets2: 集合2的桶

        Returns:
            交集
        """
        intersection = set()

        for bucket_id in range(self.num_buckets):
            items1 = set(buckets1.get(bucket_id, []))
            items2 = set(buckets2.get(bucket_id, []))
            intersection.update(items1.intersection(items2))

        return intersection


class BloomFilterPSI:
    """
    基于Bloom过滤器的PSI

    使用Bloom过滤器减少通信和计算成本

    步骤:
    1. Alice构建Bloom过滤器
    2. 发送过滤器给Bob
    3. Bob检查自己的元素是否在过滤器中
    """

    def __init__(self, size: int = 1000, num_hashes: int = 3):
        """
        初始化Bloom过滤器PSI

        Args:
            size: 过滤器大小
            num_hashes: 哈希函数数量
        """
        self.size = size
        self.num_hashes = num_hashes
        self.bit_array = np.zeros(size, dtype=int)

    def _hash_functions(self, item: str) -> List[int]:
        """计算哈希值"""
        h1 = int(hashlib.md5(item.encode()).hexdigest()[:8], 16) % self.size
        h2 = int(hashlib.sha1(item.encode()).hexdigest()[:8], 16) % self.size

        return [(h1 + i * h2) % self.size for i in range(self.num_hashes)]

    def build_filter(self, dataset: Set[str]):
        """
        构建Bloom过滤器

        Args:
            dataset: 数据集
        """
        self.bit_array = np.zeros(self.size, dtype=int)

        for item in dataset:
            indices = self._hash_functions(item)
            for idx in indices:
                self.bit_array[idx] = 1

    def check(self, item: str) -> bool:
        """
        检查元素是否可能在过滤器中

        Args:
            item: 要检查的元素

        Returns:
            True如果可能存在, False如果一定不存在
        """
        indices = self._hash_functions(item)
        return all(self.bit_array[idx] == 1 for idx in indices)

    def probe(self, dataset: Set[str]) -> Set[str]:
        """
        探测数据集中可能的交集元素

        Args:
            dataset: Bob的数据集

        Returns:
            可能的交集元素
        """
        possible_intersection = set()

        for item in dataset:
            if self.check(item):
                possible_intersection.add(item)

        return possible_intersection


class PSIProtocol:
    """
    完整PSI协议模拟

    整合多种PSI方法
    """

    def __init__(self, method: str = "bloom"):
        """
        初始化PSI协议

        Args:
            method: PSI方法
        """
        self.method = method

        if method == "bloom":
            self.psi = BloomFilterPSI(size=10000, num_hashes=5)
        elif method == "ot":
            self.psi = OBBalancedPSI(num_buckets=100)
        elif method == "dh":
            self.psi = DHPSI()
        else:
            self.psi = SimplePSI()

    def party_a_send_filter(self, dataset: Set[str]) -> any:
        """
        A方: 构建并发送Bloom过滤器

        Args:
            dataset: A的数据集

        Returns:
            过滤器或编码数据
        """
        if self.method == "bloom":
            self.psi.build_filter(dataset)
            return self.psi.bit_array.tolist()
        elif self.method == "dh":
            encoded = self.psi.encode_set(dataset)
            # A方私钥
            self.private_key = np.random.randint(1, 1000)
            return self.psi.alice_encode(encoded, self.private_key)
        else:
            return dataset

    def party_b_compute_intersection(
        self,
        filter_data: any,
        dataset: Set[str]
    ) -> Set[str]:
        """
        B方: 计算交集

        Args:
            filter_data: A发送的过滤器
            dataset: B的数据集

        Returns:
            交集
        """
        if self.method == "bloom":
            self.psi.bit_array = np.array(filter_data)
            return self.psi.probe(dataset)
        elif self.method == "ot":
            buckets = self.psi.map_to_buckets(dataset)
            # 简化: 使用简单哈希
            hash_a = {hash(x) % 10000 for x in filter_data}
            result = {x for x in dataset if hash(x) % 10000 in hash_a}
            return result
        elif self.method == "dh":
            encoded = self.psi.encode_set(dataset)
            # B方需要知道A的公钥来匹配
            result = set()
            for item in dataset:
                result.add(item)  # 简化
            return result
        else:
            return dataset.intersection(filter_data)


def psi_demo():
    """
    PSI演示
    """

    print("私有集合交集(PSI)演示")
    print("=" * 60)

    # 1. 简单PSI
    print("\n1. 简单PSI (基于哈希)")
    psi = SimplePSI()

    alice_set = {"apple", "banana", "cherry", "date"}
    bob_set = {"banana", "cherry", "elderberry", "fig"}

    intersection = psi.compute_intersection(alice_set, bob_set)
    print(f"   Alice集合: {alice_set}")
    print(f"   Bob集合: {bob_set}")
    print(f"   交集: {intersection}")

    # 2. DH-PSI
    print("\n2. DH-PSI (Diffie-Hellman PSI)")
    dh_psi = DHPSI()

    alice_items = {"hello", "world", "psi"}
    bob_items = {"world", "psi", "protocol"}

    alice_encoded = dh_psi.encode_set(alice_items)
    print(f"   Alice编码后: {len(alice_encoded)}个元素")

    # 3. Bloom过滤器PSI
    print("\n3. Bloom过滤器PSI")
    bloom_psi = BloomFilterPSI(size=1000, num_hashes=3)

    alice_data = {"user1", "user2", "user3", "user4", "user5"}
    bob_data = {"user3", "user4", "user5", "user6", "user7"}

    bloom_psi.build_filter(alice_data)
    print(f"   Alice数据: {alice_data}")
    print(f"   Bob数据: {bob_data}")

    possible = bloom_psi.probe(bob_data)
    print(f"   Bloom过滤器探测到的可能交集: {possible}")

    # 4. 实际应用场景
    print("\n4. 应用场景")
    print("   场景1: 社交网络联系人发现")
    print("   - 用户A和用户B各自拥有联系人列表")
    print("   - 想要找出共同的联系人,但不泄露其他联系人")

    alice_contacts = {"alice_friend1", "alice_friend2", "bob", "alice_friend3"}
    bob_contacts = {"bob", "bob_friend1", "bob_friend2", "alice_friend2"}

    bloom_psi.build_filter(alice_contacts)
    common = bloom_psi.probe(bob_contacts)
    print(f"   共同联系人: {common}")

    # 5. OT-PSI
    print("\n5. OT-PSI (不经意传输PSI)")
    ot_psi = OBBalancedPSI(num_buckets=50)

    alice_buckets = ot_psi.map_to_buckets(alice_set)
    bob_buckets = ot_psi.map_to_buckets(bob_set)

    intersection = ot_psi.compute_intersection_buckets(alice_buckets, bob_buckets)
    print(f"   Alice集合: {alice_set}")
    print(f"   Bob集合: {bob_set}")
    print(f"   交集: {intersection}")


if __name__ == "__main__":
    psi_demo()

    print("\n" + "=" * 60)
    print("PSI演示完成!")
    print("实际PSI系统需要: 公钥加密 + 不经意传输 + 认证通道")
    print("=" * 60)
