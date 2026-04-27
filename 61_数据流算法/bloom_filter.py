# -*- coding: utf-8 -*-

"""

算法实现：数据流算法 / bloom_filter



本文件实现 bloom_filter 相关的算法功能。

"""



import hashlib

from typing import List





class BloomFilter:

    """布隆过滤器"""



    def __init__(self, size: int, num_hashes: int):

        """

        参数：

            size: 位数组大小

            num_hashes: 哈希函数数量

        """

        self.size = size

        self.num_hashes = num_hashes

        self.bit_array = [0] * size



    def _get_hash_positions(self, item: str) -> List[int]:

        """

        获取哈希位置



        返回：位置列表

        """

        # 使用多个哈希函数

        positions = []



        for i in range(self.num_hashes):

            # 使用MD5和SHA1的不同组合

            data = f"{item}_{i}".encode()

            h = hashlib.md5(data).hexdigest()

            pos = int(h, 16) % self.size

            positions.append(pos)



        return positions



    def insert(self, item: str) -> None:

        """

        插入元素



        参数：

            item: 要插入的字符串

        """

        positions = self._get_hash_positions(item)



        for pos in positions:

            self.bit_array[pos] = 1



    def query(self, item: str) -> bool:

        """

        查询元素



        参数：

            item: 要查询的字符串



        返回：可能存在（True）或一定不存在（False）

        """

        positions = self._get_hash_positions(item)



        for pos in positions:

            if self.bit_array[pos] == 0:

                return False



        return True



    def false_positive_rate(self, n_elements: int) -> float:

        """

        估算假阳性率



        参数：

            n_elements: 已插入元素数



        返回：假阳性率估计

        """

        # (1 - e^(-k*n/m))^k

        import math



        k = self.num_hashes

        m = self.size

        n = n_elements



        exponent = -k * n / m

        fpr = (1 - math.exp(exponent)) ** k



        return fpr





def bloom_filter_vs_hash_table():

    """布隆过滤器 vs 哈希表"""

    print("=== 布隆过滤器 vs 哈希表 ===")

    print()

    print("哈希表：")

    print("  - 精确查找")

    print("  - 需要更多空间")

    print("  - 插入和查找都是 O(1)")

    print()

    print("布隆过滤器：")

    print("  - 概率查找")

    print("  - 空间节省约 10 倍")

    print("  - 有假阳性但无假阴性")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 布隆过滤器测试 ===\n")



    # 创建布隆过滤器

    size = 10000

    num_hashes = 7



    bf = BloomFilter(size, num_hashes)



    print(f"位数组大小: {size}")

    print(f"哈希函数数: {num_hashes}")

    print()



    # 插入元素

    items = ["apple", "banana", "cherry", "date", "elderberry"]



    print(f"插入: {items}")

    for item in items:

        bf.insert(item)



    # 查询

    test_items = ["apple", "grape", "cherry", "fig"]



    print("\n查询：")

    for item in test_items:

        result = bf.query(item)

        print(f"  '{item}': {'可能存在' if result else '一定不存在'}")



    # 估算假阳性率

    estimated_fpr = bf.false_positive_rate(len(items))

    print(f"\n估算假阳性率: {estimated_fpr:.6f}")



    # 实际测试

    print("\n实际测试10000个不存在的元素:")

    false_positives = 0

    for i in range(10000):

        item = f"nonexistent_{i}"

        if bf.query(item):

            false_positives += 1



    actual_fpr = false_positives / 10000

    print(f"实际假阳性率: {actual_fpr:.6f}")



    print()

    bloom_filter_vs_hash_table()



    print()

    print("说明：")

    print("  - 布隆过滤器用于快速检查")

    print("  - Chrome、Git使用")

    print("  - 数据库索引也有应用")

