"""
文本搜索与排序模块

本模块实现综合的文本搜索和排序系统。
整合倒排索引、向量搜索和学习的排序模型。

核心方法：
1. 倒排索引：高效的词项到文档映射
2. 向量搜索：语义相似度检索
3. 学习排序：结合多特征的智能排序
4. 分数融合：混合多路检索结果
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Tuple, Dict, Optional, Set
from collections import defaultdict, Counter
import math
import heapq


class InvertedIndex:
    """倒排索引"""

    def __init__(self):
        self.index = defaultdict(list)  # term -> [(doc_id, tf), ...]
        self.doc_freqs = Counter()     # term -> doc frequency
        self.doc_lengths = {}          # doc_id -> length
        self.num_docs = 0

    def add_document(self, doc_id: str, tokens: List[str]):
        """添加文档到索引"""
        tf = Counter(tokens)
        self.doc_lengths[doc_id] = len(tokens)

        for term, freq in tf.items():
            self.index[term].append((doc_id, freq))
            self.doc_freqs[term] += 1

        self.num_docs += 1

    def get_postings(self, term: str) -> List[Tuple[str, int]]:
        """获取词项的倒排列表"""
        return self.index.get(term, [])

    def search(self, query_tokens: List[str], top_k: int = 10) -> List[Tuple[str, float]]:
        """
        搜索相关文档
        :return: [(doc_id, score)]
        """
        scores = defaultdict(float)

        for term in query_tokens:
            postings = self.get_postings(term)
            if not postings:
                continue

            # IDF权重
            df = self.doc_freqs.get(term, 0)
            idf = math.log((self.num_docs + 1) / (df + 1)) + 1

            for doc_id, tf in postings:
                # TF-IDF评分
                scores[doc_id] += tf * idf

        # 归一化
        for doc_id in scores:
            doc_len = self.doc_lengths.get(doc_id, 1)
            scores[doc_id] /= math.sqrt(doc_len)

        # 取top-k
        top_items = heapq.nlargest(top_k, scores.items(), key=lambda x: x[1])
        return top_items


class VectorStore:
    """向量存储"""

    def __init__(self, dimension: int):
        self.dimension = dimension
        self.doc_vectors = {}  # doc_id -> vector
        self.doc_texts = {}    # doc_id -> text

    def add(self, doc_id: str, vector: np.ndarray, text: str = ""):
        """添加文档向量"""
        # L2归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        self.doc_vectors[doc_id] = vector
        self.doc_texts[doc_id] = text

    def search(self, query_vector: np.ndarray, top_k: int = 10) -> List[Tuple[str, float]]:
        """向量相似度搜索"""
        # 归一化
        norm = np.linalg.norm(query_vector)
        if norm > 0:
            query_vector = query_vector / norm

        scores = []
        for doc_id, doc_vector in self.doc_vectors.items():
            sim = np.dot(query_vector, doc_vector)
            scores.append((doc_id, float(sim)))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class FeatureExtractor:
    """特征提取器"""

    def __init__(self, inverted_index: InvertedIndex):
        self.inverted_index = inverted_index
        self.avg_doc_length = 0

    def compute_bm25(self, term: str, doc_id: str, doc_length: int,
                    k1: float = 1.5, b: float = 0.75) -> float:
        """计算BM25分数"""
        postings = self.inverted_index.get_postings(term)
        df = self.inverted_index.doc_freqs.get(term, 0)
        idf = math.log((self.inverted_index.num_docs - df + 0.5) / (df + 0.5) + 1)

        tf = 0
        for d, f in postings:
            if d == doc_id:
                tf = f
                break

        numerator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * doc_length / (self.avg_doc_length + 1))
        return idf * numerator / denominator

    def extract_features(self, query_tokens: List[str], doc_id: str) -> np.ndarray:
        """提取排序特征"""
        doc_length = self.inverted_index.doc_lengths.get(doc_id, 0)

        features = []
        for term in query_tokens:
            bm25 = self.compute_bm25(term, doc_id, doc_length)
            features.append(bm25)

        # 填充或截断到固定长度
        feature_dim = 20
        features = features[:feature_dim] + [0.0] * (feature_dim - len(features))
        return np.array(features)


class LearnedRanker(nn.Module):
    """学习型排序模型"""

    def __init__(self, feature_dim: int = 20, hidden_dim: int = 64):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(feature_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        """
        :param features: [batch, feature_dim]
        :return: [batch, 1]
        """
        return self.network(features)


class TextSearchEngine:
    """综合文本搜索引擎"""

    def __init__(self):
        self.inverted_index = InvertedIndex()
        self.vector_store = VectorStore(dimension=128)
        self.feature_extractor = FeatureExtractor(self.inverted_index)
        self.ranker = LearnedRanker(feature_dim=20)
        self.documents = {}  # doc_id -> text

    def index_document(self, doc_id: str, text: str, vector: Optional[np.ndarray] = None):
        """索引文档"""
        tokens = text.lower().split()
        self.inverted_index.add_document(doc_id, tokens)
        self.documents[doc_id] = text

        if vector is not None:
            self.vector_store.add(doc_id, vector, text)

    def search(self, query: str, query_vector: Optional[np.ndarray] = None,
               top_k: int = 10) -> List[Dict]:
        """
        搜索文档
        """
        query_tokens = query.lower().split()

        # 1. 倒排索引检索
        keyword_results = self.inverted_index.search(query_tokens, top_k=top_k * 2)

        # 2. 向量搜索（如果有）
        vector_results = []
        if query_vector is not None:
            vector_results = self.vector_store.search(query_vector, top_k=top_k * 2)

        # 3. 合并结果
        combined_results = {}
        for doc_id, score in keyword_results:
            combined_results[doc_id] = {
                "keyword_score": score,
                "vector_score": 0.0,
                "final_score": score
            }

        for doc_id, score in vector_results:
            if doc_id in combined_results:
                combined_results[doc_id]["vector_score"] = score
                combined_results[doc_id]["final_score"] = (
                    0.5 * combined_results[doc_id]["keyword_score"] +
                    0.5 * combined_results[doc_id]["vector_score"]
                )
            else:
                combined_results[doc_id] = {
                    "keyword_score": 0.0,
                    "vector_score": score,
                    "final_score": score
                }

        # 4. 排序
        sorted_results = sorted(
            combined_results.items(),
            key=lambda x: x[1]["final_score"],
            reverse=True
        )[:top_k]

        # 5. 构建输出
        results = []
        for rank, (doc_id, scores) in enumerate(sorted_results, 1):
            results.append({
                "doc_id": doc_id,
                "text": self.documents.get(doc_id, "")[:100],
                "rank": rank,
                "scores": scores
            })

        return results


class QueryUnderstanding:
    """查询理解"""

    def __init__(self):
        self.intent_keywords = {
            "informational": ["what", "who", "where", "when", "why", "how"],
            "navigational": ["official", "homepage", "website"],
            "transactional": ["buy", "download", "subscribe", "sign up"]
        }

    def understand(self, query: str) -> Dict:
        """
        理解查询意图
        :return: {intent, entities, modifiers}
        """
        query_lower = query.lower()

        # 意图分类
        intent = "informational"
        for intent_name, keywords in self.intent_keywords.items():
            if any(kw in query_lower for kw in keywords):
                intent = intent_name
                break

        # 实体识别（简单关键词）
        entities = []
        important_words = ["company", "person", "city", "country", "product"]
        for word in important_words:
            if word in query_lower:
                entities.append(word)

        # 修饰词
        modifiers = []
        if "latest" in query_lower or "recent" in query_lower:
            modifiers.append("temporal_recent")
        if "best" in query_lower or "top" in query_lower:
            modifiers.append("comparative_superlative")

        return {
            "intent": intent,
            "entities": entities,
            "modifiers": modifiers,
            "original_query": query
        }


def evaluate_search(results: List[Dict], relevant_docs: Set[str], k_values=[1, 5, 10]) -> Dict[str, float]:
    """评估搜索性能"""
    metrics = {}

    for k in k_values:
        retrieved_k = set(r["doc_id"] for r in results[:k])
        relevant_k = retrieved_k & relevant_docs

        recall = len(relevant_k) / len(relevant_docs) if relevant_docs else 0
        precision = len(relevant_k) / k if k > 0 else 0

        metrics[f"Recall@{k}"] = recall
        metrics[f"Precision@{k}"] = precision

        # MAP
        if k >= len(relevant_docs):
            ap = 0.0
            num_relevant = 0
            for i, r in enumerate(results[:k]):
                if r["doc_id"] in relevant_docs:
                    num_relevant += 1
                    ap += num_relevant / (i + 1)
            if relevant_docs:
                ap /= len(relevant_docs)
            metrics["MAP"] = ap

    return metrics


def demo():
    """文本搜索演示"""
    print("[文本搜索演示]")

    # 创建搜索引擎
    engine = TextSearchEngine()

    # 索引文档
    documents = [
        ("doc_1", "Apple Inc. is a technology company headquartered in Cupertino, California."),
        ("doc_2", "Apple fruit is delicious and grows in many regions around the world."),
        ("doc_3", "Machine learning algorithms enable computers to learn from data."),
        ("doc_4", "Deep learning neural networks are used for image recognition tasks."),
        ("doc_5", "Natural language processing helps computers understand human language.")
    ]

    for doc_id, text in documents:
        # 简单向量表示
        vector = np.random.randn(128)
        engine.index_document(doc_id, text, vector)

    print(f"  索引文档数: {len(engine.documents)}")

    # 查询理解
    querier = QueryUnderstanding()
    query = "What is Apple company?"
    understanding = querier.understand(query)
    print(f"\n  查询: '{query}'")
    print(f"  意图: {understanding['intent']}")
    print(f"  实体: {understanding['entities']}")

    # 搜索
    query_vector = np.random.randn(128)
    results = engine.search("Apple company", query_vector, top_k=3)

    print(f"\n  搜索结果:")
    for r in results:
        print(f"    Rank {r['rank']}: {r['doc_id']} (score={r['scores']['final_score']:.3f})")
        print(f"      {r['text'][:50]}...")

    # 评估
    relevant = {"doc_1"}
    metrics = evaluate_search(results, relevant, k_values=[1, 3])
    print(f"\n  评估指标:")
    for metric, value in metrics.items():
        print(f"    {metric}: {value:.4f}")

    print("  ✅ 文本搜索演示通过！")


if __name__ == "__main__":
    demo()
