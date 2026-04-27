# -*- coding: utf-8 -*-

"""

算法实现：08_位运算 / bloom_filter



本文件实现 bloom_filter 相关的算法功能。

"""



import hashlib



class BloomFilter:

    """布隆过滤器：空间高效的概率型集合"""



    def __init__(self, expected_n: int, false_positive_rate: float = 0.01):

        # 计算最优比特数组大小 m = -n * ln(fp) / (ln(2)^2)

        import math

        m = int(-expected_n * math.log(false_positive_rate) / (math.log(2) ** 2))

        # 计算最优哈希函数个数 k = (m/n) * ln(2)

        k = int((m / expected_n) * math.log(2))

        self.size = m

        self.num_hashes = k

        self.bits = bytearray((m + 7) // 8)  # 每字节8位



    def _get_bit_pos(self, idx: int) -> tuple[int, int]:

        """返回字节索引和位偏移"""

        byte_idx = idx // 8

        bit_offset = idx % 8

        return byte_idx, bit_offset



    def _set_bit(self, idx: int):

        """设置第idx位为1"""

        byte_idx, bit_offset = self._get_bit_pos(idx)

        self.bits[byte_idx] |= (1 << bit_offset)



    def _get_bit(self, idx: int) -> bool:

        """读取第idx位"""

        byte_idx, bit_offset = self._get_bit_pos(idx)

        return (self.bits[byte_idx] >> bit_offset) & 1 == 1



    def _hash_functions(self, item: str) -> list[int]:

        """生成k个哈希值（双哈希技术）"""

        h1 = int(hashlib.md5(item.encode()).hexdigest(), 16)

        h2 = int(hashlib.sha1(item.encode()).hexdigest(), 16)

        return [(h1 + i * h2) % self.size for i in range(self.num_hashes)]



    def add(self, item: str):

        """添加元素"""

        for idx in self._hash_functions(item):

            self._set_bit(idx)



    def contains(self, item: str) -> bool:

        """检测元素是否存在（可能假阳性）"""

        return all(self._get_bit(idx) for idx in self._hash_functions(item))





def build_bloom_filter(words: list[str], fp_rate: float = 0.001) -> BloomFilter:

    """从词列表构建布隆过滤器"""

    bf = BloomFilter(len(words), fp_rate)

    for w in words:

        bf.add(w)

    return bf





if __name__ == "__main__":

    # 示例：URL黑名单

    blacklist = [

        "evil.com", "phishing.net", "malware.org", "spam.xyz",

        "scam.info", "fake-bank.com", "tracker.evil"

    ]

    bf = build_bloom_filter(blacklist)



    test_urls = ["good.com", "evil.com", "unknown.xyz", "phishing.net"]

    for url in test_urls:

        result = bf.contains(url)

        print(f"检测 '{url}': {'⚠️ 可能命中' if result else '✓ 未命中'}")



    print(f"\n过滤器容量: {bf.size} bits, {bf.num_hashes} 个哈希函数")

    print(f"误报率估计: {0.001 * 100:.1f}%")



    # 容量测试

    large_bf = BloomFilter(100000, 0.001)

    for i in range(10000):

        large_bf.add(f"item_{i}")

    hits = sum(1 for i in range(10000, 20000) if large_bf.contains(f"item_{i}"))

    print(f"\n新元素误检数（预期~10）: {hits}")

