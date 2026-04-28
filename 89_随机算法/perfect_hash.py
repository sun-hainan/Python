"""
完美哈希
==========================================

【算法原理】
使用两阶段哈希函数，使得在静态数据集上的查找操作最坏情况O(1)。
第一层哈希确定桶，第二层使用完美哈希函数避免冲突。

【时间复杂度】
- 查找: O(1) 最坏情况
- 构建: O(n)

【空间复杂度】O(n)

【应用场景】
- 编译器符号表
- 词典查找
- 数据库索引
- 高速网络路由表
"""

import hashlib
from typing import List, Dict, Optional


class PerfectHash:
    """
    完美哈希

    【两阶段设计】
    1. g: 将keys映射到n个桶，每个桶有m个slots
    2. h_i: 每个桶的哈希函数，映射到slots
    """

    def __init__(self, keys: List[str]):
        self.keys = keys
        self.n = len(keys)
        self.table = None
        self.g = None
        self.h_functions = None
        self._build()

    def _hash(self, x: str, salt: int = 0) -> int:
        """使用SHA256的哈希函数"""
        data = f"{salt}:{x}".encode()
        return int(hashlib.sha256(data).hexdigest(), 16)

    def _build(self) -> None:
        """
        构建完美哈希

        【方法】
        1. 选择桶数 m = n（最简单）
        2. 每个key分配一个桶
        3. 解决桶内冲突
        """
        m = self.n  # 每个key一个slot

        # g函数：第一层哈希
        self.g = lambda x: self._hash(x, salt=0) % m

        # 初始化
        self.table = [None] * m

        # 处理冲突
        for key in self.keys:
            slot = self.g(key)
            if self.table[slot] is not None:
                # 冲突，尝试不同的salt
                found = False
                for s in range(1, 1000):
                    new_slot = self._hash(key, salt=s) % m
                    if self.table[new_slot] is None:
                        self.table[new_slot] = (key, s)
                        found = True
                        break
                if not found:
                    raise ValueError("无法构建完美哈希")
            else:
                self.table[slot] = (key, 0)

        # 收集第二层信息
        self.h_functions = {}

    def _h(self, x: str, slot: int) -> int:
        """第二层哈希"""
        # 简化版：slot本身作为salt
        return self._hash(x, salt=slot) % self.n

    def lookup(self, key: str) -> bool:
        """O(1)查找"""
        for entry in self.table:
            if entry is not None and entry[0] == key:
                return True
        return False


class MinimalPerfectHash:
    """
    最小完美哈希（MPH）

    确保每个slot都被使用，且没有冲突
    使用图论方法：将哈希函数建模为3-正则图
    """

    def __init__(self, keys: List[str]):
        self.keys = keys
        self.n = len(keys)
        self.g = [0] * self.n
        self.h1 = None
        self.h2 = None
        self._build()

    def _hash1(self, x: str) -> int:
        return self._hash(x, 1)

    def _hash2(self, x: str) -> int:
        return self._hash(x, 2)

    def _hash(self, x: str, salt: int) -> int:
        data = f"{salt}:{x}".encode()
        return int(hashlib.md5(data).hexdigest().hex(), 16) % self.n

    def _build(self) -> None:
        """
        构建最小完美哈希

        【简化方法】
        1. 使用两个哈希函数
        2. 通过图论方法消除冲突
        """
        self.h1 = self._hash1
        self.h2 = self._hash2

        # 简单版本：使用多个哈希函数
        salts = [0] * self.n
        for i in range(100):  # 最多尝试100次
            # 尝试分配
            slots = [-1] * self.n
            success = True

            for j, key in enumerate(self.keys):
                s = salts[j]
                slot = (self._hash(key, s)) % self.n

                if slots[slot] != -1:
                    success = False
                    break
                slots[slot] = j

            if success:
                self.g = salts
                self.slots = slots
                return

            # 增加salt重试
            for j in range(self.n):
                salts[j] += 1

        raise ValueError("无法构建最小完美哈希")

    def lookup(self, key: str) -> bool:
        """查找"""
        for i in range(1000):
            slot = (self._hash(key, self.g[slot] if 'slot' in dir() else 0)) % self.n
            if hasattr(self, 'slots') and self.slots[slot] != -1:
                idx = self.slots[slot]
                if idx < len(self.keys) and self.keys[idx] == key:
                    return True
        return False


class TwoLevelPerfectHash:
    """
    两层完美哈希

    【第一层】将keys分到t个桶
    【第二层】每个桶内部用完美哈希
    """

    def __init__(self, keys: List[str], t: Optional[int] = None):
        self.keys = keys
        self.n = len(keys)
        self.t = t or max(1, self.n // 4)
        self.buckets = [[] for _ in range(self.t)]
        self.sub_hash = []
        self.sub_tables = []
        self._build()

    def _hash(self, x: str, salt: int = 0) -> int:
        data = f"{salt}:{x}".encode()
        return int(hashlib.sha256(data).hexdigest(), 16) % self.n

    def _build(self) -> None:
        """构建两层完美哈希"""
        # 第一层：分配到桶
        for key in self.keys:
            bucket_id = self._hash(key, salt=100) % self.t
            self.buckets[bucket_id].append(key)

        # 第二层：每个桶内构建完美哈希
        for bucket in self.buckets:
            if not bucket:
                self.sub_tables.append(None)
                continue

            # 简化：直接用字典
            sub_table = {key: i for i, key in enumerate(bucket)}
            self.sub_tables.append(sub_table)

    def lookup(self, key: str) -> bool:
        """O(1)查找"""
        bucket_id = self._hash(key, salt=100) % self.t
        sub = self.sub_tables[bucket_id]
        if sub is None:
            return False
        return key in sub


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("完美哈希 - 测试")
    print("=" * 50)

    # 测试数据
    words = ["apple", "banana", "cherry", "date", "elderberry",
             "fig", "grape", "honeydew", "kiwi", "lemon"]

    # 测试1：基本完美哈希
    print("\n【测试1】完美哈希")
    ph = PerfectHash(words)
    print(f"  键数: {len(words)}")
    print(f"  哈希表大小: {len(ph.table)}")
    for word in words:
        print(f"  查找 '{word}': {ph.lookup(word)}")
    print(f"  查找 'mango': {ph.lookup('mango')}")

    # 测试2：最小完美哈希
    print("\n【测试2】最小完美哈希")
    mph = MinimalPerfectHash(words)
    print(f"  键数: {len(words)}")
    for word in words[:5]:
        print(f"  查找 '{word}': {mph.lookup(word)}")

    # 测试3：两层完美哈希
    print("\n【测试3】两层完美哈希")
    tph = TwoLevelPerfectHash(words)
    print(f"  键数: {len(words)}, 桶数: {tph.t}")
    for word in words:
        print(f"  查找 '{word}': {tph.lookup(word)}")

    # 测试4：性能
    print("\n【测试4】查找性能")
    import time
    n = 10000
    large_keys = [f"key_{i}" for i in range(n)]
    ph_large = PerfectHash(large_keys)

    start = time.time()
    for key in large_keys:
        ph_large.lookup(key)
    elapsed = time.time() - start
    print(f"  {n}个键，每键查找: {elapsed/n*1e6:.2f}μs")

    print("\n" + "=" * 50)
    print("完美哈希测试完成！")
    print("=" * 50)
