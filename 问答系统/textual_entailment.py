"""
文本蕴含识别模块

本模块实现文本蕴含识别(Textual Entailment/Natural Language Inference)任务。
判断"前提(premise)"和"假设(hypothesis)"之间的逻辑关系：
- Entailment（蕴含）：前提可以推导出假设
- Contradiction（矛盾）：前提与假设互斥
- Neutral（中立）：前提与假设既不蕴含也不矛盾

核心方法：
1. 交互式编码：联合编码前提和假设
2. 注意力对齐：捕捉两部分之间的语义对应
3. 关系分类：基于聚合表示分类
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class SoftAlignmentModule(nn.Module):
    """软对齐模块：对齐前提和假设的语义相关部分"""

    def __init__(self, hidden_size):
        super().__init__()
        self.alignment_linear = nn.Bilinear(hidden_size, hidden_size, 1)

    def forward(self, premise_hidden, hypothesis_hidden, p_mask=None, h_mask=None):
        """
        计算软对齐
        :param premise_hidden: 前提表示 [batch, p_len, hidden]
        :param hypothesis_hidden: 假设表示 [batch, h_len, hidden]
        :param p_mask: 前提掩码
        :param h_mask: 假设掩码
        :return: 对齐后的前提, 对齐后的假设
        """
        batch_size, p_len, hidden = premise_hidden.size()
        _, h_len, _ = hypothesis_hidden.size()

        # 计算相似度矩阵 [batch, p_len, h_len]
        p_exp = premise_hidden.unsqueeze(2)  # [batch, p_len, 1, hidden]
        h_exp = hypothesis_hidden.unsqueeze(1)  # [batch, 1, h_len, hidden]
        sim_matrix = self.alignment_linear(p_exp, h_exp).squeeze(-1)  # [batch, p_len, h_len]

        # 掩码处理
        if p_mask is not None and h_mask is not None:
            p_mask_exp = p_mask.float().unsqueeze(-1)  # [batch, p_len, 1]
            h_mask_exp = h_mask.float().unsqueeze(1)   # [batch, 1, h_len]
            mask = torch.bmm(p_mask_exp, h_mask_exp)   # [batch, p_len, h_len]
            sim_matrix = sim_matrix + (1 - mask) * (-1e30)

        # 归一化
        attn_probs = F.softmax(sim_matrix.view(-1, h_len), dim=-1).view(batch_size, p_len, h_len)

        # 对齐：假设对前提的注意力加权
        aligned_hypothesis = torch.bmm(attn_probs, hypothesis_hidden)  # [batch, p_len, hidden]

        # 前提对假设的注意力加权
        attn_probs_t = F.softmax(sim_matrix.max(dim=1)[0], dim=-1).unsqueeze(1)  # [batch, 1, h_len]
        aligned_premise = torch.bmm(attn_probs_t, premise_hidden)  # [batch, 1, hidden]
        aligned_premise = aligned_premise.expand(-1, h_len, -1)   # [batch, h_len, hidden]

        return aligned_premise, aligned_hypothesis


class ESIMModel(nn.Module):
    """ESIM模型：加强版序列推理模型"""

    def __init__(self, vocab_size, embed_dim=128, hidden_size=128, num_classes=3, dropout=0.2):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.dropout = nn.Dropout(dropout)

        # 输入编码
        self.input_encoder = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_size,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )

        # 软对齐
        self.alignment = SoftAlignmentModule(hidden_size * 2)

        # 推理组合
        self.inference_composer = nn.LSTM(
            input_size=hidden_size * 2 * 4,  # concat + aligned + diff
            hidden_size=hidden_size,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )

        # 输出分类
        self.output_classifier = nn.Sequential(
            nn.Linear(hidden_size * 2 * 6, hidden_size * 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size * 2, num_classes)
        )

    def forward(self, premise_ids, hypothesis_ids, p_mask=None, h_mask=None):
        """
        前向传播
        :param premise_ids: 前提token ids [batch, p_len]
        :param hypothesis_ids: 假设token ids [batch, h_len]
        :param p_mask: 前提掩码
        :param h_mask: 假设掩码
        :return: 分类logits [batch, num_classes]
        """
        # 嵌入
        premise_embed = self.dropout(self.embedding(premise_ids))
        hypothesis_embed = self.dropout(self.embedding(hypothesis_ids))

        # 输入编码
        premise_enc, _ = self.input_encoder(premise_embed)
        hypothesis_enc, _ = self.input_encoder(hypothesis_embed)

        # 软对齐
        aligned_p, aligned_h = self.alignment(premise_enc, hypothesis_enc, p_mask, h_mask)

        # 构建增强表示
        premise_diff = premise_enc - aligned_p
        hypothesis_diff = hypothesis_enc - aligned_h

        premise_enhanced = torch.cat([premise_enc, aligned_p, premise_enc * aligned_p, premise_diff], dim=-1)
        hypothesis_enhanced = torch.cat([hypothesis_enc, aligned_h, hypothesis_enc * aligned_h, hypothesis_diff], dim=-1)

        # 推理组合
        premise_comb, _ = self.inference_composer(premise_enhanced)
        hypothesis_comb, _ = self.inference_composer(hypothesis_enhanced)

        # 池化
        premise_pool = torch.cat([premise_comb.max(dim=1)[0], premise_comb.mean(dim=1)], dim=-1)
        hypothesis_pool = torch.cat([hypothesis_comb.max(dim=1)[0], hypothesis_comb.mean(dim=1)], dim=-1)

        # 分类
        combined = torch.cat([premise_pool, hypothesis_pool], dim=-1)
        logits = self.output_classifier(combined)

        return logits


class DecomposableAttentionEntailment(nn.Module):
    """可分解注意力模型：先attend后compare再aggregate"""

    def __init__(self, vocab_size, embed_dim=128, hidden_size=128, num_classes=3, dropout=0.2):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.dropout = nn.Dropout(dropout)

        # 前馈网络（用于Attend步骤）
        self.ffn = nn.Sequential(
            nn.Linear(embed_dim, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU()
        )

        # 比较层
        self.compare_fcn = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout)
        )

        # 聚合层
        self.aggregate_fcn = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, num_classes)
        )

    def attend(self, a_ids, b_ids, a_mask=None, b_mask=None):
        """
        Attend步骤：计算a对b的注意力
        :return: 注意力加权后的b表示
        """
        a_embed = self.ffn(self.dropout(self.embedding(a_ids)))
        b_embed = self.ffn(self.dropout(self.embedding(b_ids)))

        # 计算相似度
        scores = torch.matmul(a_embed, b_embed.transpose(1, 2))  # [batch, a_len, b_len]

        # 掩码
        if a_mask is not None and b_mask is not None:
            mask = torch.matmul(a_mask.float().unsqueeze(-1), b_mask.float().unsqueeze(1))
            scores = scores + (1 - mask) * (-1e30)

        # softmax
        attn = F.softmax(scores.view(-1, scores.size(-1)), dim=-1).view_as(scores)
        # 加权求和
        attended = torch.bmm(attn, b_embed)  # [batch, a_len, hidden]

        return attended, attn

    def compare(self, original, attended):
        """Compare步骤：比较原文和attend后的结果"""
        combined = torch.cat([original, attended], dim=-1)
        return self.compare_fcn(combined)

    def aggregate(self, premise_compare, hypothesis_compare, p_mask=None, h_mask=None):
        """Aggregate步骤：聚合比较结果"""
        # 池化
        p_pooled = torch.cat([premise_compare.max(dim=1)[0], premise_compare.mean(dim=1)], dim=-1)
        h_pooled = torch.cat([hypothesis_compare.max(dim=1)[0], hypothesis_compare.mean(dim=1)], dim=-1)

        # 拼接并分类
        combined = torch.cat([p_pooled, h_pooled], dim=-1)
        return self.aggregate_fcn(combined)

    def forward(self, premise_ids, hypothesis_ids, p_mask=None, h_mask=None):
        """前向传播"""
        # premise attend to hypothesis
        attended_p, _ = self.attend(premise_ids, hypothesis_ids, p_mask, h_mask)
        # hypothesis attend to premise
        attended_h, _ = self.attend(hypothesis_ids, premise_ids, h_mask, p_mask)

        # Embed原始序列
        p_embed = self.ffn(self.dropout(self.embedding(premise_ids)))
        h_embed = self.ffn(self.dropout(self.embedding(hypothesis_ids)))

        # 比较
        p_compared = self.compare(p_embed, attended_p)
        h_compared = self.compare(h_embed, attended_h)

        # 聚合
        logits = self.aggregate(p_compared, h_compared, p_mask, h_mask)

        return logits


class TransformerEntailment(nn.Module):
    """基于Transformer的文本蕴含模型"""

    def __init__(self, vocab_size, hidden_size=256, num_layers=4, num_heads=4, num_classes=3, dropout=0.1):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, hidden_size, padding_idx=0)
        self.position_embedding = nn.Embedding(512, hidden_size)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_size,
            nhead=num_heads,
            dim_feedforward=hidden_size * 4,
            batch_first=True,
            dropout=dropout
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        self.classifier = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, num_classes)
        )

    def forward(self, premise_ids, hypothesis_ids, p_mask=None, h_mask=None):
        """前向传播"""
        batch_size, p_len = premise_ids.size()
        h_len = hypothesis_ids.size(1)

        # 拼接premise和hypothesis
        combined_ids = torch.cat([premise_ids, hypothesis_ids], dim=1)

        # 创建token type ids
        token_type = torch.cat([
            torch.zeros(p_len, dtype=torch.long, device=premise_ids.device).unsqueeze(0).expand(batch_size, -1),
            torch.ones(h_len, dtype=torch.long, device=premise_ids.device).unsqueeze(0).expand(batch_size, -1)
        ], dim=1)

        # 嵌入
        embedded = self.embedding(combined_ids)
        positions = torch.arange(combined_ids.size(1), device=combined_ids.device).unsqueeze(0).expand(batch_size, -1)
        embedded = embedded + self.position_embedding(positions)

        # 掩码：padding位置为True
        mask = torch.cat([p_mask, h_mask], dim=1) if p_mask is not None else None
        if mask is not None:
            key_padding_mask = (mask == 0)
        else:
            key_padding_mask = None

        # Transformer编码
        encoded = self.transformer(embedded, src_key_padding_mask=key_padding_mask)

        # 分别取CLS位置（假设是第一个）和平均
        premise_enc = encoded[:, :p_len, :]
        hypothesis_enc = encoded[:, p_len:, :]

        # 池化
        p_pooled = torch.cat([premise_enc.max(dim=1)[0], premise_enc.mean(dim=1)], dim=-1)
        h_pooled = torch.cat([hypothesis_enc.max(dim=1)[0], hypothesis_enc.mean(dim=1)], dim=-1)

        # 分类
        combined = torch.cat([p_pooled, h_pooled], dim=-1)
        logits = self.classifier(combined)

        return logits


def compute_entailment_accuracy(predictions, labels):
    """计算文本蕴含准确率"""
    correct = (predictions == labels).float()
    return correct.mean().item()


def demo():
    """文本蕴含识别模型演示"""
    batch_size = 2
    p_len = 15
    h_len = 12
    vocab_size = 3000
    num_classes = 3

    print("[文本蕴含识别演示]")

    # ESIM模型
    esim = ESIMModel(vocab_size, embed_dim=64, hidden_size=64)
    premise_ids = torch.randint(1, vocab_size, (batch_size, p_len))
    hypothesis_ids = torch.randint(1, vocab_size, (batch_size, h_len))
    p_mask = torch.ones(batch_size, p_len)
    h_mask = torch.ones(batch_size, h_len)

    esim_logits = esim(premise_ids, hypothesis_ids, p_mask, h_mask)
    print(f"  ESIM输出形状: {esim_logits.shape}")

    # 可分解注意力模型
    decomposable = DecomposableAttentionEntailment(vocab_size, embed_dim=64, hidden_size=64)
    decomp_logits = decomposable(premise_ids, hypothesis_ids, p_mask, h_mask)
    print(f"  可分解注意力输出: {decomp_logits.shape}")

    # Transformer模型
    transformer_entailment = TransformerEntailment(vocab_size, hidden_size=128)
    trans_logits = transformer_entailment(premise_ids, hypothesis_ids, p_mask, h_mask)
    print(f"  Transformer输出: {trans_logits.shape}")

    # 模拟标签计算准确率
    labels = torch.randint(0, num_classes, (batch_size,))
    acc = compute_entailment_accuracy(trans_logits.argmax(dim=-1), labels)
    print(f"  模拟准确率: {acc:.2f}")

    print(f"  ESIM参数量: {sum(p.numel() for p in esim.parameters()):,}")
    print("  ✅ 文本蕴含识别演示通过！")


if __name__ == "__main__":
    demo()
