# -*- coding: utf-8 -*-
"""
算法实现：自然语言处理 / text_summarization

本文件实现 text_summarization 相关的算法功能。
"""

import numpy as np
import re


class TextRankSummarizer:
    """TextRank 文本摘要器（抽取式）"""

    def __init__(self, damping=0.85, max_iter=100, convergence_threshold=1e-5):
        """
        damping: PageRank 的阻尼系数 γ
        max_iter: 最大迭代次数
        convergence_threshold: 收敛阈值
        """
        self.damping = damping
        self.max_iter = max_iter
        self.threshold = convergence_threshold

    def preprocess(self, text):
        """分句和预处理"""
        # 按句子分割（中文用 。！？，英文用 .!?）
        sentences_en = re.split(r'(?<=[.!?])\s+', text)
        sentences_cn = re.split(r'(?<=[。！？])\s*', text)
        # 合并处理
        sentences = [s.strip() for s in sentences_en if len(s.strip()) > 5]
        return sentences

    def tokenize(self, text):
        """简单分词（可替换为 jieba 等）"""
        # 简单按空格/标点分词
        tokens = re.findall(r'[\w]+', text.lower())
        return set(tokens)

    def sentence_similarity(self, sent1_tokens, sent2_tokens):
        """计算两个句子集合的相似度（基于词重叠）"""
        if not sent1_tokens or not sent2_tokens:
            return 0.0
        intersection = len(sent1_tokens & sent2_tokens)
        # Jaccard 相似度
        union = len(sent1_tokens | sent2_tokens)
        return intersection / union if union > 0 else 0.0

    def build_similarity_matrix(self, sentences):
        """构建句子相似度矩阵"""
        n = len(sentences)
        # 分词
        tokenized = [self.tokenize(s) for s in sentences]
        # 计算全连接相似度
        sim_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(i + 1, n):
                sim = self.sentence_similarity(tokenized[i], tokenized[j])
                sim_matrix[i][j] = sim
                sim_matrix[j][i] = sim
        return sim_matrix

    def pagerank(self, sim_matrix):
        """PageRank 算法计算句子权重"""
        n = sim_matrix.shape[0]
        # 归一化：将每列归一化为概率矩阵（按行归一化更合理）
        # 实际 TextRank: 每行求和归一化
        row_sums = sim_matrix.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1  # 避免除零
        P = sim_matrix / row_sums  # 行归一化

        # PageRank: PR = (1-d)/n + d * P^T * PR
        pr = np.ones(n) / n  # 初始均匀分布
        for iteration in range(self.max_iter):
            new_pr = (1 - self.damping) / n + self.damping * P.T @ pr
            diff = np.linalg.norm(new_pr - pr, 1)
            pr = new_pr
            if diff < self.threshold:
                break

        return pr

    def summarize(self, text, top_k=3, as_sentences=False):
        """生成摘要
        text: 原始文本
        top_k: 选取的句子数
        as_sentences: True=返回句子列表，False=返回拼接字符串
        """
        sentences = self.preprocess(text)
        if len(sentences) <= top_k:
            return " ".join(sentences) if not as_sentences else sentences

        # 构建相似度矩阵
        sim_matrix = self.build_similarity_matrix(sentences)
        # 计算 PageRank 得分
        scores = self.pagerank(sim_matrix)
        # 选取 top_k
        top_indices = np.argsort(scores)[::-1][:top_k]
        # 按原文顺序排列
        top_indices = sorted(top_indices)
        selected = [sentences[i] for i in top_indices]

        return " ".join(selected) if not as_sentences else selected

    def extract_keyword(self, text, top_k=5):
        """提取关键词（基于词在重要句子中的出现频率）"""
        sentences = self.preprocess(text)
        tokenized = [self.tokenize(s) for s in sentences]
        # 相似度矩阵
        sim_matrix = self.build_similarity_matrix(sentences)
        scores = self.pagerank(sim_matrix)
        # 统计词的加权频率（按句子 PageRank 加权）
        word_scores = {}
        for sent_tokens, score in zip(tokenized, scores):
            for word in sent_tokens:
                if len(word) > 1:  # 忽略单字
                    word_scores[word] = word_scores.get(word, 0) + score
        # 排序
        sorted_words = sorted(word_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_words[:top_k]


if __name__ == "__main__":
    # 测试 TextRank
    article = """
    深度学习是机器学习的一个分支，它使用含有多层神经元的人工神经网络来进行学习和表示。
    深度学习在计算机视觉、自然语言处理、语音识别等领域取得了突破性的进展。
    卷积神经网络是深度学习中最重要的模型之一，它在图像分类任务中表现优异。
    循环神经网络则擅长处理序列数据，如文本和时间序列。
    Transformer 架构是近年来最成功的深度学习模型，它通过自注意力机制实现了并行计算。
    BERT 和 GPT 是基于 Transformer 的大规模预训练语言模型。
    强化学习与深度学习结合产生了深度强化学习，在游戏和机器人控制等领域取得了惊人的成果。
    迁移学习可以将一个任务上学到的知识应用到另一个相关任务上，大大减少了训练数据的需求。
    """

    summarizer = TextRankSummarizer(damping=0.85)
    summary = summarizer.summarize(article, top_k=3)
    print("原文摘要（TextRank）:")
    print(f"  {summary}")
    print(f"\n关键词: {summarizer.extract_keyword(article, top_k=5)}")
