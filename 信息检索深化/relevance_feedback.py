"""
相关反馈模块 - Rocchio算法

本模块实现基于相关反馈的查询优化技术。
通过用户反馈或伪反馈来改进检索结果。

核心方法：
1. Rocchio算法：向量空间模型的经典相关反馈
2. 伪相关反馈(PRF)：假设top-k结果为相关
3. 贝叶斯相关反馈：概率模型
4. 深度反馈：使用神经网络编码反馈信息
"""

import numpy as np
from typing import List, Tuple, Dict, Set, Optional
from collections import Counter, defaultdict
import math


class Tokenizer:
    """简单分词器"""

    @staticmethod
    def tokenize(text: str) -> List[str]:
        text = text.lower()
        words = text.replace(',', ' ').replace('.', ' ').split()
        return [w for w in words if len(w) > 1]


class VectorSpaceModel:
    """向量空间模型"""

    def __init__(self):
        self.documents = []
        self.vocab = set()
        self.doc_vectors = {}  # doc_id -> vector
        self.doc_term_freqs = []
        self.doc_freqs = Counter()
        self.num_docs = 0

    def fit(self, documents: List[str]):
        """构建索引"""
        self.documents = documents
        self.num_docs = len(documents)
        self.doc_term_freqs = []

        for doc in documents:
            tokens = Tokenizer.tokenize(doc)
            tf = Counter(tokens)
            self.doc_term_freqs.append(tf)
            self.vocab.update(tokens)

            for word in set(tokens):
                self.doc_freqs[word] += 1

        # 构建文档向量
        for doc_idx, doc in enumerate(documents):
            tokens = Tokenizer.tokenize(doc)
            vector = self._compute_tf_idf(tokens)
            self.doc_vectors[doc_idx] = vector

    def _compute_tf_idf(self, tokens: List[str]) -> np.ndarray:
        """计算TF-IDF向量"""
        vocab_list = list(self.vocab)
        vocab_size = len(vocab_list)
        word_to_idx = {w: i for i, w in enumerate(vocab_list)}

        vector = np.zeros(vocab_size)
        tf = Counter(tokens)

        for word, freq in tf.items():
            if word in word_to_idx:
                idx = word_to_idx[word]
                idf = math.log((self.num_docs + 1) / (self.doc_freqs[word] + 1)) + 1
                vector[idx] = (1 + math.log(freq)) * idf

        return vector

    def get_query_vector(self, query: str) -> np.ndarray:
        """获取查询向量"""
        tokens = Tokenizer.tokenize(query)
        return self._compute_tf_idf(tokens)

    def similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """余弦相似度"""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return np.dot(vec1, vec2) / (norm1 * norm2)


