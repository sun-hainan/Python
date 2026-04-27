# -*- coding: utf-8 -*-

"""

算法实现：25_其他工具 / counting_bloom_filter



本文件实现 counting_bloom_filter 相关的算法功能。

"""



import math





class CountingBloomFilter:

    """计数布隆过滤器"""



    def __init__(self, n: int, fp_rate: float = 0.01, counter_bits: int = 4):

        """

        参数：

            n: 预计元素数量

            fp_rate: 期望假阳性率

            counter_bits: 每个计数器位数（决定最大值）

        """

        self.n = n

        self.fp_rate = fp_rate

        self.counter_bits = counter_bits  # 通常4位够了（0-15）

        self.max_counter = (1 << counter_bits) - 1



        # 计算位数组大小和哈希函数数量

        self.m = int(-n * math.log(fp_rate) / (math.log(2) ** 2)) + 1

        self.k = int((self.m / n) * math.log(2)) + 1



        # 计数器数组（替代位数组）

        self.counters = [0] * self.m



    def _hash(self, item, seed: int) -> int:

        """哈希函数"""

        h = seed

        for char in str(item):

            h = (h * 31 + ord(char)) % self.m

        return h



    def add(self, item):

        """添加元素"""

        for seed in range(self.k):

            idx = self._hash(item, seed)

            if self.counters[idx] < self.max_counter:

                self.counters[idx] += 1



    def remove(self, item):

        """删除元素"""

        for seed in range(self.k):

            idx = self._hash(item, seed)

            if self.counters[idx] > 0:

                self.counters[idx] -= 1



    def contains(self, item) -> bool:

        """查询元素"""

        for seed in range(self.k):

            idx = self._hash(item, seed)

            if self.counters[idx] == 0:

                return False

        return True



    def get_approx_count(self, item) -> int:

        """获取元素的近似计数"""

        min_count = self.max_counter

        for seed in range(self.k):

            idx = self._hash(item, seed)

            min_count = min(min_count, self.counters[idx])

        return min_count



    def reset(self):

        """清空"""

        self.counters = [0] * self.m





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 计数布隆过滤器测试 ===\n")



    import random



    bf = CountingBloomFilter(n=1000, fp_rate=0.01)



    # 测试添加和删除

    items = ["apple", "banana", "cherry", "date", "elderberry"]



    print("添加元素：")

    for item in items:

        bf.add(item)

        print(f"  add({item}): count={bf.get_approx_count(item)}")



    print("\n查询：")

    for item in ["apple", "banana", "grape"]:

        result = bf.contains(item)

        count = bf.get_approx_count(item)

        print(f"  contains({item}): {result}, approx_count={count}")



    print("\n删除 apple：")

    bf.remove("apple")

    for item in ["apple", "banana"]:

        result = bf.contains(item)

        count = bf.get_approx_count(item)

        print(f"  contains({item}): {result}, approx_count={count}")



    print("\n多次添加同一元素：")

    bf2 = CountingBloomFilter(n=100, fp_rate=0.1)

    for _ in range(5):

        bf2.add("test_item")

    print(f"  添加5次后 count={bf2.get_approx_count('test_item')}")

    for _ in range(3):

        bf2.remove("test_item")

    print(f"  删除3次后 count={bf2.get_approx_count('test_item')}")



    print("\n说明：")

    print("  - 计数器溢出问题：达到最大值后不再增加")

    print("  - 空间开销：每个计数器需要counter_bits位")

    print("  - 假阳性率比普通布隆过滤器稍高")

