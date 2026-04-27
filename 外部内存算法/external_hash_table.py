# -*- coding: utf-8 -*-
"""
算法实现：外部内存算法 / external_hash_table

本文件实现 external_hash_table 相关的算法功能。
"""

import random


class ExternalHashTable:
    """
    外部记忆链式哈希表。

    每个桶对应一个磁盘块，支持动态扩容。
    """

    def __init__(self, bucket_size=4, num_buckets=8):
        self.bucket_size = bucket_size  # 每个桶的大小
        self.num_buckets = num_buckets
        # 桶：列表的列表
        self.buckets = [[] for _ in range(num_buckets)]
        self.num_elements = 0

    def _hash(self, key):
        """哈希函数。"""
        return hash(key) % self.num_buckets

    def insert(self, key, value):
        """
        插入键值对。

        如果桶满，需要扩容（简化：这里不允许重复溢出处理）
        """
        bucket_idx = self._hash(key)
        bucket = self.buckets[bucket_idx]

        # 检查是否已存在
        for i, (k, v) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)  # 更新
                return True

        # 插入新键值对
        if len(bucket) < self.bucket_size:
            bucket.append((key, value))
            self.num_elements += 1
            return True
        else:
            # 桶满了（需要扩容，实际实现会分裂桶）
            self._rehash()
            return self.insert(key, value)

    def search(self, key):
        """
        搜索关键字。

        返回:
            对应的值，如果未找到返回 None
        """
        bucket_idx = self._hash(key)
        bucket = self.buckets[bucket_idx]

        for k, v in bucket:
            if k == key:
                return v

        return None

    def delete(self, key):
        """删除关键字。"""
        bucket_idx = self._hash(key)
        bucket = self.buckets[bucket_idx]

        for i, (k, v) in enumerate(bucket):
            if k == key:
                del bucket[i]
                self.num_elements -= 1
                return True

        return False

    def _rehash(self):
        """扩容：增加桶数量并重新分配。"""
        old_buckets = self.buckets
        self.num_buckets *= 2
        self.buckets = [[] for _ in range(self.num_buckets)]

        for bucket in old_buckets:
            for key, value in bucket:
                new_idx = self._hash(key)
                self.buckets[new_idx].append((key, value))


