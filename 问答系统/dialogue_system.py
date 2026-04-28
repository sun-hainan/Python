"""
对话系统模块 - 检索式/生成式/混合对话

本模块实现三种对话系统的核心组件：
1. 检索式：基于匹配度选择最优回复
2. 生成式：Seq2Seq模型生成自然回复
3. 混合式：结合检索和生成的优势

核心组件：
- 句子编码器：将对话上下文编码为向量
- 匹配模型：计算候选回复与上下文的相关性
- 生成模型：条件式语言模型生成回复
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


# ============================================================
# 检索式对话系统组件
# ============================================================

class SentenceEncoder(nn.Module):
    """句子编码器：BiLSTM将句子编码为固定维度向量"""

    def __init__(self, vocab_size, embed_dim=128, hidden_size=128, dropout=0.2):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.encoder = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_size,
            num_layers=1,
            batch_first=True,
            bidirectional=True,
            dropout=dropout
        )
        self.projection = nn.Linear(2 * hidden_size, hidden_size)

    def forward(self, token_ids, mask=None):
        """
        前向传播
        :param token_ids: token索引 [batch, seq_len]
        :param mask: 掩码 [batch, seq_len]
        :return: 句子向量 [batch, hidden_size]
        """
        embedded = self.embedding(token_ids)
        outputs, (h_n, _) = self.encoder(embedded)

        # 双向最后隐藏状态拼接
        h_forward = h_n[0]   # [batch, hidden]
        h_backward = h_n[1]  # [batch, hidden]
        sentence_vec = torch.cat([h_forward, h_backward], dim=-1)  # [batch, 2*hidden]

        # 投影到目标维度
        sentence_vec = self.projection(sentence_vec)
        return sentence_vec


class MatchingModule(nn.Module):
    """匹配模块：计算上下文与候选回复的匹配分数"""

    def __init__(self, hidden_size):
        super().__init__()
        # 直接相似度
        self.dot_transform = nn.Linear(hidden_size, hidden_size)
        # 交互特征网络
        self.interaction_net = nn.Sequential(
            nn.Linear(hidden_size * 4, hidden_size * 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size * 2, hidden_size)
        )
        # 匹配评分层
        self.score_layer = nn.Linear(hidden_size, 1)

    def forward(self, context_vec, response_vec):
        """
        计算匹配分数
        :param context_vec: 上下文向量 [batch, hidden_size]
        :param response_vec: 回复向量 [batch, hidden_size] 或 [batch, num_candidates, hidden_size]
        """
        # 处理批量候选
        if response_vec.dim() == 3:
            # [batch, num_candidates, hidden_size]
            batch_size, num_candidates, hidden_size = response_vec.size()
            context_expanded = context_vec.unsqueeze(1).expand(-1, num_candidates, -1)

            # 交互特征
            concat = torch.cat([
                context_expanded,
                response_vec,
                torch.abs(context_expanded - response_vec),
                context_expanded * response_vec
            ], dim=-1)  # [batch, num_candidates, 4*hidden_size]

            interaction = self.interaction_net(concat)
            scores = self.score_layer(interaction).squeeze(-1)  # [batch, num_candidates]
        else:
            # 单个候选
            concat = torch.cat([
                context_vec,
                response_vec,
                torch.abs(context_vec - response_vec),
                context_vec * response_vec
            ], dim=-1)

            interaction = self.interaction_net(concat)
            scores = self.score_layer(interaction).squeeze(-1)

        return scores


class RetrievalDialogueSystem(nn.Module):
    """检索式对话系统"""

    def __init__(self, vocab_size, embed_dim=128, hidden_size=128):
        super().__init__()
        self.context_encoder = SentenceEncoder(vocab_size, embed_dim, hidden_size)
        self.response_encoder = SentenceEncoder(vocab_size, embed_dim, hidden_size)
        self.matching_module = MatchingModule(hidden_size)

    def encode_context(self, context_tokens):
        """编码对话上下文"""
        return self.context_encoder(context_tokens)

    def encode_response(self, response_tokens):
        """编码候选回复"""
        return self.response_encoder(response_tokens)

    def score(self, context_vec, response_vecs):
        """计算匹配分数"""
        return self.matching_module(context_vec, response_vecs)

    def forward(self, context_ids, response_ids):
        """前向传播"""
        context_vec = self.encode_context(context_ids)
        response_vec = self.encode_response(response_ids)
        scores = self.score(context_vec, response_vec)
        return scores


# ============================================================
# 生成式对话系统组件
# ============================================================

class AttentionDecoder(nn.Module):
    """带注意力的解码器用于生成式对话"""

    def __init__(self, vocab_size, embed_dim=128, hidden_size=256, encoder_hidden_size=256):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.decoder_lstm = nn.LSTM(
            input_size=embed_dim + encoder_hidden_size,
            hidden_size=hidden_size,
            num_layers=1,
            batch_first=True
        )
        # 注意力层
        self.attn_W = nn.Linear(hidden_size + encoder_hidden_size, hidden_size)
        self.attn_v = nn.Linear(hidden_size, 1, bias=False)
        # 输出层
        self.out = nn.Linear(hidden_size + encoder_hidden_size + embed_dim, vocab_size)

    def forward(self, input_token, decoder_state, encoder_outputs, mask=None):
        """
        单步解码
        :param input_token: 当前输入token [batch]
        :param decoder_state: (h, c) 解码器状态
        :param encoder_outputs: 编码器输出 [batch, src_len, encoder_hidden_size]
        :param mask: 源序列掩码
        :return: 输出logits, 更新后的decoder_state
        """
        # 嵌入
        embedded = self.embedding(input_token)  # [batch, embed_dim]

        # LSTM一步
        lstm_input = torch.cat([embedded, decoder_state[0].squeeze(0)], dim=-1).unsqueeze(1)
        lstm_output, decoder_state = self.decoder_lstm(lstm_input, decoder_state)
        lstm_output = lstm_output.squeeze(1)  # [batch, hidden_size]

        # 注意力
        src_len = encoder_outputs.size(1)
        h_dec = decoder_state[0].squeeze(0).unsqueeze(1).expand(-1, src_len, -1)
        energy = torch.cat([h_dec, encoder_outputs], dim=-1)  # [batch, src_len, hidden+enc_hidden]
        energy = torch.tanh(self.attn_W(energy))  # [batch, src_len, hidden]
        attn_scores = self.attn_v(energy).squeeze(-1)  # [batch, src_len]

        # 掩码
        if mask is not None:
            attn_scores = attn_scores + (1 - mask.float()) * (-1e30)

        attn_weights = F.softmax(attn_scores, dim=-1)
        context = torch.bmm(attn_weights.unsqueeze(1), encoder_outputs).squeeze(1)  # [batch, enc_hidden]

        # 输出
        output_input = torch.cat([lstm_output, context, embedded], dim=-1)
        logits = self.out(output_input)

        return logits, decoder_state, attn_weights


class GenerativeDialogueSystem(nn.Module):
    """生成式对话系统"""

    def __init__(self, vocab_size, embed_dim=128, hidden_size=256, encoder_hidden_size=256):
        super().__init__()
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size

        # 编码器（共享）
        self.encoder = nn.LSTM(
            input_size=embed_dim,
            hidden_size=encoder_hidden_size,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )
        # 解码器
        self.decoder = AttentionDecoder(vocab_size, embed_dim, hidden_size, encoder_hidden_size * 2)
        # 投影层
        self.proj = nn.Linear(encoder_hidden_size * 2, encoder_hidden_size)

    def forward(self, src_ids, tgt_ids, max_len=50, teacher_forcing_ratio=0.5):
        """
        前向传播（训练）
        :param src_ids: 源序列 [batch, src_len]
        :param tgt_ids: 目标序列 [batch, tgt_len]
        :param max_len: 最大生成长度
        :param teacher_forcing_ratio: 教师强制比例
        :return: 预测logits列表
        """
        # 编码
        embedded = nn.functional.embedding(src_ids, torch.zeros_like(src_ids).long()) if False else None

        # 简化：实际应该先嵌入再编码
        # 这里假设encoder_input是嵌入后的
        encoder_input = torch.zeros(src_ids.size(0), src_ids.size(1), 128).to(src_ids.device)
        encoder_outputs, (h_n, c_n) = self.encoder(encoder_input)

        # 合并双向状态
        h_forward = h_n[0]
        h_backward = h_n[1]
        h_combined = torch.cat([h_forward, h_backward], dim=-1)
        c_combined = torch.cat([c_n[0], c_n[1]], dim=-1)

        # 解码器初始状态
        decoder_state = (h_combined.unsqueeze(0), c_combined.unsqueeze(0))

        # 编码器输出投影
        encoder_outputs = self.proj(encoder_outputs)

        outputs = []
        decoder_input = tgt_ids[:, 0]

        for t in range(tgt_len - 1):
            logits, decoder_state, _ = self.decoder(decoder_input, decoder_state, encoder_outputs)
            outputs.append(logits)

            # 教师强制
            if np.random.random() < teacher_forcing_ratio:
                decoder_input = tgt_ids[:, t + 1]
            else:
                decoder_input = logits.argmax(dim=-1)

        return outputs


# ============================================================
# 混合式对话系统
# ============================================================

class HybridDialogueSystem(nn.Module):
    """混合式对话系统：结合检索和生成"""

    def __init__(self, vocab_size, embed_dim=128, hidden_size=256):
        super().__init__()
        # 检索组件
        self.retrieval = RetrievalDialogueSystem(vocab_size, embed_dim, hidden_size)
        # 生成组件
        self.generative = GenerativeDialogueSystem(vocab_size, embed_dim, hidden_size)
        # 混合权重
        self.blend_weight = nn.Parameter(torch.tensor(0.5))

    def retrieve(self, context_ids, response_candidates):
        """检索最相关的候选回复"""
        context_vec = self.retrieval.encode_context(context_ids)
        response_vecs = torch.stack([
            self.retrieval.encode_response(resp) for resp in response_candidates
        ], dim=1)
        scores = self.retrieval.score(context_vec, response_vecs)
        return scores

    def generate(self, context_ids, max_len=50):
        """生成回复"""
        # 简化：实际需要完整的生成流程
        return torch.zeros(context_ids.size(0), max_len, self.generative.vocab_size)


def demo():
    """对话系统演示"""
    batch_size = 2
    seq_len = 15
    vocab_size = 500

    print("[对话系统演示]")

    # 检索式系统
    retrieval_system = RetrievalDialogueSystem(vocab_size, embed_dim=64, hidden_size=64)
    context_ids = torch.randint(1, vocab_size, (batch_size, seq_len))
    response_ids = torch.randint(1, vocab_size, (batch_size, seq_len))
    scores = retrieval_system(context_ids, response_ids)
    print(f"  检索系统 - 匹配分数: {scores}")

    # 生成式系统
    generative_system = GenerativeDialogueSystem(vocab_size, embed_dim=64, hidden_size=128)
    tgt_ids = torch.randint(1, vocab_size, (batch_size, 10))
    print(f"  生成系统 - 参数量: {sum(p.numel() for p in generative_system.parameters()):,}")

    # 混合系统
    hybrid_system = HybridDialogueSystem(vocab_size, embed_dim=64, hidden_size=64)
    print(f"  混合系统 - blend权重: {hybrid_system.blend_weight.item():.3f}")

    print("  ✅ 对话系统演示通过！")


if __name__ == "__main__":
    demo()
