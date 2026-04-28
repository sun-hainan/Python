# -*- coding: utf-8 -*-

"""

算法实现：随机算法 / universal_hashing



本文件实现全局哈希函数族（Universal Hashing）。

核心思想：

    - 选择一个随机的哈希函数来处理每个查询

    - 对手无法构造最坏情况输入（因为不知道选哪个函数）

    - 期望冲突次数 = n/m（n 个元素，m 个槽位）



主要实现：

    - 2-universal 哈希函数族

    - 矩阵形式的全局哈希

    - 字符串哈希的全局函数族

"""

import random
import hashlib


class UniversalHashFamily:
    """
    通用哈希函数族的实现类

    一个哈希函数族 H 是全域的（universal），
    当从 H 中随机选择的函数 h，对于任意两个不同 key x ≠ y，
    Pr[h(x) = h(y)] ≤ 1/m，其中 m 是哈希表大小。

    如果这个概率正好 = 1/m，则称为强 universal（2-independent）。
    """

    def __init__(self, m: int, universe_size: int = None):
        """
        初始化通用哈希函数族

        参数：
            m: 哈希表槽位数（输出范围）
            universe_size: 键的取值范围（最大可能键值 + 1）
        """
        self.m = m
        self.universe_size = universe_size
        self._h = None  # 当前选中的哈希函数参数
        self._select_random_hash()

    def _select_random_hash(self):
        """
        从函数族中随机选择一个哈希函数

        这里使用加法哈希族：
            h_{a,b}(x) = ((a*x + b) mod p) mod m
        其中 p 是一个大于 universe_size 的素数，
        a 是 [1, p-1] 中的随机数，
        b 是 [0, p-1] 中的随机数。
        """
        # 选择一个足够大的素数作为模数
        if self.universe_size is None:
            p = self._next_prime(2**31)
        else:
            p = self._next_prime(self.universe_size * 2)

        # 随机选择参数 a 和 b
        a = random.randint(1, p - 1)
        b = random.randint(0, p - 1)

        self._p = p
        self._a = a
        self._b = b

    @staticmethod
    def _next_prime(n: int) -> int:
        """
        找到大于等于 n 的最小素数

        参数：
            n: 起始数字

        返回：
            大于等于 n 的最小素数
        """
        def is_prime(num):
            if num < 2:
                return False
            for i in range(2, int(num**0.5) + 1):
                if num % i == 0:
                    return False
            return True

        while not is_prime(n):
            n += 1
        return n

    def hash(self, x: int) -> int:
        """
        使用当前随机哈希函数对键 x 进行哈希

        参数：
            x: 要哈希的键（整数）

        返回：
            哈希值，范围 [0, m-1]
        """
        return ((self._a * x + self._b) % self._p) % self.m

    def __call__(self, x: int) -> int:
        """支持以函数方式调用 hash(x)"""
        return self.hash(x)

    def rehash(self):
        """
        重新随机选择哈希函数

        模拟每次查询使用不同的哈希函数
        """
        self._select_random_hash()


def matrix_universal_hash(key: int, m: int, w: int = 32) -> int:
    """
    基于矩阵乘法的全局哈希（全域哈希的另一种构造）

    将键 x 视为 w 位向量，哈希函数为：
        h_A(x) = floor((A·x) mod 2^w / 2^(w - log₂(m)))

    其中 A 是一个 w × w 的随机二进制矩阵。

    参数：
        key: 要哈希的键（整数）
        m: 哈希表大小（2 的幂）
        w: 位宽（默认 32）

    返回：
        哈希值
    """
    # 生成 w×w 的随机二进制矩阵 A
    # 为效率起见，这里简化为生成随机整数矩阵的种子
    random.seed(key % 1000007)
    A_rows = []
    for _ in range(w):
        row = random.getrandbits(w)
        A_rows.append(row)

    # 计算矩阵-向量乘积（逐位异或，不是算术乘法）
    result_bits = 0
    for i in range(w):
        # 计算第 i 位的结果
        bit = 0
        # 提取 key 的各位
        for j in range(w):
            if (key >> j) & 1:
                if (A_rows[i] >> j) & 1:
                    bit ^= 1
        if bit:
            result_bits |= (1 << i)

    # 取高 (w - log2(m)) 位作为哈希值
    shift = w - int(math.log2(m))
    return (result_bits >> shift) & (m - 1)


