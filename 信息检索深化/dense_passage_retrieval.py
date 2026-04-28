"""
密集段落检索模块 (DPR)

本模块实现Dense Passage Retrieval（密集段落检索）系统。
DPR使用双编码器架构，分别将查询和段落编码为稠密向量，
通过向量相似度进行检索。

核心思想：
1. 独立编码器：Query Encoder和Passage Encoder（参数可共享）
2. 稠密向量表示：每个查询/段落映射到低维向量空间
3. 向量相似度：使用余弦相似度或点积计算相关性
4. 对比学习：训练时正负样本对比优化
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Tuple, Dict


class PassageEncoder(nn.Module):
    """段落编码器：将段落编码为稠密向量"""

    def __init__(self, vocab_size, embed_dim=128, hidden_dim=256, num_layers=2):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.projection = nn.Linear(embed_dim, hidden_dim)

        # 双向LSTM编码
        self.encoder = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=0.1
        )

        # 输出投影到规范化的向量空间
        self.out_projection = nn.Linear(hidden_dim * 2, hidden_dim)

    def forward(self, token_ids, mask=None):
        """
        前向传播
        :param token_ids: token索引 [batch, seq_len]
        :param mask: 掩码 [batch, seq_len]
        :return: 段落向量 [batch, hidden_dim]
        """
        # 嵌入
        embedded = self.embedding(token_ids)  # [batch, seq_len, embed_dim]
        embedded = F.relu(self.projection(embedded))

        # LSTM编码
        outputs, (h_n, _) = self.encoder(embedded)
        # 双向最后隐藏状态拼接
        hidden = torch.cat([h_n[-2], h_n[-1]], dim=-1)  # [batch, hidden_dim*2]

        # 投影并L2归一化
        output = self.out_projection(hidden)
        output = F.normalize(output, p=2, dim=-1)

        return output


class QueryEncoder(nn.Module):
    """查询编码器（与段落编码器结构相同）"""

    def __init__(self, vocab_size, embed_dim=128, hidden_dim=256, num_layers=2):
        super().__init__()
        # 与PassageEncoder共享结构
        self.passage_encoder = PassageEncoder(vocab_size, embed_dim, hidden_dim, num_layers)

    def forward(self, token_ids, mask=None):
        """编码查询"""
        return self.passage_encoder(token_ids, mask)


class DPRModel(nn.Module):
    """完整的DPR模型"""

    def __init__(self, vocab_size, embed_dim=128, hidden_dim=256, num_layers=2, share_encoder=False):
        super().__init__()
        self.share_encoder = share_encoder

        if share_encoder:
            # 共享编码器
            self.encoder = PassageEncoder(vocab_size, embed_dim, hidden_dim, num_layers)
        else:
            # 独立编码器
            self.query_encoder = QueryEncoder(vocab_size, embed_dim, hidden_dim, num_layers)
            self.passage_encoder = PassageEncoder(vocab_size, embed_dim, hidden_dim, num_layers)

    def encode_query(self, query_ids, mask=None):
        """编码查询"""
        if self.share_encoder:
            return self.encoder(query_ids, mask)
        return self.query_encoder(query_ids, mask)

    def encode_passage(self, passage_ids, mask=None):
        """编码段落"""
        if self.share_encoder:
            return self.encoder(passage_ids, mask)
        return self.passage_encoder(passage_ids, mask)

    def forward(self, query_ids, pos_passage_ids, neg_passage_ids=None, q_mask=None, p_mask=None):
        """
        前向传播（训练）
        :param query_ids: 查询token ids
        :param pos_passage_ids: 正样本段落token ids
        :param neg_passage_ids: 负样本段落token ids（可选，用于难例挖掘）
        :return: 查询向量, 正样本向量, 负样本向量, 损失
        """
        # 编码
        q_repr = self.encode_query(query_ids, q_mask)
        pos_repr = self.encode_passage(pos_passage_ids, p_mask)

        result = {
            'query_vectors': q_repr,
            'positive_vectors': pos_repr
        }

        if neg_passage_ids is not None:
            neg_repr = self.encode_passage(neg_passage_ids, p_mask)
            result['negative_vectors'] = neg_repr

            # 计算对比损失
            loss = self._compute_loss(q_repr, pos_repr, neg_repr)
            result['loss'] = loss

        return result

    def _compute_loss(self, q_repr, pos_repr, neg_repr):
        """计算对比损失（最大间隔）"""
        # 正样本相似度
        pos_sim = (q_repr * pos_repr).sum(dim=-1)  # [batch]
        # 负样本相似度
        neg_sim = (q_repr * neg_repr).sum(dim=-1)  # [batch]

        # 最大间隔损失
        margin = 1.0
        loss = F.relu(neg_sim - pos_sim + margin).mean()

        return loss


class DPRIndexer:
    """DPR向量索引器"""

    def __init__(self, passage_encoder, device='cpu'):
        self.encoder = passage_encoder
        self.encoder.eval()
        self.device = device
        self.passages = {}  # passage_id -> passage向量
        self.passage_data = {}  # passage_id -> 原始数据

    def add_passage(self, passage_id: str, passage_text: str, vector: torch.Tensor):
        """添加段落到索引"""
        self.passages[passage_id] = vector.cpu()
        self.passage_data[passage_id] = passage_text

    def build_index(self, passage_ids: List[str], passage_tensors: List[torch.Tensor]):
        """
        构建向量索引
        :param passage_ids: 段落ID列表
        :param passage_tensors: 段落向量列表
        """
        self.passages = {}
        for pid, vec in zip(passage_ids, passage_tensors):
            self.passages[pid] = vec.cpu()
            if pid not in self.passage_data:
                self.passage_data[pid] = ""

    def search(self, query_vector: torch.Tensor, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        向量相似度搜索
        :param query_vector: 查询向量 [hidden_dim]
        :param top_k: 返回前k个
        :return: [(passage_id, score)]
        """
        query_vector = query_vector.to(self.device)

        scores = []
        for pid, passage_vector in self.passages.items():
            passage_vector = passage_vector.to(self.device)
            # 余弦相似度
            score = torch.dot(query_vector, passage_vector).item()
            scores.append((pid, score))

        # 排序
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def batch_search(self, query_vectors: torch.Tensor, top_k: int = 10) -> List[List[Tuple[str, float]]]:
        """批量搜索"""
        results = []
        for q_vec in query_vectors:
            results.append(self.search(q_vec, top_k))
        return results


