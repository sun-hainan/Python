"""
潜在语义索引模块 (LSI)

本模块实现Latent Semantic Indexing（潜在语义索引）系统。
LSI通过SVD分解将词-文档矩阵降维，捕获潜在的语义结构。

核心方法：
1. 构建词-文档矩阵（TF-IDF加权）
2. SVD奇异值分解
3. 降维表示
4. 相似度计算和检索
"""

import numpy as np
from typing import List, Tuple, Dict
from collections import Counter
import math


class Tokenizer:
    """简单分词器"""

    @staticmethod
    def tokenize(text: str) -> List[str]:
        text = text.lower()
        words = text.replace(',', ' ').replace('.', ' ').split()
        return [w for w in words if len(w) > 1]


class TFIDfMatrix:
    """TF-IDF矩阵构建器"""

    def __init__(self):
        self.documents = []
        self.vocab = []
        self.vocab_to_idx = {}
        self.doc_count = 0

    def fit(self, documents: List[str], min_df: int = 1, max_df: float = 1.0):
        """
        构建词表和文档频率统计
        :param documents: 文档列表
        :param min_df: 最小文档频率
        :param max_df: 最大文档频率比例
        """
        self.documents = documents
        self.doc_count = len(documents)

        # 统计词频和文档频率
        word_doc_freq = Counter()
        word_total_freq = Counter()

        for doc in documents:
            tokens = Tokenizer.tokenize(doc)
            unique_tokens = set(tokens)
            for token in unique_tokens:
                word_doc_freq[token] += 1
            for token in tokens:
                word_total_freq[token] += 1

        # 构建词表
        max_df_count = int(max_df * self.doc_count)
        self.vocab = [
            word for word, freq in word_doc_freq.items()
            if freq >= min_df and freq <= max_df_count
        ]
        self.vocab_to_idx = {w: i for i, w in enumerate(self.vocab)}

    def get_tf(self, tokens: List[str]) -> np.ndarray:
        """计算TF向量"""
        tf = Counter(tokens)
        total = len(tokens)
        tf_vector = np.zeros(len(self.vocab))

        for word, count in tf.items():
            if word in self.vocab_to_idx:
                tf_vector[self.vocab_to_idx[word]] = count / total if total > 0 else 0

        return tf_vector

    def get_idf(self) -> np.ndarray:
        """计算IDF向量"""
        idf = np.zeros(len(self.vocab))
        for i, word in enumerate(self.vocab):
            doc_freq = sum(1 for doc in self.documents if word in Tokenizer.tokenize(doc))
            idf[i] = math.log((self.doc_count + 1) / (doc_freq + 1)) + 1
        return idf

    def get_tfidf(self, document: str) -> np.ndarray:
        """计算TF-IDF向量"""
        tokens = Tokenizer.tokenize(document)
        tf = self.get_tf(tokens)
        idf = self.get_idf()
        return tf * idf

    def build_matrix(self) -> np.ndarray:
        """构建完整的词-文档TF-IDF矩阵"""
        num_terms = len(self.vocab)
        matrix = np.zeros((num_terms, self.doc_count))

        for doc_idx, doc in enumerate(self.documents):
            tfidf = self.get_tfidf(doc)
            matrix[:, doc_idx] = tfidf

        return matrix


class LSI:
    """潜在语义索引"""

    def __init__(self, num_topics: int = 100):
        """
        :param num_topics: 潜在主题数（降维维度）
        """
        self.num_topics = num_topics
        self.U = None  # 左奇异向量
        self.S = None  # 奇异值
        self.Vt = None  # 右奇异向量（转置）
        self.transformed_docs = None  # 文档的降维表示
        self.tfidf_matrix = None
        self.tfidf_builder = None

    def fit(self, documents: List[str]):
        """训练LSI模型"""
        # 构建TF-IDF矩阵
        self.tfidf_builder = TFIDfMatrix()
        self.tfidf_builder.fit(documents)
        self.tfidf_matrix = self.tfidf_builder.build_matrix()

        # 中心化（可选）
        # self.tfidf_matrix = self.tfidf_matrix - self.tfidf_matrix.mean(axis=1, keepdims=True)

        # SVD分解: A = U * S * Vt
        # 这里使用截断SVD
        self.U, self.S, self.Vt = np.linalg.svd(
            self.tfidf_matrix,
            full_matrices=False
        )

        # 截断到指定维度
        if self.num_topics < len(self.S):
            self.U = self.U[:, :self.num_topics]
            self.S = self.S[:self.num_topics]
            self.Vt = self.Vt[:self.num_topics, :]

        # 变换文档
        self.transformed_docs = self.S.reshape(-1, 1) * self.Vt  # [num_topics, num_docs]

    def transform_document(self, document: str) -> np.ndarray:
        """将新文档变换到LSI空间"""
        # 获取TF-IDF向量
        tfidf_vector = self.tfidf_builder.get_tfidf(document)  # [vocab_size]

        # 投影到LSI空间: doc' = S^(-1) * U^T * doc
        U_t = self.U.T  # [num_topics, vocab_size]
        tfidf_reshaped = tfidf_vector.reshape(-1, 1)  # [vocab_size, 1]

        # 加权投影
        doc_lsi = np.dot(U_t, tfidf_reshaped).squeeze() / (self.S + 1e-10)

        return doc_lsi

    def similarity(self, doc1_idx: int, doc2_idx: int) -> float:
        """计算两个文档的余弦相似度"""
        vec1 = self.transformed_docs[:, doc1_idx]
        vec2 = self.transformed_docs[:, doc2_idx]

        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return np.dot(vec1, vec2) / (norm1 * norm2)

    def search(self, query: str, top_k: int = 5) -> List[Tuple[int, float]]:
        """搜索相关文档"""
        # 变换查询
        query_vector = self.transform_document(query)  # [num_topics]

        # 计算与所有文档的相似度
        scores = []
        for doc_idx in range(self.tfidf_builder.doc_count):
            doc_vector = self.transformed_docs[:, doc_idx]
            norm_q = np.linalg.norm(query_vector)
            norm_d = np.linalg.norm(doc_vector)

            if norm_q == 0 or norm_d == 0:
                scores.append((doc_idx, 0.0))
            else:
                sim = np.dot(query_vector, doc_vector) / (norm_q * norm_d)
                scores.append((doc_idx, float(sim)))

        # 排序
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class LSIIndex:
    """LSI索引器：构建和搜索"""

    def __init__(self, num_topics: int = 100):
        self.lsi = LSI(num_topics)

    def build(self, documents: List[str]):
        """构建索引"""
        self.lsi.fit(documents)

    def search(self, query: str, top_k: int = 5) -> List[Tuple[int, float, str]]:
        """搜索文档"""
        results = self.lsi.search(query, top_k)
        return [(doc_idx, score, self.lsi.tfidf_builder.documents[doc_idx])
                for doc_idx, score in results]


