"""
段落排序模块 - BERT句子编码

本模块实现基于深度学习的段落排序(Passage Ranking)系统。
给定查询和候选段落，预测每个段落与查询的相关性得分。

核心方法：
1. BERT句子编码：将文本编码为语义向量
2. 交互式编码：建模查询-段落之间的细粒度交互
3. 重排序：基于深度模型对候选段落进行排序
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class BertSentenceEncoder(nn.Module):
    """BERT风格句子编码器：多层Transformer + [CLS]输出"""

    def __init__(self, vocab_size, hidden_size=256, num_layers=4, num_heads=4, max_len=512):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        # 词嵌入
        self.token_embedding = nn.Embedding(vocab_size, hidden_size, padding_idx=0)
        self.position_embedding = nn.Embedding(max_len, hidden_size)
        self.token_type_embedding = nn.Embedding(2, hidden_size)

        # LayerNorm和Dropout
        self.embed_norm = nn.LayerNorm(hidden_size)
        self.dropout = nn.Dropout(0.1)

        # Transformer编码器层
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_size,
            nhead=num_heads,
            dim_feedforward=hidden_size * 4,
            batch_first=True,
            dropout=0.1
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

    def forward(self, token_ids, token_type_ids=None, attention_mask=None):
        """
        前向传播
        :param token_ids: token索引 [batch, seq_len]
        :param token_type_ids: 段落类型id [batch, seq_len]
        :param attention_mask: 注意力掩码 [batch, seq_len]
        :return: 句子表示 [batch, hidden_size]
        """
        batch_size, seq_len = token_ids.size()

        # 词嵌入 + 位置嵌入
        token_embed = self.token_embedding(token_ids)
        position_ids = torch.arange(seq_len, device=token_ids.device).unsqueeze(0).expand(batch_size, -1)
        position_embed = self.position_embedding(position_ids)

        # Token类型嵌入
        if token_type_ids is None:
            token_type_ids = torch.zeros_like(token_ids)
        token_type_embed = self.token_type_embedding(token_type_ids)

        # 合并嵌入
        embedding = self.embed_norm(token_embed + position_embed + token_type_embed)
        embedding = self.dropout(embedding)

        # Transformer编码
        if attention_mask is not None:
            # 转换为Transformer需要的掩码格式
            key_padding_mask = (attention_mask == 0)
        else:
            key_padding_mask = None

        encoded = self.transformer(embedding, src_key_padding_mask=key_padding_mask)

        # 取[CLS]位置的输出作为句子表示
        cls_output = encoded[:, 0, :]

        return cls_output


class InteractionEncoder(nn.Module):
    """交互式编码器：建模查询-段落的细粒度交互"""

    def __init__(self, vocab_size, hidden_size=256, num_layers=2, num_heads=4):
        super().__init__()
        self.hidden_size = hidden_size

        # 嵌入层
        self.token_embedding = nn.Embedding(vocab_size, hidden_size, padding_idx=0)

        # 查询编码
        self.query_transformer = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(
                d_model=hidden_size,
                nhead=num_heads,
                dim_feedforward=hidden_size * 4,
                batch_first=True
            ),
            num_layers=num_layers
        )

        # 交互编码
        self.interaction_transformer = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(
                d_model=hidden_size * 3,  # query + passage + cross
                nhead=num_heads,
                dim_feedforward=hidden_size * 4,
                batch_first=True
            ),
            num_layers=num_layers
        )

        # 输出投影
        self.output_proj = nn.Linear(hidden_size * 3, hidden_size)

    def forward(self, query_ids, passage_ids, query_mask=None, passage_mask=None):
        """
        前向传播
        :param query_ids: 查询token ids [batch, q_len]
        :param passage_ids: 段落token ids [batch, p_len]
        :param query_mask: 查询掩码
        :param passage_mask: 段落掩码
        :return: 交互表示 [batch, hidden_size]
        """
        # 嵌入
        query_embed = self.token_embedding(query_ids)
        passage_embed = self.token_embedding(passage_ids)

        # 分别编码
        query_encoded = self.query_transformer(
            query_embed,
            src_key_padding_mask=(query_mask == 0) if query_mask is not None else None
        )
        passage_encoded = self.query_transformer(
            passage_embed,
            src_key_padding_mask=(passage_mask == 0) if passage_mask is not None else None
        )

        # 交互特征：拼接 + 逐元素乘积
        cross_product = query_encoded.unsqueeze(2) * passage_encoded.unsqueeze(1)  # [batch, q, p, hidden]
        # 聚合段落对查询的表示
        passage_from_query = cross_product.max(dim=1)[0]  # [batch, p, hidden]
        query_from_passage = cross_product.max(dim=2)[0]  # [batch, q, hidden]

        # 交互序列：交替拼接query和passage表示
        interaction_input = torch.cat([
            query_encoded,
            passage_encoded,
            query_from_passage
        ], dim=1)  # [batch, q+p, 3*hidden]

        # 交互编码
        interaction_encoded = self.interaction_transformer(
            self.output_proj(interaction_input)
        )

        # 池化输出
        pooled = interaction_encoded.mean(dim=1)  # [batch, hidden]

        return pooled


class CrossEncoder(nn.Module):
    """交叉编码器：将查询和段落拼接后联合编码"""

    def __init__(self, vocab_size, hidden_size=256, num_layers=4, num_heads=4):
        super().__init__()
        self.hidden_size = hidden_size

        # 嵌入层
        self.embedding = nn.Embedding(vocab_size, hidden_size, padding_idx=0)
        self.position_embedding = nn.Embedding(512, hidden_size)

        # 编码器
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_size,
            nhead=num_heads,
            dim_feedforward=hidden_size * 4,
            batch_first=True
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        # 分类头
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_size, 1)
        )

    def forward(self, input_ids, attention_mask=None):
        """
        前向传播
        :param input_ids: 拼接后的token ids [batch, seq_len]
        :param attention_mask: 注意力掩码
        :return: 相关性分数 [batch]
        """
        batch_size, seq_len = input_ids.size()

        # 嵌入
        embedded = self.embedding(input_ids)
        position_ids = torch.arange(seq_len, device=input_ids.device).unsqueeze(0).expand(batch_size, -1)
        embedded = embedded + self.position_embedding(position_ids)

        # 编码
        if attention_mask is not None:
            key_padding_mask = (attention_mask == 0)
        else:
            key_padding_mask = None

        encoded = self.encoder(embedded, src_key_padding_mask=key_padding_mask)

        # 取[CLS]位置预测
        cls_output = encoded[:, 0, :]
        scores = self.classifier(cls_output).squeeze(-1)

        return scores


class BiEncoderRanker(nn.Module):
    """双编码器排序器：分别编码查询和段落"""

    def __init__(self, vocab_size, hidden_size=256):
        super().__init__()
        self.query_encoder = BertSentenceEncoder(vocab_size, hidden_size)
        self.passage_encoder = BertSentenceEncoder(vocab_size, hidden_size)

    def forward(self, query_ids, passage_ids):
        """前向传播"""
        query_repr = self.query_encoder(query_ids)
        passage_repr = self.passage_encoder(passage_ids)
        # 计算余弦相似度
        similarity = F.cosine_similarity(query_repr, passage_repr, dim=-1)
        return similarity


class PassageRanker:
    """段落排序器封装"""

    def __init__(self, model_type="cross", vocab_size=5000, hidden_size=256):
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size

        if model_type == "cross":
            self.model = CrossEncoder(vocab_size, hidden_size)
        elif model_type == "bi":
            self.model = BiEncoderRanker(vocab_size, hidden_size)
        else:
            self.model = InteractionEncoder(vocab_size, hidden_size)

        self.model.eval()

    def score(self, query: str, passages: List[str], tokenizer) -> List[float]:
        """
        对候选段落打分
        :param query: 查询字符串
        :param passages: 候选段落列表
        :param tokenizer: 分词器
        :return: 每个段落的得分
        """
        scores = []

        with torch.no_grad():
            for passage in passages:
                # 分词
                query_tokens = tokenizer.encode(query)
                passage_tokens = tokenizer.encode(passage)

                # 拼接
                if self.model.__class__.__name__ == "CrossEncoder":
                    # 交叉编码：[CLS] query [SEP] passage [SEP]
                    input_ids = [101] + query_tokens + [102] + passage_tokens + [102]
                    input_ids = torch.tensor([input_ids])
                    score = self.model(input_ids).item()
                else:
                    # 双编码
                    q_ids = torch.tensor([query_tokens[:128]])
                    p_ids = torch.tensor([passage_tokens[:512]])
                    score = self.model(q_ids, p_ids).item()

                scores.append(score)

        return scores

    def rerank(self, query: str, passages: List[str], top_k: int = 10) -> List[Tuple[int, float]]:
        """
        对段落重排序
        :param query: 查询
        :param passages: 候选段落列表
        :param top_k: 返回前k个
        :return: [(passage_idx, score)]列表
        """
        # 简单评分器模拟
        class SimpleTokenizer:
            def encode(self, text):
                words = text.lower().split()
                return [hash(w) % 5000 + 1 for w in words[:100]]

        tokenizer = SimpleTokenizer()
        scores = self.score(query, passages, tokenizer)

        # 排序
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]


def compute_ndcg(relevance_scores: List[float], predicted_order: List[int], k: int = 10) -> float:
    """
    计算NDCG@k
    :param relevance_scores: 真实相关性分数
    :param predicted_order: 预测的排序（索引列表）
    :param k: 考虑前k个
    :return: NDCG@k
    """
    def dcg(scores, k):
        scores = scores[:k]
        return sum((2 ** rel - 1) / np.log2(idx + 2) for idx, rel in enumerate(scores))

    # 理想排序
    ideal_scores = sorted(relevance_scores, reverse=True)

    # DCG
    pred_dcg = dcg([relevance_scores[i] for i in predicted_order[:k]], k)
    ideal_dcg = dcg(ideal_scores[:k], k)

    return pred_dcg / ideal_dcg if ideal_dcg > 0 else 0.0


def demo():
    """段落排序系统演示"""
    vocab_size = 5000
    hidden_size = 128

    print("[段落排序系统演示]")

    # 交叉编码器
    cross_encoder = CrossEncoder(vocab_size, hidden_size, num_layers=2)
    input_ids = torch.randint(1, vocab_size, (2, 50))
    cross_scores = cross_encoder(input_ids)
    print(f"  交叉编码器输出: {cross_scores.shape}")

    # 双编码器
    bi_encoder = BiEncoderRanker(vocab_size, hidden_size)
    q_ids = torch.randint(1, vocab_size, (2, 20))
    p_ids = torch.randint(1, vocab_size, (2, 100))
    bi_scores = bi_encoder(q_ids, p_ids)
    print(f"  双编码器输出: {bi_scores.shape}")

    # 交互编码器
    interaction_encoder = InteractionEncoder(vocab_size, hidden_size)
    interaction_repr = interaction_encoder(q_ids, p_ids)
    print(f"  交互编码器输出: {interaction_repr.shape}")

    # 排序器
    ranker = PassageRanker(model_type="cross", vocab_size=vocab_size, hidden_size=hidden_size)

    # 模拟排序
    class SimpleTokenizer:
        def encode(self, text):
            return [hash(w) % vocab_size + 1 for w in text.split()[:50]]

    query = "What is machine learning?"
    passages = [
        "Machine learning is a subset of artificial intelligence.",
        "Deep learning uses neural networks.",
        "The weather is nice today.",
        "Python is a programming language.",
        "AI stands for artificial intelligence."
    ]

    ranked = ranker.rerank(query, passages, top_k=3)
    print(f"\n  查询: {query}")
    print(f"  排序结果:")
    for idx, score in ranked:
        print(f"    [{score:.3f}] {passages[idx][:40]}...")

    # NDCG评估
    relevance = [1.0, 0.8, 0.0, 0.5, 0.9]
    predicted = [i for i, _ in ranked] + [1, 2]
    ndcg = compute_ndcg(relevance, predicted, k=3)
    print(f"\n  NDCG@3: {ndcg:.4f}")

    print("  ✅ 段落排序系统演示通过！")


if __name__ == "__main__":
    demo()