class InBatchNegativeSampler:
    """In-batch负采样：使用batch内其他样本作为负样本"""

    def __init__(self):
        pass

    def sample(self, positive_idx: int, batch_size: int) -> List[int]:
        """
        采样负样本索引
        :param positive_idx: 正样本在batch中的索引
        :param batch_size: batch大小
        :return: 负样本索引列表
        """
        negatives = []
        for i in range(batch_size):
            if i != positive_idx:
                negatives.append(i)
        return negatives


class HardNegativeMiner:
    """难例挖掘：从检索到的候选中选取最难的负样本"""

    def __init__(self, encoder):
        self.encoder = encoder

    def mine(self, query_vectors: torch.Tensor, candidate_passage_vectors: torch.Tensor,
             top_k: int = 1) -> torch.Tensor:
        """
        挖掘难例负样本
        :param query_vectors: 查询向量 [batch, hidden]
        :param candidate_passage_vectors: 候选段落向量 [batch * num_candidates, hidden]
        :param top_k: 选取前k个最难的
        :return: 难例负样本向量 [batch, top_k, hidden]
        """
        batch_size = query_vectors.size(0)
        num_candidates = candidate_passage_vectors.size(0) // batch_size

        # 重塑为 [batch, num_candidates, hidden]
        candidates = candidate_passage_vectors.view(batch_size, num_candidates, -1)

        # 计算与每个查询的相似度
        # [batch, 1, hidden] vs [batch, num_candidates, hidden] -> [batch, num_candidates]
        sim_matrix = torch.bmm(
            query_vectors.unsqueeze(1),
            candidates.transpose(1, 2)
        ).squeeze(1)

        # 选取相似度最高的（最难）
        hard_negatives = []
        for b in range(batch_size):
            _, top_indices = sim_matrix[b].topk(top_k)
            hard_negatives.append(candidates[b, top_indices])

        return torch.stack(hard_negatives)


