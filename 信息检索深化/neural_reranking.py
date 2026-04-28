"""
神经重排序模块 - BERT交叉编码器

本模块实现基于深度神经网络的文档重排序系统。
给定初始检索的结果，使用BERT等Transformer模型对候选文档进行精细排序。

核心方法：
1. 交叉编码器：联合编码查询和文档
2. BERT重排序：BERT-Cross-Encoder
3. LambdaMART重排：使用神经分数作为特征
4. 列表wise损失：直接优化排序指标
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Tuple, Dict, Optional


class BERTCrossEncoder(nn.Module):
    """BERT交叉编码器：联合编码查询和文档"""

    def __init__(self, vocab_size: int, hidden_size: int = 256, num_layers: int = 4,
                 num_heads: int = 4, max_len: int = 512, dropout: float = 0.1):
        super().__init__()
        self.hidden_size = hidden_size
        self.max_len = max_len

        # 词嵌入
        self.token_embedding = nn.Embedding(vocab_size, hidden_size, padding_idx=0)
        self.position_embedding = nn.Embedding(max_len, hidden_size)
        self.segment_embedding = nn.Embedding(3, hidden_size)  # 0=pad, 1=query, 2=doc

        # Transformer编码器
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_size,
            nhead=num_heads,
            dim_feedforward=hidden_size * 4,
            dropout=dropout,
            batch_first=True
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        # 输出层：预测相关性分数
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.Tanh(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, 1)
        )

    def forward(self, query_ids, doc_ids, query_mask=None, doc_mask=None):
        """
        前向传播
        :param query_ids: 查询token ids [batch, q_len]
        :param doc_ids: 文档token ids [batch, d_len]
        :param query_mask: 查询掩码
        :param doc_mask: 文档掩码
        :return: 相关性分数 [batch]
        """
        batch_size = query_ids.size(0)
        q_len = query_ids.size(1)
        d_len = doc_ids.size(1)

        # 构造联合序列
        # [CLS] query [SEP] doc [SEP]
        input_ids = torch.cat([
            query_ids,
            doc_ids[:, 1:]  # 去掉query末尾的[SEP]后的doc部分
        ], dim=1)

        # Token type ids: 1 for query, 2 for doc
        token_type_ids = torch.cat([
            torch.ones_like(query_ids) * 1,
            torch.ones_like(doc_ids[:, 1:]) * 2
        ], dim=1)

        # Position ids
        seq_len = input_ids.size(1)
        position_ids = torch.arange(seq_len, device=input_ids.device).unsqueeze(0).expand(batch_size, -1)

        # 嵌入
        token_embed = self.token_embedding(input_ids)
        position_embed = self.position_embedding(position_ids)
        segment_embed = self.segment_embedding(token_type_ids)

        hidden = token_embed + position_embed + segment_embed

        # 掩码
        key_padding_mask = (input_ids == 0)  # True表示需要mask的位置

        # Transformer编码
        encoded = self.encoder(hidden, src_key_padding_mask=key_padding_mask)

        # 取[CLS]位置的输出预测分数
        cls_output = encoded[:, 0, :]
        score = self.classifier(cls_output).squeeze(-1)

        return score


class ListwiseLTR(nn.Module):
    """Listwise学习排序模型"""

    def __init__(self, vocab_size: int, hidden_size: int = 256, num_layers: int = 2):
        super().__init__()
        self.hidden_size = hidden_size

        # 编码器
        self.query_encoder = nn.LSTM(
            input_size=hidden_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True
        )
        self.doc_encoder = nn.LSTM(
            input_size=hidden_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True
        )

        # 融合层
        self.fusion = nn.Linear(hidden_size * 4, hidden_size)

        # 排序层
        self.ranker = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, 1)
        )

    def forward(self, query_ids, doc_ids_list, labels=None):
        """
        前向传播
        :param query_ids: 查询 [batch, q_len]
        :param doc_ids_list: 候选文档列表 [batch, num_docs, d_len]
        :param labels: 相关性标签 [batch, num_docs]
        :return: 排序分数或损失
        """
        batch_size, num_docs, d_len = doc_ids_list.size()

        # 编码查询
        query_embed = nn.functional.embedding(query_ids, torch.zeros_like(query_ids).float().unsqueeze(-1).expand(-1, -1, self.hidden_size))
        _, q_hidden = self.query_encoder(query_embed)
        q_repr = torch.cat([q_hidden[0], q_hidden[1]], dim=-1)  # [batch, hidden*2]

        # 编码每个文档
        doc_scores = []
        for d_idx in range(num_docs):
            doc_ids = doc_ids_list[:, d_idx, :]
            doc_embed = nn.functional.embedding(doc_ids, torch.zeros_like(doc_ids).float().unsqueeze(-1).expand(-1, -1, self.hidden_size))
            _, d_hidden = self.doc_encoder(doc_embed)
            d_repr = torch.cat([d_hidden[0], d_hidden[1]], dim=-1)  # [batch, hidden*2]

            # 融合查询和文档
            fused = torch.cat([q_repr, d_repr], dim=-1)  # [batch, hidden*4]
            fused = self.fusion(fused)

            # 打分
            score = self.ranker(fused).squeeze(-1)  # [batch]
            doc_scores.append(score)

        doc_scores = torch.stack(doc_scores, dim=1)  # [batch, num_docs]

        # 如果有标签，计算损失
        if labels is not None:
            loss = self._listwise_loss(doc_scores, labels)
            return doc_scores, loss

        return doc_scores, None

    def _listwise_loss(self, scores: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        """
        Listwise排序损失
        :param scores: 预测分数 [batch, num_docs]
        :param labels: 相关性标签 [batch, num_docs]
        :return: 损失
        """
        # 简化的排名损失：按分数排序后与标签排序比较
        batch_size = scores.size(0)

        loss = 0.0
        for b in range(batch_size):
            pred_rank = torch.argsort(scores[b], descending=True)
            label_rank = torch.argsort(labels[b], descending=True)

            # Kendall tau距离（简化）
            diff = (pred_rank.float() - label_rank.float()).abs().sum()
            loss += diff

        return loss / batch_size


class LambdaRankModel(nn.Module):
    """LambdaRank模型：使用神经网络估计Lambda梯度"""

    def __init__(self, input_dim: int, hidden_dim: int = 128):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        """前向传播"""
        return self.network(features).squeeze(-1)

    def compute_lambdas(self, scores: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        """
        计算Lambda梯度
        :param scores: 预测分数 [batch, num_docs]
        :param labels: 相关性标签 [batch, num_docs]
        :return: Lambda梯度
        """
        batch_size, num_docs = scores.size()
        lambdas = torch.zeros_like(scores)

        for b in range(batch_size):
            s = scores[b]
            l = labels[b]

            for i in range(num_docs):
                for j in range(num_docs):
                    if l[i] > l[j]:
                        # Lambda_ij
                        delta = torch.sigmoid(s[j] - s[i])
                        lambda_ij = 0.5 * (1 - delta)
                        lambda_ji = -lambda_ij

                        # DCG权重差
                        delta_ndcg = abs((2 ** l[i] - 2 ** l[j]) / (1 + torch.log2(1 + torch.maximum(s[i], s[j]))))

                        lambdas[b, i] += lambda_ij * delta_ndcg
                        lambdas[b, j] += lambda_ji * delta_ndcg

        return lambdas


class CrossEncoderReranker:
    """交叉编码器重排序器封装"""

    def __init__(self, vocab_size: int, hidden_size: int = 256):
        self.model = BERTCrossEncoder(vocab_size, hidden_size)
        self.model.eval()

    def rerank(self, query_ids: torch.Tensor, candidate_doc_ids: torch.Tensor,
               top_k: int = 10) -> List[Tuple[int, float]]:
        """
        对候选文档重排序
        :param query_ids: 查询 [q_len]
        :param candidate_doc_ids: 候选文档列表 [num_candidates, d_len]
        :param top_k: 返回前k个
        :return: [(doc_idx, score)]
        """
        with torch.no_grad():
            # 批量编码
            scores = []
            batch_size = 32

            for i in range(0, len(candidate_doc_ids), batch_size):
                batch_docs = candidate_doc_ids[i:i + batch_size]
                batch_query = query_ids.unsqueeze(0).expand(len(batch_docs), -1)

                batch_scores = self.model(batch_query, batch_docs)
                scores.extend(batch_scores.tolist())

            # 排序
            scored_docs = list(enumerate(scores))
            scored_docs.sort(key=lambda x: x[1], reverse=True)

            return scored_docs[:top_k]


def compute_ndcg(scores: torch.Tensor, labels: torch.Tensor, k: int = 10) -> float:
    """计算NDCG@k"""
    batch_size = scores.size(0)
    ndcgs = []

    for b in range(batch_size):
        # 排序
        ranked_indices = torch.argsort(scores[b], descending=True)[:k]
        ranked_labels = labels[b, ranked_indices]

        # DCG
        dcg = 0.0
        for i, label in enumerate(ranked_labels):
            dcg += (2 ** label - 1) / torch.log2(torch.tensor(i + 2))

        # IDCG
        ideal_labels, _ = torch.sort(labels[b], descending=True)[:k]
        idcg = 0.0
        for i, label in enumerate(ideal_labels):
            idcg += (2 ** label - 1) / torch.log2(torch.tensor(i + 2))

        ndcg = dcg / idcg if idcg > 0 else 0.0
        ndcgs.append(ndcg.item())

    return np.mean(ndcgs)


def demo():
    """神经重排序演示"""
    vocab_size = 5000
    hidden_size = 128

    print("[神经重排序演示]")

    # BERT交叉编码器
    cross_encoder = BERTCrossEncoder(vocab_size, hidden_size, num_layers=2)
    query_ids = torch.randint(1, vocab_size, (4, 10))  # batch=4, q_len=10
    doc_ids = torch.randint(1, vocab_size, (4, 30))     # batch=4, d_len=30

    scores = cross_encoder(query_ids, doc_ids)
    print(f"  BERT交叉编码器输出: {scores.shape}")

    # Listwise LTR
    listwise = ListwiseLTR(vocab_size, hidden_size)
    batch_size = 2
    num_docs = 5
    q_ids = torch.randint(1, vocab_size, (batch_size, 10))
    d_ids = torch.randint(1, vocab_size, (batch_size, num_docs, 20))
    labels = torch.randint(0, 3, (batch_size, num_docs)).float()

    doc_scores, loss = listwise(q_ids, d_ids, labels)
    print(f"  Listwise输出形状: {doc_scores.shape}, 损失: {loss.item():.4f}")

    # LambdaRank
    lambda_model = LambdaRankModel(input_dim=20, hidden_dim=64)
    features = torch.randn(4, 10, 20)  # batch=4, 10 docs, 20 features
    scores_in = features.mean(dim=2)  # 简化
    labels_in = torch.randint(0, 3, (4, 10)).float()
    lambdas = lambda_model.compute_lambdas(scores_in, labels_in)
    print(f"  Lambda梯度形状: {lambdas.shape}")

    # 重排序器
    reranker = CrossEncoderReranker(vocab_size, hidden_size)
    print(f"  重排序器模型参数量: {sum(p.numel() for p in cross_encoder.parameters()):,}")

    # NDCG评估
    scores_tensor = torch.tensor([[3.0, 1.0, 2.0, 0.0], [2.0, 3.0, 1.0, 0.0]])
    labels_tensor = torch.tensor([[2, 0, 1, 0], [1, 2, 0, 0]])
    ndcg = compute_ndcg(scores_tensor, labels_tensor, k=3)
    print(f"\n  模拟NDCG@3: {ndcg:.4f}")

    print("  ✅ 神经重排序演示通过！")


if __name__ == "__main__":
    demo()
