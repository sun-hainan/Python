"""
布谷鸟哈希
==========================================

【算法原理】
使用多个哈希函数，发生冲突时将旧元素"踢出"到另一个位置。
元素可能被放在多个位置之一，最终达到O(1)期望查找/删除。

【时间复杂度】
- 查找: O(1) 最坏
- 删除: O(1) 最坏
- 插入: O(1) 期望（可能重新哈希）

【空间利用率】可达约98%

【应用场景】
- 高性能键值存储
- 网络包缓存
- 防火墙规则表
- 数据库缓冲池
"""

import random
import hashlib
from typing import List, Optional, Set


class CuckooHash:
    """
    布谷鸟哈希

    【核心思想】
    - 两个哈希表 T1 和 T2
    - 每个元素 x 可以在 T1[f1(x)] 或 T2[f2(x)]
    - 冲突时，将已有元素"踢出"到其另一个位置
    - 如果踢出次数过多，重新哈希

    【两种变体】
    - Cuckoo Hashing：两个表，路径探测
    - Cuckoo Filter：近似成员查询（Bloom filter替代）
    """

    def __init__(self, capacity: int, num_tables: int = 2,
                 max_displacements: int = 500):
        self.capacity = capacity
        self.num_tables = num_tables
        self.max_displacements = max_displacements
        self.tables = [[None] * capacity for _ in range(num_tables)]
        self.size = 0

    def _hash(self, x, table_id: int) -> int:
        """哈希函数：table_id决定使用哪个哈希"""
        data = f"{table_id}:{x}".encode()
        h = int(hashlib.sha256(data).hexdigest(), 16)
        return h % self.capacity

    def _get_position(self, x, table_id: int) -> int:
        """获取元素x在指定表中的位置"""
        return self._hash(x, table_id)

    def insert(self, x) -> bool:
        """插入元素x"""
        if self.size >= self.capacity * 0.95:  # 负载因子控制
            if not self._rehash():
                return False

        return self._insert(x, 0)

    def _insert(self, x, start_table: int) -> bool:
        """
        递归插入

        【步骤】
        1. 在start_table对应的位置尝试插入x
        2. 如果该位置为空，直接插入
        3. 如果已有元素y，将x和y交换
        4. 递归将y插入到另一个表
        """
        for _ in range(self.max_displacements):
            table_id = start_table % self.num_tables
            pos = self._hash(x, table_id)

            if self.tables[table_id][pos] is None:
                self.tables[table_id][pos] = x
                self.size += 1
                return True

            # 交换x和已有元素
            x, self.tables[table_id][pos] = self.tables[table_id][pos], x

            # 切换到另一个表
            start_table = (start_table + 1) % self.num_tables

        return False

    def _rehash(self) -> bool:
        """重新哈希，扩容"""
        old_tables = self.tables
        old_cap = self.capacity

        self.capacity *= 2
        self.tables = [[None] * self.capacity for _ in range(self.num_tables)]
        self.size = 0

        for table in old_tables:
            for item in table:
                if item is not None:
                    if not self.insert(item):
                        return False
        return True

    def lookup(self, x) -> bool:
        """查找元素x是否存在"""
        for table_id in range(self.num_tables):
            pos = self._hash(x, table_id)
            if self.tables[table_id][pos] == x:
                return True
        return False

    def delete(self, x) -> bool:
        """删除元素x"""
        for table_id in range(self.num_tables):
            pos = self._hash(x, table_id)
            if self.tables[table_id][pos] == x:
                self.tables[table_id][pos] = None
                self.size -= 1
                return True
        return False

    def get_load_factor(self) -> float:
        """获取负载因子"""
        return self.size / (self.capacity * self.num_tables)


