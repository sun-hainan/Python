# -*- coding: utf-8 -*-
"""
算法实现：自然语言处理 / tfidf

本文件实现 tfidf 相关的算法功能。
"""

import numpy as np
import re
from collections import Counter, defaultdict


class TFIDFVectorizer:
    """TF-IDF 向量化器"""

    def __init__(self, min_df=1, max_df=1.0, stop_words=None):
        # min_df: 最小文档频率阈值
        # max_df: 最大文档频率比例阈值
        # stop_words: 停用词集合
        self.min_df = min_df
        self.max_df = max_df
        self.stop_words = set(stop_words) if stop_words else set()
        self.vocabulary = {}  # 词 -> 索引
        self.idf = None  # 逆文档频率向量

    def fit(self, documents):
        """构建词汇表并计算 IDF"""
        # 分词
        tokenized = [self._tokenize(doc) for doc in documents]
        # 统计文档频率 df[t] = 包含词 t 的文档数
        df = Counter()
        for tokens in tokenized:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                df[token] += 1

        # 根据 min_df / max_df 过滤词汇
        n_docs = len(documents)
        for token, freq in list(df.items()):
            if freq < self.min_df or freq > n_docs * self.max_df:
                del df[token]
            elif token in self.stop_words:
                del df[token]

        # 建立词汇表（按频率排序）
        self.vocabulary = {token: idx for idx, (token, _) in enumerate(df.most_common())}
        vocab_size = len(self.vocabulary)
        self.idf = np.zeros(vocab_size)

        # 计算 IDF: log((N + 1) / (df + 1)) + 1（平滑版本）
        for token, idx in self.vocabulary.items():
            self.idf[idx] = np.log((n_docs + 1) / (df[token] + 1)) + 1

        return self

    def transform(self, documents):
        """将文档转换为 TF-IDF 向量矩阵"""
        n_docs = len(documents)
        vocab_size = len(self.vocabulary)
        # TF-IDF 矩阵 (n_docs, vocab_size)
        tfidf_matrix = np.zeros((n_docs, vocab_size))

        for doc_idx, doc in enumerate(documents):
            tokens = self._tokenize(doc)
            token_counts = Counter(tokens)
            total_tokens = len(tokens)
            for token, count in token_counts.items():
                if token in self.vocabulary:
                    idx = self.vocabulary[token]
                    # TF = 词频 / 总词数
                    tf = count / total_tokens
                    tfidf_matrix[doc_idx, idx] = tf * self.idf[idx]

        return tfidf_matrix

    def fit_transform(self, documents):
        """拟合并转换"""
        self.fit(documents)
        return self.transform(documents)

    def _tokenize(self, text):
        """简单分词：转小写，去除非字母字符"""
        text = text.lower()
        tokens = re.findall(r'[a-z]+', text)
        return [t for t in tokens if t not in self.stop_words]

    def cosine_similarity(self, vec1, vec2):
        """计算两个向量的余弦相似度"""
        dot = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)


if __name__ == "__main__":
    # 测试 TF-IDF
    corpus = [
        "the sky is blue and the sky is beautiful",
        "the sun is bright and the sun is shining",
        "the moon is bright and the night is dark",
        "machine learning is great and artificial intelligence is amazing"
    ]
    vectorizer = TFIDFVectorizer()
    tfidf_matrix = vectorizer.fit_transform(corpus)
    print(f"TF-IDF 矩阵形状: {tfidf_matrix.shape}")
    print(f"词汇表大小: {len(vectorizer.vocabulary)}")

    # 计算文档相似度
    sim = vectorizer.cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])
    print(f"文档0 与 文档1 的余弦相似度: {sim:.4f}")

    # 查询示例
    query = "the sky is blue"
    query_vec = vectorizer.transform([query])[0]
    scores = [vectorizer.cosine_similarity(query_vec, doc_vec)
              for doc_vec in tfidf_matrix]
    print(f"查询「{query}」与各文档的相似度: {[f'{s:.4f}' for s in scores]}")
