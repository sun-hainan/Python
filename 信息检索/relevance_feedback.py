# -*- coding: utf-8 -*-
"""
算法实现：信息检索 / relevance_feedback

本文件实现 relevance_feedback 相关的算法功能。
"""

import math
from typing import List, Dict, Tuple, Set


class RocchioRelevanceFeedback:
    """Rocchio相关性反馈"""

    def __init__(self, alpha: float = 1.0, beta: float = 0.75, gamma: float = 0.25):
        """
        参数：
            alpha: 原始查询权重
            beta: 相关文档权重
            gamma: 不相关文档权重
        """
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

    def compute_new_query(self, original_query: Dict[str, float],
                        relevant_docs: List[Dict[str, float]],
                        non_relevant_docs: List[Dict[str, float]],
                        vocab: List[str]) -> Dict[str, float]:
        """
        计算新查询向量

        参数：
            original_query: 原始查询 {term: weight}
            relevant_docs: 相关文档列表 [{term: weight}, ...]
            non_relevant_docs: 不相关文档列表
            vocab: 词汇表

        返回：新查询向量
        """
        new_query = {}

        # α * Q
        for term, weight in original_query.items():
            new_query[term] = self.alpha * weight

        # β * (1/|R|) * ΣDr
        if relevant_docs:
            beta_factor = self.beta / len(relevant_docs)
            for term in vocab:
                term_sum = sum(doc.get(term, 0) for doc in relevant_docs)
                if term not in new_query:
                    new_query[term] = 0
                new_query[term] += beta_factor * term_sum

        # -γ * (1/|N|) * ΣDn
        if non_relevant_docs:
            gamma_factor = self.gamma / len(non_relevant_docs)
            for term in vocab:
                term_sum = sum(doc.get(term, 0) for doc in non_relevant_docs)
                if term not in new_query:
                    new_query[term] = 0
                new_query[term] -= gamma_factor * term_sum

        # 移除负值
        new_query = {k: max(0, v) for k, v in new_query.items()}

        return new_query

    def cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """计算余弦相似度"""
        dot = sum(vec1.get(t, 0) * vec2.get(t, 0) for t in set(vec1) | set(vec2))
        norm1 = math.sqrt(sum(v*v for v in vec1.values()))
        norm2 = math.sqrt(sum(v*v for v in vec2.values()))

        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 相关性反馈测试 ===\n")

    # 简化示例
    vocab = ["python", "java", "machine", "learning", "data", "science"]

    # 原始查询
    original_query = {"python": 0.5, "java": 0.3, "programming": 0.2}

    # 用户反馈
    relevant = [
        {"python": 0.8, "machine": 0.6, "learning": 0.5},
        {"python": 0.7, "data": 0.4, "science": 0.3},
    ]

    non_relevant = [
        {"java": 0.9, "enterprise": 0.5},
    ]

    rocchio = RocchioRelevanceFeedback(alpha=1.0, beta=0.75, gamma=0.15)
    new_query = rocchio.compute_new_query(original_query, relevant, non_relevant, vocab)

    print(f"原始查询: {original_query}")
    print(f"\n新查询: {new_query}")

    # 找最高权重的词
    sorted_terms = sorted(new_query.items(), key=lambda x: x[1], reverse=True)
    print(f"\n按权重排序: {sorted_terms[:5]}")

    print("\n说明：")
    print("  - Rocchio是经典的相关反馈算法")
    print("  - 用于搜索引擎的查询优化")
    print("  - 实际系统可能用点击数据代替显式反馈")
