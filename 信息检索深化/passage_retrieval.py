"""
段落检索模块 - TF-IDF/BM25/密集检索

本模块实现综合的段落检索系统，整合多种检索方法。
段落检索是问答系统和搜索引擎的核心组件。

核心方法：
1. 稀疏检索：TF-IDF、BM25
2. 密集检索：Dense Passage Retrieval
3. 混合检索：稀疏+密集融合
4. 段落选择：基于语义相似度选择最佳段落
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Tuple, Dict, Optional
from collections import Counter, defaultdict
import math


class Tokenizer:
    """简单分词器"""

    @staticmethod
    def tokenize(text: str) -> List[str]:
        text = text.lower()
        words = text.replace(',', ' ').replace('.', ' ').replace('?', ' ').split()
        return [w for w in words if len(w) > 1]


class TFIDfRetriever:
    """TF-IDF段落检索器"""

    def __init__(self):
        self.documents = []
        self.vocab = set()
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

    def _compute_tf(self, term: str, doc_idx: int) -> float:
        """计算TF"""
        tf = self.doc_term_freqs[doc_idx].get(term, 0)
        return 1 + math.log(tf) if tf > 0 else 0

    def _compute_idf(self, term: str) -> float:
        """计算IDF"""
        df = self.doc_freqs.get(term, 0)
        return math.log((self.num_docs + 1) / (df + 1)) + 1

    def score(self, query: str, doc_idx: int) -> float:
        """计算TF-IDF分数"""
        tokens = Tokenizer.tokenize(query)
        score = 0.0

        for term in tokens:
            if term in self.vocab:
                tf = self._compute_tf(term, doc_idx)
                idf = self._compute_idf(term)
                score += tf * idf

        return score

    def retrieve(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """检索相关段落"""
        scores = []
        for doc_idx in range(self.num_docs):
            score = self.score(query, doc_idx)
            scores.append((doc_idx, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class BM25Retriever:
    """BM25段落检索器"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents = []
        self.vocab = set()
        self.doc_term_freqs = []
        self.doc_len = {}
        self.doc_freqs = Counter()
        self.num_docs = 0
        self.avgdl = 0.0

    def fit(self, documents: List[str]):
        """构建索引"""
        self.documents = documents
        self.num_docs = len(documents)
        self.doc_term_freqs = []
        total_len = 0

        for doc_idx, doc in enumerate(documents):
            tokens = Tokenizer.tokenize(doc)
            tf = Counter(tokens)
            self.doc_term_freqs.append(tf)
            self.vocab.update(tokens)
            self.doc_len[doc_idx] = len(tokens)
            total_len += len(tokens)

            for word in set(tokens):
                self.doc_freqs[word] += 1

        self.avgdl = total_len / self.num_docs if self.num_docs > 0 else 1

    def _compute_idf(self, term: str) -> float:
        """计算IDF"""
        df = self.doc_freqs.get(term, 0)
        return math.log((self.num_docs - df + 0.5) / (df + 0.5) + 1)

    def score(self, query: str, doc_idx: int) -> float:
        """计算BM25分数"""
        tokens = Tokenizer.tokenize(query)
        tf = self.doc_term_freqs[doc_idx]
        doc_len = self.doc_len[doc_idx]

        score = 0.0
        for term in tokens:
            if term not in self.vocab:
                continue

            tf_doc = tf.get(term, 0)
            idf = self._compute_idf(term)

            numerator = tf_doc * (self.k1 + 1)
            denominator = tf_doc + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
            score += idf * numerator / denominator

        return score

    def retrieve(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """检索"""
        scores = [(doc_idx, self.score(query, doc_idx)) for doc_idx in range(self.num_docs)]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class DensePassageEncoder(nn.Module):
    """密集段落编码器"""

    def __init__(self, vocab_size: int, embed_dim: int = 128, hidden_dim: int = 256):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.encoder = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )
        self.projection = nn.Linear(hidden_dim * 2, hidden_dim)

    def forward(self, token_ids: torch.Tensor, mask: Optional[torch.Tensor] = None):
        """编码"""
        embed = self.embedding(token_ids)
        outputs, (h_n, _) = self.encoder(embed)
        # 双向最后隐藏状态拼接
        hidden = torch.cat([h_n[0], h_n[1]], dim=-1)
        # 投影
        output = self.projection(hidden)
        output = F.normalize(output, p=2, dim=-1)
        return output