class CuckooFilter:
    """
    布谷鸟过滤器

    【与布谷鸟哈希的区别】
    - 存储项目的指纹（fingerprint）而非完整项目
    - 支持近似成员查询
    - 空间效率更高

    【准确定位】已知插入位置可以找到元素
    【近似成员查询】可以判断"可能存在"或"一定不存在"
    """

    def __init__(self, capacity: int, fingerprint_size: int = 8,
                 max_displacements: int = 500):
        """
        初始化布谷鸟过滤器

        【参数】
        - capacity: 预计插入元素数量
        - fingerprint_size: 指纹字节数（越长误报率越低）
        - max_displacements: 最大位移次数
        """
        self.capacity = capacity
        self.fingerprint_size = fingerprint_size
        self.max_displacements = max_displacements

        # 桶大小（每个桶可存几个指纹）
        self.bucket_size = 4

        # 哈希表大小（2的幂次）
        self.table_size = 1
        while self.table_size < capacity / self.bucket_size:
            self.table_size *= 2

        self.table = [[] for _ in range(self.table_size)]

    def _hash(self, x) -> int:
        """主哈希函数"""
        data = str(x).encode()
        return int(hashlib.sha256(data).hexdigest(), 16) % self.table_size

    def _fingerprint(self, x) -> str:
        """计算指纹"""
        data = str(x).encode()
        fp = hashlib.sha256(data).digest()
        return fp[:self.fingerprint_size]

    def _get_buckets(self, x):
        """
        获取候选桶位置

        【两个哈希函数】
        - f(x): 主哈希
        - g(x) = f(x) XOR h(fingerprint): 备用位置
        """
        i = self._hash(x)
        fp = self._fingerprint(x)
        h = self._hash(fp)
        j = i ^ h
        return i, j

    def insert(self, x) -> bool:
        """插入元素x"""
        i, j = self._get_buckets(x)
        fp = self._fingerprint(x)

        # 尝试插入到桶i
        if len(self.table[i]) < self.bucket_size:
            self.table[i].append(fp)
            return True

        # 尝试插入到桶j
        if len(self.table[j]) < self.bucket_size:
            self.table[j].append(fp)
            return True

        # 桶都满了，位移
        return self._insert_with_displacement(i, fp)

    def _insert_with_displacement(self, bucket_i: int, fp: str) -> bool:
        """带位移的插入"""
        for _ in range(self.max_displacements):
            # 随机选择一个指纹踢出
            bucket = self.table[bucket_i]
            idx = random.randint(0, len(bucket) - 1)
            old_fp = bucket[idx]
            bucket[idx] = fp

            # 计算被踢出指纹的备用位置
            h = self._hash(old_fp)
            bucket_j = bucket_i ^ h

            if len(self.table[bucket_j]) < self.bucket_size:
                self.table[bucket_j].append(old_fp)
                return True

            # 继续踢出
            fp = old_fp
            bucket_i = bucket_j

        return False

    def lookup(self, x) -> bool:
        """查找元素x"""
        i, j = self._get_buckets(x)
        fp = self._fingerprint(x)
        return fp in self.table[i] or fp in self.table[j]

    def delete(self, x) -> bool:
        """删除元素x（只能删除一个副本）"""
        i, j = self._get_buckets(x)
        fp = self._fingerprint(x)

        if fp in self.table[i]:
            self.table[i].remove(fp)
            return True
        if fp in self.table[j]:
            self.table[j].remove(fp)
            return True
        return False

    def get_load_factor(self) -> float:
        """负载因子"""
        total_slots = self.table_size * self.bucket_size
        used = sum(len(bucket) for bucket in self.table)
        return used / total_slots


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("布谷鸟哈希 - 测试")
    print("=" * 50)

    # 测试1：基本布谷鸟哈希
    print("\n【测试1】基本布谷鸟哈希")
    ch = CuckooHash(capacity=100)

    for i in range(50):
        ch.insert(i)

    print(f"  负载因子: {ch.get_load_factor():.2%}")
    print(f"  查找 25: {ch.lookup(25)}")
    print(f"  查找 100: {ch.lookup(100)}")

    # 测试2：删除
    print("\n【测试2】删除")
    ch.delete(25)
    print(f"  删除25后查找25: {ch.lookup(25)}")
    print(f"  负载因子: {ch.get_load_factor():.2%}")

    # 测试3：布谷鸟过滤器
    print("\n【测试3】布谷鸟过滤器")
    cf = CuckooFilter(capacity=1000)

    for i in range(500):
        cf.insert(f"item_{i}")

    print(f"  负载因子: {cf.get_load_factor():.2%}")
    print(f"  查找 'item_100': {cf.lookup('item_100')}")
    print(f"  查找 'item_999': {cf.lookup('item_999')}")

    # 测试4：高负载
    print("\n【测试4】高负载插入")
    cf2 = CuckooFilter(capacity=1000)
    inserted = 0
    for i in range(950):
        if cf2.insert(f"key_{i}"):
            inserted += 1
    print(f"  尝试插入950个，成功: {inserted}")
    print(f"  负载因子: {cf2.get_load_factor():.2%}")

    # 测试5：误报率
    print("\n【测试5】误报率测试")
    cf3 = CuckooFilter(capacity=10000)
    for i in range(5000):
        cf3.insert(f"key_{i}")

    false_positives = 0
    for i in range(5000, 10000):
        if cf3.lookup(f"key_{i}"):
            false_positives += 1

    print(f"  未插入的10000个key中，误报: {false_positives}")
    print(f"  误报率: {false_positives / 10000:.4%}")

    print("\n" + "=" * 50)
    print("布谷鸟哈希测试完成！")
    print("=" * 50)
