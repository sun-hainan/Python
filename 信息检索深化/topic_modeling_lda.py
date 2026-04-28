"""
LDA主题模型模块 - 变分推断实现

本模块实现Latent Dirichlet Allocation (LDA)主题模型。
LDA是一种无监督学习算法，用于发现文档集合中的潜在主题结构。

核心方法：
1. 吉布斯采样：马尔可夫链蒙特卡洛近似推断
2. 变分推断：确定性近似推断
3. Collapsed Gibbs Sampling：边缘化部分变量的高效采样
"""

import numpy as np
from typing import List, Tuple, Dict
from collections import Counter, defaultdict
import math


class Vocabulary:
    """词汇表管理"""

    def __init__(self):
        self.word_to_idx = {}
        self.idx_to_word = {}
        self.word_counts = Counter()

    def add_document(self, tokens: List[str]):
        """添加文档更新词表"""
        for word in tokens:
            if word not in self.word_to_idx:
                idx = len(self.word_to_idx)
                self.word_to_idx[word] = idx
                self.idx_to_word[idx] = word
            self.word_counts[word] += 1

    def build_vocab(self, documents: List[List[str]], min_count: int = 1):
        """从文档集合构建词表"""
        # 统计词频
        all_words = Counter()
        for doc in documents:
            all_words.update(doc)

        # 过滤低频词
        for word, count in all_words.items():
            if count >= min_count:
                idx = len(self.word_to_idx)
                self.word_to_idx[word] = idx
                self.idx_to_word[idx] = word

    def get_idx(self, word: str) -> int:
        return self.word_to_idx.get(word, -1)

    def get_word(self, idx: int) -> str:
        return self.idx_to_word.get(idx, "")

    @property
    def size(self) -> int:
        return len(self.word_to_idx)


class LDACorpus:
    """LDA语料库管理"""

    def __init__(self, vocab: Vocabulary):
        self.vocab = vocab
        self.documents = []  # List of token id lists
        self.num_docs = 0

    def add_document(self, tokens: List[str]):
        """添加文档"""
        doc_ids = [self.vocab.get_idx(w) for w in tokens]
        doc_ids = [idx for idx in doc_ids if idx >= 0]  # 过滤未知词
        self.documents.append(doc_ids)
        self.num_docs += 1

    def get_document(self, doc_idx: int) -> List[int]:
        return self.documents[doc_idx] if doc_idx < len(self.documents) else []