def evaluate_retrieval(recalled_ids: List[List[int]], relevant_ids: List[List[int]], k_values=[1, 5, 10, 20]):
    """
    评估检索性能
    :param recalled_ids: 每条查询检索到的文档ID列表
    :param relevant_ids: 每条查询的相关文档ID列表
    :param k_values: 评估的k值
    :return: 各指标结果
    """
    results = {}

    for k in k_values:
        recalls = []
        precisions = []

        for recalled, relevant in zip(recalled_ids, relevant_ids):
            recalled_set = set(recalled[:k])
            relevant_set = set(relevant)

            # Recall@K
            recall = len(recalled_set & relevant_set) / len(relevant_set) if relevant_set else 0
            recalls.append(recall)

            # Precision@K
            precision = len(recalled_set & relevant_set) / k if k > 0 else 0
            precisions.append(precision)

        results[f"Recall@{k}"] = np.mean(recalls)
        results[f"Precision@{k}"] = np.mean(precisions)

    # MAP (Mean Average Precision)
    average_precisions = []
    for recalled, relevant in zip(recalled_ids, relevant_ids):
        ap = 0.0
        num_relevant = 0
        for i, doc_id in enumerate(recalled):
            if doc_id in relevant:
                num_relevant += 1
                ap += num_relevant / (i + 1)
        if relevant:
            ap /= len(relevant)
        average_precisions.append(ap)
    results["MAP"] = np.mean(average_precisions)

    return results


def demo():
    """DPR密集段落检索演示"""
    vocab_size = 5000
    embed_dim = 64
    hidden_dim = 128

    print("[DPR密集段落检索演示]")

    # 初始化模型
    dpr = DPRModel(vocab_size, embed_dim, hidden_dim, share_encoder=True)

    # 模拟数据
    batch_size = 4
    q_len = 10
    p_len = 30

    query_ids = torch.randint(1, vocab_size, (batch_size, q_len))
    pos_passage_ids = torch.randint(1, vocab_size, (batch_size, p_len))
    neg_passage_ids = torch.randint(1, vocab_size, (batch_size, p_len))

    # 前向传播
    result = dpr(query_ids, pos_passage_ids, neg_passage_ids)
    print(f"  查询向量形状: {result['query_vectors'].shape}")
    print(f"  正样本向量形状: {result['positive_vectors'].shape}")
    print(f"  负样本向量形状: {result['negative_vectors'].shape}")
    print(f"  损失值: {result['loss'].item():.4f}")

    # 编码器演示
    encoder = dpr.encoder if dpr.share_encoder else dpr.passage_encoder
    test_ids = torch.randint(1, vocab_size, (2, 20))
    vectors = encoder(test_ids)
    print(f"  编码向量形状: {vectors.shape}, L2范数: {vectors.norm(dim=-1)}")

    # 评估演示
    recalled = [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10]]
    relevant = [[1, 3, 5, 7], [6, 9]]
    metrics = evaluate_retrieval(recalled, relevant)
    print(f"\n  检索评估:")
    for metric, value in metrics.items():
        print(f"    {metric}: {value:.4f}")

    print(f"  DPR模型参数量: {sum(p.numel() for p in dpr.parameters()):,}")
    print("  ✅ DPR演示通过！")


if __name__ == "__main__":
    demo()
