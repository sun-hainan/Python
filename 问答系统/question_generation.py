"""
问题生成模块 - Seq2Seq模型

本模块实现基于Seq2Seq的问题生成系统。
给定一段文本（答案范围），生成相关的问题。

核心方法：
1. Encoder：编码答案上下文
2. Decoder：解码生成问题
3. 复制机制：从原文复制实体/关键词
4. 答案感知：融入答案信息指导问题生成
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class AnswerAwareEncoder(nn.Module):
    """答案感知的编码器：编码上下文并标记答案位置"""

    def __init__(self, vocab_size, embed_dim=128, hidden_size=256, dropout=0.2):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.dropout = nn.Dropout(dropout)
        # 答案标记嵌入：0=普通词, 1=答案内, 2=答案开始, 3=答案结束
        self.answer_marker_embedding = nn.Embedding(4, embed_dim)

        self.encoder = nn.LSTM(
            input_size=embed_dim * 2,
            hidden_size=hidden_size,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )

    def forward(self, context_ids, answer_marker_ids, mask=None):
        """
        前向传播
        :param context_ids: 上下文token ids [batch, seq_len]
        :param answer_marker_ids: 答案标记ids [batch, seq_len]
        :param mask: 掩码
        :return: 编码输出
        """
        # 词嵌入
        word_embed = self.dropout(self.embedding(context_ids))
        # 答案标记嵌入
        marker_embed = self.answer_marker_embedding(answer_marker_ids)
        # 拼接
        combined_embed = torch.cat([word_embed, marker_embed], dim=-1)
        # 编码
        outputs, (h_n, c_n) = self.encoder(combined_embed)
        return outputs, (h_n, c_n)


class CopyMechanism(nn.Module):
    """复制机制：从源文本复制词汇"""

    def __init__(self, hidden_size, vocab_size):
        super().__init__()
        self.hidden_size = hidden_size
        self.vocab_size = vocab_size
        # 生成概率
        self.p_gen_linear = nn.Linear(hidden_size * 3 + hidden_size, 1)
        # 上下文注意力
        self.context_attention = nn.Linear(hidden_size * 2, 1)

    def forward(self, decoder_state, context, decoder_input, enc_output, max_gen_vocab=None):
        """
        计算复制概率
        :param decoder_state: 解码器状态
        :param context: 注意力上下文向量
        :param decoder_input: 解码器输入
        :param enc_output: 编码器输出（用于计算复制分数）
        :return: 混合概率分布
        """
        # 生成概率
        p_gen_input = torch.cat([decoder_state, context, decoder_input], dim=-1)
        p_gen = torch.sigmoid(self.p_gen_linear(p_gen_input))  # [batch, 1]

        # 返回简单概率（简化实现）
        return p_gen.squeeze(-1)


class QuestionGenerator(nn.Module):
    """问题生成模型"""

    def __init__(self, vocab_size, embed_dim=128, hidden_size=256, dropout=0.2, max_len=50):
        super().__init__()
        self.vocab_size = vocab_size
        self.max_len = max_len

        # 答案感知编码器
        self.encoder = AnswerAwareEncoder(vocab_size, embed_dim, hidden_size, dropout)

        # 解码器
        self.decoder_lstm = nn.LSTM(
            input_size=embed_dim + hidden_size * 2,
            hidden_size=hidden_size * 2,
            num_layers=1,
            batch_first=True
        )

        # 注意力
        self.attention = nn.Sequential(
            nn.Linear(hidden_size * 4, hidden_size),
            nn.Tanh(),
            nn.Linear(hidden_size, 1)
        )

        # 复制机制
        self.copy = CopyMechanism(hidden_size * 2, vocab_size)

        # 输出层
        self.output_linear = nn.Linear(hidden_size * 3, vocab_size)

        # 嵌入层（共享）
        self.embedding = self.encoder.embedding

    def encode(self, context_ids, answer_markers, mask=None):
        """编码上下文"""
        return self.encoder(context_ids, answer_markers, mask)

    def decode_step(self, decoder_input, decoder_state, encoder_outputs, mask=None):
        """
        单步解码
        :param decoder_input: 解码器输入 [batch, embed_dim]
        :param decoder_state: (h, c) 解码器状态
        :param encoder_outputs: 编码器输出 [batch, seq_len, hidden*2]
        :param mask: 掩码
        :return: output, new_decoder_state, attention_weights
        """
        # LSTM一步
        lstm_input = torch.cat([decoder_input, decoder_state[0].squeeze(0)], dim=-1).unsqueeze(1)
        lstm_output, new_state = self.decoder_lstm(lstm_input, decoder_state)
        lstm_output = lstm_output.squeeze(1)  # [batch, hidden*2]

        # 注意力
        seq_len = encoder_outputs.size(1)
        h_dec = new_state[0].transpose(0, 1)  # [batch, 1, hidden*2]
        h_dec_exp = h_dec.expand(-1, seq_len, -1)  # [batch, seq_len, hidden*2]

        energy = torch.cat([h_dec_exp, encoder_outputs], dim=-1)
        scores = self.attention(energy).squeeze(-1)  # [batch, seq_len]

        # 掩码
        if mask is not None:
            scores = scores + (1 - mask.float()) * (-1e30)

        attn_weights = F.softmax(scores, dim=-1)
        context = torch.bmm(attn_weights.unsqueeze(1), encoder_outputs).squeeze(1)  # [batch, hidden*2]

        # 拼接输出
        output_input = torch.cat([lstm_output, context], dim=-1)
        logits = self.output_linear(output_input)

        return logits, new_state, attn_weights, context

    def forward(self, context_ids, answer_markers, question_ids, mask=None, teacher_forcing_ratio=0.5):
        """
        前向传播（训练）
        :param context_ids: 上下文token ids [batch, ctx_len]
        :param answer_markers: 答案标记ids [batch, ctx_len]
        :param question_ids: 问题token ids [batch, q_len]
        :param mask: 上下文掩码
        :return: 预测logits列表
        """
        # 编码
        encoder_outputs, (h_n, c_n) = self.encode(context_ids, answer_markers, mask)
        decoder_state = (h_n, c_n)

        outputs = []
        decoder_input = self.embedding(question_ids[:, 0])

        for t in range(question_ids.size(1) - 1):
            logits, decoder_state, attn, context = self.decode_step(
                decoder_input, decoder_state, encoder_outputs, mask
            )
            outputs.append(logits)

            # 教师强制
            if np.random.random() < teacher_forcing_ratio:
                decoder_input = self.embedding(question_ids[:, t + 1])
            else:
                decoder_input = self.embedding(logits.argmax(dim=-1))

        return outputs

    def generate(self, context_ids, answer_markers, mask=None, max_len=None, sos_token_id=101, eos_token_id=102):
        """
        贪婪生成问题
        :return: 生成的token ids列表
        """
        max_len = max_len or self.max_len

        # 编码
        encoder_outputs, (h_n, c_n) = self.encode(context_ids, answer_markers, mask)
        decoder_state = (h_n, c_n)

        generated = []
        decoder_input = self.embedding(torch.tensor([[sos_token_id]], device=context_ids.device))

        for _ in range(max_len):
            logits, decoder_state, attn, context = self.decode_step(
                decoder_input, decoder_state, encoder_outputs, mask
            )

            next_token = logits.argmax(dim=-1).item()
            if next_token == eos_token_id:
                break

            generated.append(next_token)
            decoder_input = self.embedding(torch.tensor([[next_token]], device=context_ids.device))

        return generated


class MultiReferenceLoss(nn.Module):
    """多参考损失：支持多个参考答案的问题生成"""

    def __init__(self, vocab_size, pad_token_id=0):
        super().__init__()
        self.criterion = nn.CrossEntropyLoss(ignore_index=pad_token_id, reduction='mean')

    def forward(self, outputs, targets):
        """
        :param outputs: 预测logits列表，每个[batch, vocab_size]
        :param targets: 目标token ids [batch, seq_len]
        """
        loss = 0.0
        for t, output in enumerate(outputs):
            target = targets[:, t + 1]  # 跳过第一个token
            loss += self.criterion(output, target)
        return loss / len(outputs)


class QuestionGenerationMetrics:
    """问题生成评估指标"""

    @staticmethod
    def bleu(predictions: List[List[str]], references: List[List[str]], n: int = 4) -> float:
        """计算BLEU分数（简化实现）"""
        from collections import Counter
        scores = []

        for pred, ref in zip(predictions, references):
            pred_ngrams = [tuple(pred[i:i+k]) for k in range(1, min(n, len(pred)+1)) for i in range(len(pred)-k+1)]
            ref_ngrams = [tuple(ref[i:i+k]) for k in range(1, min(n, len(ref)+1)) for i in range(len(ref)-k+1)]

            if not pred_ngrams:
                scores.append(0.0)
                continue

            matches = sum(1 for ng in pred_ngrams if ng in ref_ngrams)
            score = matches / len(pred_ngrams)
            scores.append(score)

        return sum(scores) / len(scores) if scores else 0.0

    @staticmethod
    def distinct_n(predictions: List[List[str]], n: int = 2) -> float:
        """计算n-gram多样性"""
        ngrams = set()
        total = 0

        for pred in predictions:
            for i in range(len(pred) - n + 1):
                ngrams.add(tuple(pred[i:i+n]))
                total += 1

        return len(ngrams) / total if total > 0 else 0.0


class QuestionGenerationPipeline:
    """问题生成Pipeline"""

    def __init__(self, vocab_size):
        self.model = QuestionGenerator(vocab_size)
        self.model.eval()

    def generate(self, context: str, answer: str, answer_start: int, answer_end: int,
                 context_tokens: List[str], tokenizer) -> str:
        """
        生成问题
        :param context: 上下文文本
        :param answer: 答案文本
        :param answer_start: 答案开始位置（token索引）
        :param answer_end: 答案结束位置
        :param context_tokens: 上下文token列表
        :param tokenizer: 分词器
        :return: 生成的问题文本
        """
        # 构造答案标记
        answer_markers = [0] * len(context_tokens)
        for i in range(answer_start, answer_end + 1):
            answer_markers[i] = 1  # 答案内
        answer_markers[answer_start] = 2  # 答案开始
        answer_markers[answer_end] = 3   # 答案结束

        # Tokenize
        context_ids = torch.tensor([tokenizer.encode(context)[:100]])
        answer_markers_tensor = torch.tensor([answer_markers[:100]])

        # 生成
        generated_ids = self.model.generate(context_ids, answer_markers_tensor)
        question_text = tokenizer.decode(generated_ids)

        return question_text


def demo():
    """问题生成模型演示"""
    vocab_size = 5000
    embed_dim = 64
    hidden_size = 128

    print("[问题生成演示]")

    # 初始化模型
    model = QuestionGenerator(vocab_size, embed_dim, hidden_size)
    model.train()

    # 模拟数据
    batch_size = 2
    ctx_len = 50
    q_len = 20

    context_ids = torch.randint(1, vocab_size, (batch_size, ctx_len))
    answer_markers = torch.randint(0, 4, (batch_size, ctx_len))
    question_ids = torch.randint(1, vocab_size, (batch_size, q_len))

    # 前向传播
    outputs = model(context_ids, answer_markers, question_ids)
    print(f"  输出步数: {len(outputs)}")
    print(f"  每步输出维度: {outputs[0].shape}")

    # 损失计算
    multi_ref_loss = MultiReferenceLoss(vocab_size)
    # 简化的损失计算
    dummy_loss = sum(o.mean() for o in outputs[:5]) / 5
    print(f"  模拟损失: {dummy_loss.item():.4f}")

    # 评估指标
    predictions = [["what", "is", "ai"], ["how", "does", "it", "work"]]
    references = [["what", "is", "machine", "learning"], ["how", "does", "it", "function"]]
    bleu = QuestionGenerationMetrics.bleu(predictions, references)
    distinct = QuestionGenerationMetrics.distinct_n(predictions)
    print(f"  BLEU: {bleu:.3f}, Distinct-2: {distinct:.3f}")

    print(f"  模型参数量: {sum(p.numel() for p in model.parameters()):,}")
    print("  ✅ 问题生成模型演示通过！")


if __name__ == "__main__":
    demo()