class DenseRetriever:
    """密集段落检索器"""

    def __init__(self, encoder: DensePassageEncoder):
        self.encoder = encoder
        self.encoder.eval()
        self.passage_embeddings = {}
        self.passage_texts = {}

    def index_passage(self, passage_id: str, passage_text: str, token_ids: torch.Tensor):
        """索引段落"""
        with torch.no_grad():
            embedding = self.encoder(token_ids.unsqueeze(0)).squeeze(0)
            self.passage_embeddings[passage_id] = embedding
            self.passage_texts[passage_id] = passage_text

    def search(self, query_embedding: torch.Tensor, top_k: int = 10) -> List[Tuple[str, float]]:
        """向量搜索"""
        scores = []
        for pid, emb in self.passage_embeddings.items():
            sim = F.cosine_similarity(query_embedding.unsqueeze(0), emb.unsqueeze(0)).item()
            scores.append((pid, sim))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class HybridRetriever:
    """混合检索器：稀疏 + 密集"""

    def __init__(self, sparse_weight: float = 0.5, dense_weight: float = 0.5):
        self.sparse_weight = sparse_weight
        self.dense_weight = dense_weight

        self.tfidf_retriever = TFIDfRetriever()
        self.bm25_retriever = BM25Retriever()
        self.dense_retriever = None

    def fit_sparse(self, documents: List[str]):
        """构建稀疏索引"""
        self.tfidf_retriever.fit(documents)
        self.bm25_retriever.fit(documents)

    def fit_dense(self, encoder: DensePassageEncoder, tokenized_documents: List[torch.Tensor]):
        """构建密集索引"""
        self.dense_retriever = DenseRetriever(encoder)

        for doc_idx, tokens in enumerate(tokenized_documents):
            self.dense_retriever.index_passage(f"doc_{doc_idx}", "", tokens)

    def retrieve(self, query: str, query_embedding: Optional[torch.Tensor] = None,
                 top_k: int = 10) -> List[Tuple[int, float]]:
        """混合检索"""
        # 稀疏检索
        bm25_scores = self.bm25_retriever.retrieve(query, top_k=top_k * 2)
        tfidf_scores = self.tfidf_retriever.retrieve(query, top_k=top_k * 2)

        # 归一化稀疏分数
        max_bm25 = max(s for _, s in bm25_scores) if bm25_scores else 1.0
        max_tfidf = max(s for _, s in tfidf_scores) if tfidf_scores else 1.0

        combined_scores = defaultdict(float)

        for doc_idx, score in bm25_scores:
            combined_scores[doc_idx] += self.sparse_weight * (score / max_bm25 if max_bm25 > 0 else 0)

        for doc_idx, score in tfidf_scores:
            combined_scores[doc_idx] += self.sparse_weight * 0.5 * (score / max_tfidf if max_tfidf > 0 else 0)

        # 密集检索
        if self.dense_retriever and query_embedding is not None:
            dense_results = self.dense_retriever.search(query_embedding, top_k=top_k * 2)
            max_dense = max(s for _, s in dense_results) if dense_results else 1.0

            for doc_id, score in dense_results:
                # 从doc_id提取doc_idx
                try:
                    doc_idx = int(doc_id.split('_')[1])
                    combined_scores[doc_idx] += self.dense_weight * (score / max_dense if max_dense > 0 else 0)
                except:
                    pass

        # 排序
        sorted_scores = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_scores[:top_k]