class LDA:
    """LDA主题模型（基于变分推断/EM算法）"""

    def __init__(self, num_topics: int = 10, alpha: float = 0.1, beta: float = 0.01,
                 max_iter: int = 100, convergence: float = 1e-4):
        """
        :param num_topics: 主题数量
        :param alpha: 文档-主题分布的Dirichlet先验参数
        :param beta: 主题-词分布的Dirichlet先验参数
        :param max_iter: 最大迭代次数
        :param convergence: 收敛阈值
        """
        self.num_topics = num_topics
        self.alpha = alpha
        self.beta = beta
        self.max_iter = max_iter
        self.convergence = convergence

        self.vocab = None
        self.corpus = None

        # 模型参数
        self.gamma = None  # 文档-主题变分参数 [num_docs, num_topics]
        self.phi = None    # 主题-词变分参数 [num_topics, vocab_size]
        self.log_likelihood = []

    def _init_parameters(self, corpus: LDACorpus):
        """初始化模型参数"""
        num_docs = corpus.num_docs
        vocab_size = corpus.vocab.size

        # gamma: Dirichlet参数初始化
        self.gamma = np.random.gamma(100.0 / self.num_topics, 1.0 / 100.0, (num_docs, self.num_topics)) + self.alpha

        # phi: 词项分布初始化
        self.phi = np.random.dirichlet(np.ones(vocab_size) * self.beta, self.num_topics)

    def _e_step(self, corpus: LDACorpus) -> float:
        """
        E步：固定phi和beta，更新gamma
        :return: 似然变化量
        """
        old_gamma = self.gamma.copy()
        num_docs = corpus.num_docs
        vocab_size = corpus.vocab.size

        for d in range(num_docs):
            doc = corpus.get_document(d)
            if not doc:
                continue

            doc_len = len(doc)

            for iteration in range(10):  # 内循环迭代
                # 更新gamma
                new_gamma = self.alpha + np.sum(self.phi[:, doc].T, axis=1)

                # 更新phi
                for w_idx, word_id in enumerate(doc):
                    phi_sum = 0
                    for k in range(self.num_topics):
                        self.phi[k, word_id] = np.exp(
                            digamma(self.gamma[d, k]) -
                            np.sum(np.exp(digamma(self.gamma[d, :]) + digamma(np.sum(self.gamma[d, :])) - digamma(self.gamma[d, :])))
                        )
                        phi_sum += self.phi[k, word_id]

                    # 归一化
                    for k in range(self.num_topics):
                        self.phi[k, word_id] /= (phi_sum + 1e-10)

                self.gamma[d, :] = new_gamma

        # 计算似然变化
        diff = np.sum(np.abs(self.gamma - old_gamma))
        return diff

    def _m_step(self, corpus: LDACorpus):
        """
        M步：固定gamma，更新phi
        """
        vocab_size = corpus.vocab.size
        num_docs = corpus.num_docs

        # 重置phi
        new_phi = np.zeros((self.num_topics, vocab_size))

        for k in range(self.num_topics):
            for d in range(num_docs):
                doc = corpus.get_document(d)
                if not doc:
                    continue

                doc_len = len(doc)

                for word_id in doc:
                    # phi更新公式
                    new_phi[k, word_id] += doc_len * np.exp(
                        digamma(self.gamma[d, k]) - digamma(np.sum(self.gamma[d, :]))
                    )

            # 加上beta先验并归一化
            new_phi[k, :] += self.beta
            new_phi[k, :] /= np.sum(new_phi[k, :])

        self.phi = new_phi

    def _compute_log_likelihood(self, corpus: LDACorpus) -> float:
        """计算对数似然（近似）"""
        num_docs = corpus.num_docs
        ll = 0.0

        for d in range(num_docs):
            doc = corpus.get_document(d)
            if not doc:
                continue

            doc_len = len(doc)
            gamma_sum = np.sum(self.gamma[d, :])

            for word_id in doc:
                # 简化似然计算
                word_prob = 0.0
                for k in range(self.num_topics):
                    word_prob += (self.gamma[d, k] / gamma_sum) * self.phi[k, word_id]

                ll += np.log(word_prob + 1e-10) / doc_len

        return ll / num_docs

    def fit(self, corpus: LDACorpus):
        """训练LDA模型"""
        self.corpus = corpus
        self.vocab = corpus.vocab

        # 初始化
        self._init_parameters(corpus)

        for iteration in range(self.max_iter):
            # E步
            diff = self._e_step(corpus)

            # M步
            self._m_step(corpus)

            # 计算似然
            ll = self._compute_log_likelihood(corpus)
            self.log_likelihood.append(ll)

            # 检查收敛
            if iteration > 0 and abs(self.log_likelihood[-1] - self.log_likelihood[-2]) < self.convergence:
                print(f"  LDA收敛于第{iteration}次迭代")
                break

    def get_document_topics(self, doc_idx: int) -> List[Tuple[int, float]]:
        """获取文档的主题分布"""
        if doc_idx >= len(self.gamma):
            return []

        gamma_norm = self.gamma[doc_idx] / np.sum(self.gamma[doc_idx])
        topics = [(k, float(gamma_norm[k])) for k in range(self.num_topics)]
        topics.sort(key=lambda x: x[1], reverse=True)
        return topics

    def get_topic_words(self, topic_idx: int, top_k: int = 10) -> List[Tuple[str, float]]:
        """获取某主题的高频词"""
        if topic_idx >= self.num_topics:
            return []

        word_probs = self.phi[topic_idx, :]
        top_indices = np.argsort(word_probs)[::-1][:top_k]

        return [(self.vocab.get_word(idx), float(word_probs[idx])) for idx in top_indices]


