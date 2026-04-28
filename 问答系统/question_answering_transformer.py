"""
Transformer问答模块 - BERT风格阅读理解

本模块实现基于Transformer架构的阅读理解模型。
核心思想：使用预训练语言模型（BERT风格）进行问答任务的微调。
模型接收问题和文档的拼接序列，输出答案在文档中的位置。

核心组件：
1. Transformer编码器：多头自注意力建模上下文
2. 问题-文档融合：特殊分隔符标记问题/文档边界
3. 答案位置预测：预测答案span的起始和结束位置
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class PositionalEncoding(nn.Module):
    """位置编码：为序列中的每个位置添加位置信息"""

    def __init__(self, d_model, max_len=512, dropout=0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        # 创建位置编码矩阵
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))

        # 正弦和余弦交替
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # [1, max_len, d_model]

        self.register_buffer('pe', pe)

    def forward(self, x):
        """
        前向传播
        :param x: 输入张量 [batch, seq_len, d_model]
        :return: 带位置编码的输出
        """
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)


class MultiHeadAttention(nn.Module):
    """多头自注意力机制"""

    def __init__(self, d_model, num_heads, dropout=0.1):
        super().__init__()
        assert d_model % num_heads == 0
        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads

        # QKV投影
        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)

        self.dropout = nn.Dropout(dropout)

    def split_heads(self, x):
        """将hidden维度分割为多头"""
        batch_size, seq_len, d_model = x.size()
        x = x.view(batch_size, seq_len, self.num_heads, self.d_k)
        return x.permute(0, 2, 1, 3)  # [batch, heads, seq_len, d_k]

    def forward(self, query, key, value, mask=None):
        """
        前向传播
        :param query: Q张量 [batch, seq_len, d_model]
        :param key: K张量
        :param value: V张量
        :param mask: 注意力掩码
        :return: 输出, 注意力权重
        """
        batch_size = query.size(0)

        # 线性投影并分割多头
        Q = self.split_heads(self.W_q(query))
        K = self.split_heads(self.W_k(key))
        V = self.split_heads(self.W_v(value))

        # 计算注意力分数
        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.d_k)  # [batch, heads, seq_len, seq_len]

        # 应用掩码
        if mask is not None:
            scores = scores + (1 - mask.unsqueeze(1).unsqueeze(2).float()) * (-1e9)

        # 归一化
        attention_weights = F.softmax(scores, dim=-1)
        attention_weights = self.dropout(attention_weights)

        # 加权求和
        context = torch.matmul(attention_weights, V)  # [batch, heads, seq_len, d_k]

        # 合并多头
        context = context.permute(0, 2, 1, 3).contiguous()
        context = context.view(batch_size, -1, self.d_model)

        # 输出投影
        output = self.W_o(context)

        return output, attention_weights


class TransformerBlock(nn.Module):
    """Transformer编码器块：多头注意力 + 前馈网络"""

    def __init__(self, d_model, num_heads, d_ff, dropout=0.1):
        super().__init__()
        self.attention = MultiHeadAttention(d_model, num_heads, dropout)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)

        # 前馈网络
        self.feed_forward = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model),
            nn.Dropout(dropout)
        )

    def forward(self, x, mask=None):
        """
        前向传播
        :param x: 输入 [batch, seq_len, d_model]
        :param mask: 掩码
        :return: 输出, 注意力权重
        """
        # 多头注意力 + 残差连接
        attn_output, attn_weights = self.attention(x, x, x, mask)
        x = self.norm1(x + attn_output)

        # 前馈网络 + 残差连接
        ff_output = self.feed_forward(x)
        x = self.norm2(x + ff_output)

        return x, attn_weights


class TransformerQA(nn.Module):
    """基于Transformer的阅读理解模型"""

    def __init__(self, vocab_size, d_model=256, num_heads=4, num_layers=3,
                 d_ff=1024, max_len=512, dropout=0.1):
        super().__init__()
        self.d_model = d_model

        # 词嵌入
        self.token_embedding = nn.Embedding(vocab_size, d_model, padding_idx=0)
        # 位置编码
        self.position_encoding = PositionalEncoding(d_model, max_len, dropout)
        # Segment嵌入：区分问题和文档
        self.segment_embedding = nn.Embedding(3, d_model)  # 0=pad, 1=question, 2=document

        # Transformer编码器层堆叠
        self.encoder_blocks = nn.ModuleList([
            TransformerBlock(d_model, num_heads, d_ff, dropout)
            for _ in range(num_layers)
        ])

        # 答案位置预测层
        self.qa_outputs = nn.Linear(d_model, 2)  # 起始和结束位置

    def forward(self, input_ids, segment_ids=None, attention_mask=None):
        """
        前向传播
        :param input_ids: 输入token ids [batch, seq_len]
        :param segment_ids: 段落id [batch, seq_len]，标记问题/文档边界
        :param attention_mask: 注意力掩码 [batch, seq_len]
        :return: 起始logits, 结束logits
        """
        batch_size, seq_len = input_ids.size()

        # 词嵌入 + 位置编码 + 段落嵌入
        token_embed = self.token_embedding(input_ids)  # [batch, seq_len, d_model]
        position_embed = self.position_encoding.pe[:, :seq_len, :].transpose(0, 1)
        token_embed = token_embed + position_embed

        if segment_ids is not None:
            segment_embed = self.segment_embedding(segment_ids)
            token_embed = token_embed + segment_embed

        # 创建注意力掩码
        if attention_mask is not None:
            # 扩展掩码维度
            extended_mask = attention_mask.unsqueeze(1).unsqueeze(2)  # [batch, 1, 1, seq_len]
            mask = extended_mask.to(dtype=token_embed.dtype)
            mask = (1.0 - mask) * -10000.0
        else:
            mask = None

        # 通过Transformer编码器
        x = token_embed
        all_attn_weights = []
        for block in self.encoder_blocks:
            x, attn_weights = block(x, mask)
            all_attn_weights.append(attn_weights)

        # 答案位置预测
        logits = self.qa_outputs(x)  # [batch, seq_len, 2]
        start_logits = logits[:, :, 0]  # [batch, seq_len]
        end_logits = logits[:, :, 1]    # [batch, seq_len]

        # 掩码：padding位置设为负无穷
        if attention_mask is not None:
            mask_float = attention_mask.float()
            start_logits = start_logits + (1 - mask_float) * (-1e30)
            end_logits = end_logits + (1 - mask_float) * (-1e30)

        return start_logits, end_logits


def create_mask(input_ids, pad_token_id=0):
    """
    创建注意力掩码
    :param input_ids: 输入token ids
    :param pad_token_id: padding token的id
    :return: 掩码，1表示有效位置，0表示padding
    """
    mask = (input_ids != pad_token_id).long()
    return mask


def compute_span_loss(start_logits, end_logits, start_positions, end_positions):
    """
    计算答案span的交叉熵损失
    :param start_logits: 起始位置logits [batch, seq_len]
    :param end_logits: 结束位置logits [batch, seq_len]
    :param start_positions: 真实起始位置 [batch]
    :param end_positions: 真实结束位置 [batch]
    :return: 损失标量
    """
    # 起始位置损失
    start_loss = F.cross_entropy(start_logits, start_positions)
    # 结束位置损失
    end_loss = F.cross_entropy(end_logits, end_positions)
    # 总损失
    total_loss = (start_loss + end_loss) / 2
    return total_loss


def decode_predictions(start_logits, end_logits, input_ids, tokenizer,
                       max_answer_len=30, n_best=3):
    """
    解码预测结果
    :param start_logits: 起始位置logits
    :param end_logits: 结束位置logits
    :param input_ids: 输入token ids
    :param tokenizer: 分词器
    :param max_answer_len: 答案最大长度
    :param n_best: 返回的候选答案数量
    :return: 最佳答案字符串
    """
    # 获取top-k起始和结束位置
    start_indexes = start_logits.topk(n_best).indices
    end_indexes = end_logits.topk(n_best).indices

    best_score = -1e9
    best_answer = ""

    for start_index in start_indexes:
        for end_index in end_indexes:
            # 确保结束位置在起始位置之后
            if end_index < start_index:
                continue
            # 确保答案长度合理
            if end_index - start_index > max_answer_len:
                continue

            score = start_logits[start_index] + end_logits[end_index]

            if score > best_score:
                best_score = score
                # 解码答案span
                answer_tokens = input_ids[start_index:end_index + 1]
                best_answer = tokenizer.decode(answer_tokens, skip_special_tokens=True)

    return best_answer


def demo():
    """Transformer QA模型演示"""
    batch_size = 2
    seq_len = 50
    vocab_size = 3000

    # 初始化模型
    model = TransformerQA(
        vocab_size=vocab_size,
        d_model=128,
        num_heads=4,
        num_layers=2,
        d_ff=512,
        max_len=128
    )
    model.train()

    # 构造输入
    input_ids = torch.randint(1, vocab_size, (batch_size, seq_len))
    segment_ids = torch.zeros(batch_size, seq_len, dtype=torch.long)
    segment_ids[:, seq_len // 2:] = 1  # 前半是问题，后半是文档
    attention_mask = torch.ones(batch_size, seq_len)

    # 前向传播
    start_logits, end_logits = model(input_ids, segment_ids, attention_mask)

    # 模拟损失计算
    start_positions = torch.randint(0, seq_len, (batch_size,))
    end_positions = torch.clamp(start_positions + torch.randint(1, 10, (batch_size,)), max=seq_len - 1)
    loss = compute_span_loss(start_logits, end_logits, start_positions, end_positions)

    print(f"[Transformer阅读理解演示]")
    print(f"  序列长度: {seq_len}")
    print(f"  起始logits形状: {start_logits.shape}")
    print(f"  结束logits形状: {end_logits.shape}")
    print(f"  损失值: {loss.item():.4f}")
    print(f"  模型参数量: {sum(p.numel() for p in model.parameters()):,}")
    print("  ✅ Transformer QA模型演示通过！")


if __name__ == "__main__":
    demo()
