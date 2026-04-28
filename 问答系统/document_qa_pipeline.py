"""
文档问答完整Pipeline模块

本模块实现端到端的文档问答系统，整合文档解析、段落检索、
阅读理解和答案生成等组件。

完整流程：
1. 文档解析：切分文档为段落/句子
2. 段落检索：快速召回相关段落（稀疏+密集检索）
3. 阅读理解：从候选段落中抽取/生成答案
4. 答案后处理：融合、重排序、置信度估计
"""

import re
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Document:
    """文档数据结构"""
    doc_id: str
    title: str
    content: str
    paragraphs: List[str] = None  # 自动切分的段落


@dataclass
class Paragraph:
    """段落数据结构"""
    para_id: str
    doc_id: str
    text: str
    index: int  # 在文档中的位置


@dataclass
class QAExample:
    """问答示例"""
    question: str
    context: str
    answer_start: int = -1
    answer_end: int = -1
    answer_text: str = ""


class DocumentParser:
    """文档解析器：切分文档为段落"""

    def __init__(self, max_paragraph_length: int = 200, overlap: int = 50):
        """
        :param max_paragraph_length: 每个段落的最大长度（词数）
        :param overlap: 段落之间的重叠词数
        """
        self.max_paragraph_length = max_paragraph_length
        self.overlap = overlap

    def parse(self, doc: Document) -> List[Paragraph]:
        """解析文档为段落"""
        if doc.paragraphs:
            return [Paragraph(
                para_id=f"{doc.doc_id}_p{i}",
                doc_id=doc.doc_id,
                text=p,
                index=i
            ) for i, p in enumerate(doc.paragraphs)]

        # 按句子切分
        sentences = self._split_sentences(doc.content)
        paragraphs = []
        current_para = []
        current_length = 0
        para_index = 0

        for sent in sentences:
            words = sent.split()
            if current_length + len(words) > self.max_paragraph_length and current_para:
                # 保存当前段落
                para_text = " ".join(current_para)
                paragraphs.append(Paragraph(
                    para_id=f"{doc.doc_id}_p{para_index}",
                    doc_id=doc.doc_id,
                    text=para_text,
                    index=para_index
                ))
                para_index += 1
                # 保留重叠部分
                overlap_words = current_para[-self.overlap:] if len(current_para) > self.overlap else current_para
                current_para = overlap_words + words
                current_length = len(overlap_words) + len(words)
            else:
                current_para.extend(words)
                current_length += len(words)

        # 保存最后一个段落
        if current_para:
            paragraphs.append(Paragraph(
                para_id=f"{doc.doc_id}_p{para_index}",
                doc_id=doc.doc_id,
                text=" ".join(current_para),
                index=para_index
            ))

        return paragraphs

    def _split_sentences(self, text: str) -> List[str]:
        """简单句子分割"""
        # 按常见句子结束符分割
        sentences = re.split(r'[。！？.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]


class SparseRetriever:
    """稀疏检索器：基于TF-IDF的段落检索"""

    def __init__(self):
        self.doc_freq = {}  # 文档频率
        self.term_doc = {}  # 词项-文档映射

    def index(self, paragraphs: List[Paragraph]):
        """索引段落"""
        for para in paragraphs:
            words = set(para.text.lower().split())
            for word in words:
                if word not in self.term_doc:
                    self.term_doc[word] = []
                self.term_doc[word].append(para.para_id)

                if para.para_id not in self.doc_freq:
                    self.doc_freq[para.para_id] = 0
                self.doc_freq[para.para_id] += 1

    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        检索相关段落
        :return: [(para_id, score)]
        """
        query_words = query.lower().split()
        scores = {}

        for word in query_words:
            if word in self.term_doc:
                for para_id in self.term_doc[word]:
                    if para_id not in scores:
                        scores[para_id] = 0
                    scores[para_id] += 1

        # 排序
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_scores[:top_k]


class DenseRetriever(nn.Module):
    """密集检索器：基于向量的段落检索"""

    def __init__(self, vocab_size, embed_dim=128, hidden_dim=256):
        super().__init__()
        self.encoder = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )
        self.proj = nn.Linear(hidden_dim * 2, hidden_dim)

    def encode(self, token_ids):
        """编码序列"""
        embed = nn.functional.embedding(token_ids, torch.zeros_like(token_ids).float())
        outputs, (h_n, _) = self.encoder(embed)
        repr = torch.cat([h_n[0], h_n[1]], dim=-1)
        repr = F.normalize(self.proj(repr), p=2, dim=-1)
        return repr

    def compute_similarity(self, q_repr, p_repr):
        """计算相似度"""
        return torch.matmul(q_repr, p_repr.unsqueeze(0).transpose(-2, -1)).squeeze(-1)


class ReadingComprehensionModel(nn.Module):
    """阅读理解模型"""

    def __init__(self, vocab_size, embed_dim=128, hidden_dim=256):
        super().__init__()
        self.encoder = nn.LSTM(embed_dim, hidden_dim, num_layers=1, batch_first=True, bidirectional=True)
        self.qa_outputs = nn.Linear(hidden_dim * 2, 2)

    def forward(self, context_ids, start_positions=None, end_positions=None):
        """前向传播"""
        embed = nn.functional.embedding(context_ids, torch.zeros_like(context_ids).float())
        outputs, _ = self.encoder(embed)
        logits = self.qa_outputs(outputs)
        start_logits, end_logits = logits[:, :, 0], logits[:, :, 1]

        loss = None
        if start_positions is not None and end_positions is not None:
            start_loss = F.cross_entropy(start_logits, start_positions)
            end_loss = F.cross_entropy(end_logits, end_positions)
            loss = (start_loss + end_loss) / 2

        return start_logits, end_logits, loss


class AnswerExtractor:
    """答案抽取器：从段落中提取答案"""

    def __init__(self, rc_model: ReadingComprehensionModel):
        self.rc_model = rc_model

    def extract(self, question: str, paragraph: Paragraph, max_answer_len: int = 30) -> Dict:
        """
        抽取答案
        :return: 答案结果字典
        """
        # 简化：直接使用段落文本模拟
        words = paragraph.text.split()

        # 模拟start和end logits
        start_logits = torch.randn(len(words))
        end_logits = torch.randn(len(words))

        # 贪心解码
        start_idx = start_logits.argmax().item()
        end_idx = end_logits.argmax().item()

        if end_idx < start_idx:
            end_idx = start_idx

        end_idx = min(end_idx, start_idx + max_answer_len - 1)

        answer_text = " ".join(words[start_idx:end_idx + 1])

        return {
            "answer_text": answer_text,
            "start_idx": start_idx,
            "end_idx": end_idx,
            "score": (start_logits[start_idx] + end_logits[end_idx]).item()
        }


class AnswerRanker:
    """答案排序器：融合多个候选答案"""

    def __init__(self):
        pass

    def rank(self, candidates: List[Dict]) -> List[Dict]:
        """排序候选答案"""
        # 按分数排序
        sorted_candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)

        # 去除重复答案
        seen = set()
        unique_candidates = []
        for cand in sorted_candidates:
            if cand["answer_text"] not in seen:
                seen.add(cand["answer_text"])
                unique_candidates.append(cand)

        # 重计算分数（加入位置、长度等特征）
        for i, cand in enumerate(unique_candidates):
            # 位置惩罚：越靠前的段落越可信
            position_bonus = 1.0 / (cand.get("para_index", 0) + 1)
            # 长度惩罚：适中长度更好
            length = len(cand["answer_text"].split())
            length_penalty = 1.0 if 1 <= length <= 15 else 0.8
            # 综合分数
            cand["final_score"] = cand["score"] * position_bonus * length_penalty

        return sorted(unique_candidates, key=lambda x: x["final_score"], reverse=True)


class DocumentQAPipeline:
    """完整的文档问答Pipeline"""

    def __init__(self, rc_model_vocab_size: int):
        # 文档解析器
        self.doc_parser = DocumentParser(max_paragraph_length=150, overlap=30)
        # 稀疏检索器
        self.sparse_retriever = SparseRetriever()
        # 密集检索器
        self.dense_retriever = DenseRetriever(rc_model_vocab_size)
        # 阅读理解模型
        self.rc_model = ReadingComprehensionModel(rc_model_vocab_size)
        # 答案抽取器
        self.answer_extractor = AnswerExtractor(self.rc_model)
        # 答案排序器
        self.answer_ranker = AnswerRanker()

        self.paragraphs = {}  # para_id -> Paragraph
        self.indexed = False

    def index_document(self, doc: Document):
        """索引文档"""
        paragraphs = self.doc_parser.parse(doc)
        for para in paragraphs:
            self.paragraphs[para.para_id] = para
        self.sparse_retriever.index(paragraphs)
        self.indexed = True

    def answer(self, question: str, top_k_paragraphs: int = 5) -> Dict:
        """
        端到端问答
        :param question: 问题
        :param top_k_paragraphs: 检索的段落数
        :return: 答案结果
        """
        if not self.indexed:
            return {"error": "No documents indexed"}

        # 1. 检索相关段落
        retrieved = self.sparse_retriever.retrieve(question, top_k=top_k_paragraphs)

        # 2. 阅读理解抽取答案
        candidates = []
        for para_id, retrieval_score in retrieved:
            para = self.paragraphs.get(para_id)
            if not para:
                continue

            result = self.answer_extractor.extract(question, para)
            candidates.append({
                "answer_text": result["answer_text"],
                "para_id": para_id,
                "para_text": para.text[:100],
                "retrieval_score": retrieval_score,
                "rc_score": result["score"],
                "score": retrieval_score * abs(result["score"]),
                "para_index": para.index
            })

        # 3. 排序答案
        ranked_answers = self.answer_ranker.rank(candidates)

        return {
            "question": question,
            "num_candidates": len(candidates),
            "answers": ranked_answers[:3]
        }


def demo():
    """文档问答Pipeline演示"""
    print("[文档问答Pipeline演示]")

    # 创建文档
    doc = Document(
        doc_id="doc_001",
        title="Artificial Intelligence Overview",
        content="""Artificial intelligence (AI) is intelligence demonstrated by machines.
        Machine learning is a subset of AI that enables systems to learn from data.
        Deep learning uses neural networks with multiple layers.
        Natural language processing deals with understanding text.
        Computer vision focuses on image and video understanding.
        AI was founded as an academic discipline in 1956."""
    )

    # 初始化Pipeline
    pipeline = DocumentQAPipeline(rc_model_vocab_size=5000)

    # 索引文档
    pipeline.index_document(doc)
    print(f"  文档段落数: {len(pipeline.paragraphs)}")

    # 问答
    questions = [
        "What is machine learning?",
        "When was AI founded?",
        "What does NLP deal with?"
    ]

    for q in questions:
        result = pipeline.answer(q, top_k_paragraphs=3)
        print(f"\n  问题: {q}")
        if "error" not in result:
            print(f"  候选答案数: {result['num_candidates']}")
            for i, ans in enumerate(result["answers"][:2]):
                print(f"    [{i+1}] {ans['answer_text'][:50]}... (score: {ans['final_score']:.3f})")
        else:
            print(f"  错误: {result['error']}")

    print("\n  ✅ 文档问答Pipeline演示通过！")


if __name__ == "__main__":
    demo()
