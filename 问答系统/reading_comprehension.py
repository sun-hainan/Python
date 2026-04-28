"""
机器阅读理解模块 - BiDAF / 注意力机制实现

本模块实现双向注意力流(BiDAF)网络，用于机器阅读理解任务。
BiDAF 通过双向注意力机制同时建模上下文到问题和问题到上下文的依赖关系。

核心思想：
1. 嵌入层：将词级和字符级表示融合
2. 编码层：双向LSTM编码上下文和问题
3. 注意力层：双向注意力流融合两种信息
4. 输出层：预测答案span的起始和结束位置
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class CharacterEmbedding(nn.Module):
    """字符级嵌入层：使用卷积神经网络从字符序列中提取词表示"""

    def __init__(self, char_vocab_size, embed_dim=16, out_channels=100, kernel_size=5):
        super().__init__()
        # 字符嵌入矩阵，维度 [字符表大小, 嵌入维度]
        self.char_embedding = nn.Embedding(char_vocab_size, embed_dim, padding_idx=0)
        # 卷积层：提取字符级n-gram特征
        self.conv = nn.Conv2d(
            in_channels=1,       # 输入通道数（单通道图像类比）
            out_channels=out_channels,  # 输出通道数
            kernel_size=(kernel_size, embed_dim)  # 卷积核尺寸
        )

    def forward(self, char_tensor):
        """
        前向传播
        :param char_tensor: 字符张量，形状 [batch, seq_len, max_word_len]
        :return: 字符级特征，形状 [batch, seq_len, out_channels]
        """
        # [batch, seq_len, max_word_len, embed_dim]
        char_embed = self.char_embedding(char_tensor)
        # 压缩第4维，适配Conv2d要求 [batch, 1, seq_len, max_word_len*embed_dim]
        batch_size, seq_len, max_word_len, embed_dim = char_embed.shape
        char_embed = char_embed.view(batch_size, 1, seq_len, max_word_len * embed_dim)
        # 卷积 + ReLU激活
        conv_out = torch.relu(self.conv(char_embed))
        # 最大池化，取每个通道的最大值
        pooled, _ = conv_out.max(dim=3)  # [batch, out_channels, seq_len]
        # 转置为 [batch, seq_len, out_channels]
        return pooled.transpose(1, 2)


class WordEmbedding(nn.Module):
    """词级嵌入层：预训练词向量 + 可训练偏置"""

    def __init__(self, vocab_size, embed_dim, pretrained_embeddings=None, trainable=True):
        super().__init__()
        # 词嵌入矩阵
        self.word_embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        # 加载预训练词向量（可选）
        if pretrained_embeddings is not None:
            self.word_embedding.weight.data.copy_(torch.from_numpy(pretrained_embeddings))
        # 是否训练词向量
        self.word_embedding.weight.requires_grad = trainable

    def forward(self, word_tensor):
        """
        前向传播
        :param word_tensor: 词索引张量，形状 [batch, seq_len]
        :return: 词向量，形状 [batch, seq_len, embed_dim]
        """
        return self.word_embedding(word_tensor)


class BiDAFAttention(nn.Module):
    """双向注意力流层：计算上下文-问题双向注意力"""
    # similarity_matrix 中使用的可训练标量
    sim_weight = None

    def __init__(self, hidden_size):
        super().__init__()
        self.hidden_size = hidden_size
        # 相似度矩阵的可训练权重
        self.sim_weight = nn.Parameter(torch.randn(hidden_size, 3))
        # 输出变换层：融合注意力后的表示
        self.context_transform = nn.Linear(6 * hidden_size, hidden_size)
        # 注意力权重初始化
        nn.init.xavier_uniform_(self.sim_weight)

    def forward(self, context_encoded, question_encoded, context_mask=None, question_mask=None):
        """
        双向注意力流前向传播
        :param context_encoded: 编码后的上下文 [batch, c_len, hidden_size]
        :param question_encoded: 编码后的问题 [batch, q_len, hidden_size]
        :param context_mask: 上下文掩码 [batch, c_len]
        :param question_mask: 问题掩码 [batch, q_len]
        :return: 注意力增强的上下文表示 [batch, c_len, 6*hidden_size]
        """
        batch_size, c_len, _ = context_encoded.shape
        q_len = question_encoded.shape[1]

        # 扩展维度便于批量计算相似度
        # [batch, c_len, 1, hidden] vs [batch, 1, q_len, hidden]
        c_expanded = context_encoded.unsqueeze(2)          # [batch, c_len, 1, hidden]
        q_expanded = question_encoded.unsqueeze(1)        # [batch, 1, q_len, hidden]

        # 相似度矩阵：c^T * W * [c, q, c◦q]
        # 逐元素乘法表示hadamard积
        hadamard = c_expanded * q_expanded                  # [batch, c_len, q_len, hidden]
        # 拼接三种交互信息
        combined = torch.cat([c_expanded, q_expanded, hadamard], dim=-1)  # [batch, c_len, q_len, 3*hidden]

        # 计算相似度分数
        # sim_weight: [hidden_size, 3] -> 广播至 [batch, c_len, q_len, 3*hidden_size]
        sim_scores = torch.matmul(combined, self.sim_weight)  # [batch, c_len, q_len, hidden_size]
        sim_scores = torch.tanh(sim_scores).sum(dim=-1)       # [batch, c_len, q_len]

        # 应用掩码（填充位置设为负无穷）
        if context_mask is not None and question_mask is not None:
            c_mask_expanded = context_mask.unsqueeze(-1).float()      # [batch, c_len, 1]
            q_mask_expanded = question_mask.unsqueeze(1).float()      # [batch, 1, q_len]
            mask_matrix = torch.bmm(c_mask_expanded, q_mask_expanded).squeeze(1)  # [batch, c_len, q_len]
            sim_scores = sim_scores + (1 - mask_matrix) * (-1e30)

        # ----- C2Q 注意力：问题到上下文 -----
        # 问题侧softmax：每个上下文位置关注最相关的问题词
        q2c_attn = F.softmax(sim_scores, dim=2)                      # [batch, c_len, q_len]
        # 加权求和：聚合问题信息
        q2c_context = torch.bmm(q2c_attn, question_encoded)          # [batch, c_len, hidden_size]

        # ----- C2Q 注意力：上下文到问题 -----
        # 上下文侧softmax：识别最重要的问题词
        c2q_attn = F.softmax(sim_scores.max(dim=1)[0], dim=1)       # [batch, q_len]
        # 全局问题表示
        question_summarized = torch.bmm(c2q_attn.unsqueeze(1), question_encoded)  # [batch, 1, hidden]
        question_summarized = question_summarized.expand(-1, c_len, -1)          # [batch, c_len, hidden]

        # 拼接原始上下文 + C2Q + 元素积 + 元素差
        G = torch.cat([
            context_encoded,                # 原始上下文
            q2c_context,                    # 问题到上下文注意力
            context_encoded * q2c_context,  # hadamard积
            context_encoded * question_summarized,  # 与问题摘要的交互
            torch.abs(context_encoded - q2c_context),  # L1距离
            torch.abs(context_encoded - question_summarized)  # 与摘要的L1距离
        ], dim=-1)  # [batch, c_len, 6*hidden_size]

        return G


class BiDAFOutput(nn.Module):
    """BiDAF输出层：预测答案span的起始和结束位置"""

    def __init__(self, hidden_size):
        super().__init__()
        # 第一层：融合注意力表示
        self.fusion_layer = nn.Linear(6 * hidden_size, hidden_size)
        # 第二层：双向LSTM建模答案边界
        self.lstm = nn.LSTM(
            input_size=hidden_size,
            hidden_size=hidden_size // 2,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )
        # 起始位置预测层
        self.start_layer = nn.Linear(hidden_size, 1)
        # 结束位置预测层
        self.end_layer = nn.Linear(hidden_size, 1)

    def forward(self, G, context_mask=None):
        """
        前向传播
        :param G: 注意力增强表示 [batch, c_len, 6*hidden_size]
        :param context_mask: 上下文掩码 [batch, c_len]
        :return: 起始概率 [batch, c_len], 结束概率 [batch, c_len]
        """
        # 融合 + ReLU + Dropout
        fused = torch.relu(self.fusion_layer(G))
        fused = F.dropout(fused, p=0.2, training=self.training)
        # 双向LSTM
        lstm_out, _ = self.lstm(fused)  # [batch, c_len, hidden_size]

        # 预测起始位置
        start_logits = self.start_layer(lstm_out).squeeze(-1)  # [batch, c_len]
        # 预测结束位置
        end_logits = self.end_layer(lstm_out).squeeze(-1)      # [batch, c_len]

        # 掩码：填充位置设为负无穷
        if context_mask is not None:
            mask = (1 - context_mask.float()) * (-1e30)
            start_logits = start_logits + mask
            end_logits = end_logits + mask

        # 归一化为概率分布
        start_probs = F.softmax(start_logits, dim=-1)
        end_probs = F.softmax(end_logits, dim=-1)

        return start_probs, end_probs


class BiDAFModel(nn.Module):
    """完整的BiDAF模型：嵌入 -> 编码 -> 注意力 -> 输出"""

    def __init__(self, char_vocab_size, word_vocab_size, char_embed_dim=16, word_embed_dim=100,
                 hidden_size=100, pretrained_embeddings=None):
        super().__init__()
        # 字符级嵌入
        self.char_embed = CharacterEmbedding(char_vocab_size, char_embed_dim, hidden_size)
        # 词级嵌入
        self.word_embed = WordEmbedding(word_vocab_size, word_embed_dim, pretrained_embeddings)
        # 编码层：双向LSTM
        self.context_encoder = nn.LSTM(
            input_size=word_embed_dim + hidden_size,
            hidden_size=hidden_size,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )
        self.question_encoder = nn.LSTM(
            input_size=word_embed_dim + hidden_size,
            hidden_size=hidden_size,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )
        # 注意力层
        self.attention = BiDAFAttention(hidden_size)
        # 输出层
        self.output = BiDAFOutput(hidden_size)

    def forward(self, context_word, context_char, question_word, question_char,
                context_mask=None, question_mask=None):
        """
        完整前向传播
        :param context_word: 上下文词索引 [batch, c_len]
        :param context_char: 上下文字符张量 [batch, c_len, max_word_len]
        :param question_word: 问题词索引 [batch, q_len]
        :param question_char: 问题字符张量 [batch, q_len, max_word_len]
        :param context_mask: 上下文掩码
        :param question_mask: 问题掩码
        :return: 起始概率, 结束概率
        """
        # 获取嵌入
        context_word_embed = self.word_embed(context_word)
        question_word_embed = self.word_embed(question_word)
        context_char_embed = self.char_embed(context_char)
        question_char_embed = self.char_embed(question_char)

        # 拼接词级和字符级嵌入
        context_embedded = torch.cat([context_word_embed, context_char_embed], dim=-1)
        question_embedded = torch.cat([question_word_embed, question_char_embed], dim=-1)

        # 编码
        context_encoded, _ = self.context_encoder(context_embedded)
        question_encoded, _ = self.question_encoder(question_embedded)

        # 双向注意力
        G = self.attention(context_encoded, question_encoded, context_mask, question_mask)

        # 输出答案span
        return self.output(G, context_mask)


def demo():
    """BiDAF模型演示"""
    # 超参数
    batch_size = 2
    c_len = 15  # 上下文长度
    q_len = 8   # 问题长度
    max_word_len = 10
    char_vocab_size = 50
    word_vocab_size = 1000
    hidden_size = 64

    # 随机初始化模型
    model = BiDAFModel(
        char_vocab_size=char_vocab_size,
        word_vocab_size=word_vocab_size,
        hidden_size=hidden_size
    )
    model.train()

    # 构造假数据
    context_word = torch.randint(0, word_vocab_size, (batch_size, c_len))
    context_char = torch.randint(0, char_vocab_size, (batch_size, c_len, max_word_len))
    question_word = torch.randint(0, word_vocab_size, (batch_size, q_len))
    question_char = torch.randint(0, char_vocab_size, (batch_size, q_len, max_word_len))
    context_mask = torch.ones(batch_size, c_len)
    question_mask = torch.ones(batch_size, q_len)

    # 前向传播
    start_probs, end_probs = model(
        context_word, context_char, question_word, question_char,
        context_mask, question_mask
    )

    # 输出结果
    print(f"[BiDAF 演示]")
    print(f"  上下文长度: {c_len}, 问题长度: {q_len}")
    print(f"  起始概率形状: {start_probs.shape}")
    print(f"  结束概率形状: {end_probs.shape}")
    print(f"  预测起始位置: {start_probs.argmax(dim=1)}")
    print(f"  预测结束位置: {end_probs.argmax(dim=1)}")
    # 验证输出维度
    assert start_probs.shape == (batch_size, c_len), "起始概率维度错误"
    assert end_probs.shape == (batch_size, c_len), "结束概率维度错误"
    print("  ✅ BiDAF模型演示通过！")


if __name__ == "__main__":
    demo()
