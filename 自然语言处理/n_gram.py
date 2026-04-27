# -*- coding: utf-8 -*-
"""
算法实现：自然语言处理 / n_gram

本文件实现 n_gram 相关的算法功能。
"""

import numpy as np
from collections import Counter, defaultdict


class NGramLM:
    """N-gram 语言模型"""

    def __init__(self, n=3, smoothing_k=1.0):
        """
        n: n-gram 的 n 值（2=bigram, 3=trigram, 4=4-gram...）
        smoothing_k: Add-k 平滑参数
        """
        self.n = n
        self.smoothing_k = smoothing_k

        # n-gram 计数: counts[(w_{i-n+1},...,w_i)] = frequency
        self.ngram_counts = Counter()
        # (n-1)-gram 上下文计数: counts[(w_{i-n+1},...,w_{i-1})] = frequency
        self.context_counts = Counter()

        # 词汇表
        self.vocab = set()
        self.vocab_size = 0

        # 概率表（缓存）
        self.prob_table = {}

    def tokenize(self, text):
        """简单分词"""
        return ["<BOS>"] + text.lower().split() + ["<EOS>"]

    def build(self, corpus):
        """从语料库构建 N-gram 模型"""
        # 统计计数
        for sentence in corpus:
            tokens = self.tokenize(sentence)
            self.vocab.update(tokens)

            # 遍历所有 n-gram
            for i in range(len(tokens)):
                # n-gram: tokens[max(0,i-n+1):i+1]
                ngram = tuple(tokens[max(0, i - n + 1):i + 1])
                self.ngram_counts[ngram] += 1
                # 上下文 (n-1)-gram
                if len(ngram) > 1:
                    context = ngram[:-1]
                    self.context_counts[context] += 1

        self.vocab_size = len(self.vocab)

        # 预计算所有条件概率
        self._compute_probabilities()

        return self

    def _compute_probabilities(self):
        """预计算条件概率 P(w_i | context)"""
        for ngram, count in self.ngram_counts.items():
            context = ngram[:-1]
            context_count = self.context_counts.get(context, 0)
            # Add-k 平滑
            prob = (count + self.smoothing_k) / (context_count + self.smoothing_k * self.vocab_size)
            self.prob_table[ngram] = prob

    def probability(self, ngram):
        """返回 P(w_n | w_1,...,w_{n-1})"""
        if ngram in self.prob_table:
            return self.prob_table[ngram]
        # 回退到 (n-1)-gram（如果是 bigram 则用均匀分布）
        if len(ngram) > 2:
            return self.probability(ngram[1:])
        return 1.0 / self.vocab_size

    def sentence_log_prob(self, sentence):
        """计算句子的对数概率 log P(sentence)"""
        tokens = self.tokenize(sentence)
        if len(tokens) < self.n:
            return float('-inf')
        log_prob = 0.0
        for i in range(self.n - 1, len(tokens)):
            ngram = tuple(tokens[i - self.n + 1:i + 1])
            prob = self.probability(ngram)
            log_prob += np.log(prob + 1e-10)
        return log_prob

    def sentence_prob(self, sentence):
        """计算句子的概率（注意：概率很小，容易下溢）"""
        log_prob = self.sentence_log_prob(sentence)
        return np.exp(log_prob)

    def perplexity(self, corpus):
        """计算语料库的困惑度（越低越好）"""
        total_log_prob = 0.0
        total_tokens = 0
        for sentence in corpus:
            tokens = self.tokenize(sentence)
            total_tokens += len(tokens) - 1  # 不计 <BOS>
            total_log_prob += self.sentence_log_prob(sentence)
        avg_log_prob = total_log_prob / total_tokens
        perplexity = np.exp(-avg_log_prob)
        return perplexity

    def generate(self, max_len=20, seed=None):
        """生成随机句子"""
        if seed is not None:
            np.random.seed(seed)
        tokens = ["<BOS>"]
        for _ in range(max_len):
            # 当前上下文
            context = tuple(tokens[-(self.n - 1):])
            # 采样下一个词
            probs = []
            candidates = []
            for w in self.vocab:
                ngram = context + (w,)
                prob = self.probability(ngram)
                probs.append(prob)
                candidates.append(w)
            probs = np.array(probs)
            probs /= probs.sum()
            next_token = np.random.choice(candidates, p=probs)
            tokens.append(next_token)
            if next_token == "<EOS>":
                break
        return " ".join(tokens[1:-1]) if tokens[-1] == "<EOS>" else " ".join(tokens[1:])


if __name__ == "__main__":
    # 测试 N-gram 语言模型
    corpus = [
        "the cat sat on the mat",
        "the dog ran in the yard",
        "the cat ran to the door",
        "the dog sat on the floor",
        "a cat is better than a dog",
        "a dog is better than a cat",
        "i love machine learning",
        "machine learning is fun",
        "natural language processing is interesting",
        "deep learning is powerful"
    ]

    # 训练 Trigram 模型
    lm = NGramLM(n=3, smoothing_k=0.1)
    lm.build(corpus)

    # 测试句子概率
    test_sentences = [
        "the cat sat on the mat",
        "the cat ran to the door",
        "a dog is better than a cat",
        "machine learning is fun"
    ]
    print("Trigram LM 句子对数概率:")
    for s in test_sentences:
        lp = lm.sentence_log_prob(s)
        print(f"  '{s}': {lp:.4f}")

    # 计算困惑度
    pp = lm.perplexity(corpus)
    print(f"\n语料库困惑度: {pp:.2f}")

    # 生成句子
    print("\n生成句子:")
    for _ in range(5):
        print(f"  {lm.generate(max_len=15)}")

    # Bigram 模型对比
    lm2 = NGramLM(n=2, smoothing_k=0.1)
    lm2.build(corpus)
    print(f"\nBigram 困惑度: {lm2.perplexity(corpus):.2f}")
    print(f"Trigram 困惑度: {pp:.2f}")