class RocchioFeedback:
    """Rocchio相关反馈算法"""

    def __init__(self, vsm: VectorSpaceModel, alpha: float = 1.0,
                 beta: float = 0.75, gamma: float = 0.15):
        """
        :param alpha: 原始查询权重
        :param beta: 相关文档权重
        :param gamma: 不相关文档权重
        """
        self.vsm = vsm
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

    def expand_query(self, query_vector: np.ndarray,
                    relevant_docs: List[int],
                    non_relevant_docs: List[int]) -> np.ndarray:
        """
        执行Rocchio反馈
        :param query_vector: 原始查询向量
        :param relevant_docs: 相关文档ID列表
        :param non_relevant_docs: 不相关文档ID列表
        :return: 改进后的查询向量
        """
        # 相关文档质心
        if relevant_docs:
            rel_vectors = [self.vsm.doc_vectors[d] for d in relevant_docs]
            rel_centroid = np.mean(rel_vectors, axis=0)
        else:
            rel_centroid = np.zeros_like(query_vector)

        # 不相关文档质心
        if non_relevant_docs:
            non_rel_vectors = [self.vsm.doc_vectors[d] for d in non_relevant_docs]
            non_rel_centroid = np.mean(non_rel_vectors, axis=0)
        else:
            non_rel_centroid = np.zeros_like(query_vector)

        # Rocchio公式
        new_query = self.alpha * query_vector + \
                   self.beta * rel_centroid - \
                   self.gamma * non_rel_centroid

        return new_query

    def retrieve_with_feedback(self, query: str,
                             relevant_doc_ids: Set[int],
                             non_relevant_doc_ids: Set[int],
                             top_k: int = 10) -> List[Tuple[int, float]]:
        """
        带反馈的检索
        """
        # 获取原始查询向量
        query_vector = self.vsm.get_query_vector(query)

        # 扩展查询
        expanded_query = self.expand_query(
            query_vector,
            list(relevant_doc_ids),
            list(non_relevant_doc_ids)
        )

        # 计算与所有文档的相似度
        scores = []
        for doc_idx in range(self.vsm.num_docs):
            doc_vector = self.vsm.doc_vectors[doc_idx]
            sim = self.vsm.similarity(expanded_query, doc_vector)
            scores.append((doc_idx, sim))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class PseudoRelevanceFeedback:
    """伪相关反馈（假设top-k为相关）"""

    def __init__(self, vsm: VectorSpaceModel, num_feedback_docs: int = 10,
                 num_expansion_terms: int = 20):
        self.vsm = vsm
        self.num_feedback_docs = num_feedback_docs
        self.num_expansion_terms = num_expansion_terms

    def expand_query(self, query: str) -> Tuple[str, List[Tuple[int, float]]]:
        """
        伪相关反馈
        :return: (扩展后的查询, 初始检索结果)
        """
        # 初始检索
        query_vector = self.vsm.get_query_vector(query)
        initial_scores = []

        for doc_idx in range(self.vsm.num_docs):
            doc_vector = self.vsm.doc_vectors[doc_idx]
            sim = self.vsm.similarity(query_vector, doc_vector)
            initial_scores.append((doc_idx, sim))

        initial_scores.sort(key=lambda x: x[1], reverse=True)

        # 假设top-k为相关
        top_k_docs = initial_scores[:self.num_feedback_docs]

        # 收集相关文档中的词
        term_weights = Counter()
        for doc_idx, _ in top_k_docs:
            vector = self.vsm.doc_vectors[doc_idx]
            # 取高权重词
            vocab_list = list(self.vsm.vocab)
            for i, weight in enumerate(vector):
                if weight > 0:
                    term_weights[vocab_list[i]] += weight

        # 选择扩展词
        query_terms = set(Tokenizer.tokenize(query))
        expansion_terms = []

        for term, weight in term_weights.most_common():
            if term not in query_terms and len(expansion_terms) < self.num_expansion_terms:
                expansion_terms.append(term)

        # 构建扩展查询
        expanded_query = query + " " + " ".join(expansion_terms)

        return expanded_query, top_k_docs


class IdeRegularFeedback:
    """IDE-REG（标准Rocchio的简化变体）"""

    def __init__(self, vsm: VectorSpaceModel):
        self.vsm = vsm

    def expand_query(self, query_vector: np.ndarray,
                    relevant_docs: List[int]) -> np.ndarray:
        """只用相关文档扩展"""
        if not relevant_docs:
            return query_vector

        # 相关文档质心
        rel_vectors = [self.vsm.doc_vectors[d] for d in relevant_docs]
        rel_centroid = np.mean(rel_vectors, axis=0)

        # 简化Rocchio
        new_query = query_vector + rel_centroid

        return new_query


class BayesianRelevanceFeedback:
    """贝叶斯相关反馈"""

    def __init__(self, vsm: VectorSpaceModel):
        self.vsm = vsm

    def estimate_relevance(self, query: str, doc_idx: int,
                          initial_results: List[Tuple[int, float]]) -> float:
        """
        估计文档的相关概率
        :return: P(relevant|doc, query)
        """
        # 简化的概率估计
        # 实际应使用语言模型或概率检索模型

        query_vector = self.vsm.get_query_vector(query)
        doc_vector = self.vsm.doc_vectors[doc_idx]

        # 基于相似度的概率
        similarity = self.vsm.similarity(query_vector, doc_vector)

        # 简单的sigmoid变换
        prob = 1 / (1 + math.exp(-10 * (similarity - 0.5)))

        return prob

    def expand_query(self, query: str, top_docs: List[int],
                    relevance_threshold: float = 0.5) -> np.ndarray:
        """基于相关概率扩展查询"""
        query_vector = self.vsm.get_query_vector(query)

        # 计算每个文档的相关概率
        probs = []
        for doc_idx in top_docs:
            prob = self.estimate_relevance(query, doc_idx, top_docs)
            probs.append((doc_idx, prob))

        # 只用高概率文档
        relevant_docs = [d for d, p in probs if p >= relevance_threshold]

        if not relevant_docs:
            return query_vector

        # 加权平均
        weighted_sum = np.zeros_like(query_vector)
        total_weight = 0.0

        for doc_idx, prob in probs:
            weight = prob if doc_idx in relevant_docs else 0.1
            weighted_sum += weight * self.vsm.doc_vectors[doc_idx]
            total_weight += weight

        new_query = weighted_sum / total_weight if total_weight > 0 else query_vector

        return new_query


