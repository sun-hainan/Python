# -*- coding: utf-8 -*-

"""

算法实现：25_其他工具 / cuckoo_filter



本文件实现 cuckoo_filter 相关的算法功能。

"""



import math

import random





class CuckooFilter:

    """Cuckoo Filter"""



    def __init__(self, capacity: int, fp_rate: float = 0.01):

        """

        参数：

            capacity: 预计元素数量

            fp_rate: 期望假阳性率

        """

        self.capacity = capacity



        # 计算桶数量（每个桶4个slot）

        self.bucket_size = 4

        self.num_buckets = int(math.ceil(capacity / self.bucket_size / 0.85))  # 0.85是装载因子



        # 指纹大小（bits）

        self.fingerprint_size = int(math.ceil(-math.log2(fp_rate))) + 1



        # 桶数组

        self.buckets = [[None] * self.bucket_size for _ in range(self.num_buckets)]



        # 哈希函数种子

        self.seeds = [random.randint(0, 1000000) for _ in range(4)]



    def _hash1(self, item: str) -> int:

        """第一个哈希函数：确定桶位置"""

        h = self.seeds[0]

        for char in item:

            h = (h * 31 + ord(char)) % (self.num_buckets * self.bucket_size)

        return h % self.num_buckets



    def _hash2(self, item: str) -> int:

        """第二个哈希函数"""

        h = self.seeds[1]

        for char in item:

            h = (h * 31 + ord(char)) % (self.num_buckets * self.bucket_size)

        return h % self.num_buckets



    def _fingerprint(self, item: str) -> int:

        """计算指纹"""

        h = self.seeds[2]

        for char in item:

            h = (h * 31 + ord(char)) % (2 ** self.fingerprint_size)

        return h



    def _get_alt_index(self, fingerprint: int, bucket_idx: int) -> int:

        """计算备选桶位置"""

        h = self.seeds[3]

        h = (h * fingerprint) % self.num_buckets

        return (bucket_idx ^ h) % self.num_buckets



    def insert(self, item: str) -> bool:

        """插入元素"""

        fingerprint = self._fingerprint(item)

        idx1 = self._hash1(item)

        idx2 = self._hash2(item)



        # 尝试放入 idx1

        for i in range(self.bucket_size):

            if self.buckets[idx1][i] is None:

                self.buckets[idx1][i] = fingerprint

                return True



        # 尝试放入 idx2

        for i in range(self.bucket_size):

            if self.buckets[idx2][i] is None:

                self.buckets[idx2][i] = fingerprint

                return True



        # 都需要驱逐，随机选择一个

        idx = idx1 if random.random() < 0.5 else idx2

        slot = random.randint(0, self.bucket_size - 1)

        old_fingerprint = self.buckets[idx][slot]

        self.buckets[idx][slot] = fingerprint



        # 驱逐循环（最多尝试10次）

        for _ in range(10):

            alt_idx = self._get_alt_index(old_fingerprint, idx)



            # 尝试放入备选桶

            for i in range(self.bucket_size):

                if self.buckets[alt_idx][i] is None:

                    self.buckets[alt_idx][i] = old_fingerprint

                    return True



            # 需要继续驱逐

            idx = alt_idx

            slot = random.randint(0, self.bucket_size - 1)

            old_fingerprint, self.buckets[idx][slot] = self.buckets[idx][slot], old_fingerprint



        return False  # 插入失败（过滤器满）



    def contains(self, item: str) -> bool:

        """查询元素"""

        fingerprint = self._fingerprint(item)

        idx1 = self._hash1(item)

        idx2 = self._hash2(item)



        # 检查两个桶

        for fp in self.buckets[idx1]:

            if fp == fingerprint:

                return True

        for fp in self.buckets[idx2]:

            if fp == fingerprint:

                return True



        return False



    def delete(self, item: str) -> bool:

        """删除元素"""

        fingerprint = self._fingerprint(item)

        idx1 = self._hash1(item)

        idx2 = self._hash2(item)



        # 从 idx1 删除

        for i in range(self.bucket_size):

            if self.buckets[idx1][i] == fingerprint:

                self.buckets[idx1][i] = None

                return True



        # 从 idx2 删除

        for i in range(self.bucket_size):

            if self.buckets[idx2][i] == fingerprint:

                self.buckets[idx2][i] = None

                return True



        return False  # 元素不存在





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== Cuckoo Filter 测试 ===\n")



    cf = CuckooFilter(capacity=100, fp_rate=0.01)



    # 测试基本操作

    items = ["apple", "banana", "cherry", "date", "elderberry"]



    print("插入：")

    for item in items:

        success = cf.insert(item)

        print(f"  {item}: {'✅' if success else '❌'}")



    print("\n查询：")

    for item in items + ["grape"]:

        result = cf.contains(item)

        print(f"  {item}: {'✅ 可能存在' if result else '❌ 不存在'}")



    print("\n删除：")

    cf.delete("banana")

    cf.delete("cherry")

    print(f"  删除 banana, cherry 后：")

    print(f"  banana: {'✅' if cf.contains('banana') else '❌'}")

    print(f"  cherry: {'✅' if cf.contains('cherry') else '❌'}")

    print(f"  apple: {'✅' if cf.contains('apple') else '❌'}")



    print("\n空间效率对比：")

    n = 10000

    fp_rate = 0.01



    bf_space = int(-n * math.log(fp_rate) / (math.log(2) ** 2)) / 8

    cf_space = n / 0.85 / 4 * (math.log2(1/fp_rate) + 1) / 8



    print(f"  布隆过滤器: ~{bf_space:.0f} bytes")

    print(f"  Cuckoo Filter: ~{cf_space:.0f} bytes")

    print(f"  节省: {(1 - cf_space/bf_space)*100:.1f}%")



    print("\n说明：")

    print("  - Cuckoo Filter 空间效率约为布隆过滤器的50-70%")

    print("  - 支持删除操作（布隆过滤器不支持）")

    print("  - 查询/插入/删除都是O(1)")

    print("  - 适用于需要删除功能的场景")

