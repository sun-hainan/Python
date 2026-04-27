# -*- coding: utf-8 -*-

"""

算法实现：细粒度复杂性 / minhash



本文件实现 minhash 相关的算法功能。

"""



import hashlib

from typing import List, Set





class MinHash:

    """

    MinHash算法

    使用多个哈希函数找最小哈希值来估计Jaccard相似度

    """

    

    def __init__(self, num_hashes: int = 100, seed: int = 42):

        """

        初始化

        

        Args:

            num_hashes: 哈希函数数量

            seed: 随机种子

        """

        self.num_hashes = num_hashes

        self.seed = seed

        

        # 预生成哈希函数参数

        self._generate_hash_functions()

    

    def _generate_hash_functions(self):

        """生成哈希函数参数"""

        import random

        

        random.seed(self.seed)

        

        # 对于每个哈希函数,生成a和b参数

        # h(x) = (a*x + b) mod large_prime

        self.hash_params = []

        for _ in range(self.num_hashes):

            a = random.randint(1, 2**31 - 1)

            b = random.randint(0, 2**31 - 1)

            self.hash_params.append((a, b))

    

    def _hash(self, item: str, a: int, b: int) -> int:

        """计算单个哈希值"""

        h = hashlib.sha256(f"{a}{item}{b}".encode()).hexdigest()

        return int(h, 16) % (2**31 - 1)

    

    def _compute_signature(self, items: Set[str]) -> List[int]:

        """计算集合的签名"""

        signature = [float('inf')] * self.num_hashes

        

        for item in items:

            for i, (a, b) in enumerate(self.hash_params):

                h = self._hash(item, a, b)

                signature[i] = min(signature[i], h)

        

        return signature

    

    def estimate_jaccard(self, set1: Set[str], set2: Set[str]) -> float:

        """

        估计两个集合的Jaccard相似度

        

        Args:

            set1: 集合1

            set2: 集合2

        

        Returns:

            估计的Jaccard相似度

        """

        if not set1 or not set2:

            return 0.0

        

        sig1 = self._compute_signature(set1)

        sig2 = self._compute_signature(set2)

        

        # 统计相同签名的数量

        matches = sum(1 for i in range(self.num_hashes) if sig1[i] == sig2[i])

        

        return matches / self.num_hashes

    

    def containment(self, set1: Set[str], set2: Set[str]) -> float:

        """

        估计set1在set2中的包含度

        

        Args:

            set1: 子集

            set2: 超集

        

        Returns:

            估计的包含度

        """

        if not set1:

            return 0.0

        

        sig1 = self._compute_signature(set1)

        sig2 = self._compute_signature(set2)

        

        matches = sum(1 for i in range(self.num_hashes) if sig1[i] == sig2[i])

        

        return matches / self.num_hashes





class MinHashIndex:

    """

    MinHash索引

    用于快速查找相似集合

    """

    

    def __init__(self, num_hashes: int = 100):

        self.minhash = MinHash(num_hashes)

        self.signatures = {}

    

    def add(self, id: str, items: Set[str]):

        """添加集合"""

        sig = self.minhash._compute_signature(items)

        self.signatures[id] = sig

    

    def find_similar(self, items: Set[str], threshold: float = 0.5, 

                    top_k: int = 10) -> List[tuple]:

        """

        查找相似集合

        

        Args:

            items: 查询集合

            threshold: 相似度阈值

            top_k: 返回前k个

        

        Returns:

            [(id, similarity), ...]

        """

        query_sig = self.minhash._compute_signature(items)

        

        results = []

        for id, sig in self.signatures.items():

            matches = sum(1 for i in range(self.minhash.num_hashes) 

                        if query_sig[i] == sig[i])

            similarity = matches / self.minhash.num_hashes

            

            if similarity >= threshold:

                results.append((id, similarity))

        

        results.sort(key=lambda x: -x[1])

        return results[:top_k]





# 测试代码

if __name__ == "__main__":

    # 测试1: 基本功能

    print("测试1 - 基本功能:")

    mh = MinHash(50)

    

    set1 = {"apple", "banana", "cherry", "date"}

    set2 = {"banana", "cherry", "elderberry", "fig"}

    set3 = {"grape", "hazelnut", "apple"}

    

    sim_12 = mh.estimate_jaccard(set1, set2)

    sim_13 = mh.estimate_jaccard(set1, set3)

    sim_23 = mh.estimate_jaccard(set2, set3)

    

    print(f"  集合1: {set1}")

    print(f"  集合2: {set2}")

    print(f"  集合3: {set3}")

    print(f"  相似度(1,2): {sim_12:.4f}")

    print(f"  相似度(1,3): {sim_13:.4f}")

    print(f"  相似度(2,3): {sim_23:.4f}")

    

    # 精确Jaccard

    def exact_jaccard(s1, s2):

        return len(s1 & s2) / len(s1 | s2)

    

    print(f"\n  精确Jaccard(1,2): {exact_jaccard(set1, set2):.4f}")

    

    # 测试2: 大规模测试

    print("\n测试2 - 大规模:")

    import random

    

    random.seed(42)

    

    # 生成大集合

    universe = list(range(10000))

    set_a = set(random.sample(universe, 1000))

    set_b = set(random.sample(universe, 1000))

    

    # 估计相似度

    mh_large = MinHash(200)

    est_sim = mh_large.estimate_jaccard(set_a, set_b)

    exact_sim = exact_jaccard(set_a, set_b)

    

    print(f"  估计相似度: {est_sim:.4f}")

    print(f"  精确相似度: {exact_sim:.4f}")

    print(f"  误差: {abs(est_sim - exact_sim):.4f}")

    

    # 测试3: 索引查找

    print("\n测试3 - 索引查找:")

    index = MinHashIndex(100)

    

    documents = {

        "doc1": {"python", "java", "programming", "code"},

        "doc2": {"python", "machine", "learning", "ai"},

        "doc3": {"java", "spring", "backend", "web"},

        "doc4": {"python", "data", "science", "ml"},

        "doc5": {"javascript", "web", "frontend", "react"},

    }

    

    for id, words in documents.items():

        index.add(id, words)

    

    query = {"python", "learning", "data"}

    similar = index.find_similar(query, threshold=0.1)

    

    print(f"  查询: {query}")

    print(f"  相似文档:")

    for doc_id, sim in similar:

        print(f"    {doc_id}: {sim:.4f}")

    

    # 测试4: 包含度估计

    print("\n测试4 - 包含度:")

    set_parent = {"apple", "banana", "cherry", "date", "elderberry"}

    set_child = {"apple", "banana", "cherry"}

    set_unrelated = {"fig", "grape"}

    

    mh_cont = MinHash(100)

    cont_parent_child = mh_cont.containment(set_child, set_parent)

    cont_unrelated = mh_cont.containment(set_unrelated, set_parent)

    

    print(f"  子集在父集中: {cont_parent_child:.4f}")

    print(f"  不相关在父集中: {cont_unrelated:.4f}")

    

    print("\n所有测试完成!")

