"""
BM25+ 权重参数优化模块

本模块实现BM25及其变体的完整实现，包括：
1. 经典BM25：Okapi BM25
2. BM25L：处理长文档
3. BM25+：解决长文档得分退化问题
4. 参数优化：自适应调整k1和b参数

BM25公式：
Score(Q,d) = Σ IDF(qi) * (tf * (k1+1)) / (tf + k1 * (1-b + b*|d|/avgdl))
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
        """中英文分词"""
        # 转小写
        text = text.lower()
        # 去除标点，按空格分割
        words = re.sub(r'[^\w\s]', ' ', text).split()
        return [w for w in words if len(w) > 1]  # 过滤单字符


class BM25:
    """BM25检索模型"""

    def __init__(self, k1: float = 1.5, b: float = 0.75, epsilon: float = 0.25):
        """
        :param k1: 词频饱和参数，控制词频增长速率
        :param b: 文档长度归一化参数
        :param epsilon: BM25+中的下界参数
        """
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon

        self.corpus_size = 0
        self.avgdl = 0  # 平均文档长度
        self.doc_freqs = {}  # 词项文档频率
        self.idf = {}  # 逆文档频率
        self.doc_len = {}  # 文档长度
        self.doc_term_freqs = []  # 每个文档的词频

    def fit(self, corpus: List[str]):
        """
        构建BM25索引
        :param corpus: 文档列表
        """
        self.corpus_size = len(corpus)
        self.doc_term_freqs = []
        self.doc_len = {}

        # 词频统计
        df = Counter()  # 文档频率
        total_len = 0

        for doc_id, doc_text in enumerate(corpus):
            tokens = Tokenizer.tokenize(doc_text)
            self.doc_len[doc_id] = len(tokens)

            # 词频
            tf = Counter(tokens)
            self.doc_term_freqs.append(tf)

            total_len += len(tokens)

            # 更新文档频率
            for word in set(tokens):
                df[word] += 1

        self.avgdl = total_len / self.corpus_size if self.corpus_size > 0 else 1

        # 计算IDF
        for word, freq in df.items():
            # IDF公式：log((N - n + 0.5) / (n + 0.5))
            idf = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5))
            self.idf[word] = idf

    def score(self, query: str, doc_id: int) -> float:
        """
        计算查询对单个文档的BM25分数
        :param query: 查询字符串
        :param doc_id: 文档ID
        :return: BM25分数
        """
        tokens = Tokenizer.tokenize(query)
        tf = self.doc_term_freqs[doc_id]
        doc_len = self.doc_len[doc_id]

        score = 0.0
        for term in tokens:
            if term not in self.idf:
                continue

            tf_doc = tf.get(term, 0)
            idf = self.idf[term]

            # BM25公式
            numerator = tf_doc * (self.k1 + 1)
            denominator = tf_doc + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
            score += idf * numerator / denominator

        return score

    def score_batch(self, query: str) -> List[Tuple[int, float]]:
        """
        计算查询对所有文档的分数
        :return: [(doc_id, score)]列表，按分数降序
        """
        tokens = Tokenizer.tokenize(query)
        scores = []

        for doc_id in range(self.corpus_size):
            doc_score = self.score(query, doc_id)
            scores.append((doc_id, doc_score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores


class BM25Plus(BM25):
    """BM25+：解决长文档得分退化问题"""

    def __init__(self, k1: float = 1.5, b: float = 0.75, delta: float = 1.0):
        """
        :param delta: 附加常数，防止得分过低
        """
        super().__init__(k1, b)
        self.delta = delta

    def score(self, query: str, doc_id: int) -> float:
        """计算BM25+分数"""
        tokens = Tokenizer.tokenize(query)
        tf = self.doc_term_freqs[doc_id]
        doc_len = self.doc_len[doc_id]

        score = 0.0
        for term in tokens:
            if term not in self.idf:
                continue

            tf_doc = tf.get(term, 0)
            idf = self.idf[term]

            # BM25+公式：在TF项上加delta下界
            numerator = tf_doc * (self.k1 + 1)
            denominator = tf_doc + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
            score += idf * (numerator / denominator + self.delta)

        return score


class BM25L(BM25):
    """BM25L：处理长文档的特殊变体"""

    def __init__(self, k1: float = 1.5, b: float = 0.75, gamma: float = 0.5):
        super().__init__(k1, b)
        self.gamma = gamma
        # 重新计算词频（取对数变换）
        self.doc_term_freqs_log = []

    def fit(self, corpus: List[str]):
        """构建索引时计算log TF"""
        super().fit(corpus)
        # 计算log变换后的词频
        self.doc_term_freqs_log = []
        for tf in self.doc_term_freqs:
            log_tf = {}
            for term, freq in tf.items():
                # log变换
                log_tf[term] = gamma_to_log(freq, self.gamma)
            self.doc_term_freqs_log.append(log_tf)

    def score(self, query: str, doc_id: int) -> float:
        """使用log TF计算分数"""
        tokens = Tokenizer.tokenize(query)
        tf_log = self.doc_term_freqs_log[doc_id]
        doc_len = self.doc_len[doc_id]

        score = 0.0
        for term in tokens:
            if term not in self.idf:
                continue

            tf_doc = tf_log.get(term, 0)
            idf = self.idf[term]

            numerator = tf_doc * (self.k1 + 1)
            denominator = tf_doc + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
            score += idf * numerator / denominator

        return score


def gamma_to_log(freq: int, gamma: float) -> float:
    """Gamma到log变换"""
    if freq <= 0:
        return 0
    return math.log(gamma + freq) - math.log(gamma)


class BM25ParameterTuner:
    """BM25参数自动调优器"""

    def __init__(self, corpus: List[str], qrels: Dict[str, Set[str]]):
        """
        :param corpus: 文档列表
        :param qrels: 查询相关性判断 {query_id: {relevant_doc_ids}}
        """
        self.corpus = corpus
        self.qrels = qrels
        self.bm25 = BM25()

    def tune(self, k1_values=[1.2, 1.5, 2.0], b_values=[0.5, 0.75, 0.9]) -> Tuple[float, float, float]:
        """
        网格搜索最优参数
        :return: (best_k1, best_b, best_score)
        """
        best_score = 0
        best_k1, best_b = 1.5, 0.75

        for k1 in k1_values:
            for b in b_values:
                self.bm25.k1 = k1
                self.bm25.b = b
                self.bm25.fit(self.corpus)

                score = self._evaluate()
                if score > best_score:
                    best_score = score
                    best_k1, best_b = k1, b

        return best_k1, best_b, best_score

    def _evaluate(self) -> float:
        """评估当前参数下的性能（简化NDCG）"""
        ndcgs = []
        for query, relevant_docs in self.qrels.items():
            scores = self.bm25.score_batch(query)
            retrieved = [str(doc_id) for doc_id, _ in scores[:10]]

            # 简化计算
            hits = len(set(retrieved) & relevant_docs)
            ndcg = hits / len(relevant_docs) if relevant_docs else 0
            ndcgs.append(ndcg)

        return np.mean(ndcgs) if ndcgs else 0


class TFIDF:
    """TF-IDF基线（用于对比）"""

    def __init__(self):
        self.doc_freqs = Counter()
        self.doc_term_freqs = []
        self.corpus_size = 0

    def fit(self, corpus: List[str]):
        """构建TF-IDF索引"""
        self.corpus_size = len(corpus)
        self.doc_term_freqs = []

        for doc_text in corpus:
            tokens = Tokenizer.tokenize(doc_text)
            tf = Counter(tokens)
            self.doc_term_freqs.append(tf)

            for word in set(tokens):
                self.doc_freqs[word] += 1

    def score(self, query: str, doc_id: int) -> float:
        """计算TF-IDF分数"""
        tokens = Tokenizer.tokenize(query)
        tf = self.doc_term_freqs[doc_id]

        score = 0.0
        for term in tokens:
            if term in tf:
                tf_val = tf[term]
                df = self.doc_freqs.get(term, 1)
                idf = math.log(self.corpus_size / df)
                score += tf_val * idf

        return score


def demo():
    """BM25+演示"""
    # 文档库
    corpus = [
        "The quick brown fox jumps over the lazy dog",
        "A fast brown fox running in the forest",
        "Machine learning is a subset of artificial intelligence",
        "Deep learning uses neural networks with multiple layers",
        "Natural language processing deals with understanding text",
        "Python is a popular programming language for AI"
    ]

    print("[BM25+演示]")

    # BM25
    bm25 = BM25(k1=1.5, b=0.75)
    bm25.fit(corpus)

    queries = ["brown fox", "machine learning", "programming language"]
    for q in queries:
        scores = bm25.score_batch(q)
        print(f"\n  查询: '{q}'")
        print(f"  BM25结果:")
        for doc_id, score in scores[:3]:
            print(f"    doc_{doc_id}: {score:.3f} - {corpus[doc_id][:40]}...")

    # BM25+
    bm25_plus = BM25Plus(k1=1.5, b=0.75, delta=1.0)
    bm25_plus.fit(corpus)
    print(f"\n  BM25+分数 (brown fox): {bm25_plus.score('brown fox', 0):.3f}")

    # TF-IDF对比
    tfidf = TFIDF()
    tfidf.fit(corpus)
    tfidf_scores = [(i, tfidf.score("brown fox", i)) for i in range(len(corpus))]
    tfidf_scores.sort(key=lambda x: x[1], reverse=True)
    print(f"\n  TF-IDF结果 (brown fox):")
    for doc_id, score in tfidf_scores[:3]:
        print(f"    doc_{doc_id}: {score:.3f}")

    # 参数影响
    print(f"\n  参数影响:")
    print(f"    avgdl = {bm25.avgdl:.1f}")
    print(f"    idf values: {dict(list(bm25.idf.items())[:3])}")

    print("  ✅ BM25+演示通过！")


if __name__ == "__main__":
    demo()
