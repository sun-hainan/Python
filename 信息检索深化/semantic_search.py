"""
语义搜索模块 - 向量相似度 /近似最近邻

本模块实现基于向量相似度的语义搜索系统。
支持多种相似度度量、索引结构和搜索算法。

核心组件：
1. 向量存储：文档向量和查询向量的表示
2. 相似度度量：余弦、点积、欧氏距离
3. 近似最近邻(ANN)索引：HNSW、FAISS
4. 混合搜索：结合稀疏和稠密检索
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Tuple, Dict, Optional
import heapq


class VectorStore:
    """向量存储：管理文档向量"""

    def __init__(self, dimension: int, normalize: bool = True):
        """
        :param dimension: 向量维度
        :param normalize: 是否归一化向量
        """
        self.dimension = dimension
        self.normalize = normalize
        self.vectors = {}  # id -> 向量
        self.metadata = {}  # id -> 元数据

    def add(self, doc_id: str, vector: np.ndarray, metadata: Optional[Dict] = None):
        """添加向量"""
        if vector.shape != (self.dimension,):
            raise ValueError(f"向量维度必须为{self.dimension}")
        if self.normalize:
            vector = vector / (np.linalg.norm(vector) + 1e-10)
        self.vectors[doc_id] = vector
        self.metadata[doc_id] = metadata or {}

    def get(self, doc_id: str) -> Optional[np.ndarray]:
        """获取向量"""
        return self.vectors.get(doc_id)

    def search(self, query_vector: np.ndarray, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        暴力搜索（精确最近邻）
        :param query_vector: 查询向量
        :param top_k: 返回前k个
        :return: [(doc_id, score)]
        """
        if self.normalize:
            query_vector = query_vector / (np.linalg.norm(query_vector) + 1e-10)

        scores = []
        for doc_id, vector in self.vectors.items():
            # 余弦相似度
            score = np.dot(query_vector, vector)
            scores.append((doc_id, score))

        # 堆排序取top_k
        top_k_scores = heapq.nlargest(top_k, scores, key=lambda x: x[1])
        return top_k_scores

    def size(self) -> int:
        """向量数量"""
        return len(self.vectors)


