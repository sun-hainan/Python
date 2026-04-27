# -*- coding: utf-8 -*-

"""

算法实现：细粒度复杂性 / bloom_filter



本文件实现 bloom_filter 相关的算法功能。

"""



import hashlib

from typing import List, Set, Optional





class BloomFilter:

    """

    布隆过滤器

    使用多个哈希函数映射到一位数组

    """

    

    def __init__(self, size: int, num_hashes: int = None):

        """

        初始化

        

        Args:

            size: 位数组大小(位数)

            num_hashes: 哈希函数数量

        """

        self.size = size

        self.bit_array = [0] * size

        

        # 计算最佳哈希函数数量

        # k = (m/n) * ln(2), 其中m是位数,n是预期元素数

        # 这里假设n = size/10

        if num_hashes is None:

            self.num_hashes = int((size / 10) * 0.693147)  # m/n * ln(2)

            self.num_hashes = max(1, self.num_hashes)

        else:

            self.num_hashes = num_hashes

    

    def _get_hash_positions(self, item: str) -> List[int]:

        """计算元素的哈希位置"""

        # 使用双哈希技术生成多个哈希值

        hash1 = int(hashlib.md5(item.encode()).hexdigest(), 16)

        hash2 = int(hashlib.sha1(item.encode()).hexdigest(), 16)

        

        positions = []

        for i in range(self.num_hashes):

            pos = (hash1 + i * hash2) % self.size

            positions.append(pos)

        

        return positions

    

    def insert(self, item: str):

        """插入元素"""

        for pos in self._get_hash_positions(item):

            self.bit_array[pos] = 1

    

    def contains(self, item: str) -> bool:

        """

        检查元素是否可能存在

        可能返回True(假阳性)但不会返回False(确定性不存在)

        """

        for pos in self._get_hash_positions(item):

            if self.bit_array[pos] == 0:

                return False

        return True

    

    def clear(self):

        """清空过滤器"""

        self.bit_array = [0] * self.size

    

    def false_positive_rate(self, num_items: int) -> float:

        """

        估计假阳性率

        

        Args:

            num_items: 已插入的元素数量

        

        Returns:

            估计的假阳性率

        """

        import math

        

        # p = (1 - e^(-kn/m))^k

        # k = 哈希函数数

        # n = 元素数

        # m = 位数组大小

        

        k = self.num_hashes

        m = self.size

        n = num_items

        

        exponent = -k * n / m

        p = (1 - math.exp(exponent)) ** k

        

        return p

    

    def __len__(self) -> int:

        """返回位数组大小"""

        return self.size





def create_bloom_filter(expected_items: int, false_positive_rate: float = 0.01) -> BloomFilter:

    """

    根据预期元素数和假阳性率创建布隆过滤器

    

    Args:

        expected_items: 预期元素数量

        false_positive_rate: 期望的假阳性率

    

    Returns:

        布隆过滤器

    """

    import math

    

    # m = -n * ln(p) / (ln(2)^2)

    # k = (m/n) * ln(2)

    

    n = expected_items

    p = false_positive_rate

    

    m = int(-n * math.log(p) / (math.log(2) ** 2))

    k = int((m / n) * math.log(2))

    

    return BloomFilter(m, k)





# 测试代码

if __name__ == "__main__":

    # 测试1: 基本功能

    print("测试1 - 基本功能:")

    bf = BloomFilter(100, 5)

    

    words = ["hello", "world", "python", "bloom", "filter"]

    

    for word in words:

        bf.insert(word)

        print(f"  插入'{word}'")

    

    # 查询

    print("\n  查询结果:")

    test_words = ["hello", "world", "notexist", "python"]

    for word in test_words:

        result = bf.contains(word)

        print(f"    '{word}': {'可能存在' if result else '不存在'}")

    

    # 测试2: 估计假阳性率

    print("\n测试2 - 假阳性率:")

    print(f"  理论假阳性率: {bf.false_positive_rate(5):.4f}")

    

    # 测试3: 不同参数

    print("\n测试3 - 不同参数:")

    for size in [100, 1000, 10000]:

        bf = BloomFilter(size)

        print(f"  size={size}, hashes={bf.num_hashes}, 估计FPR={bf.false_positive_rate(50):.4f}")

    

    # 测试4: 便捷函数

    print("\n测试4 - 便捷函数:")

    bf_auto = create_bloom_filter(1000, 0.01)

    print(f"  1000元素, 1%FPR: size={bf_auto.size}, hashes={bf_auto.num_hashes}")

    

    # 测试5: 大规模测试

    print("\n测试5 - 大规模测试:")

    import random

    import string

    

    random.seed(42)

    

    n = 10000

    bf_large = create_bloom_filter(n, 0.01)

    

    # 插入n个元素

    words_large = [''.join(random.choices(string.ascii_lowercase, k=10)) for _ in range(n)]

    for word in words_large:

        bf_large.insert(word)

    

    # 测试查询

    correct = 0

    false_positive = 0

    not_exist_words = [''.join(random.choices(string.ascii_lowercase, k=10)) for _ in range(n)]

    

    for word in words_large:

        if bf_large.contains(word):

            correct += 1

    

    for word in not_exist_words:

        if bf_large.contains(word):

            false_positive += 1

    

    print(f"  插入{n}个元素")

    print(f"  已存在元素正确率: {correct}/{n} = {correct/n:.4f}")

    print(f"  假阳性数: {false_positive}/{n}")

    print(f"  观察假阳性率: {false_positive/n:.4f}")

    print(f"  理论假阳性率: {bf_large.false_positive_rate(n):.4f}")

    

    print("\n所有测试完成!")

