# -*- coding: utf-8 -*-
"""
算法实现：数据挖掘 / lda

本文件实现 lda 相关的算法功能。
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import random
import math


class LDA:
    """
    LDA主题模型
    
    使用吉布斯采样进行参数估计
    
    参数:
        n_topics: 主题数K
        alpha: 文档-主题分布的Dirichlet先验
        beta: 主题-词汇分布的Dirichlet先验
        n_iterations: 迭代次数
        random_state: 随机种子
    """
    
    def __init__(self, n_topics: int = 5, alpha: float = 0.1, beta: float = 0.01,
                 n_iterations: int = 100, random_state: int = 42):
        self.n_topics = n_topics
        self.alpha = alpha  # 文档-主题Dirichlet参数
        self.beta = beta    # 主题-词汇Dirichlet参数
        self.n_iterations = n_iterations
        self.random_state = random_state
        
        # 词汇表
        self.vocab: List[str] = []
        self.word_to_idx: Dict[str, int] = {}
        
        # 文档数据
        self.docs: List[List[int]] = []  # 文档，词索引序列
        self.n_docs = 0
        self.n_words = 0  # 词汇表大小
        
        # 计数矩阵
        # n_d_k[doc, topic]: 文档d中分配给主题k的词数
        self.n_d_k: Optional[np.ndarray] = None
        # n_k_w[topic, word]: 主题k中词w被分配的次数
        self.n_k_w: Optional[np.ndarray] = None
        # n_k[topic]: 主题k被分配的总数
        self.n_k: Optional[np.ndarray] = None
        
        # Z矩阵：每篇文档每个词的 topic 分配
        self.z: List[List[int]] = []
        
        # 主题-词汇分布
        self.phi: Optional[np.ndarray] = None  # [K, V]
        
        # 文档-主题分布
        self.theta: Optional[np.ndarray] = None  # [D, K]
    
    def _preprocess(self, documents: List[str]) -> None:
        """预处理文档"""
        # 构建词汇表
        word_counts = defaultdict(int)
        for doc in documents:
            words = doc.lower().split()
            for w in words:
                word_counts[w] += 1
        
        # 过滤低频词
        self.vocab = [w for w, c in word_counts.items() if c >= 2]
        self.word_to_idx = {w: i for i, w in enumerate(self.vocab)}
        self.n_words = len(self.vocab)
        
        # 转换文档为词索引序列
        self.docs = []
        for doc in documents:
            words = doc.lower().split()
            indices = [self.word_to_idx[w] for w in words if w in self.word_to_idx]
            self.docs.append(indices)
        
        self.n_docs = len(self.docs)
    
    def fit(self, documents: List[str]) -> 'LDA':
        """
        训练LDA模型
        
        参数:
            documents: 文档列表
        """
        # 预处理
        self._preprocess(documents)
        
        # 初始化计数矩阵
        self.n_d_k = np.zeros((self.n_docs, self.n_topics))
        self.n_k_w = np.zeros((self.n_topics, self.n_words))
        self.n_k = np.zeros(self.n_topics)
        
        # 初始化Z（随机分配主题）
        random.seed(self.random_state)
        np.random.seed(self.random_state)
        
        self.z = []
        for d, doc in enumerate(self.docs):
            z_d = [random.randint(0, self.n_topics - 1) for _ in doc]
            self.z.append(z_d)
            
            # 更新计数
            for i, k in enumerate(z_d):
                w = doc[i]
                self.n_d_k[d, k] += 1
                self.n_k_w[k, w] += 1
                self.n_k[k] += 1
        
        # 吉布斯采样
        for iteration in range(self.n_iterations):
            self._gibbs_sweep()
            
            if (iteration + 1) % 20 == 0:
                perplexity = self._compute_perplexity()
                print(f"  迭代 {iteration + 1}: 困惑度 = {perplexity:.2f}")
        
        # 估计最终参数
        self._estimate_parameters()
        
        return self
    
    def _gibbs_sweep(self) -> None:
        """吉布斯采样一次迭代"""
        for d in range(self.n_docs):
            doc = self.docs[d]
            
            for i, w in enumerate(doc):
                k = self.z[d][i]
                
                # 移除当前分配
                self.n_d_k[d, k] -= 1
                self.n_k_w[k, w] -= 1
                self.n_k[k] -= 1
                
                # 计算新主题的采样概率
                probs = self._compute_topic_probs(d, w)
                
                # 采样新主题
                k_new = self._sample_from_probs(probs)
                
                # 添加新分配
                self.z[d][i] = k_new
                self.n_d_k[d, k_new] += 1
                self.n_k_w[k_new, w] += 1
                self.n_k[k_new] += 1
    
    def _compute_topic_probs(self, d: int, w: int) -> np.ndarray:
        """
        计算词w在文档d被分配到各主题的概率
        
        P(z=k | z_{-d,i}, w) ∝ (n_d,k + alpha) * (n_k,w + beta) / (n_k + beta * V)
        """
        probs = np.zeros(self.n_topics)
        
        for k in range(self.n_topics):
            # 文档-主题权重
            doc_topic = (self.n_d_k[d, k] + self.alpha)
            # 主题-词汇权重
            topic_word = (self.n_k_w[k, w] + self.beta) / (self.n_k[k] + self.beta * self.n_words)
            
            probs[k] = doc_topic * topic_word
        
        # 归一化
        probs /= probs.sum()
        return probs
    
    def _sample_from_probs(self, probs: np.ndarray) -> int:
        """从概率分布中采样"""
        r = random.random() * probs.sum()
        cumsum = 0.0
        for k, p in enumerate(probs):
            cumsum += p
            if cumsum >= r:
                return k
        return self.n_topics - 1
    
    def _estimate_parameters(self) -> None:
        """估计phi和theta参数"""
        # phi[k,w] = (n_k_w + beta) / (n_k + beta * V)
        self.phi = (self.n_k_w + self.beta) / (self.n_k[:, np.newaxis] + self.beta * self.n_words)
        
        # theta[d,k] = (n_d_k + alpha) / (n_d + alpha * K)
        doc_totals = self.n_d_k.sum(axis=1)
        self.theta = (self.n_d_k + self.alpha) / (doc_totals[:, np.newaxis] + self.alpha * self.n_topics)
    
    def _compute_perplexity(self) -> float:
        """计算困惑度"""
        log_likelihood = 0.0
        total_words = 0
        
        for d, doc in enumerate(self.docs):
            for w in doc:
                # 计算词w的边际概率
                prob = 0.0
                for k in range(self.n_topics):
                    prob += self.theta[d, k] * self.phi[k, w]
                
                if prob > 0:
                    log_likelihood += math.log(prob)
                total_words += 1
        
        perplexity = math.exp(-log_likelihood / total_words)
        return perplexity
    
    def get_top_words(self, topic_id: int, n_words: int = 10) -> List[Tuple[str, float]]:
        """获取某主题的top词"""
        if self.phi is None:
            return []
        
        topic_probs = self.phi[topic_id]
        top_indices = topic_probs.argsort()[::-1][:n_words]
        
        return [(self.vocab[idx], topic_probs[idx]) for idx in top_indices]
    
    def get_top_topics(self, doc_id: int, n_topics: int = 3) -> List[Tuple[int, float]]:
        """获取某文档的top主题"""
        if self.theta is None:
            return []
        
        doc_probs = self.theta[doc_id]
        top_indices = doc_probs.argsort()[::-1][:n_topics]
        
        return [(idx, doc_probs[idx]) for idx in top_indices]
    
    def print_topics(self, n_words: int = 10) -> None:
        """打印所有主题"""
        print("=" * 50)
        print(f"发现的主题 ({self.n_topics} 个)")
        print("=" * 50)
        
        for k in range(self.n_topics):
            top_words = self.get_top_words(k, n_words)
            print(f"\n主题 {k}:")
            for word, prob in top_words:
                print(f"  {word}: {prob:.4f}")
    
    def transform(self, document: str) -> np.ndarray:
        """
        获取新文档的主题分布
        
        使用已训练的主题-词汇分布
        """
        words = document.lower().split()
        indices = [self.word_to_idx.get(w) for w in words if w in self.word_to_idx]
        
        if not indices:
            return np.zeros(self.n_topics)
        
        # 简单的词袋主题分布
        topic_dist = np.zeros(self.n_topics)
        for w_idx in indices:
            topic_dist += self.phi[:, w_idx]
        
        topic_dist /= topic_dist.sum()
        return topic_dist


# ==================== 测试代码 ====================
if __name__ == "__main__":
    print("=" * 50)
    print("LDA主题模型测试")
    print("=" * 50)
    
    # 测试文档集
    documents = [
        "bank financial money investment banking interest rates",
        "bank river water stream flow bridge bank",
        "banking financial services credit loans deposits",
        "river water fish swimming boat fishing",
        "financial investment stocks bonds market portfolio",
        "water river lake ocean sea wave",
        "loans credit banking mortgage interest",
        "ocean water marine fish coral reef",
        "stocks financial market trading shares",
        "fishing boat river lake water sport",
    ]
    
    print("\n文档集:")
    for i, doc in enumerate(documents):
        print(f"  文档{i}: {doc[:50]}...")
    
    # 训练LDA
    print("\n--- 训练LDA模型 ---")
    
    lda = LDA(n_topics=3, alpha=0.1, beta=0.01, n_iterations=100)
    lda.fit(documents)
    
    # 打印主题
    lda.print_topics(n_words=5)
    
    # 测试新文档
    print("\n--- 新文档主题分析 ---")
    
    new_docs = [
        "financial investment banking stocks",
        "river water boat fishing",
        "bank loans credit money"
    ]
    
    for doc in new_docs:
        topic_dist = lda.transform(doc)
        top_topic = topic_dist.argsort()[::-1][0]
        print(f"\n文档: {doc}")
        print(f"主题分布: {topic_dist}")
        print(f"主要主题: 主题{top_topic}")
    
    # 文档主题分布
    print("\n--- 文档主题分布 ---")
    
    for i, doc in enumerate(documents[:5]):
        top_topics = lda.get_top_topics(i, 2)
        print(f"文档{i}: {doc[:40]}...")
        print(f"  主要主题: {top_topics}")
    
    # 大规模测试
    print("\n" + "=" * 50)
    print("大规模文档测试")
    print("=" * 50)
    
    import time
    
    # 生成大规模测试数据
    n_docs = 1000
    n_words_per_doc = 50
    
    topics_keywords = [
        "computer science programming software algorithm data",
        "sports football basketball player team game match",
        "music concert singer song album band rock",
        "food restaurant cooking recipe cuisine chef meal",
        "travel hotel vacation destination beach mountain"
    ]
    
    large_docs = []
    for _ in range(n_docs):
        topic_idx = random.randint(0, len(topics_keywords) - 1)
        words = topics_keywords[topic_idx].split()
        doc = " ".join([random.choice(words) for _ in range(n_words_per_doc)])
        large_docs.append(doc)
    
    print(f"生成 {n_docs} 文档")
    
    lda_large = LDA(n_topics=5, n_iterations=50)
    
    start = time.time()
    lda_large.fit(large_docs)
    elapsed = time.time() - start
    
    print(f"\n训练时间: {elapsed:.3f}秒")
    
    lda_large.print_topics(n_words=3)