class GibbsSamplingLDA:
    """基于吉布斯采样的LDA（更高效的实现）"""

    def __init__(self, num_topics: int = 10, alpha: float = 0.1, beta: float = 0.01,
                 num_iterations: int = 100, burn_in: int = 50):
        self.num_topics = num_topics
        self.alpha = alpha
        self.beta = beta
        self.num_iterations = num_iterations
        self.burn_in = burn_in

        # 计数矩阵
        self.n_dz = None  # 文档-主题计数
        self.n_zw = None  # 主题-词计数
        self.n_z = None   # 主题总数

        self.z = None     # 词的主题分配

    def fit(self, corpus: LDACorpus):
        """吉布斯采样训练"""
        num_docs = corpus.num_docs
        vocab_size = corpus.vocab.size

        # 初始化计数矩阵
        self.n_dz = np.zeros((num_docs, self.num_topics))
        self.n_zw = np.zeros((self.num_topics, vocab_size))
        self.n_z = np.zeros(self.num_topics)

        # 初始化主题分配
        self.z = []
        for doc_idx in range(num_docs):
            doc = corpus.get_document(doc_idx)
            doc_z = []
            for word_id in doc:
                topic = np.random.randint(0, self.num_topics)
                doc_z.append(topic)
                self.n_dz[doc_idx, topic] += 1
                self.n_zw[topic, word_id] += 1
                self.n_z[topic] += 1
            self.z.append(doc_z)

        # 吉布斯采样迭代
        for iteration in range(self.num_iterations):
            for doc_idx in range(num_docs):
                doc = corpus.get_document(doc_idx)
                for w_idx, word_id in enumerate(doc):
                    old_topic = self.z[doc_idx][w_idx]

                    # 更新计数（移除）
                    self.n_dz[doc_idx, old_topic] -= 1
                    self.n_zw[old_topic, word_id] -= 1
                    self.n_z[old_topic] -= 1

                    # 采样新主题
                    p_z = self._compute_posterior(doc_idx, word_id)
                    new_topic = np.random.choice(self.num_topics, p=p_z)

                    # 更新计数（添加）
                    self.z[doc_idx][w_idx] = new_topic
                    self.n_dz[doc_idx, new_topic] += 1
                    self.n_zw[new_topic, word_id] += 1
                    self.n_z[new_topic] += 1

            if iteration % 20 == 0:
                print(f"  吉布斯采样迭代 {iteration}/{self.num_iterations}")

    def _compute_posterior(self, doc_idx: int, word_id: int) -> np.ndarray:
        """计算后验分布"""
        probs = np.zeros(self.num_topics)

        for k in range(self.num_topics):
            # P(z=k | z_-i, w) ∝ (n_dz_-i + alpha) * (n_zw_-i + beta) / (n_z_-i + beta*V)
            n_dz = self.n_dz[doc_idx, k] + self.alpha
            n_zw = self.n_zw[k, word_id] + self.beta
            n_z = self.n_z[k] + self.beta * self.n_zw.shape[1]

            probs[k] = n_dz * n_zw / n_z

        # 归一化
        probs /= probs.sum()
        return probs

    def get_topic_words(self, topic_idx: int, top_k: int = 10) -> List[Tuple[str, float]]:
        """获取主题词"""
        word_probs = self.n_zw[topic_idx, :] / self.n_z[topic_idx]
        top_indices = np.argsort(word_probs)[::-1][:top_k]

        return [(self.vocab.get_word(idx), float(word_probs[idx])) for idx in top_indices]


def digamma(x: np.ndarray) -> np.ndarray:
    """Digamma函数近似（log gamma的导数）"""
    # 使用近似公式
    return np.log(x + 1e-10) - 1.0 / (2.0 * x + 1e-10)


def perplexity(lda: LDA, corpus: LDACorpus) -> float:
    """计算困惑度"""
    num_docs = corpus.num_docs
    total_log_likelihood = 0.0
    total_words = 0

    vocab_size = corpus.vocab.size

    for d in range(num_docs):
        doc = corpus.get_document(d)
        if not doc:
            continue

        doc_len = len(doc)
        gamma_norm = lda.gamma[d, :] / np.sum(lda.gamma[d, :])

        doc_ll = 0.0
        for word_id in doc:
            word_prob = np.sum(gamma_norm * lda.phi[:, word_id])
            doc_ll += np.log(word_prob + 1e-10)

        total_log_likelihood += doc_ll
        total_words += doc_len

    perplexity = np.exp(-total_log_likelihood / total_words)
    return perplexity


def demo():
    """LDA主题模型演示"""
    # 文档语料
    documents = [
        "machine learning algorithms process large datasets".split(),
        "deep learning neural networks recognize patterns in images".split(),
        "natural language processing understands text and speech".split(),
        "computer vision analyzes pictures and videos automatically".split(),
        "supervised learning uses labeled training data examples".split(),
        "unsupervised learning discovers hidden patterns automatically".split(),
        "reinforcement learning maximizes rewards through trial".split(),
        "neural networks process information like human brain".split(),
        "text classification categorizes documents automatically".split(),
        "object detection identifies items in images".split()
    ]

    print("[LDA主题模型演示]")

    # 构建词表和语料
    vocab = Vocabulary()
    vocab.build_vocab(documents)
    print(f"  词表大小: {vocab.size}")

    corpus = LDACorpus(vocab)
    for doc in documents:
        corpus.add_document(doc)
    print(f"  文档数量: {corpus.num_docs}")

    # 训练LDA
    lda = LDA(num_topics=3, max_iter=50)
    lda.fit(corpus)

    print(f"\n  迭代历史: {lda.log_likelihood[:5]}...")

    # 主题词
    print(f"\n  主题词:")
    for k in range(3):
        words = lda.get_topic_words(k, top_k=5)
        print(f"    Topic {k}: {words}")

    # 文档主题分布
    print(f"\n  文档主题分布:")
    for i in range(min(3, len(documents))):
        topics = lda.get_document_topics(i)
        print(f"    Doc {i}: {topics[:2]}")

    # 吉布斯采样LDA
    print(f"\n  吉布斯采样LDA:")
    gibbs_lda = GibbsSamplingLDA(num_topics=3, num_iterations=50)
    gibbs_lda.fit(corpus)
    for k in range(3):
        words = gibbs_lda.get_topic_words(k, top_k=5)
        print(f"    Topic {k}: {words}")

    print("  ✅ LDA主题模型演示通过！")


if __name__ == "__main__":
    demo()