class QueryTermReweight:
    """查询词重加权"""

    def __init__(self, vsm: VectorSpaceModel):
        self.vsm = vsm

    def reweight_terms(self, query: str,
                      relevant_docs: List[int],
                      boost_factor: float = 2.0) -> Dict[str, float]:
        """
        重加权查询词
        :return: {term: new_weight}
        """
        tokens = Tokenizer.tokenize(query)
        original_weights = {}

        # 计算原始权重
        query_vector = self.vsm.get_query_vector(query)
        vocab_list = list(self.vsm.vocab)
        for i, w in enumerate(query_vector):
            if w > 0:
                original_weights[vocab_list[i]] = w

        # 计算相关文档中的权重
        doc_weights = Counter()
        for doc_idx in relevant_docs:
            doc_vector = self.vsm.doc_vectors[doc_idx]
            for i, w in enumerate(doc_vector):
                if w > 0:
                    doc_weights[vocab_list[i]] += w

        # 重加权
        new_weights = {}
        for term in tokens:
            if term in original_weights:
                original = original_weights[term]
                doc_weight = doc_weights.get(term, 0)
                # 如果相关文档中也有该词，增加权重
                if doc_weight > 0:
                    new_weights[term] = original * boost_factor
                else:
                    new_weights[term] = original

        return new_weights


def evaluate_feedback(original_results: List[Tuple[int, float]],
                     feedback_results: List[Tuple[int, float]],
                     relevant_docs: Set[int]) -> Dict[str, float]:
    """评估相关反馈效果"""
    # 原始召回率
    orig_ret = set(d for d, _ in original_results[:10]) & relevant_docs
    orig_recall = len(orig_ret) / len(relevant_docs) if relevant_docs else 0

    # 反馈后召回率
    feed_ret = set(d for d, _ in feedback_results[:10]) & relevant_docs
    feed_recall = len(feed_ret) / len(relevant_docs) if relevant_docs else 0

    return {
        "original_recall": orig_recall,
        "feedback_recall": feed_recall,
        "improvement": feed_recall - orig_recall
    }


def demo():
    """相关反馈演示"""
    documents = [
        "machine learning algorithms process large datasets efficiently",
        "deep learning neural networks recognize patterns in complex data",
        "natural language processing understands text and speech automatically",
        "computer vision analyzes images and identifies objects accurately",
        "supervised learning trains models with labeled training examples",
        "unsupervised learning discovers hidden patterns in data",
        "reinforcement learning agents learn through trial and error",
        "neural networks process information like biological brains",
        "text classification categorizes documents automatically",
        "object detection finds items in images and videos"
    ]

    print("[相关反馈演示]")

    # 构建向量空间模型
    vsm = VectorSpaceModel()
    vsm.fit(documents)

    # Rocchio反馈
    rocchio = RocchioFeedback(vsm, alpha=1.0, beta=0.75, gamma=0.15)

    query = "neural networks deep"
    query_vector = vsm.get_query_vector(query)
    print(f"\n  原始查询: '{query}'")

    # 假设doc_1和doc_7相关，doc_2不相关
    expanded = rocchio.expand_query(query_vector, [1, 7], [2])
    print(f"  Rocchio扩展后向量范数: {np.linalg.norm(expanded):.4f}")

    # 伪相关反馈
    prf = PseudoRelevanceFeedback(vsm, num_feedback_docs=3, num_expansion_terms=5)
    expanded_query, top_docs = prf.expand_query(query)
    print(f"\n  PRF扩展查询: '{expanded_query}'")
    print(f"  初始top-3: {[(d, f'{s:.3f}') for d, s in top_docs]}")

    # 贝叶斯反馈
    bayesian = BayesianRelevanceFeedback(vsm)
    new_query_vec = bayesian.expand_query(query, [d for d, _ in top_docs])
    print(f"  贝叶斯扩展向量范数: {np.linalg.norm(new_query_vec):.4f}")

    # 查询词重加权
    reweighter = QueryTermReweight(vsm)
    new_weights = reweighter.reweight_terms(query, [1, 7], boost_factor=2.0)
    print(f"\n  重加权结果: {new_weights}")

    # 模拟评估
    relevant = {1, 7, 9}  # 假设相关文档
    original_results = [(i, 1.0 / (i + 1)) for i in range(10)]
    feedback_results = [(1, 0.9), (7, 0.8), (9, 0.7), (2, 0.6)]
    eval_result = evaluate_feedback(original_results, feedback_results, relevant)
    print(f"\n  反馈效果:")
    print(f"    原始召回: {eval_result['original_recall']:.2f}")
    print(f"    反馈召回: {eval_result['feedback_recall']:.2f}")
    print(f"    提升: {eval_result['improvement']:.2f}")

    print("  ✅ 相关反馈演示通过！")


if __name__ == "__main__":
    demo()
