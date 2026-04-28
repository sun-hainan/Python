"""
抽取式问答模块 - Span提取 / 指针网络

本模块实现基于指针网络(Pointer Network)的抽取式问答系统。
给定文档和问题，模型从文档中抽取出回答的起始和结束位置。

核心思想：
1. 编码器：双向LSTM编码文档和问题上下文
2. 指针网络：通过注意力机制直接预测答案span的位置
3. 跨距限制：结束位置必须不早于起始位置
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class EncoderLayer(nn.Module):
    """编码器层：双向LSTM将输入序列编码为上下文表示"""

    def __init__(self, vocab_size, embed_dim, hidden_size, dropout=0.2):
        super().__init__()
        # 词嵌入层
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        # 双向LSTM编码器
        self.encoder = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_size,
            num_layers=1,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if True else 0  # 仅用于多层LSTM时
        )
        # 层归一化
        self.layer_norm = nn.LayerNorm(2 * hidden_size)
        self.dropout = nn.Dropout(dropout)

    def forward(self, token_ids, mask=None):
        """
        前向传播
        :param token_ids: token索引 [batch, seq_len]
        :param mask: 注意力掩码 [batch, seq_len]
        :return: 编码后的表示 [batch, seq_len, 2*hidden_size]
        """
        # 词嵌入
        embedded = self.embedding(token_ids)  # [batch, seq_len, embed_dim]
        embedded = self.dropout(embedded)
        # LSTM编码
        encoded, _ = self.encoder(embedded)   # [batch, seq_len, 2*hidden_size]
        encoded = self.layer_norm(encoded)
        return encoded


class PointerNetwork(nn.Module):
    """指针网络：预测答案的起始和结束位置"""

    def __init__(self, hidden_size):
        super().__init__()
        self.hidden_size = hidden_size
        # 起始位置注意力层
        self.start_attention = nn.Linear(2 * hidden_size, 1, bias=False)
        # 结束位置注意力层
        self.end_attention = nn.Linear(2 * hidden_size, 1, bias=False)
        # 门控机制：融合编码器输出和起始位置信息
        self.gate_layer = nn.Linear(4 * hidden_size, 2 * hidden_size)

    def forward(self, encoded, start_probs=None, mask=None):
        """
        指针网络前向传播
        :param encoded: 编码表示 [batch, seq_len, 2*hidden_size]
        :param start_probs: 先前预测的起始概率（用于第二跳，可选）
        :param mask: 掩码 [batch, seq_len]
        :return: span概率分布
        """
        seq_len = encoded.size(1)
        # 起始位置预测
        start_logits = self.start_attention(encoded).squeeze(-1)  # [batch, seq_len]

        # 掩码处理
        if mask is not None:
            start_logits = start_logits + (1 - mask.float()) * (-1e30)

        start_probs = F.softmax(start_logits, dim=-1)  # [batch, seq_len]

        # 结束位置预测：融合起始位置信息
        # 起始位置的加权上下文表示
        start_context = torch.bmm(start_probs.unsqueeze(1), encoded)  # [batch, 1, 2*hidden_size]
        start_context = start_context.expand(-1, seq_len, -1)          # [batch, seq_len, 2*hidden_size]

        # 门控融合
        combined = torch.cat([encoded, start_context], dim=-1)  # [batch, seq_len, 4*hidden_size]
        gated = torch.sigmoid(self.gate_layer(combined))
        encoded_gated = gated * encoded

        # 结束位置注意力
        end_logits = self.end_attention(encoded_gated).squeeze(-1)  # [batch, seq_len]

        # 掩码处理
        if mask is not None:
            end_logits = end_logits + (1 - mask.float()) * (-1e30)

        end_probs = F.softmax(end_logits, dim=-1)  # [batch, seq_len]

        return start_probs, end_probs


class ExtractiveQA(nn.Module):
    """完整的抽取式问答模型"""

    def __init__(self, vocab_size, embed_dim=128, hidden_size=256, dropout=0.2):
        super().__init__()
        # 文档编码器
        self.document_encoder = EncoderLayer(vocab_size, embed_dim, hidden_size, dropout)
        # 问题编码器（独立参数）
        self.question_encoder = EncoderLayer(vocab_size, embed_dim, hidden_size, dropout)
        # 文档-问题融合层
        self.fusion_layer = nn.Linear(4 * hidden_size, 2 * hidden_size)
        # 指针网络
        self.pointer = PointerNetwork(hidden_size)
        # 问题导向的注意力加权
        self.question_attention = nn.Linear(2 * hidden_size, 1)

    def forward(self, document_ids, question_ids, document_mask=None, question_mask=None):
        """
        前向传播
        :param document_ids: 文档token索引 [batch, doc_len]
        :param question_ids: 问题token索引 [batch, q_len]
        :param document_mask: 文档掩码 [batch, doc_len]
        :param question_mask: 问题掩码 [batch, q_len]
        :return: 起始概率, 结束概率
        """
        # 编码文档
        doc_encoded = self.document_encoder(document_ids, document_mask)  # [batch, doc_len, 2*hidden]
        # 编码问题
        q_encoded = self.question_encoder(question_ids, question_mask)    # [batch, q_len, 2*hidden]

        # 文档-问题注意力
        # 计算文档-问题相关矩阵
        # [batch, doc_len, 1, 2*hidden] vs [batch, 1, q_len, 2*hidden]
        doc_expanded = doc_encoded.unsqueeze(2)    # [batch, doc_len, 1, 2*hidden]
        q_expanded = q_encoded.unsqueeze(1)        # [batch, 1, q_len, 2*hidden]
        # 点积注意力
        attn_scores = torch.matmul(doc_expanded, q_expanded.transpose(-2, -1))  # [batch, doc_len, q_len]
        attn_scores = attn_scores / np.sqrt(doc_encoded.size(-1))  # 缩放

        # 问题掩码
        if question_mask is not None:
            q_mask = question_mask.unsqueeze(0).unsqueeze(0).float()  # [1, 1, q_len]
            attn_scores = attn_scores + (1 - q_mask) * (-1e30)

        attn_probs = F.softmax(attn_scores.view(-1, q_encoded.size(1)), dim=-1)  # [batch*doc_len, q_len]
        # 聚合问题信息
        q_aggregated = torch.bmm(attn_probs, q_encoded)  # [batch*doc_len, 2*hidden]
        q_aggregated = q_aggregated.view_as(doc_encoded)  # [batch, doc_len, 2*hidden]

        # 融合文档表示和问题聚合表示
        fused = torch.cat([doc_encoded, q_aggregated, doc_encoded * q_aggregated], dim=-1)  # [batch, doc_len, 6*hidden]
        fused = torch.relu(self.fusion_layer(fused))

        # 指针网络预测span
        start_probs, end_probs = self.pointer(fused, mask=document_mask)

        return start_probs, end_probs


def compute_span_loss(start_probs, end_probs, start_targets, end_targets):
    """
    计算答案span的负对数似然损失
    :param start_probs: 预测的起始概率 [batch, seq_len]
    :param end_probs: 预测的结束概率 [batch, seq_len]
    :param start_targets: 真实的起始位置 [batch]
    :param end_targets: 真实的结束位置 [batch]
    :return: 损失标量
    """
    # 起始位置损失
    start_loss = F.nll_loss(
        torch.log(start_probs + 1e-10).clamp(min=-20),  # 防止log(0)
        start_targets,
        reduction='mean'
    )
    # 结束位置损失
    end_loss = F.nll_loss(
        torch.log(end_probs + 1e-10).clamp(min=-20),
        end_targets,
        reduction='mean'
    )
    # 总损失
    return start_loss + end_loss


def decode_answer(document_tokens, start_probs, end_probs, max_len=30):
    """
    解码答案：从预测的起始和结束位置提取答案文本
    :param document_tokens: 文档token列表
    :param start_probs: 起始概率向量
    :param end_probs: 结束概率向量
    :param max_len: 答案最大长度
    :return: 答案字符串
    """
    seq_len = len(document_tokens)
    # 获取top-k候选
    top_k = 5
    start_topk = start_probs.topk(top_k)
    end_topk = end_probs.topk(top_k)

    best_score = -1e9
    best_answer = ""

    for i, s_prob in zip(start_topk.indices, start_topk.values):
        for j, e_prob in zip(end_topk.indices, end_topk.values):
            if j >= i and j - i < max_len:
                score = s_prob * e_prob
                if score > best_score:
                    best_score = score
                    best_answer = "".join(document_tokens[i:j + 1])

    return best_answer


def demo():
    """抽取式问答模型演示"""
    batch_size = 2
    doc_len = 20
    q_len = 8
    vocab_size = 500

    # 初始化模型
    model = ExtractiveQA(vocab_size=vocab_size, embed_dim=64, hidden_size=128)
    model.train()

    # 构造假数据
    document_ids = torch.randint(1, vocab_size, (batch_size, doc_len))
    question_ids = torch.randint(1, vocab_size, (batch_size, q_len))
    document_mask = torch.ones(batch_size, doc_len)
    question_mask = torch.ones(batch_size, q_len)

    # 前向传播
    start_probs, end_probs = model(document_ids, question_ids, document_mask, question_mask)

    # 模拟损失计算
    start_targets = torch.randint(0, doc_len - 5, (batch_size,))
    end_targets = start_targets + torch.randint(3, 6, (batch_size,))
    end_targets = end_targets.clamp(max=doc_len - 1)

    loss = compute_span_loss(start_probs, end_probs, start_targets, end_targets)

    print(f"[抽取式问答演示]")
    print(f"  文档长度: {doc_len}, 问题长度: {q_len}")
    print(f"  起始概率形状: {start_probs.shape}")
    print(f"  结束概率形状: {end_probs.shape}")
    print(f"  损失值: {loss.item():.4f}")
    print(f"  预测起始: {start_probs.argmax(dim=1)}")
    print(f"  预测结束: {end_probs.argmax(dim=1)}")
    print("  ✅ 抽取式问答模型演示通过！")


if __name__ == "__main__":
    demo()
