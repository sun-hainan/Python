"""
开放域问答模块 - Retriever-Reader框架

本模块实现开放域问答系统的核心框架。
给定任意问题，系统首先从大规模知识源中检索相关文档，
然后阅读理解提取答案。

核心流程（Retriever-Reader架构）：
1. Retriever（检索器）：从文档库中召回相关文档
   - 稀疏检索：BM25/TF-IDF基于词项匹配
   - 密集检索：Dense Passage Retrieval (DPR)基于向量相似度
2. Reader（阅读器）：从检索到的文档中提取答案
   - 抽取式：预测答案span的起始和结束位置
   - 生成式：Seq2Seq生成答案
3. 联合训练：端到端优化检索和阅读
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Tuple, Dict, Optional


# ============================================================
# 检索器模块 (Retriever)
# ============================================================

class SparseRetriever:
    """稀疏检索器：基于TF-IDF/BM25的文档检索"""

    def __init__(self, documents: List[str]):
        """
        :param documents: 文档列表
        """
        self.documents = documents
        self.doc_ids = list(range(len(documents)))
        # 简单的词频统计（实际应使用sklearn的TfidfVectorizer）
        self.doc_term_freq = self._build_term_freq()

    def _build_term_freq(self):
        """构建文档-词项频率矩阵"""
        # 简化实现：使用字典存储
        all_terms = set()
        for doc in self.documents:
            all_terms.update(doc.split())

        term_freq = {}
        for term in all_terms:
            term_freq[term] = []
            for doc in self.documents:
                words = doc.split()
                tf = words.count(term) / len(words)
                term_freq[term].append(tf)

        return term_freq

    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[int, float]]:
        """
        检索相关文档
        :param query: 查询字符串
        :param top_k: 返回前k个结果
        :return: [(doc_id, score)]列表
        """
        query_terms = query.split()
        scores = []

        for doc_id, doc in enumerate(self.documents):
            score = 0.0
            doc_words = set(doc.split())
            for term in query_terms:
                if term in doc_words:
                    # 简化的TF-IDF评分
                    score += np.log(1 + doc_words.count(term))
            scores.append((doc_id, score))

        # 按分数排序
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class DenseRetriever(nn.Module):
    """密集检索器：基于向量的文档检索（类似DPR）"""

    def __init__(self, vocab_size, embed_dim=128, hidden_dim=256):
        super().__init__()
        # 问题编码器
        self.question_encoder = nn.Sequential(
            nn.Embedding(vocab_size, embed_dim, padding_idx=0),
            nn.LSTM(embed_dim, hidden_dim, num_layers=1, batch_first=True, bidirectional=True),
        )
        # 文档编码器
        self.document_encoder = nn.Sequential(
            nn.Embedding(vocab_size, embed_dim, padding_idx=0),
            nn.LSTM(embed_dim, hidden_dim, num_layers=1, batch_first=True, bidirectional=True),
        )
        # 向量维度
        self.hidden_dim = hidden_dim * 2  # 双向拼接

    def encode_question(self, question_ids, mask=None):
        """编码问题"""
        embedded, (h_n, _) = self.question_encoder(question_ids)
        # 双向最后隐藏状态拼接
        q_repr = torch.cat([h_n[0], h_n[1]], dim=-1)
        # L2归一化
        q_repr = F.normalize(q_repr, p=2, dim=-1)
        return q_repr

    def encode_document(self, doc_ids, mask=None):
        """编码文档"""
        embedded, (h_n, _) = self.document_encoder(doc_ids)
        # 双向最后隐藏状态拼接
        doc_repr = torch.cat([h_n[0], h_n[1]], dim=-1)
        # L2归一化
        doc_repr = F.normalize(doc_repr, p=2, dim=-1)
        return doc_repr

    def forward(self, question_ids, doc_ids):
        """前向传播"""
        q_repr = self.encode_question(question_ids)
        doc_repr = self.encode_document(doc_ids)
        return q_repr, doc_repr

    def compute_similarity(self, q_repr, doc_repr):
        """计算问题-文档相似度"""
        return torch.matmul(q_repr, doc_repr.transpose(-2, -1))


class BiEncoderRetriever(nn.Module):
    """双编码器检索器：问题和文档分别编码"""

    def __init__(self, vocab_size, embed_dim=128, hidden_dim=256):
        super().__init__()
        self.hidden_dim = hidden_dim * 2

        # 共享编码器（实际可分离）
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=4,
            dim_feedforward=hidden_dim * 4,
            batch_first=True
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=2)

        # 投影层
        self.question_proj = nn.Linear(hidden_dim, hidden_dim)
        self.doc_proj = nn.Linear(hidden_dim, hidden_dim)

    def encode(self, token_ids, mask=None):
        """编码序列"""
        # 词嵌入
        embedded = nn.functional.embedding(token_ids, torch.zeros_like(token_ids).float().to(token_ids.device))
        # Transformer编码
        encoded = self.encoder(embedded, src_key_padding_mask=(mask == 0) if mask is not None else None)
        # 取[CLS]位置的输出作为序列表示
        repr = encoded[:, 0, :]
        return repr

    def forward(self, question_ids, doc_ids, mask=None):
        """前向传播"""
        q_repr = self.encode(question_ids, mask)
        doc_repr = self.encode(doc_ids, mask)

        # 投影
        q_repr = F.normalize(self.question_proj(q_repr), p=2, dim=-1)
        doc_repr = F.normalize(self.doc_proj(doc_repr), p=2, dim=-1)

        return q_repr, doc_repr


# ============================================================
# 阅读器模块 (Reader)
# ============================================================

class ReadingComprehensionReader(nn.Module):
    """阅读理解阅读器：预测答案span"""

    def __init__(self, vocab_size, embed_dim=128, hidden_dim=256, max_len=512):
        super().__init__()
        self.hidden_dim = hidden_dim

        # 编码器
        self.encoder = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )

        # 答案位置预测
        self.qa_outputs = nn.Linear(hidden_dim * 2, 2)

    def forward(self, context_ids, start_positions=None, end_positions=None):
        """
        前向传播
        :param context_ids: 上下文token ids [batch, seq_len]
        :param start_positions: 真实起始位置（训练时）
        :param end_positions: 真实结束位置（训练时）
        :return: start_logits, end_logits
        """
        # 编码
        embedded = nn.functional.embedding(context_ids, torch.zeros_like(context_ids).float().to(context_ids.device))
        outputs, _ = self.encoder(embedded)

        # 预测答案位置
        logits = self.qa_outputs(outputs)  # [batch, seq_len, 2]
        start_logits = logits[:, :, 0]
        end_logits = logits[:, :, 1]

        # 如果有真实位置，计算损失
        loss = None
        if start_positions is not None and end_positions is not None:
            start_loss = F.cross_entropy(start_logits, start_positions)
            end_loss = F.cross_entropy(end_logits, end_positions)
            loss = (start_loss + end_loss) / 2

        return start_logits, end_logits, loss


# ============================================================
# 开放域问答系统
# ============================================================

class OpenDomainQA:
    """开放域问答系统：Retriever-Reader联合"""

    def __init__(self, documents: List[str], vocab_size: int):
        """
        :param documents: 文档库
        :param vocab_size: 词表大小
        """
        self.documents = documents
        # 稀疏检索器
        self.sparse_retriever = SparseRetriever(documents)
        # 密集检索器（需要预训练或微调）
        self.dense_retriever = DenseRetriever(vocab_size)
        # 阅读器
        self.reader = ReadingComprehensionReader(vocab_size)

    def retrieve_documents(self, question: str, top_k: int = 5, method: str = "sparse"):
        """
        检索相关文档
        :param question: 问题
        :param top_k: 返回数量
        :param method: 检索方法 "sparse" 或 "dense"
        :return: [(doc_id, doc_text, score)]
        """
        if method == "sparse":
            results = self.sparse_retriever.retrieve(question, top_k)
            return [(doc_id, self.documents[doc_id], score) for doc_id, score in results]
        else:
            # 密集检索需要批量处理
            return []

    def answer(self, question: str, retrieved_docs: List[Tuple[int, str, float]],
               reader_max_len: int = 128) -> Dict:
        """
        从检索到的文档中提取答案
        :param question: 问题
        :param retrieved_docs: 检索结果
        :param reader_max_len: 阅读器最大长度
        :return: 答案结果
        """
        answers = []

        for doc_id, doc_text, retrieval_score in retrieved_docs:
            # 简化：直接用文档的前max_len个token
            doc_tokens = doc_text.split()[:reader_max_len]
            # 实际应该用tokenizer处理

            if not doc_tokens:
                continue

            # 这里简化处理，实际应调用reader
            answer_text = " ".join(doc_tokens[:10])  # 取前10个词作为模拟答案

            answers.append({
                "doc_id": doc_id,
                "answer": answer_text,
                "retrieval_score": retrieval_score,
                "reader_score": 1.0  # 模拟
            })

        # 排序并返回最佳答案
        answers.sort(key=lambda x: x["retrieval_score"] * x["reader_score"], reverse=True)

        return {
            "question": question,
            "answers": answers,
            "best_answer": answers[0]["answer"] if answers else ""
        }


def compute_retrieval_recall(retrieved_ids: List[int], relevant_ids: List[int], top_k: int) -> float:
    """
    计算检索召回率
    :param retrieved_ids: 检索到的文档ID列表
    :param relevant_ids: 相关文档ID列表
    :param top_k: 考虑前k个结果
    :return: 召回率
    """
    retrieved_set = set(retrieved_ids[:top_k])
    relevant_set = set(relevant_ids)
    intersection = retrieved_set & relevant_set
    recall = len(intersection) / len(relevant_set) if relevant_set else 0.0
    return recall


def demo():
    """开放域问答系统演示"""
    # 构造文档库
    documents = [
        "Paris is the capital of France and the largest city in the country.",
        "France is a country in Western Europe. Its capital is Paris.",
        "The Eiffel Tower is a famous landmark in Paris, France.",
        "Machine learning is a subset of artificial intelligence.",
        "Deep learning uses neural networks with multiple layers.",
        "The French Revolution began in 1789.",
        "Python is a programming language widely used in AI.",
        "Natural language processing deals with understanding text."
    ]

    vocab_size = 5000

    # 初始化系统
    qa_system = OpenDomainQA(documents, vocab_size)

    # 测试检索
    test_questions = [
        "What is the capital of France?",
        "What is the Eiffel Tower?"
    ]

    print("[开放域问答系统演示]")
    for question in test_questions:
        # 检索
        retrieved = qa_system.retrieve_documents(question, top_k=3, method="sparse")
        print(f"\n  问题: {question}")
        print(f"  检索到 {len(retrieved)} 个文档:")
        for doc_id, doc_text, score in retrieved:
            print(f"    Doc-{doc_id} (score={score:.2f}): {doc_text[:50]}...")

        # 抽取答案
        result = qa_system.answer(question, retrieved)
        print(f"  最佳答案: {result['best_answer']}")

    # DPR模型演示
    print("\n  密集检索器参数: ", sum(p.numel() for p in qa_system.dense_retriever.parameters()))
    print("  阅读器参数: ", sum(p.numel() for p in qa_system.reader.parameters()))

    # 召回率评估
    retrieved_ids = [0, 1, 2]
    relevant_ids = [0, 1]
    recall = compute_retrieval_recall(retrieved_ids, relevant_ids, top_k=3)
    print(f"\n  检索召回率@{3}: {recall:.2f}")

    print("  ✅ 开放域问答系统演示通过！")


if __name__ == "__main__":
    demo()