class CuckooHashExternal:
    """
    外部记忆 Cuckoo 哈希。

    Cuckoo 哈希保证查找为 O(1)，通过踢出（cuckoo）操作
    解决冲突。外部版本将桶组织成磁盘块。
    """

    def __init__(self, bucket_size=4, num_buckets=8):
        self.bucket_size = bucket_size
        self.num_buckets = num_buckets
        self.buckets = [[None] * bucket_size for _ in range(num_buckets)]
        self.key_pos = {}  # key -> (bucket_idx, slot_idx)
        self.num_elements = 0

    def _hash1(self, key):
        """第一个哈希函数。"""
        return hash(key) % self.num_buckets

    def _hash2(self, key):
        """第二个哈希函数。"""
        return hash(str(key)[::-1]) % self.num_buckets

    def _get_position(self, key):
        """获取 key 的两个可能位置。"""
        h1 = self._hash1(key)
        h2 = self._hash2(key)
        return h1, h2

    def _find_slot(self, bucket_idx, key):
        """在桶中找到 key 的槽位索引。"""
        bucket = self.buckets[bucket_idx]
        for i, item in enumerate(bucket):
            if item is not None and item[0] == key:
                return i
        return None

    def _find_empty_slot(self, bucket_idx):
        """找空槽位。"""
        bucket = self.buckets[bucket_idx]
        for i, item in enumerate(bucket):
            if item is None:
                return i
        return None

    def insert(self, key, value):
        """插入键值对（带驱逐）。"""
        if self.num_elements >= self.num_buckets * self.bucket_size * 0.9:
            self._rehash()

        h1, h2 = self._get_position(key)

        # 尝试插入到 h1
        if self._insert_at(key, value, h1):
            return True

        # 尝试插入到 h2
        if self._insert_at(key, value, h2):
            return True

        # 需要驱逐
        return self._cuckoo_insert(key, value, h1)

    def _insert_at(self, key, value, bucket_idx):
        """尝试将键值对插入指定桶。"""
        slot = self._find_empty_slot(bucket_idx)
        if slot is not None:
            self.buckets[bucket_idx][slot] = (key, value)
            self.key_pos[key] = (bucket_idx, slot)
            self.num_elements += 1
            return True
        return False

    def _cuckoo_insert(self, key, value, bucket_idx):
        """Cuckoo 风格的插入（带驱逐）。"""
        max_iterations = 100  # 防止无限循环

        for _ in range(max_iterations):
            slot = self._find_empty_slot(bucket_idx)
            if slot is None:
                # 需要驱逐一个
                slot = random.randint(0, self.bucket_size - 1)

            old_key, old_value = self.buckets[bucket_idx][slot]
            self.buckets[bucket_idx][slot] = (key, value)
            self.key_pos[key] = (bucket_idx, slot)

            # 踢出的元素尝试另一个位置
            h1, h2 = self._get_position(old_key)
            new_bucket = h2 if bucket_idx == h1 else h1

            new_slot = self._find_empty_slot(new_bucket)
            if new_slot is not None:
                self.buckets[new_bucket][new_slot] = (old_key, old_value)
                self.key_pos[old_key] = (new_bucket, new_slot)
                return True

            # 继续驱逐
            key, value = old_key, old_value
            bucket_idx = new_bucket

        # 插入失败，需要扩容
        self._rehash()
        return self.insert(key, value)

    def search(self, key):
        """搜索关键字。"""
        h1, h2 = self._get_position(key)

        slot = self._find_slot(h1, key)
        if slot is not None:
            return self.buckets[h1][slot][1]

        slot = self._find_slot(h2, key)
        if slot is not None:
            return self.buckets[h2][slot][1]

        return None

    def delete(self, key):
        """删除关键字。"""
        if key not in self.key_pos:
            return False

        bucket_idx, slot_idx = self.key_pos[key]
        self.buckets[bucket_idx][slot_idx] = None
        del self.key_pos[key]
        self.num_elements -= 1
        return True

    def _rehash(self):
        """扩容。"""
        old_buckets = self.buckets
        old_num = self.num_buckets

        self.num_buckets *= 2
        self.buckets = [[None] * self.bucket_size for _ in range(self.num_buckets)]
        self.key_pos = {}
        self.num_elements = 0

        for bucket in old_buckets:
            for item in bucket:
                if item is not None:
                    key, value = item
                    self.insert(key, value)


if __name__ == "__main__":
    print("=== 外部记忆哈希表测试 ===")

    # 链式哈希表测试
    print("\n--- 链式哈希表 ---")
    ht = ExternalHashTable(bucket_size=4, num_buckets=4)

    # 插入
    test_items = [('apple', 1), ('banana', 2), ('cherry', 3), ('date', 4),
                  ('elderberry', 5), ('fig', 6), ('grape', 7)]
    for key, value in test_items:
        ht.insert(key, value)
        print(f"插入 {key}={value}, 桶数={ht.num_buckets}, 元素数={ht.num_elements}")

    # 搜索
    print("\n搜索测试:")
    for key in ['banana', 'grape', 'pear']:
        result = ht.search(key)
        print(f"  {key}: {result}")

    # 删除
    print("\n删除测试:")
    ht.delete('banana')
    print(f"删除 banana 后搜索: {ht.search('banana')}")

    # Cuckoo 哈希测试
    print("\n--- Cuckoo 哈希表 ---")
    ch = CuckooHashExternal(bucket_size=4, num_buckets=4)

    for key, value in test_items:
        ch.insert(key, value)

    print(f"元素数: {ch.num_elements}")

    # 搜索
    print("\n搜索测试:")
    for key in ['apple', 'cherry', 'date']:
        result = ch.search(key)
        print(f"  {key}: {result}")

    print("\n外部哈希表特性:")
    print("  链式哈希：简单，但查找需要遍历链表")
    print("  Cuckoo 哈希：O(1) 期望查找和删除")
    print("  扩容策略影响性能：装填因子保持在 0.5 以下")
