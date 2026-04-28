"""
神经信息检索模块 - ColBERT Late交互

本模块实现基于ColBERT的神经信息检索系统。
ColBERT是一种late交互的检索模型，分别编码查询和文档，
在后期通过高效的最大相似度匹配计算交互分数。

核心思想：
1. Query编码：独立的query编码器，输出每个词的向量
2. Document编码：独立的doc编码器，输出每个词的向量
3. Late交互：查询向量与文档向量计算点积相似度
4. MaxSim：每个查询词取与所有文档词的最大相似度求和
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class ColBERTEncoder(nn.Module):
    """ColBERT编码器：生成词级向量表示"""

    def __init__(self, vocab_size, embed_dim=128, hidden_dim=256, num_layers=2):
        super().__init__()
        self.embed_dim = embed_dim
        self.hidden_dim = hidden_dim

        # 词嵌入
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        # 线性变换：嵌入维度 -> 压缩向量维度
        self.linear = nn.Linear(embed_dim, hidden_dim)
        # LayerNorm
        self.norm = nn.LayerNorm(hidden_dim)

        # 更深的编码层（可选）
        self.encoder_layers = nn.ModuleList([
            nn.Linear(hidden_dim, hidden_dim) for _ in range(num_layers - 1)
        ])

    def forward(self, token_ids, mask=None):
        """
        前向传播
        :param token_ids: token索引 [batch, seq_len]
        :param mask: 注意力掩码 [batch, seq_len]
        :return: 压缩后的词向量 [batch, seq_len, hidden_dim]
        """
        # 词嵌入
        embedded = self.embedding(token_ids)  # [batch, seq_len, embed_dim]
        # 线性变换 + LayerNorm
        encoded = self.norm(F.relu(self.linear(embedded)))  # [batch, seq_len, hidden_dim]

        # 额外编码层
        for layer in self.encoder_layers:
            encoded = self.norm(F.relu(layer(encoded)))

        # 与掩码相乘（将padding位置的向量置零）
        if mask is not None:
            encoded = encoded * mask.unsqueeze(-1).float()

        return encoded


class ColBERTModel(nn.Module):
    """ColBERT模型：Query和Document使用独立的编码器"""

    def __init__(self, vocab_size, embed_dim=128, hidden_dim=128, num_encoder_layers=2):
        super().__init__()
        # Query编码器
        self.query_encoder = ColBERTEncoder(vocab_size, embed_dim, hidden_dim, num_encoder_layers)
        # Document编码器（结构相同但参数独立）
        self.document_encoder = ColBERTEncoder(vocab_size, embed_dim, hidden_dim, num_encoder_layers)

    def encode_query(self, query_ids, mask=None):
        """编码查询，返回词级向量"""
        return self.query_encoder(query_ids, mask)

    def encode_document(self, doc_ids, mask=None):
        """编码文档，返回词级向量"""
        return self.document_encoder(doc_ids, mask)

    def score(self, query_vectors, doc_vectors, query_mask=None, doc_mask=None):
        """
        计算ColBERT分数：MaxSim
        :param query_vectors: 查询向量 [batch, q_len, hidden_dim]
        :param doc_vectors: 文档向量 [batch, d_len, hidden_dim]
        :return: 相似度分数 [batch]
        """
        # 调整维度进行批量矩阵乘法
        # query_vectors: [batch, q_len, hidden]
        # doc_vectors: [batch, d_len, hidden]
        # 扩展以便计算每个query词与所有doc词的相似度
        # [batch, q_len, 1, hidden] vs [batch, 1, d_len, hidden]
        q_exp = query_vectors.unsqueeze(2)  # [batch, q_len, 1, hidden]
        d_exp = doc_vectors.unsqueeze(1)    # [batch, 1, d_len, hidden]

        # 点积相似度
        sim_matrix = torch.sum(q_exp * d_exp, dim=-1)  # [batch, q_len, d_len]

        # 掩码处理
        if doc_mask is not None:
            # [batch, 1, d_len] -> 扩展为 [batch, q_len, d_len]
            d_mask_exp = doc_mask.unsqueeze(1).float()
            sim_matrix = sim_matrix + (1 - d_mask_exp) * (-1e30)

        # MaxSim: 每个query词取max similarity，然后求和
        # [batch, q_len, d_len] -> [batch, q_len] -> [batch]
        max_sim = sim_matrix.max(dim=2)[0]  # [batch, q_len]
        scores = max_sim.sum(dim=1)  # [batch]

        return scores

    def forward(self, query_ids, doc_ids, query_mask=None, doc_mask=None):
        """前向传播"""
        query_vectors = self.encode_query(query_ids, query_mask)
        doc_vectors = self.encode_document(doc_ids, doc_mask)
        scores = self.score(query_vectors, doc_vectors, query_mask, doc_mask)
        return scores


class LateInteractionScorer(nn.Module):
    """Late交互评分器：更高效的交互实现"""

    def __init__(self, hidden_dim):
        super().__init__()
        self.hidden_dim = hidden_dim

    def forward(self, query_vectors, doc_vectors, mask_dim=None):
        """
        Late交互评分
        :param query_vectors: [batch, q_len, hidden]
        :param doc_vectors: [batch, d_len, hidden]
        :return: 分数 [batch]
        """
        batch_size, q_len, _ = query_vectors.size()
        _, d_len, _ = doc_vectors.size()

        # 点积相似度矩阵
        # [batch, q_len, hidden] @ [batch, hidden, d_len] -> [batch, q_len, d_len]
        sim_matrix = torch.bmm(query_vectors, doc_vectors.transpose(1, 2))

        # 掩码
        if mask_dim is not None:
            mask = (1 - mask_dim.float()).unsqueeze(1) * (-1e30)
            sim_matrix = sim_matrix + mask

        # MaxSim
        max_sim = sim_matrix.max(dim=2)[0]  # [batch, q_len]
        scores = max_sim.sum(dim=1)

        return scores


class ColBERTReranker(nn.Module):
    """ColBERT重排序器：用于候选重排"""

    def __init__(self, vocab_size, hidden_dim=128):
        super().__init__()
        self.colbert = ColBERTModel(vocab_size, hidden_dim=hidden_dim)
        # 额外的评分层
        self.score_layer = nn.Sequential(
            nn.Linear(1, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )

    def rerank(self, query_ids, candidate_doc_ids_list, top_k=10):
        """
        对候选文档重排序
        :param query_ids: 查询token ids
        :param candidate_doc_ids_list: 候选文档列表
        :param top_k: 返回前k个
        :return: 重排后的doc ids
        """
        batch_size = query_ids.size(0)
        scores = []

        for doc_ids in candidate_doc_ids_list:
            doc_ids = doc_ids.unsqueeze(0) if doc_ids.dim() == 1 else doc_ids
            score = self.colbert.score(query_ids, doc_ids)
            scores.append(score)

        all_scores = torch.stack(scores, dim=1)  # [batch, num_candidates]
        ranked_indices = all_scores.topk(top_k, dim=1)[1]

        return ranked_indices


class ColBERTIndexer:
    """ColBERT索引器：构建文档向量索引"""

    def __init__(self, model, device='cpu'):
        self.model = model
        self.model.eval()
        self.device = device
        self.document_vectors = {}  # doc_id -> 向量列表

    def index_document(self, doc_id: str, doc_ids: torch.Tensor, doc_mask: torch.Tensor):
        """
        索引单个文档
        :param doc_id: 文档ID
        :param doc_ids: 文档token ids
        :param doc_mask: 文档掩码
        """
        with torch.no_grad():
            vectors = self.model.encode_document(doc_ids.to(self.device), doc_mask.to(self.device))
            # 归一化
            vectors = F.normalize(vectors, p=2, dim=-1)
            self.document_vectors[doc_id] = vectors.cpu()

    def search(self, query_ids: torch.Tensor, query_mask: torch.Tensor, top_k: int = 10):
        """
        搜索相关文档
        :param query_ids: 查询token ids
        :param query_mask: 查询掩码
        :param top_k: 返回前k个
        :return: [(doc_id, score)]
        """
        with torch.no_grad():
            query_vectors = self.model.encode_query(query_ids.to(self.device), query_mask.to(self.device))
            query_vectors = F.normalize(query_vectors, p=2, dim=-1)

            results = []
            for doc_id, doc_vectors in self.document_vectors.items():
                doc_vectors = doc_vectors.to(self.device)
                # 计算分数
                score = self._compute_score(query_vectors, doc_vectors)
                results.append((doc_id, score.item()))

            # 排序
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]

    def _compute_score(self, query_vectors, doc_vectors):
        """计算query和doc的ColBERT分数"""
        # [1, q_len, hidden] vs [d_len, hidden]
        sim_matrix = torch.matmul(query_vectors[0], doc_vectors[0].transpose(0, 1))
        max_sim = sim_matrix.max(dim=1)[0]
        return max_sim.sum()


def compute_colbert_loss(query_vectors, pos_doc_vectors, neg_doc_vectors):
    """
    计算ColBERT的对比损失
    :param query_vectors: 查询向量 [batch, q_len, hidden]
    :param pos_doc_vectors: 正样本文档向量 [batch, d_len, hidden]
    :param neg_doc_vectors: 负样本文档向量 [batch, d_len, hidden]
    :return: 损失标量
    """
    # 正样本分数
    pos_scores = (query_vectors * pos_doc_vectors).sum(dim=-1).max(dim=1)[0].sum(dim=0)
    # 负样本分数
    neg_scores = (query_vectors * neg_doc_vectors).sum(dim=-1).max(dim=1)[0].sum(dim=0)

    # 最大间隔损失
    margin = 0.2
    loss = F.relu(neg_scores - pos_scores + margin).mean()

    return loss


def demo():
    """ColBERT神经信息检索演示"""
    batch_size = 2
    q_len = 10
    d_len = 30
    vocab_size = 5000
    hidden_dim = 128

    print("[ColBERT神经信息检索演示]")

    # 初始化模型
    colbert = ColBERTModel(vocab_size, embed_dim=64, hidden_dim=hidden_dim)

    # 构造输入
    query_ids = torch.randint(1, vocab_size, (batch_size, q_len))
    doc_ids = torch.randint(1, vocab_size, (batch_size, d_len))
    query_mask = torch.ones(batch_size, q_len)
    doc_mask = torch.ones(batch_size, d_len)

    # 前向传播
    scores = colbert(query_ids, doc_ids, query_mask, doc_mask)
    print(f"  查询长度: {q_len}, 文档长度: {d_len}")
    print(f"  ColBERT分数: {scores}")

    # Late交互
    late_scorer = LateInteractionScorer(hidden_dim)
    q_vectors = colbert.encode_query(query_ids, query_mask)
    d_vectors = colbert.encode_document(doc_ids, doc_mask)
    late_scores = late_scorer(q_vectors, d_vectors)
    print(f"  Late交互分数: {late_scores}")

    # 损失计算
    pos_doc_ids = torch.randint(1, vocab_size, (batch_size, d_len))
    neg_doc_ids = torch.randint(1, vocab_size, (batch_size, d_len))
    loss = compute_colbert_loss(q_vectors, pos_doc_ids.float().unsqueeze(-1).expand(-1, -1, hidden_dim),
                                 neg_doc_ids.float().unsqueeze(-1).expand(-1, -1, hidden_dim))
    print(f"  对比损失: {loss.item():.4f}")

    print(f"  ColBERT模型参数量: {sum(p.numel() for p in colbert.parameters()):,}")
    print("  ✅ ColBERT演示通过！")


if __name__ == "__main__":
    demo()
