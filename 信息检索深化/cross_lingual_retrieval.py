"""
跨语言检索模块

本模块实现跨语言信息检索（CLIR）系统。
支持不同语言之间的查询-文档匹配。

核心方法：
1. 翻译式：翻译查询或文档到目标语言
2. 跨语言词嵌入：多语言统一向量空间
3. 多语言BERT：mBERT/XLM-R
4. 伪双语语料：无监督跨语言对齐
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Tuple, Dict, Optional


class BilingualDictionary:
    """双语词典：用于跨语言对齐"""

    def __init__(self):
        self.dictionary = {}  # src_word -> {lang: [translations]}

    def add_pair(self, word: str, translation: str, src_lang: str, tgt_lang: str):
        """添加翻译对"""
        if word not in self.dictionary:
            self.dictionary[word] = {}
        if tgt_lang not in self.dictionary[word]:
            self.dictionary[word][tgt_lang] = []
        self.dictionary[word][t_lang].append(translation)

    def translate(self, word: str, src_lang: str, tgt_lang: str) -> List[str]:
        """翻译单词"""
        if word not in self.dictionary:
            return []
        return self.dictionary[word].get(tgt_lang, [])


class TranslationModel:
    """简单翻译模型（基于词对齐）"""

    def __init__(self, src_lang: str, tgt_lang: str):
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        self.word_translations = {}  # src -> {tgt: prob}
        self.vocab = set()

    def add_bilingual_corpus(self, src_sentences: List[str], tgt_sentences: List[str]):
        """添加双语平行语料"""
        for src, tgt in zip(srcences, tgt_sentences):
            src_words = src.lower().split()
            tgt_words = tgt.lower().split()

            for sw in src_words:
                self.vocab.add(sw)
                if sw not in self.word_translations:
                    self.word_translations[sw] = {}
                for tw in tgt_words:
                    self.word_translations[sw][tw] = self.word_translations[sw].get(tw, 0) + 1

        # 归一化为概率
        for sw in self.word_translations:
            total = sum(self.word_translations[sw].values())
            for tw in self.word_translations[sw]:
                self.word_translations[sw][tw] /= total

    def translate_sentence(self, sentence: str, top_k: int = 5) -> List[str]:
        """翻译句子"""
        src_words = sentence.lower().split()
        translations = []

        for word in src_words:
            if word in self.word_translations:
                # 取概率最高的翻译
                sorted_trans = sorted(
                    self.word_translations[word].items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                translations.append(sorted_trans[0][0])
            else:
                translations.append(word)  # 保留原词

        return translations


class CrossLingualWordEmbedding(nn.Module):
    """跨语言词嵌入：将不同语言映射到统一向量空间"""

    def __init__(self, vocab_size: int, embed_dim: int = 128, num_langs: int = 2):
        super().__init__()
        self.embed_dim = embed_dim
        self.num_langs = num_langs

        # 每种语言的独立嵌入
        self.lang_embeddings = nn.ModuleList([
            nn.Embedding(vocab_size, embed_dim) for _ in range(num_langs)
        ])

        # 共享的跨语言映射
        self.projection = nn.Sequential(
            nn.Linear(embed_dim, embed_dim),
            nn.ReLU(),
            nn.Linear(embed_dim, embed_dim)
        )

    def encode(self, token_ids: torch.Tensor, lang_idx: int) -> torch.Tensor:
        """
        编码特定语言的文本
        :param token_ids: token ids
        :param lang_idx: 语言索引
        :return: 嵌入向量
        """
        embed = self.lang_embeddings[lang_idx](token_ids)
        # 投影到共享空间
        projected = self.projection(embed.mean(dim=1))
        projected = F.normalize(projected, p=2, dim=-1)
        return projected

    def forward(self, src_ids: torch.Tensor, tgt_ids: torch.Tensor, src_lang: int, tgt_lang: int):
        """
        前向传播：计算跨语言相似度
        """
        src_embed = self.encode(src_ids, src_lang)
        tgt_embed = self.encode(tgt_ids, tgt_lang)

        # 余弦相似度
        similarity = F.cosine_similarity(src_embed, tgt_embed, dim=-1)

        return similarity


class XLMEncoder(nn.Module):
    """简化的多语言Transformer编码器（类XLM-R）"""

    def __init__(self, vocab_size: int, hidden_size: int = 256,
                 num_layers: int = 4, num_heads: int = 4, max_len: int = 512):
        super().__init__()
        self.hidden_size = hidden_size

        # 词嵌入
        self.embedding = nn.Embedding(vocab_size, hidden_size, padding_idx=0)
        self.position_embedding = nn.Embedding(max_len, hidden_size)

        # 语言嵌入
        self.lang_embedding = nn.Embedding(100, hidden_size)  # 支持100种语言

        # Transformer编码器
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_size,
            nhead=num_heads,
            dim_feedforward=hidden_size * 4,
            batch_first=True,
            dropout=0.1
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        # 输出层
        self.pooler = nn.Linear(hidden_size, hidden_size)

    def forward(self, token_ids: torch.Tensor, lang_ids: torch.Tensor,
                attention_mask: Optional[torch.Tensor] = None):
        """
        前向传播
        :param token_ids: token ids [batch, seq_len]
        :param lang_ids: 语言id [batch]
        :param attention_mask: 注意力掩码
        :return: 句子表示
        """
        batch_size, seq_len = token_ids.size()

        # 嵌入
        token_embed = self.embedding(token_ids)
        position_ids = torch.arange(seq_len, device=token_ids.device).unsqueeze(0).expand(batch_size, -1)
        position_embed = self.position_embedding(position_ids)
        lang_embed = self.lang_embedding(lang_ids).unsqueeze(1)

        hidden = token_embed + position_embed + lang_embed

        # 编码
        if attention_mask is not None:
            key_padding_mask = (attention_mask == 0)
        else:
            key_padding_mask = None

        encoded = self.encoder(hidden, src_key_padding_mask=key_padding_mask)

        # 池化：取[CLS]或平均
        pooled = encoded[:, 0, :]  # [CLS]
        pooled = torch.tanh(self.pooler(pooled))

        return pooled


class CrossLingualRetriever:
    """跨语言检索器"""

    def __init__(self, encoder: XLMEncoder, device='cpu'):
        self.encoder = encoder
        self.encoder.to(device)
        self.encoder.eval()
        self.device = device

        # 文档索引
        self.doc_embeddings = {}  # doc_id -> (embedding, lang_id)

    def index_document(self, doc_id: str, doc_tokens: torch.Tensor, lang_id: int):
        """索引文档"""
        with torch.no_grad():
            embedding = self.encoder(doc_tokens.unsqueeze(0).to(self.device),
                                    torch.tensor([lang_id]).to(self.device))
            self.doc_embeddings[doc_id] = (embedding.cpu(), lang_id)

    def search(self, query_tokens: torch.Tensor, query_lang_id: int,
               top_k: int = 10) -> List[Tuple[str, float]]:
        """
        搜索跨语言文档
        """
        with torch.no_grad():
            # 编码查询
            query_embedding = self.encoder(
                query_tokens.unsqueeze(0).to(self.device),
                torch.tensor([query_lang_id]).to(self.device)
            )

            # 计算与所有文档的相似度
            scores = []
            for doc_id, (doc_emb, doc_lang) in self.doc_embeddings.items():
                # 跨语言相似度（同一向量空间）
                doc_emb = doc_emb.to(self.device)
                sim = F.cosine_similarity(query_embedding, doc_emb, dim=-1).item()
                scores.append((doc_id, sim, doc_lang))

            # 排序
            scores.sort(key=lambda x: x[1], reverse=True)

            return [(doc_id, score) for doc_id, score, _ in scores[:top_k]]


class PseudoBilingualCorpus:
    """伪双语语料生成：无监督跨语言对齐"""

    def __init__(self, monolingual_corpora: Dict[str, List[str]]):
        """
        :param monolingual_corpora: {lang: [sentences]}
        """
        self.corpora = monolingual_corpora
        self.languages = list(monolingual_corpora.keys())

    def generate_parallel_pairs(self, num_pairs: int = 1000) -> List[Tuple[str, str]]:
        """生成伪平行句对"""
        pairs = []

        for _ in range(num_pairs):
            # 随机选择两种语言
            lang1, lang2 = np.random.choice(self.languages, 2, replace=False)

            # 随机选择句子
            sent1 = np.random.choice(self.corpora[lang1])
            sent2 = np.random.choice(self.corpora[lang2])

            pairs.append((sent1, sent2))

        return pairs


class CrossLingualMine:
    """跨语言MINE：无监督跨语言对齐"""

    def __init__(self, embed_dim: int = 128):
        self.embed_dim = embed_dim

    def align_embeddings(self, src_embeddings: np.ndarray, tgt_embeddings: np.ndarray,
                        iterations: int = 100) -> Tuple[np.ndarray, np.ndarray]:
        """
        对齐源语言和目标语言嵌入
        :return: 对齐后的嵌入
        """
        # 简化：使用线性变换对齐
        src_mean = src_embeddings.mean(axis=0)
        tgt_mean = tgt_embeddings.mean(axis=0)

        src_centered = src_embeddings - src_mean
        tgt_centered = tgt_embeddings - tgt_mean

        # SVD求最优变换
        covariance = src_centered.T @ tgt_centered
        U, _, Vt = np.linalg.svd(covariance)
        R = Vt.T @ U.T

        # 变换
        src_aligned = src_centered @ R + tgt_mean

        return src_aligned, tgt_embeddings


def mine_cross_lingual_words(src_word: str, tgt_sentence: str, src_model, tgt_model) -> List[Tuple[str, float]]:
    """
    跨语言词汇挖掘：找出目标语句中与源词最相关的词
    """
    # 编码
    src_vec = src_model.get_word_vector(src_word)
    tgt_tokens = tgt_sentence.lower().split()

    scores = []
    for token in tgt_tokens:
        tgt_vec = tgt_model.get_word_vector(token)
        # 相似度
        sim = np.dot(src_vec, tgt_vec) / (np.linalg.norm(src_vec) * np.linalg.norm(tgt_vec) + 1e-10)
        scores.append((token, float(sim)))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores


def demo():
    """跨语言检索演示"""
    vocab_size = 5000
    hidden_size = 128

    print("[跨语言检索演示]")

    # XLM编码器
    xlm = XLMEncoder(vocab_size, hidden_size, num_layers=2)
    print(f"  XLM编码器参数量: {sum(p.numel() for p in xlm.parameters()):,}")

    # 跨语言词嵌入
    clwe = CrossLingualWordEmbedding(vocab_size, embed_dim=64, num_langs=2)
    src_ids = torch.randint(1, vocab_size, (4, 10))
    tgt_ids = torch.randint(1, vocab_size, (4, 10))

    similarity = clwe(src_ids, tgt_ids, src_lang=0, tgt_lang=1)
    print(f"  跨语言相似度: {similarity}")

    # 翻译模型
    translation_model = TranslationModel("en", "zh")
    translation_model.add_bilingual_corpus(
        ["hello world", "machine learning is great"],
        ["你好 世界", "机器学习 很棒"]
    )
    translated = translation_model.translate_sentence("hello world")
    print(f"\n  翻译示例: 'hello world' -> {' '.join(translated)}")

    # 伪双语语料
    monolingual = {
        "en": ["machine learning algorithms", "deep neural networks", "natural language processing"],
        "zh": ["机器学习算法", "深度神经网络", "自然语言处理"]
    }
    pseudo_corpus = PseudoBilingualCorpus(monolingual)
    pairs = pseudo_corpus.generate_parallel_pairs(5)
    print(f"\n  伪平行句对示例: {pairs[0]}")

    # 跨语言检索器
    retriever = CrossLingualRetriever(xlm)
    print(f"\n  跨语言检索器初始化完成")

    print("  ✅ 跨语言检索演示通过！")


if __name__ == "__main__":
    demo()
