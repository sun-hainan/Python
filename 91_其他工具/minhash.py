# -*- coding: utf-8 -*-

"""

算法实现：25_其他工具 / minhash



本文件实现 minhash 相关的算法功能。

"""



import random

import hashlib





class MinHash:

    """MinHash 相似度估计器"""



    def __init__(self, num_hashes: int = 100, seed: int = 42):

        """

        参数：

            num_hashes: 哈希函数数量

            seed: 随机种子

        """

        self.num_hashes = num_hashes

        self.seed = seed

        random.seed(seed)



        # 生成哈希函数的参数（a, b）

        # h(x) = (a*x + b) mod p

        self.params = [(random.randint(1, 2**31-1), random.randint(0, 2**31-1))

                       for _ in range(num_hashes)]



        # 大素数

        self.prime = 2**61 - 1



    def _hash_items(self, items: set) -> list:

        """计算集合的MinHash签名"""

        signature = []



        for a, b in self.params:

            min_hash = self.prime

            for item in items:

                # 将item转为整数

                if isinstance(item, str):

                    item = int(hashlib.md5(item.encode()).hexdigest(), 16)

                # 计算哈希值

                h = (a * item + b) % self.prime

                min_hash = min(min_hash, h)

            signature.append(min_hash)



        return signature



    def estimate_similarity(self, set1: set, set2: set) -> float:

        """

        估计两个集合的Jaccard相似度



        |A ∩ B| / |A ∪ B|

        """

        if not set1 or not set2:

            return 0.0



        sig1 = self._hash_items(set1)

        sig2 = self._hash_items(set2)



        # 统计相同位置哈希值的数量

        matches = sum(1 for s1, s2 in zip(sig1, sig2) if s1 == s2)

        return matches / self.num_hashes



    def exact_similarity(self, set1: set, set2: set) -> float:

        """精确Jaccard相似度"""

        intersection = len(set1 & set2)

        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0





class MinHashForest:

    """MinHash森林（用于近似最近邻搜索）"""



    def __init__(self, num_hashes: int = 100, num_trees: int = 10):

        self.num_hashes = num_hashes

        self.num_trees = num_trees

        self.minhash = MinHash(num_hashes)

        self.documents = {}  # doc_id -> set



    def add_document(self, doc_id: str, words: list):

        """添加文档"""

        self.documents[doc_id] = set(words)



    def find_similar(self, doc_id: str, top_k: int = 5) -> list:

        """查找最相似的k个文档"""

        if doc_id not in self.documents:

            return []



        target_set = self.documents[doc_id]

        similarities = []



        for other_id, other_set in self.documents.items():

            if other_id == doc_id:

                continue

            sim = self.minhash.estimate_similarity(target_set, other_set)

            similarities.append((other_id, sim))



        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== MinHash 测试 ===\n")



    # 测试文档相似度

    doc1_words = ["python", "java", "c++", "programming", "software", "code", "algorithm"]

    doc2_words = ["python", "java", "programming", "development", "software"]

    doc3_words = ["basketball", "football", "sports", "game", "player"]



    mh = MinHash(num_hashes=50)



    # 计算相似度

    set1 = set(doc1_words)

    set2 = set(doc2_words)

    set3 = set(doc3_words)



    print("文档相似度：")

    print(f"  doc1 vs doc2 (编程相关):")

    exact = mh.exact_similarity(set1, set2)

    estimate = mh.estimate_similarity(set1, set2)

    print(f"    精确Jaccard: {exact:.4f}")

    print(f"    MinHash估计: {estimate:.4f}")



    print(f"\n  doc1 vs doc3 (不同领域):")

    exact = mh.exact_similarity(set1, set3)

    estimate = mh.estimate_similarity(set1, set3)

    print(f"    精确Jaccard: {exact:.4f}")

    print(f"    MinHash估计: {estimate:.4f}")



    print(f"\n  doc2 vs doc3:")

    exact = mh.exact_similarity(set2, set3)

    estimate = mh.estimate_similarity(set2, set3)

    print(f"    精确Jaccard: {exact:.4f}")

    print(f"    MinHash估计: {estimate:.4f}")



    # 性能测试

    import time



    print("\n--- 性能测试 ---")

    sizes = [100, 1000, 10000]



    for size in sizes:

        # 生成两个大集合

        set_a = set(f"word_{i}" for i in range(size))

        set_b = set(f"word_{i}" for i in range(size // 2, size + size // 2))



        mh_test = MinHash(num_hashes=100)



        # MinHash估计

        start = time.time()

        est = mh_test.estimate_similarity(set_a, set_b)

        mh_time = time.time() - start



        # 精确计算

        start = time.time()

        exc = mh_test.exact_similarity(set_a, set_b)

        ex_time = time.time() - start



        print(f"  n={size:5d}: MinHash={mh_time*1000:.2f}ms, 精确={ex_time*1000:.2f}ms, 估计={est:.3f}, 精确={exc:.3f}")



    print("\n说明：")

    print("  - MinHash将集合映射为固定长度的签名")

    print("  - 签名相似度 ≈ Jaccard相似度")

    print("  - 用于大规模集合相似度搜索（搜索引擎、推荐系统）")

