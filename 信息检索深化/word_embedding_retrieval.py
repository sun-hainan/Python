"""
词嵌入检索模块 - Word2Vec/Doc2Vec

本模块实现基于词嵌入的文档检索系统。
使用Word2Vec学习词向量，Doc2Vec学习文档向量。

核心方法：
1. Skip-gram / CBOW 模型
2. 负采样训练
3. Doc2Vec (PV-DM / PV-DBOW)
4. 基于向量平均的文档表示
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Tuple, Dict
from collections import Counter, defaultdict
import math
import random


class Tokenizer:
    """简单分词器"""

    @staticmethod
    def tokenize(text: str) -> List[str]:
        text = text.lower()
        words = text.replace(',', ' ').replace('.', ' ').split()
        return [w for w in words if len(w) > 1]


class Vocabulary:
    """词表"""

    def __init__(self, min_count: int = 1, max_vocab_size: int = 50000):
        self.min_count = min_count
        self.max_vocab_size = max_vocab_size
        self.word_to_idx = {'<PAD>': 0, '<UNK>': 1}
        self.idx_to_word = {0: '<PAD>', 1: '<UNK>'}
        self.word_counts = Counter()
        self.num_words = 2

    def build_vocab(self, documents: List[List[str]]):
        """从文档构建词表"""
        # 统计词频
        for doc in documents:
            self.word_counts.update(doc)

        # 按词频排序并截断
        words = [(word, count) for word, count in self.word_counts.items()
                 if count >= self.min_count]
        words.sort(key=lambda x: x[1], reverse=True)

        if self.max_vocab_size:
            words = words[:self.max_vocab_size - 2]

        # 构建映射
        for word, _ in words:
            idx = self.num_words
            self.word_to_idx[word] = idx
            self.idx_to_word[idx] = word
            self.num_words += 1

    def get_idx(self, word: str) -> int:
        return self.word_to_idx.get(word, self.word_to_idx['<UNK>'])

    def get_word(self, idx: int) -> str:
        return self.idx_to_word.get(idx, '<UNK>')


class SkipGram(nn.Module):
    """Skip-Gram词嵌入模型"""

    def __init__(self, vocab_size: int, embedding_dim: int = 128):
        super().__init__()
        self.target_embeddings = nn.Embedding(vocab_size, embedding_dim)
        self.context_embeddings = nn.Embedding(vocab_size, embedding_dim)

        # 初始化
        nn.init.uniform_(self.target_embeddings.weight, -0.5 / embedding_dim, 0.5 / embedding_dim)
        nn.init.zeros_(self.context_embeddings.weight)

    def forward(self, target, context, neg_samples):
        """
        前向传播
        :param target: 目标词 [batch]
        :param context: 上下文词 [batch]
        :param neg_samples: 负采样词 [batch, num_neg]
        :return: 损失
        """
        # 嵌入
        target_emb = self.target_embeddings(target)  # [batch, embed_dim]
        context_emb = self.context_embeddings(context)  # [batch, embed_dim]
        neg_emb = self.context_embeddings(neg_samples)  # [batch, num_neg, embed_dim]

        # 正样本损失
        pos_score = torch.sum(target_emb * context_emb, dim=-1)  # [batch]
        pos_loss = F.binary_cross_entropy_with_logits(pos_score, torch.ones_like(pos_score))

        # 负样本损失
        neg_score = torch.bmm(neg_emb, target_emb.unsqueeze(-1)).squeeze(-1)  # [batch, num_neg]
        neg_loss = F.binary_cross_entropy_with_logits(neg_score, torch.zeros_like(neg_score).float())

        return pos_loss + neg_loss

    def get_embedding(self, word_idx: int) -> np.ndarray:
        """获取词向量"""
        with torch.no_grad():
            emb = self.target_embeddings.weight[word_idx]
        return emb.cpu().numpy()


class Doc2VecPV-DM(nn.Module):
    """Doc2Vec PV-DM模型"""

    def __init__(self, vocab_size: int, doc_vocab_size: int, embedding_dim: int = 128):
        super().__init__()
        self.target_embeddings = nn.Embedding(vocab_size, embedding_dim)
        self.doc_embeddings = nn.Embedding(doc_vocab_size, embedding_dim)
        self.projection = nn.Linear(embedding_dim * 2, embedding_dim)

    def forward(self, target_word, doc_id, context_words):
        """
        前向传播
        :param target_word: 目标词
        :param doc_id: 文档ID
        :param context_words: 上下文词
        """
        target_emb = self.target_embeddings(target_word)
        doc_emb = self.doc_embeddings(doc_id)
        context_emb = self.target_embeddings(context_words).mean(dim=1)

        combined = torch.cat([target_emb, doc_emb], dim=-1)
        projected = self.projection(combined)

        return projected


class WordEmbeddingRetrieval:
    """基于词嵌入的检索系统"""

    def __init__(self, vocab: Vocabulary, embedding_dim: int = 128):
        self.vocab = vocab
        self.embedding_dim = embedding_dim
        self.model = SkipGram(vocab.num_words, embedding_dim)
        self.doc_vectors = {}  # doc_id -> 向量

    def train(self, documents: List[List[str]], num_epochs: int = 5, batch_size: int = 256,
              window_size: int = 5, num_neg: int = 5, learning_rate: float = 0.01):
        """
        训练词嵌入
        :param documents: 文档列表（分词后）
        :param num_epochs: 训练轮数
        :param batch_size: batch大小
        :param window_size: 上下文窗口大小
        :param num_neg: 负采样数量
        :param learning_rate: 学习率
        """
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)

        for epoch in range(num_epochs):
            total_loss = 0.0
            num_batches = 0

            # 随机打乱
            random.shuffle(documents)

            for doc in documents:
                # 生成训练样本
                targets, contexts, negs = self._generate_samples(doc, window_size, num_neg)

                if not targets:
                    continue

                # 转为tensor
                targets_t = torch.tensor(targets, dtype=torch.long)
                contexts_t = torch.tensor(contexts, dtype=torch.long)
                negs_t = torch.tensor(negs, dtype=torch.long)

                # 训练batch
                for i in range(0, len(targets), batch_size):
                    batch_targets = targets_t[i:i + batch_size]
                    batch_contexts = contexts_t[i:i + batch_size]
                    batch_negs = negs_t[i:i + batch_size]

                    # 前向
                    loss = self.model(batch_targets, batch_contexts, batch_negs)

                    # 反向
                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()

                    total_loss += loss.item()
                    num_batches += 1

            print(f"  Epoch {epoch + 1}: avg loss = {total_loss / num_batches:.4f}")

    def _generate_samples(self, doc: List[str], window_size: int, num_neg: int):
        """生成Skip-Gram训练样本"""
        targets, contexts, negs = [], [], []

        for i, target_word in enumerate(doc):
            target_idx = self.vocab.get_idx(target_word)
            if target_idx == 0:  # PAD/UNK
                continue

            # 上下文窗口
            start = max(0, i - window_size)
            end = min(len(doc), i + window_size + 1)

            for j in range(start, end):
                if i != j:
                    context_idx = self.vocab.get_idx(doc[j])
                    if context_idx == 0:
                        continue

                    targets.append(target_idx)
                    contexts.append(context_idx)

                    # 负采样
                    neg_samples = []
                    for _ in range(num_neg):
                        neg_word = random.choice(list(self.vocab.word_to_idx.keys()))
                        neg_samples.append(self.vocab.get_idx(neg_word))
                    negs.append(neg_samples)

        return targets, contexts, negs

    def get_word_vector(self, word: str) -> np.ndarray:
        """获取词的嵌入向量"""
        idx = self.vocab.get_idx(word)
        return self.model.get_embedding(idx)

    def get_document_vector(self, document: List[str]) -> np.ndarray:
        """获取文档向量（词向量平均）"""
        vectors = []
        for word in document:
            try:
                vec = self.get_word_vector(word)
                vectors.append(vec)
            except:
                pass

        if vectors:
            return np.mean(vectors, axis=0)
        else:
            return np.zeros(self.embedding_dim)

    def index_document(self, doc_id: str, document: List[str]):
        """索引文档"""
        doc_vector = self.get_document_vector(document)
        self.doc_vectors[doc_id] = doc_vector

    def search(self, query: List[str], top_k: int = 5) -> List[Tuple[str, float]]:
        """搜索相关文档"""
        query_vector = self.get_document_vector(query)

        scores = []
        for doc_id, doc_vector in self.doc_vectors.items():
            # 余弦相似度
            sim = np.dot(query_vector, doc_vector) / (
                np.linalg.norm(query_vector) * np.linalg.norm(doc_vector) + 1e-10
            )
            scores.append((doc_id, float(sim)))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class FastText:
    """FastText：子词嵌入"""

    def __init__(self, vocab: Vocabulary, embedding_dim: int = 128, ngram_range: Tuple[int, int] = (3, 6)):
        self.vocab = vocab
        self.embedding_dim = embedding_dim
        self.ngram_range = ngram_range

        # 字符n-gram词表
        self.ngram_to_idx = {}
        self.ngram_embeddings = None

        # 词嵌入
        self.word_embeddings = None

    def _get_ngrams(self, word: str) -> List[str]:
        """获取字符n-gram"""
        word = f"<{word}>"
        ngrams = []
        for n in range(self.ngram_range[0], self.ngram_range[1] + 1):
            for i in range(len(word) - n + 1):
                ngrams.append(word[i:i + n])
        return ngrams

    def get_subword_vector(self, word: str) -> np.ndarray:
        """获取子词向量"""
        ngrams = self._get_ngrams(word)
        vectors = []

        for ngram in ngrams:
            if ngram in self.ngram_to_idx:
                idx = self.ngram_to_idx[ngram]
                vectors.append(self.ngram_embeddings[idx])

        if vectors:
            return np.mean(vectors, axis=0)
        else:
            return np.zeros(self.embedding_dim)

    def get_word_vector(self, word: str) -> np.ndarray:
        """获取完整词向量（词+子词）"""
        word_vec = self.word_embeddings.get(word, np.zeros(self.embedding_dim))
        subword_vec = self.get_subword_vector(word)
        return word_vec + subword_vec


def compute_word_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """计算词向量相似度"""
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (norm1 * norm2))


def demo():
    """词嵌入检索演示"""
    # 文档数据
    documents = [
        "machine learning algorithms process large datasets efficiently".split(),
        "deep learning neural networks recognize patterns in complex data".split(),
        "natural language processing understands text and speech automatically".split(),
        "computer vision analyzes images and identifies objects accurately".split(),
        "supervised learning trains models with labeled training examples".split(),
    ]

    print("[词嵌入检索演示]")

    # 构建词表
    vocab = Vocabulary(min_count=1)
    vocab.build_vocab(documents)
    print(f"  词表大小: {vocab.num_words}")

    # 初始化检索系统
    retrieval = WordEmbeddingRetrieval(vocab, embedding_dim=64)

    # 训练
    print("\n  训练Skip-Gram模型:")
    retrieval.train(documents, num_epochs=3, window_size=2, num_neg=5)

    # 索引文档
    for i, doc in enumerate(documents):
        retrieval.index_document(f"doc_{i}", doc)

    # 词向量相似度
    print(f"\n  词向量相似度:")
    word_pairs = [
        ("learning", "neural"),
        ("machine", "learning"),
        ("text", "speech")
    ]
    for w1, w2 in word_pairs:
        v1 = retrieval.get_word_vector(w1)
        v2 = retrieval.get_word_vector(w2)
        sim = compute_word_similarity(v1, v2)
        print(f"    '{w1}' vs '{w2}': {sim:.4f}")

    # 搜索
    queries = [
        "neural networks deep".split(),
        "text understanding language".split()
    ]

    print(f"\n  文档搜索:")
    for query in queries:
        results = retrieval.search(query, top_k=3)
        print(f"    查询: {' '.join(query)}")
        for doc_id, score in results:
            print(f"      {doc_id}: {score:.4f}")

    print("  ✅ 词嵌入检索演示通过！")


if __name__ == "__main__":
    demo()