class StringUniversalHash:
    """
    字符串的全局哈希函数族

    将字符串视为字符编码序列，使用多项式哈希：
        h_{a}(s) = (Σ s[i]·a^i) mod p

    通过随机选择 a 来获得全域性质。
    """

    def __init__(self, m: int, p: int = None):
        """
        初始化字符串全局哈希

        参数：
            m: 哈希表大小
            p: 大素数模数（默认为大于所有可能字符编码和的素数）
        """
        self.m = m
        # 选择一个足够大的素数
        self.p = p or self._next_prime(2**20)
        # 随机选择 a，范围 [1, p-1]
        self.a = random.randint(1, self.p - 1)

    @staticmethod
    def _next_prime(n: int) -> int:
        while True:
            is_prime = all(n % i != 0 for i in range(2, int(n**0.5) + 1))
            if is_prime:
                return n
            n += 1

    def hash(self, s: str) -> int:
        """
        计算字符串 s 的哈希值

        参数：
            s: 输入字符串

        返回：
            哈希值 [0, m-1]
        """
        result = 0
        a_power = 1

        for char in s:
            # 使用字符的 Unicode 编码
            code = ord(char)
            result = (result + code * a_power) % self.p
            a_power = (a_power * self.a) % self.p

        return result % self.m

    def __call__(self, s: str) -> int:
        return self.hash(s)


import math


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 全局哈希函数族测试 ===\n")

    random.seed(42)

    # 测试 1: 基本整数哈希
    print("--- 全局哈希（整数）---")

    m = 100  # 哈希表大小
    uh = UniversalHashFamily(m, universe_size=1000)

    keys = list(range(100))  # 100 个不同的键
    hashes = [uh.hash(k) for k in keys]

    # 统计冲突
    from collections import Counter
    counter = Counter(hashes)
    collisions = len(keys) - len(set(hashes))
    print(f"  哈希表大小 m = {m}")
    print(f"  键数量 n = {len(keys)}")
    print(f"  冲突次数 = {collisions}")
    print(f"  期望冲突 ≈ n²/(2m) = {len(keys)**2 / (2*m):.1f}")

    # 测试 2: 冲突概率验证
    print("\n--- 冲突概率验证 ---")

    n_trials = 10000
    m = 1000
    uh = UniversalHashFamily(m, universe_size=10000)

    x, y = 123, 456  # 两个固定的不同键
    collision_count = 0

    for _ in range(n_trials):
        uh.rehash()  # 重新选择哈希函数
        if uh.hash(x) == uh.hash(y):
            collision_count += 1

    empirical_prob = collision_count / n_trials
    theoretical_prob = 1 / m

    print(f"  不同键 x≠y: x={x}, y={y}")
    print(f"  理论冲突概率 1/m = {theoretical_prob:.4f}")
    print(f"  经验冲突概率 = {empirical_prob:.4f}")
    print(f"  接近理论值: {'✅' if abs(empirical_prob - theoretical_prob) < 0.05 else '❌'}")

    # 测试 3: 字符串哈希
    print("\n--- 字符串全局哈希 ---")

    sh = StringUniversalHash(m=100)
    strings = ["hello", "world", "algorithm", "hash", "universal", "random"]

    for s in strings:
        h = sh.hash(s)
        print(f"  '{s}' → hash = {h}")

    # 测试 4: 字符串哈希冲突分析
    print("\n--- 字符串哈希冲突分析 ---")

    m = 1000
    sh = StringUniversalHash(m=m)

    test_strings = [f"string_{i}" for i in range(200)]
    hashes = [sh.hash(s) for s in test_strings]

    counter = Counter(hashes)
    collision_count = len(test_strings) - len(set(hashes))
    expected = len(test_strings) ** 2 / (2 * m)

    print(f"  字符串数量: {len(test_strings)}")
    print(f"  哈希表大小: {m}")
    print(f"  实际冲突: {collision_count}")
    print(f"  期望冲突: {expected:.1f}")

    print("\n说明：")
    print("  - 全局哈希：对手无法构造最坏情况输入")
    print("  - 加法哈希族：h_{a,b}(x) = (ax+b mod p) mod m")
    print("  - 冲突概率 ≤ 1/m 是全域哈希的核心性质")
    print("  - 每次查询重新随机选择哈希函数，保证平均性能")