class PassageSelector:
    """段落选择器：选择最佳答案段落"""

    def __init__(self):
        self.min_length = 10
        self.max_length = 300

    def select(self, query: str, passages: List[Tuple[int, float, str]],
               answer_hint: Optional[str] = None) -> List[Dict]:
        """
        选择最佳段落
        :param passages: [(doc_idx, score, text)]
        :param answer_hint: 答案提示词
        :return: 排序后的段落列表
        """
        selected = []

        for doc_idx, score, text in passages:
            # 长度过滤
            words = text.split()
            if len(words) < self.min_length or len(words) > self.max_length:
                continue

            # 计算额外特征
            features = {
                "doc_idx": doc_idx,
                "retrieval_score": score,
                "length": len(words),
                "contains_answer_hint": 0.0
            }

            # 检查答案提示
            if answer_hint:
                if answer_hint.lower() in text.lower():
                    features["contains_answer_hint"] = 1.0

            # 综合分数
            final_score = score * (1 + 0.2 * features["contains_answer_hint"])

            selected.append({
                "doc_idx": doc_idx,
                "text": text,
                "score": final_score,
                "features": features
            })

        # 排序
        selected.sort(key=lambda x: x["score"], reverse=True)
        return selected


def evaluate_retrieval(retrieved: List[List[int]], relevant: List[List[int]],
                       k_values=[1, 5, 10, 20]) -> Dict[str, float]:
    """评估检索性能"""
    results = {}

    for k in k_values:
        recalls = []
        precisions = []

        for ret, rel in zip(retrieved, relevant):
            ret_set = set(ret[:k])
            rel_set = set(rel)

            recall = len(ret_set & rel_set) / len(rel_set) if rel_set else 0
            precision = len(ret_set & rel_set) / k if k > 0 else 0

            recalls.append(recall)
            precisions.append(precision)

        results[f"Recall@{k}"] = np.mean(recalls)
        results[f"Precision@{k}"] = np.mean(precisions)

    return results


def demo():
    """段落检索演示"""
    documents = [
        "Machine learning is a subset of artificial intelligence that enables systems to learn from data.",
        "Deep learning uses neural networks with multiple layers to process complex patterns.",
        "Natural language processing deals with understanding and generating human language.",
        "Computer vision focuses on analyzing and understanding images and videos.",
        "Supervised learning trains models using labeled training examples.",
        "Unsupervised learning discovers hidden patterns without labeled data.",
        "Reinforcement learning trains agents through rewards and punishments.",
        "Neural networks are computational models inspired by biological brains."
    ]

    print("[段落检索演示]")

    # TF-IDF检索
    tfidf = TFIDfRetriever()
    tfidf.fit(documents)
    results = tfidf.retrieve("machine learning", top_k=3)
    print(f"  TF-IDF检索 'machine learning':")
    for idx, score in results:
        print(f"    doc_{idx}: {score:.3f} - {documents[idx][:50]}...")

    # BM25检索
    bm25 = BM25Retriever()
    bm25.fit(documents)
    results = bm25.retrieve("neural networks", top_k=3)
    print(f"\n  BM25检索 'neural networks':")
    for idx, score in results:
        print(f"    doc_{idx}: {score:.3f} - {documents[idx][:50]}...")

    # 密集检索
    encoder = DensePassageEncoder(vocab_size=5000, embed_dim=64, hidden_dim=128)
    dense = DenseRetriever(encoder)
    for i, doc in enumerate(documents):
        tokens = torch.randint(1, 5000, (len(doc.split()),))
        dense.index_passage(f"doc_{i}", doc, tokens)

    query_tokens = torch.randint(1, 5000, (4,))
    with torch.no_grad():
        query_emb = encoder(query_tokens)
    dense_results = dense.search(query_emb, top_k=3)
    print(f"\n  密集检索结果: {dense_results}")

    # 混合检索
    hybrid = HybridRetriever(sparse_weight=0.6, dense_weight=0.4)
    hybrid.fit_sparse(documents)
    hybrid_retrieved = hybrid.retrieve("deep learning neural", query_emb, top_k=5)
    print(f"\n  混合检索结果:")
    for idx, score in hybrid_retrieved:
        print(f"    doc_{idx}: {score:.4f}")

    # 段落选择
    selector = PassageSelector()
    passages = [(i, 1.0 / (i + 1), d) for i, d in enumerate(documents)]
    selected = selector.select("learning", passages, answer_hint="learning")
    print(f"\n  段落选择结果: {len(selected)}个段落被选中")

    print("  ✅ 段落检索演示通过！")


if __name__ == "__main__":
    demo()
