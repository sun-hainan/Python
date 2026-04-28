"""
多选问答系统模块

本模块实现多选问答任务的核心组件。
给定一个问题和多个候选选项，模型需要选择最正确的答案。

核心方法：
1. 联合编码：问题和选项联合编码
2. 交叉注意力：建模问题与各选项之间的交互
3. 选项排序：对所有选项进行排序选择
4. 答案选择：基于排序结果选择答案
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class OptionEncoder(nn.Module):
    """选项编码器：将问题和选项编码为联合表示"""

    def __init__(self, vocab_size, embed_dim=128, hidden_size=128, dropout=0.2):
        super().__init__()
        # 词嵌入
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        # 双向LSTM编码器
        self.encoder = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_size,
            num_layers=1,
            batch_first=True,
            bidirectional=True,
            dropout=dropout
        )
        # 融合层
        self.fusion = nn.Linear(4 * hidden_size, hidden_size)

    def encode_sequence(self, token_ids):
        """编码单个序列"""
        embedded = self.embedding(token_ids)
        outputs, (h_n, _) = self.encoder(embedded)
        # 双向最后隐藏状态
        h_combined = torch.cat([h_n[0], h_n[1]], dim=-1)
        return outputs, h_combined

    def forward(self, question_ids, option_ids):
        """
        联合编码问题和选项
        :param question_ids: 问题token ids [batch, q_len]
        :param option_ids: 选项token ids [batch, o_len]
        :return: 联合表示 [batch, 2*hidden_size]
        """
        # 分别编码
        q_outputs, q_hidden = self.encode_sequence(question_ids)
        o_outputs, o_hidden = self.encode_sequence(option_ids)

        # 拼接问题和选项的最终隐藏状态
        joint_hidden = torch.cat([q_hidden, o_hidden], dim=-1)  # [batch, 4*hidden_size]

        # 融合
        fused = torch.relu(self.fusion(joint_hidden))

        return fused


class CrossAttentionModule(nn.Module):
    """交叉注意力模块：建模问题和选项之间的交互"""

    def __init__(self, hidden_size):
        super().__init__()
        # QKV投影
        self.W_q = nn.Linear(hidden_size, hidden_size)
        self.W_k = nn.Linear(hidden_size, hidden_size)
        self.W_v = nn.Linear(hidden_size, hidden_size)
        self.W_o = nn.Linear(hidden_size, hidden_size)

    def forward(self, question_repr, option_repr, q_mask=None, o_mask=None):
        """
        计算交叉注意力
        :param question_repr: 问题表示 [batch, q_len, hidden_size]
        :param option_repr: 选项表示 [batch, o_len, hidden_size]
        :param q_mask: 问题掩码
        :param o_mask: 选项掩码
        :return: 交叉注意力增强的表示
        """
        # Q来自问题，K和V来自选项
        Q = self.W_q(question_repr)
        K = self.W_k(option_repr)
        V = self.W_v(option_repr)

        # 计算注意力分数
        scores = torch.matmul(Q, K.transpose(-2, -1)) / np.sqrt(Q.size(-1))  # [batch, q_len, o_len]

        # 掩码处理
        if q_mask is not None and o_mask is not None:
            mask = torch.matmul(q_mask.float().unsqueeze(-1), o_mask.float().unsqueeze(1))
            scores = scores + (1 - mask) * (-1e30)

        # 归一化
        attn_weights = F.softmax(scores, dim=-1)
        # 加权求和
        context = torch.matmul(attn_weights, V)  # [batch, q_len, hidden_size]

        # 输出
        output = self.W_o(context)

        return output, attn_weights


class MultipleChoiceModel(nn.Module):
    """多选问答模型"""

    def __init__(self, vocab_size, num_options=4, embed_dim=128,
                 hidden_size=128, dropout=0.2):
        super().__init__()
        self.num_options = num_options
        self.hidden_size = hidden_size

        # 选项编码器
        self.option_encoder = OptionEncoder(vocab_size, embed_dim, hidden_size, dropout)
        # 交叉注意力
        self.cross_attention = CrossAttentionModule(hidden_size)
        # 问题-选项交互层
        self.interaction = nn.Linear(4 * hidden_size, hidden_size)
        # 分类器
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(hidden_size * 2, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, 1)
        )

    def forward(self, question_ids, option_ids_list, q_mask=None, o_masks=None):
        """
        前向传播
        :param question_ids: 问题token ids [batch, q_len]
        :param option_ids_list: 选项token ids列表，长度为num_options，每个[batch, o_len]
        :param q_mask: 问题掩码 [batch, q_len]
        :param o_masks: 选项掩码列表
        :return: 每个选项的得分 [batch, num_options]
        """
        batch_size = question_ids.size(0)
        option_scores = []

        for i, option_ids in enumerate(option_ids_list):
            o_mask = o_masks[i] if o_masks is not None else None

            # 编码问题和选项
            joint_repr = self.option_encoder(question_ids, option_ids)

            # 简化：直接用joint表示预测
            # 实际应用中可以用交叉注意力进一步建模
            score = self.classifier(joint_repr)  # [batch, 1]
            option_scores.append(score)

        # 拼接所有选项得分
        all_scores = torch.cat(option_scores, dim=1)  # [batch, num_options]

        # softmax归一化（可选）
        probs = F.softmax(all_scores, dim=-1)

        return all_scores, probs


class DecomposableAttentionModel(nn.Module):
    """可分解注意力模型(ESIM变体)：先attend后compare再aggregate"""

    def __init__(self, vocab_size, embed_dim=128, hidden_size=128, dropout=0.2):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.dropout = nn.Dropout(dropout)

        # 输入编码层
        self.input_encoder = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_size,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )

        # 注意力层
        self.attention = nn.Linear(4 * hidden_size, hidden_size)

        # 推理组合层
        self.inference_layer = nn.LSTM(
            input_size=4 * hidden_size,
            hidden_size=hidden_size,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )

        # 输出分类层
        self.output_classifier = nn.Sequential(
            nn.Linear(8 * hidden_size, hidden_size),
            nn.Tanh(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, 1)
        )

    def soft_attention_align(self, x, y, x_mask, y_mask):
        """软注意力对齐"""
        # 计算相似度矩阵
        x_exp = x.unsqueeze(2)  # [batch, x_len, 1, hidden]
        y_exp = y.unsqueeze(1)  # [batch, 1, y_len, hidden]
        sim = torch.sum(x_exp * y_exp, dim=-1)  # [batch, x_len, y_len]

        # 掩码处理
        if x_mask is not None and y_mask is not None:
            x_mask_exp = x_mask.float().unsqueeze(2)
            y_mask_exp = y_mask.float().unsqueeze(1)
            sim = sim + (1 - torch.matmul(x_mask_exp, y_mask_exp)) * (-1e30)

        # x对y的注意力
        attn_y = F.softmax(sim.view(-1, sim.size(-1)), dim=-1)
        attn_y = attn_y.view(sim.size(0), sim.size(1), -1)  # [batch, x_len, y_len]
        y_weighted = torch.bmm(attn_y, y)  # [batch, x_len, hidden]

        # y对x的注意力
        attn_x = F.softmax(sim.max(dim=2)[0], dim=-1).unsqueeze(1)  # [batch, 1, x_len]
        x_weighted = torch.bmm(attn_x, x)  # [batch, 1, hidden]
        x_weighted = x_weighted.expand(-1, x.size(1), -1)  # [batch, x_len, hidden]

        return y_weighted, x_weighted

    def forward(self, premise_ids, hypothesis_ids, p_mask=None, h_mask=None):
        """
        前向传播（可用于问题和选项）
        :param premise_ids: 前提序列 [batch, p_len]
        :param hypothesis_ids: 假设序列 [batch, h_len]
        :param p_mask: 前提掩码
        :param h_mask: 假设掩码
        :return: 预测logits
        """
        # 嵌入
        premise_embed = self.dropout(self.embedding(premise_ids))
        hypothesis_embed = self.dropout(self.embedding(hypothesis_ids))

        # 输入编码
        premise_enc, _ = self.input_encoder(premise_embed)
        hypothesis_enc, _ = self.input_encoder(hypothesis_embed)

        # 注意力对齐
        p_weighted, h_weighted = self.soft_attention_align(
            premise_enc, hypothesis_enc, p_mask, h_mask
        )

        # 构建增强表示
        premise_diff = premise_enc - p_weighted
        hypothesis_diff = hypothesis_enc - h_weighted

        premise_enhanced = torch.cat([
            premise_enc, p_weighted, premise_enc * p_weighted, premise_diff
        ], dim=-1)

        hypothesis_enhanced = torch.cat([
            hypothesis_enc, h_weighted, hypothesis_enc * h_weighted, hypothesis_diff
        ], dim=-1)

        # 推理组合
        premise_comb, _ = self.inference_layer(premise_enhanced)
        hypothesis_comb, _ = self.inference_layer(hypothesis_enhanced)

        # 池化
        premise_pool = torch.cat([premise_comb.max(dim=1)[0], premise_comb.mean(dim=1)], dim=-1)
        hypothesis_pool = torch.cat([hypothesis_comb.max(dim=1)[0], hypothesis_comb.mean(dim=1)], dim=-1)

        # 拼接并分类
        combined = torch.cat([premise_pool, hypothesis_pool], dim=-1)
        logits = self.output_classifier(combined)

        return logits.squeeze(-1)


class MultiChoiceQA:
    """多选问答系统封装"""

    def __init__(self, vocab_size, num_options=4):
        self.num_options = num_options
        # 可使用不同的基础模型
        self.model = MultipleChoiceModel(vocab_size, num_options)
        self.model.eval()

    def predict(self, question_ids, option_ids_list):
        """预测答案索引"""
        with torch.no_grad():
            scores, probs = self.model(question_ids, option_ids_list)
            predictions = probs.argmax(dim=-1)
        return predictions, probs


def demo():
    """多选问答系统演示"""
    batch_size = 2
    num_options = 4
    q_len = 15
    o_len = 10
    vocab_size = 2000

    # 初始化模型
    model = MultipleChoiceModel(vocab_size, num_options)
    model.train()

    # 构造输入
    question_ids = torch.randint(1, vocab_size, (batch_size, q_len))
    option_ids_list = [torch.randint(1, vocab_size, (batch_size, o_len)) for _ in range(num_options)]

    # 前向传播
    scores, probs = model(question_ids, option_ids_list)

    print(f"[多选问答系统演示]")
    print(f"  选项数量: {num_options}")
    print(f"  得分形状: {scores.shape}")
    print(f"  概率分布形状: {probs.shape}")
    print(f"  预测答案: {probs.argmax(dim=1)}")
    print(f"  模型参数量: {sum(p.numel() for p in model.parameters()):,}")

    # 可分解注意力模型演示
    decomposable = DecomposableAttentionModel(vocab_size)
    logits = decomposable(question_ids, option_ids_list[0])
    print(f"  可分解注意力模型输出: {logits.shape}")

    print("  ✅ 多选问答系统演示通过！")


if __name__ == "__main__":
    demo()
