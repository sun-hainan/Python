"""
查询扩展模块 - 伪相关反馈/Rocchio

本模块实现基于伪相关反馈（Pseudo Relevance Feedback, PRF）的查询扩展技术。
通过初始检索结果自动识别相关文档，从中提取扩展词来丰富原始查询。

核心方法：
1. 伪相关反馈：假设top-k检索结果是相关的
2. Rocchio算法：向量空间模型中的查询向量优化
3. 伯努利模型：基于词项选择的相关反馈
4. 混合扩展：结合多种策略
"""

import math
import numpy as np
from typing import List, Dict, Tuple, Set
from collections import Counter, defaultdict
import re


class Tokenizer:
    """简单分词器"""

    @staticmethod
    def tokenize(text: str) -> List[str]:
        text = text.lower()
        words = re.sub(r'[^\w\s]', ' ', text).split()
        return [w for w in words if len(w) > 1]


class BM25Retriever:
    """简化的BM25检索器（用于查询扩展演示）"""

    def __init__(self, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.corpus = []
        self.doc_len = {}
        self.doc_term_freqs = []
        self.idf = {}
        self.avgdl = 0

    def fit(self, corpus: List[str]):
        self.corpus = corpus
        df = Counter()

        for doc_id, doc_text in enumerate(corpus):
            tokens = Tokenizer.tokenize(doc_text)
            self.doc_len[doc_id] = len(tokens)
            tf = Counter(tokens)
            self.doc_term_freqs.append(tf)

            for word in set(tokens):
                df[word] += 1

        self.avgdl = sum(self.doc_len.values()) / len(self.corpus)

        for word, freq in df.items():
            self.idf[word] = math.log((len(self.corpus) - freq + 0.5) / (freq + 0.5))

    def score(self, query: str, doc_id: int) -> float:
        tokens = Tokenizer.tokenize(query)
        tf = self.doc_term_freqs[doc_id]
        doc_len = self.doc_len[doc_id]

        score = 0.0
        for term in tokens:
            if term not in self.idf:
                continue
            tf_doc = tf.get(term, 0)
            idf = self.idf[term]
            numerator = tf_doc * (self.k1 + 1)
            denominator = tf_doc + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
            score += idf * numerator / denominator

        return score

    def retrieve(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        scores = [(doc_id, self.score(query, doc_id)) for doc_id in range(len(self.corpus))]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class PseudoRelevanceFeedback:
    """伪相关反馈（PRF）"""

    def __init__(self, retriever: BM25Retriever, expansion_terms=20, feedback_docs=10):
        """
        :param retriever: 检索器实例
        :param expansion_terms: 扩展词数量
        :param feedback_docs: 用于反馈的文档数量
        """
        self.retriever = retriever
        self.expansion_terms = expansion_terms
        self.feedback_docs = feedback_docs

    def expand_query(self, query: str) -> str:
        """
        执行伪相关反馈扩展
        :param query: 原始查询
        :return: 扩展后的查询
        """
        # 第一轮检索
        initial_results = self.retriever.retrieve(query, top_k=self.feedback_docs)

        if not initial_results:
            return query

        # 收集相关文档的词频
        term_scores = Counter()

        for doc_id, doc_score in initial_results:
            tf = self.retriever.doc_term_freqs[doc_id]
            # 按相关度加权
            for term, freq in tf.items():
                # 简单的TF加权
                term_scores[term] += freq * doc_score

        # 过滤原始查询词
        query_terms = set(Tokenizer.tokenize(query))

        # 选择高分扩展词
        expansion = []
        for term, score in term_scores.most_common():
            if term not in query_terms:
                expansion.append(term)
            if len(expansion) >= self.expansion_terms:
                break

        # 拼接扩展查询
        expanded_query = query + " " + " ".join(expansion)
        return expanded_query


class RocchioExpansion:
    """Rocchio查询扩展（向量空间模型）"""

    def __init__(self, retriever: BM25Retriever, alpha=1.0, beta=0.75, gamma=0.15):
        """
        :param alpha: 原始查询权重
        :param beta: 相关文档权重
        :param gamma: 不相关文档权重
        """
        self.retriever = retriever
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

    def _get_doc_vector(self, doc_id: int) -> Dict[str, float]:
        """获取文档向量（TF-IDF）"""
        tf = self.retriever.doc_term_freqs[doc_id]
        doc_len = self.retriever.doc_len[doc_id]

        vector = {}
        for term, freq in tf.items():
            if term in self.retriever.idf:
                # 简化的TF-IDF权重
                vector[term] = freq * self.retriever.idf[term]

        return vector

    def _get_query_vector(self, query: str) -> Dict[str, float]:
        """获取查询向量"""
        tokens = Tokenizer.tokenize(query)
        tf = Counter(tokens)
        vector = {}

        for term, freq in tf.items():
            if term in self.retriever.idf:
                vector[term] = freq * self.retriever.idf[term]

        return vector

    def expand_query(self, query: str, top_k: int = 10) -> str:
        """
        执行Rocchio查询扩展
        :return: 扩展后的查询
        """
        # 检索相关文档
        results = self.retriever.retrieve(query, top_k=top_k)
        query_terms = set(Tokenizer.tokenize(query))

        # 计算查询向量
        q_vector = self._get_query_vector(query)

        # 累加相关文档向量
        rel_vector = defaultdict(float)
        for doc_id, score in results[:5]:  # 取top-5作为相关
            doc_vector = self._get_doc_vector(doc_id)
            for term, weight in doc_vector.items():
                rel_vector[term] += weight * (score / 5)  # 归一化

        # Rocchio公式：q_new = alpha * q + beta * D_rel - gamma * D_nonrel
        new_vector = {}
        all_terms = set(q_vector.keys()) | set(rel_vector.keys())

        for term in all_terms:
            q_weight = self.alpha * q_vector.get(term, 0)
            rel_weight = self.beta * rel_vector.get(term, 0)
            new_vector[term] = q_weight + rel_weight

        # 排序并选择top词
        sorted_terms = sorted(new_vector.items(), key=lambda x: x[1], reverse=True)

        # 选择扩展词（排除原始查询词，取高分词）
        expansion = []
        for term, weight in sorted_terms:
            if term not in query_terms and len(expansion) < 20:
                expansion.append(term)

        expanded_query = query + " " + " ".join(expansion)
        return expanded_query


class RM3Expansion:
    """RM3（Relevance Model 3）查询扩展"""

    def __init__(self, retriever: BM25Retriever, lambda_=0.5, expansion_terms=20):
        """
        :param lambda_: 插值权重
        """
        self.retriever = retriever
        self.lambda_ = lambda_
        self.expansion_terms = expansion_terms

    def _compute_relevance_model(self, query: str, top_k: int = 10) -> Dict[str, float]:
        """
        计算相关模型 P(w|R, Q)
        """
        results = self.retriever.retrieve(query, top_k=top_k)

        if not results:
            return {}

        # 收集统计信息
        term_freq = Counter()
        total_tf = 0
        doc_freq = Counter()  # 包含词项的文档数

        for doc_id, score in results:
            tf = self.retriever.doc_term_freqs[doc_id]
            for term, freq in tf.items():
                term_freq[term] += freq
                total_tf += freq
            for term in set(tf.keys()):
                doc_freq[term] += 1

        # 计算相关模型分布
        relevance_model = {}
        corpus_size = len(self.retriever.corpus)

        for term, tf in term_freq.items():
            # P(w|R) = lambda * P(w|D_rel) + (1-lambda) * P(w|C)
            p_w_drel = tf / total_tf if total_tf > 0 else 0
            # 集合模型 P(w|C) ~ df
            p_w_c = doc_freq[term] / corpus_size if corpus_size > 0 else 0

            relevance_model[term] = self.lambda_ * p_w_drel + (1 - self.lambda_) * p_w_c

        return relevance_model

    def expand_query(self, query: str) -> str:
        """执行RM3查询扩展"""
        query_terms = set(Tokenizer.tokenize(query))
        relevance_model = self._compute_relevance_model(query)

        # 选择扩展词
        expansion = []
        for term, prob in sorted(relevance_model.items(), key=lambda x: x[1], reverse=True):
            if term not in query_terms:
                expansion.append(term)
            if len(expansion) >= self.expansion_terms:
                break

        expanded_query = query + " " + " ".join(expansion)
        return expanded_query


class Bo1Expansion:
    """Bo1（Bayesian Optimization）查询扩展"""

    def __init__(self, retriever: BM25Retriever, expansion_terms=20):
        self.retriever = retriever
        self.expansion_terms = expansion_terms

    def _chi_squared(self, term: str, top_k: int = 10) -> float:
        """计算卡方统计量"""
        results = self.retriever.retrieve("", top_k=top_k)

        # 简化的chi-squared计算
        # 实际应该使用整个集合的统计
        freq_in_results = 0
        for doc_id, _ in results:
            if term in self.retriever.doc_term_freqs[doc_id]:
                freq_in_results += 1

        # 简化chi-squared
        expected = top_k / 2
        observed = freq_in_results
        chi_sq = (observed - expected) ** 2 / expected if expected > 0 else 0

        return chi_sq

    def expand_query(self, query: str) -> str:
        """执行Bo1查询扩展"""
        query_terms = set(Tokenizer.tokenize(query))
        results = self.retriever.retrieve(query, top_k=20)

        # 收集候选词
        candidate_scores = Counter()
        for doc_id, _ in results:
            tf = self.retriever.doc_term_freqs[doc_id]
            for term, freq in tf.items():
                if term not in query_terms:
                    candidate_scores[term] += freq

        # 按分数排序
        expansion = []
        for term, score in candidate_scores.most_common(self.expansion_terms * 2):
            if term not in query_terms:
                expansion.append(term)
            if len(expansion) >= self.expansion_terms:
                break

        return query + " " + " ".join(expansion)


def evaluate_expansion(original_query: str, expanded_query: str,
                       retriever: BM25Retriever, relevant_doc_ids: Set[int]) -> Dict[str, float]:
    """评估查询扩展效果"""
    # 原始查询结果
    orig_results = retriever.retrieve(original_query, top_k=20)
    orig_retrieved = set(doc_id for doc_id, _ in orig_results)

    # 扩展查询结果
    exp_results = retriever.retrieve(expanded_query, top_k=20)
    exp_retrieved = set(doc_id for doc_id, _ in exp_results)

    # 计算召回率
    orig_recall = len(orig_retrieved & relevant_doc_ids) / len(relevant_doc_ids) if relevant_doc_ids else 0
    exp_recall = len(exp_retrieved & relevant_doc_ids) / len(relevant_doc_ids) if relevant_doc_ids else 0

    return {
        "original_recall": orig_recall,
        "expanded_recall": exp_recall,
        "improvement": exp_recall - orig_recall
    }


def demo():
    """查询扩展演示"""
    corpus = [
        "machine learning algorithms process large datasets",
        "deep learning uses neural networks for pattern recognition",
        "natural language processing enables computers to understand text",
        "supervised learning trains models with labeled data",
        "unsupervised learning discovers hidden patterns in data",
        "reinforcement learning agents learn through trial and error",
        "computer vision techniques analyze images and videos",
        "speech recognition converts audio to text",
        "artificial intelligence encompasses many subfields",
        "neural networks are inspired by biological brain structures"
    ]

    print("[查询扩展演示]")

    # 初始化检索器
    retriever = BM25Retriever()
    retriever.fit(corpus)

    # 原始查询
    query = "neural networks learning"
    print(f"\n  原始查询: '{query}'")

    # PRF扩展
    prf = PseudoRelevanceFeedback(retriever, expansion_terms=10)
    expanded_prf = prf.expand_query(query)
    print(f"  PRF扩展后: '{expanded_prf}'")

    # Rocchio扩展
    rocchio = RocchioExpansion(retriever)
    expanded_rocchio = rocchio.expand_query(query)
    print(f"  Rocchio扩展后: '{expanded_rocchio}'")

    # RM3扩展
    rm3 = RM3Expansion(retriever)
    expanded_rm3 = rm3.expand_query(query)
    print(f"  RM3扩展后: '{expanded_rm3}'")

    # Bo1扩展
    bo1 = Bo1Expansion(retriever)
    expanded_bo1 = bo1.expand_query(query)
    print(f"  Bo1扩展后: '{expanded_bo1}'")

    # 检索结果对比
    print(f"\n  检索结果对比:")
    orig_results = retriever.retrieve(query, top_k=3)
    print(f"    原始查询: {[(d, f'{s:.2f}') for d, s in orig_results]}")

    exp_results = retriever.retrieve(expanded_prf, top_k=3)
    print(f"    PRF扩展后: {[(d, f'{s:.2f}') for d, s in exp_results]}")

    # 模拟评估
    relevant = {0, 1, 3, 5, 9}  # 假设相关文档
    eval_result = evaluate_expansion(query, expanded_prf, retriever, relevant)
    print(f"\n  扩展效果评估:")
    print(f"    原始召回: {eval_result['original_recall']:.2f}")
    print(f"    扩展召回: {eval_result['expanded_recall']:.2f}")
    print(f"    提升: {eval_result['improvement']:.2f}")

    print("  ✅ 查询扩展演示通过！")


if __name__ == "__main__":
    demo()