def compute_topic_diversity(lsi: LSI, top_k: int = 10) -> float:
    """
    计算主题多样性
    :param lsi: LSI模型
    :param top_k: 每个主题取前k个词
    :return: 多样性分数
    """
    vocab_size = len(lsi.tfidf_builder.vocab)

    # 获取每个维度的top词
    topic_words = []
    for topic_idx in range(lsi.num_topics):
        # 从V^T的行获取主题-词关联
        topic_word_weights = lsi.Vt[topic_idx, :]
        top_word_indices = np.argsort(np.abs(topic_word_weights))[::-1][:top_k]
        topic_words.append(set(top_word_indices))

    # 计算主题间的重叠
    total_overlap = 0
    num_pairs = 0
    for i in range(len(topic_words)):
        for j in range(i + 1, len(topic_words)):
            overlap = len(topic_words[i] & topic_words[j])
            total_overlap += overlap / top_k
            num_pairs += 1

    avg_overlap = total_overlap / num_pairs if num_pairs > 0 else 0
    diversity = 1 - avg_overlap

    return diversity


def compute_reconstruction_error(original: np.ndarray, reconstructed: np.ndarray) -> float:
    """计算重构误差"""
    return np.linalg.norm(original - reconstructed, 'fro')


def demo():
    """LSI潜在语义索引演示"""
    # 文档集合
    documents = [
        "machine learning algorithms process large datasets efficiently",
        "deep learning neural networks recognize patterns in complex data",
        "natural language processing understands text and speech automatically",
        "computer vision analyzes images and identifies objects accurately",
        "supervised learning trains models with labeled training examples",
        "unsupervised learning discovers hidden patterns in unlabeled data",
        "reinforcement learning agents learn through trial and error",
        "neural networks process information similar to human brain",
        "text classification categorizes documents automatically",
        "object detection finds items in images and videos"
    ]

    print("[LSI潜在语义索引演示]")

    # 构建LSI
    num_topics = 5
    lsi = LSI(num_topics=num_topics)
    lsi.fit(documents)

    print(f"  词表大小: {len(lsi.tfidf_builder.vocab)}")
    print(f"  主题数: {num_topics}")
    print(f"  奇异值: {lsi.S[:5]}...")

    # 重构误差
    reconstructed = lsi.U @ np.diag(lsi.S) @ lsi.Vt
    error = compute_reconstruction_error(lsi.tfidf_matrix, reconstructed)
    print(f"  重构误差(Frobenius): {error:.4f}")

    # 文档相似度
    print(f"\n  文档相似度:")
    sim_0_1 = lsi.similarity(0, 1)  # ML和DL应该相似
    sim_0_4 = lsi.similarity(0, 4)  # ML和监督学习应该相似
    print(f"    doc_0 vs doc_1 (ML vs DL): {sim_0_1:.4f}")
    print(f"    doc_0 vs doc_4 (ML vs 监督): {sim_0_4:.4f}")

    # 搜索
    queries = ["neural networks deep learning", "text classification", "computer vision images"]

    print(f"\n  搜索演示:")
    for query in queries:
        results = lsi.search(query, top_k=3)
        print(f"\n  查询: '{query}'")
        for doc_idx, score in results:
            print(f"    [{score:.3f}] doc_{doc_idx}: {documents[doc_idx][:50]}...")

    # 主题多样性
    diversity = compute_topic_diversity(lsi, top_k=10)
    print(f"\n  主题多样性: {diversity:.4f}")

    print("  ✅ LSI演示通过！")


if __name__ == "__main__":
    demo()
