# -*- coding: utf-8 -*-
"""
算法实现：软件工程算法 / semantic_search

本文件实现 semantic_search 相关的算法功能。
"""

from typing import List, Tuple, Optional
import math


# ============= 简化的 Embedding 模型（演示用）=============

class SimpleCodeEmbedding:
    """
    简化版代码嵌入器

    基于词袋（BoW）+ 位置加权的启发式嵌入。
    实际生产中应使用预训练模型（如 GraphCodeBERT、CodeBERT）。

    特征维度：
        - 代码操作符词频（op_tokens）
        - 数据类型词频（type_tokens）
        - API 调用词频（api_tokens）
        - 结构特征（缩进深度、循环/分支密度）
    """

    def __init__(self, dim: int = 64):
        # dim: 嵌入向量维度
        self.dim = dim
        # 操作符集合
        self.op_tokens = {"if", "else", "for", "while", "return", "def", "class",
                           "try", "except", "raise", "import", "yield", "lambda",
                           "and", "or", "not", "in", "is", "switch", "case", "break"}
        # 数据类型集合
        self.type_tokens = {"int", "str", "float", "bool", "list", "dict", "set",
                            "tuple", "void", "char", "long", "double", "int64", "uint32"}
        # API 关键词
        self.api_tokens = {"len", "print", "range", "map", "filter", "reduce",
                           "sort", "sorted", "enumerate", "zip", "open", "read",
                           "write", "http", "request", "query", "fetch", "save"}

    def tokenize(self, code: str) -> dict:
        """将代码 token 化为特征字典"""
        words = code.split()
        features = {
            "ops": sum(1 for w in words if w in self.op_tokens),
            "types": sum(1 for w in words if w in self.type_tokens),
            "apis": sum(1 for w in words if w in self.api_tokens),
            "loops": words.count("for") + words.count("while"),
            "conditionals": words.count("if"),
            "defs": words.count("def"),
            "classes": words.count("class"),
            "lines": code.count("\n") + 1,
            "indent_avg": self._avg_indent(code),
        }
        return features

    def _avg_indent(self, code: str) -> float:
        """计算平均缩进深度（衡量代码复杂度）"""
        lines = code.split("\n")
        indents = []
        for line in lines:
            stripped = line.lstrip("\t ")
            if stripped:
                indents.append(len(line) - len(stripped))
        return sum(indents) / len(indents) if indents else 0.0

    def embed(self, code: str) -> List[float]:
        """将代码映射为 dim 维向量"""
        features = self.tokenize(code)
        tokens = code.split()

        # ---- 构建词袋向量（截断到 dim//2 维度）----
        bow_dim = self.dim // 2
        all_tokens = set(tokens) & (self.op_tokens | self.type_tokens | self.api_tokens)
        token_list = sorted(all_tokens)[:bow_dim]
        token_idx = {t: i for i, t in enumerate(token_list)}

        vec = [0.0] * self.dim

        # 词袋部分（前半）
        for token in tokens:
            if token in token_idx:
                vec[token_idx[token]] += 1.0

        # 特征部分（后半）
        feat_start = bow_dim
        feat_vals = [
            float(features["ops"]),
            float(features["types"]),
            float(features["apis"]),
            float(features["loops"]),
            float(features["conditionals"]),
            float(features["defs"]),
            float(features["classes"]),
            float(features["lines"]),
            features["indent_avg"],
        ]
        for i, val in enumerate(feat_vals):
            if feat_start + i < self.dim:
                vec[feat_start + i] = val

        # L2 归一化
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """计算两个向量的余弦相似度"""
        dot = sum(av * bv for av, bv in zip(a, b))
        return dot  # 归一化后 dot 即为 cos 相似度


class SemanticCodeSearcher:
    """代码语义搜索引擎"""

    def __init__(self, embedding_model: Optional[SimpleCodeEmbedding] = None):
        self.embedding_model = embedding_model or SimpleCodeEmbedding(dim=64)
        # code_base: 代码库，每项为 (id, code_snippet, embedding)
        self.code_base: List[Tuple[int, str, List[float]]] = []

    def index(self, code_snippets: List[str]):
        """将代码片段批量索引"""
        self.code_base = []
        for idx, snippet in enumerate(code_snippets):
            emb = self.embedding_model.embed(snippet)
            self.code_base.append((idx, snippet, emb))

    def search(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.3,
    ) -> List[Tuple[int, str, float]]:
        """
        语义搜索

        Args:
            query:    查询代码片段
            top_k:    返回前 top_k 个结果
            min_similarity: 最低相似度阈值

        Returns:
            List of (id, code_snippet, similarity_score)
        """
        query_emb = self.embedding_model.embed(query)

        results: List[Tuple[int, str, float]] = []
        for idx, snippet, emb in self.code_base:
            sim = self.embedding_model.cosine_similarity(query_emb, emb)
            if sim >= min_similarity:
                results.append((idx, snippet, sim))

        # 按相似度降序排序
        results.sort(key=lambda x: x[2], reverse=True)
        return results[:top_k]


if __name__ == "__main__":
    print("=" * 50)
    print("代码语义搜索（Semantic Code Search）- 单元测试")
    print("=" * 50)

    # 代码库示例
    code_corpus = [
        "def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1",
        "def quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quicksort(left) + middle + quicksort(right)",
        "def bubble_sort(arr):\n    n = len(arr)\n    for i in range(n):\n        for j in range(0, n - i - 1):\n            if arr[j] > arr[j + 1]:\n                arr[j], arr[j + 1] = arr[j + 1], arr[j]\n    return arr",
        "class LRUCache:\n    def __init__(self, capacity):\n        self.capacity = capacity\n        self.cache = {}\n        self.order = []\n\n    def get(self, key):\n        if key in self.cache:\n            self.order.remove(key)\n            self.order.append(key)\n            return self.cache[key]\n        return -1",
        "def fibonacci(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a",
        "def merge_sort(arr):\n    if len(arr) <= 1:\n        return arr\n    mid = len(arr) // 2\n    left = merge_sort(arr[:mid])\n    right = merge_sort(arr[mid:])\n    return merge(left, right)",
    ]

    searcher = SemanticCodeSearcher()
    searcher.index(code_corpus)

    # 查询
    queries = [
        "排序数组，用递归的方式",
        "折半查找目标元素",
        "缓存机制，最近最少使用",
        "斐波那契数列迭代计算",
    ]

    print("\n语义搜索测试:")
    for q in queries:
        print(f"\n查询: '{q}'")
        results = searcher.search(q, top_k=3, min_similarity=0.2)
        if results:
            for idx, snippet, sim in results:
                first_line = snippet.split("\n")[0][:60]
                print(f"  [相似度={sim:.3f}] {first_line}")
        else:
            print("  无匹配结果")

    # 测试相似度计算
    print("\n直接相似度测试（排序算法内部相似度）:")
    sim = searcher.embedding_model.cosine_similarity(
        searcher.embedding_model.embed(code_corpus[1]),  # quicksort
        searcher.embedding_model.embed(code_corpus[2]),  # bubble_sort
    )
    print(f"  quicksort vs bubble_sort: {sim:.4f}")

    print(f"\n复杂度: O(N * D) 索引 + O(K * D) 搜索（N=代码库大小，D=嵌入维度）")
    print("注意: 此为简化演示，生产环境应使用预训练代码嵌入模型（如 CodeBERT）")
    print("算法完成。")