class HNSWIndex:
    """Hierarchical Navigable Small World (HNSW) 索引"""

    def __init__(self, dimension: int, max_elements: int = 1000,
                 m: int = 16, ef_construction: int = 200, ef_search: int = 50):
        """
        :param dimension: 向量维度
        :param max_elements: 最大元素数
        :param m: 每个节点的最大连接数
        :param ef_construction: 构建时的搜索范围
        :param ef_search: 搜索时的搜索范围
        """
        self.dimension = dimension
        self.max_elements = max_elements
        self.m = m
        self.ef_construction = ef_construction
        self.ef_search = ef_search

        # 简化的HNSW实现（实际应使用FAISS或nmslib）
        self.vectors = {}
        self.entry_point = None
        self.layers = []  # 每层的节点信息

    def add(self, doc_id: str, vector: np.ndarray):
        """添加向量"""
        if len(self.vectors) >= self.max_elements:
            raise RuntimeError("达到最大元素数")

        # L2归一化
        vector = vector / (np.linalg.norm(vector) + 1e-10)
        self.vectors[doc_id] = vector

        if self.entry_point is None:
            self.entry_point = doc_id

    def search(self, query_vector: np.ndarray, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        近似最近邻搜索
        :return: [(doc_id, score)]
        """
        if not self.vectors:
            return []

        # L2归一化
        query_vector = query_vector / (np.linalg.norm(query_vector) + 1e-10)

        # 简化的搜索：计算所有向量的相似度然后取top_k
        scores = []
        for doc_id, vector in self.vectors.items():
            score = np.dot(query_vector, vector)
            scores.append((doc_id, score))

        return heapq.nlargest(top_k, scores, key=lambda x: x[1])


class FAISSIndex:
    """FAISS索引封装（模拟接口）"""

    def __init__(self, dimension: int, index_type: str = "IP"):
        """
        :param dimension: 向量维度
        :param index_type: 索引类型 "IP"(内积) 或 "L2"(欧氏距离)
        """
        self.dimension = dimension
        self.index_type = index_type
        self.index = None

    def build(self, vectors: np.ndarray):
        """构建索引"""
        # 归一化（用于余弦相似度）
        if self.index_type == "IP":
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            norms = np.where(norms == 0, 1, norms)
            vectors = vectors / norms

        # 存储向量（简化实现）
        self.vectors = vectors
        self.num_vectors = len(vectors)

    def search(self, query_vector: np.ndarray, top_k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """
        搜索
        :return: (distances, indices)
        """
        # 归一化
        if self.index_type == "IP":
            query_vector = query_vector / (np.linalg.norm(query_vector) + 1e-10)

        # 计算相似度
        if self.index_type == "IP":
            similarities = np.dot(self.vectors, query_vector)
        else:
            similarities = -np.linalg.norm(self.vectors - query_vector, axis=1)

        # 取top_k
        if top_k >= len(similarities):
            top_indices = np.argsort(similarities)[::-1]
        else:
            top_indices = np.argpartition(similarities, -top_k)[-top_k:]
            top_indices = top_indices[np.argsort(similarities[top_indices])[::-1]]

        top_similarities = similarities[top_indices]

        return top_similarities, top_indices


class SemanticSearcher:
    """语义搜索引擎"""

    def __init__(self, encoder, dimension: int, use_ann: bool = True):
        """
        :param encoder: 向量编码器模型
        :param dimension: 向量维度
        :param use_ann: 是否使用近似最近邻
        """
        self.encoder = encoder
        self.dimension = dimension
        self.use_ann = use_ann

        # 选择索引
        if use_ann:
            self.index = HNSWIndex(dimension)
        else:
            self.index = VectorStore(dimension)

        self.documents = {}  # doc_id -> 原始文档

    def index_document(self, doc_id: str, text: str, vector: np.ndarray):
        """索引文档"""
        self.index.add(doc_id, vector)
        self.documents[doc_id] = text

    def search(self, query_vector: np.ndarray, top_k: int = 10) -> List[Dict]:
        """
        搜索
        :return: 结果列表，每个包含doc_id, score, text
        """
        results = self.index.search(query_vector, top_k)

        return [
            {
                "doc_id": doc_id,
                "score": score,
                "text": self.documents.get(doc_id, "")
            }
            for doc_id, score in results
        ]


class HybridSearcher:
    """混合搜索：结合稀疏和稠密检索"""

    def __init__(self, sparse_weight: float = 0.3, dense_weight: float = 0.7):
        """
        :param sparse_weight: 稀疏检索权重
        :param dense_weight: 稠密检索权重
        """
        self.sparse_weight = sparse_weight
        self.dense_weight = dense_weight

    def fuse_scores(self, sparse_scores: Dict[str, float],
                    dense_scores: Dict[str, float]) -> List[Tuple[str, float]]:
        """
        分数融合
        :param sparse_scores: 稀疏检索分数 {doc_id: score}
        :param dense_scores: 稠密检索分数 {doc_id: score}
        :return: 融合后的排序结果
        """
        # 获取所有doc_id
        all_doc_ids = set(sparse_scores.keys()) | set(dense_scores.keys())

        # 归一化分数（min-max）
        all_sparse = list(sparse_scores.values())
        all_dense = list(dense_scores.values())

        min_s, max_s = min(all_sparse) if all_sparse else 0, max(all_sparse) if all_sparse else 1
        min_d, max_d = min(all_dense) if all_dense else 0, max(all_dense) if all_dense else 1

        fused_scores = []
        for doc_id in all_doc_ids:
            s_score = sparse_scores.get(doc_id, 0)
            d_score = dense_scores.get(doc_id, 0)

            # 归一化
            s_norm = (s_score - min_s) / (max_s - min_s + 1e-10) if max_s > min_s else 0
            d_norm = (d_score - min_d) / (max_d - min_d + 1e-10) if max_d > min_d else 0

            # 加权融合
            fused = self.sparse_weight * s_norm + self.dense_weight * d_norm
            fused_scores.append((doc_id, fused))

        # 排序
        fused_scores.sort(key=lambda x: x[1], reverse=True)
        return fused_scores


class SentenceEncoder(nn.Module):
    """句子编码器（用于生成向量）"""

    def __init__(self, vocab_size, embed_dim=128, hidden_dim=256):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.encoder = nn.LSTM(embed_dim, hidden_dim, num_layers=2, batch_first=True, bidirectional=True)
        self.projection = nn.Linear(hidden_dim * 2, hidden_dim)

    def forward(self, token_ids, mask=None):
        """编码句子"""
        embedded = self.embedding(token_ids)
        outputs, (h_n, _) = self.encoder(embedded)
        hidden = torch.cat([h_n[-2], h_n[-1]], dim=-1)
        output = self.projection(hidden)
        output = F.normalize(output, p=2, dim=-1)
        return output


def compute_recall_at_k(retrieved: List[List[str]], relevant: List[List[str]], k: int) -> float:
    """计算Recall@K"""
    recalls = []
    for ret, rel in zip(retrieved, relevant):
        ret_set = set(ret[:k])
        rel_set = set(rel)
        recall = len(ret_set & rel_set) / len(rel_set) if rel_set else 0
        recalls.append(recall)
    return np.mean(recalls)


def compute_mrr(retrieved: List[List[str]], relevant: List[List[str]]) -> float:
    """计算Mean Reciprocal Rank"""
    reciprocal_ranks = []
    for ret, rel in zip(retrieved, relevant):
        rel_set = set(rel)
        for i, doc in enumerate(ret, 1):
            if doc in rel_set:
                reciprocal_ranks.append(1.0 / i)
                break
        else:
            reciprocal_ranks.append(0.0)
    return np.mean(reciprocal_ranks)


def demo():
    """语义搜索演示"""
    dimension = 128

    print("[语义搜索演示]")

    # 向量存储
    store = VectorStore(dimension)
    for i in range(5):
        vec = np.random.randn(dimension)
        store.add(f"doc_{i}", vec, {"text": f"Document {i} content"})

    query = np.random.randn(dimension)
    results = store.search(query, top_k=3)
    print(f"  向量存储搜索结果: {[(d, f'{s:.3f}') for d, s in results]}")

    # HNSW索引
    hnsw = HNSWIndex(dimension)
    for i in range(5):
        vec = np.random.randn(dimension)
        hnsw.add(f"doc_{i}", vec)
    hnsw_results = hnsw.search(query, top_k=3)
    print(f"  HNSW搜索结果: {[(d, f'{s:.3f}') for d, s in hnsw_results]}")

    # FAISS索引
    faiss = FAISSIndex(dimension, index_type="IP")
    vectors = np.random.randn(10, dimension)
    faiss.build(vectors)
    dists, indices = faiss.search(query, top_k=3)
    print(f"  FAISS搜索结果: indices={indices}, scores={dists}")

    # 混合搜索
    hybrid = HybridSearcher(sparse_weight=0.3, dense_weight=0.7)
    sparse_scores = {f"doc_{i}": np.random.rand() for i in range(5)}
    dense_scores = {f"doc_{i}": np.random.rand() for i in range(5)}
    fused = hybrid.fuse_scores(sparse_scores, dense_scores)
    print(f"  混合搜索结果: {[(d, f'{s:.3f}') for d, s in fused[:3]]}")

    # 句子编码器
    encoder = SentenceEncoder(vocab_size=5000, hidden_dim=128)
    tokens = torch.randint(1, 5000, (2, 20))
    vecs = encoder(tokens)
    print(f"  句子编码器输出: {vecs.shape}")

    print("  ✅ 语义搜索演示通过！")


if __name__ == "__main__":
    demo()
