# -*- coding: utf-8 -*-
"""
算法实现：25_深度学习核心算法 / embedding_word2vec

本文件实现 embedding_word2vec 相关的算法功能。
"""

import numpy as np


# ============================
# Embedding层
# ============================

def embedding_forward(indices, embedding_table):
    """
    Embedding查表前馈传播
    
    参数:
        indices: 词索引 (batch_size, seq_len) 整数
        embedding_table: 嵌入表 (vocab_size, embedding_dim)
    返回:
        output: 嵌入向量 (batch_size, seq_len, embedding_dim)
    """
    batch_size, seq_len = indices.shape
    vocab_size, embedding_dim = embedding_table.shape
    
    # 将indices展平以便于查表
    indices_flat = indices.flatten()  # (batch_size * seq_len,)
    
    # 查表
    output_flat = embedding_table[indices_flat]  # (batch_size * seq_len, embedding_dim)
    
    # 恢复形状
    output = output_flat.reshape(batch_size, seq_len, embedding_dim)
    
    return output


def embedding_backward(dout, indices, vocab_size):
    """
    Embedding反向传播
    
    参数:
        dout: 输出梯度 (batch_size, seq_len, embedding_dim)
        indices: 输入索引
        vocab_size: 词汇表大小
    返回:
        d_embedding_table: 对嵌入表的梯度
    """
    batch_size, seq_len, embedding_dim = dout.shape
    
    # 展平
    dout_flat = dout.reshape(batch_size * seq_len, embedding_dim)
    indices_flat = indices.flatten()
    
    # 初始化梯度表
    d_embedding_table = np.zeros((vocab_size, embedding_dim))
    
    # 累加梯度（多个样本可能指向同一个词）
    np.add.at(d_embedding_table, indices_flat, dout_flat)
    
    return d_embedding_table


class Embedding:
    """
    Embedding层
    
    参数:
        vocab_size: 词汇表大小
        embedding_dim: 嵌入维度
    """
    
    def __init__(self, vocab_size, embedding_dim):
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        
        # Xavier初始化
        self.weight = np.random.randn(vocab_size, embedding_dim) * np.sqrt(2.0 / vocab_size)
        self.grad = np.zeros_like(self.weight)
        
        # 缓存
        self.indices_cache = None
        self.output_cache = None
    
    def forward(self, indices):
        """前馈传播"""
        self.indices_cache = indices
        self.output_cache = embedding_forward(indices, self.weight)
        return self.output_cache
    
    def backward(self, dout):
        """反向传播"""
        self.grad = embedding_backward(dout, self.indices_cache, self.vocab_size)
        return None  # embedding层对输入的梯度通常不计算


# ============================
# Word2Vec Skip-gram
# ============================

def sigmoid(x):
    """Sigmoid（数值稳定）"""
    return np.where(x >= 0, 
                    1 / (1 + np.exp(-x)), 
                    np.exp(x) / (1 + np.exp(x)))


def skip_gram_forward(center_word, context_words, center_embedding, context_embedding, 
                      neg_samples=None):
    """
    Skip-gram前馈传播
    
    参数:
        center_word: 中心词索引
        context_words: 上下文词索引列表
        center_embedding: 中心词嵌入 (embedding_dim,)
        context_embedding: 上下文词嵌入 (num_neg + 1, embedding_dim)
        neg_samples: 负采样索引
    返回:
        loss: 总损失
        pos_score: 正样本分数
        neg_scores: 负样本分数
    """
    # 正样本分数
    pos_score = np.dot(center_embedding, context_embedding[0])
    pos_prob = sigmoid(pos_score)
    pos_loss = -np.log(pos_prob + 1e-8)
    
    # 负样本分数
    neg_scores = np.dot(center_embedding, context_embedding[1:].T)
    neg_probs = sigmoid(-neg_scores)  # 目标是0
    neg_loss = -np.sum(np.log(neg_probs + 1e-8))
    
    return pos_loss + neg_loss, pos_score, neg_scores


class SkipGram:
    """
    Word2Vec Skip-gram模型
    
    参数:
        vocab_size: 词汇表大小
        embedding_dim: 嵌入维度
        neg_samples: 负采样数量
    """
    
    def __init__(self, vocab_size, embedding_dim, neg_samples=5):
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.neg_samples = neg_samples
        
        # 两个嵌入矩阵（input和output embedding）
        self.W_in = np.random.randn(vocab_size, embedding_dim) * 0.1
        self.W_out = np.random.randn(vocab_size, embedding_dim) * 0.1
    
    def sample_negatives(self, positive_word, num_samples):
        """
        负采样：排除正样本词
        
        参数:
            positive_word: 正样本词索引
            num_samples: 采样数量
        返回:
            neg_words: 负样本词索引
        """
        neg_words = []
        while len(neg_words) < num_samples:
            neg = np.random.randint(0, self.vocab_size)
            if neg != positive_word and neg not in neg_words:
                neg_words.append(neg)
        return np.array(neg_words)
    
    def forward(self, center_idx, context_idx):
        """
        前馈传播
        
        参数:
            center_idx: 中心词索引
            context_idx: 上下文词索引
        返回:
            loss: 损失
        """
        # 获取中心词嵌入
        center_emb = self.W_in[center_idx]
        
        # 获取正样本上下文嵌入
        pos_emb = self.W_out[context_idx]
        
        # 负采样
        neg_indices = self.sample_negatives(context_idx, self.neg_samples)
        neg_embs = self.W_out[neg_indices]
        
        # 正样本分数
        pos_score = np.dot(center_emb, pos_emb)
        pos_prob = sigmoid(pos_score)
        pos_loss = -np.log(pos_prob + 1e-8)
        
        # 负样本分数
        neg_scores = np.dot(center_emb, neg_embs.T)
        neg_probs = sigmoid(-neg_scores)
        neg_loss = -np.sum(np.log(neg_probs + 1e-8))
        
        return pos_loss + neg_loss, pos_score, neg_scores
    
    def backward(self, center_idx, context_idx, loss):
        """
        反向传播（简化版）
        
        参数:
            center_idx: 中心词索引
            context_idx: 上下文词索引
            loss: 损失值
        """
        # 简化的梯度更新
        lr = 0.01
        center_emb = self.W_in[center_idx]
        pos_emb = self.W_out[context_idx]
        
        # 正样本梯度
        grad = (1 - sigmoid(np.dot(center_emb, pos_emb))) * lr
        self.W_in[center_idx] -= grad * pos_emb
        self.W_out[context_idx] -= grad * center_emb


# ============================
# Word2Vec CBOW
# ============================

class CBOW:
    """
    Word2Vec CBOW（Continuous Bag of Words）模型
    通过上下文词预测中心词
    
    参数:
        vocab_size: 词汇表大小
        embedding_dim: 嵌入维度
        window_size: 窗口大小
        neg_samples: 负采样数量
    """
    
    def __init__(self, vocab_size, embedding_dim, window_size=2, neg_samples=5):
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.window_size = window_size
        self.neg_samples = neg_samples
        
        self.W_in = np.random.randn(vocab_size, embedding_dim) * 0.1
        self.W_out = np.random.randn(vocab_size, embedding_dim) * 0.1
    
    def get_context_embeddings(self, context_indices):
        """
        获取上下文词的嵌入并求和
        
        参数:
            context_indices: 上下文词索引列表
        返回:
            context_emb: 上下文嵌入向量 (embedding_dim,)
        """
        context_embs = self.W_in[context_indices]
        return np.sum(context_embs, axis=0)
    
    def sample_negatives(self, positive_word, num_samples):
        """负采样"""
        neg_words = []
        while len(neg_words) < num_samples:
            neg = np.random.randint(0, self.vocab_size)
            if neg != positive_word and neg not in neg_words:
                neg_words.append(neg)
        return np.array(neg_words)
    
    def forward(self, context_indices, center_idx):
        """
        CBOW前馈传播
        
        参数:
            context_indices: 上下文词索引列表
            center_idx: 中心词索引
        返回:
            loss: 损失
        """
        # 获取上下文嵌入（求和）
        context_emb = self.get_context_embeddings(context_indices)
        
        # 获取正样本中心词嵌入
        center_emb = self.W_out[center_idx]
        
        # 负采样
        neg_indices = self.sample_negatives(center_idx, self.neg_samples)
        neg_embs = self.W_out[neg_indices]
        
        # 计算损失
        pos_score = np.dot(context_emb, center_emb)
        pos_prob = sigmoid(pos_score)
        pos_loss = -np.log(pos_prob + 1e-8)
        
        neg_scores = np.dot(context_emb, neg_embs.T)
        neg_probs = sigmoid(-neg_scores)
        neg_loss = -np.sum(np.log(neg_probs + 1e-8))
        
        return pos_loss + neg_loss
    
    def get_embedding(self, word_idx):
        """获取词嵌入"""
        return self.W_in[word_idx]


# ============================
# 测试代码
# ============================

if __name__ == "__main__":
    np.random.seed(42)
    
    print("=" * 55)
    print("Embedding层和Word2Vec测试")
    print("=" * 55)
    
    vocab_size = 10000
    embedding_dim = 64
    batch_size = 32
    seq_len = 20
    
    # 测试1：Embedding层
    print("\n--- Embedding层测试 ---")
    emb_layer = Embedding(vocab_size, embedding_dim)
    
    # 模拟词索引
    indices = np.random.randint(0, vocab_size, size=(batch_size, seq_len))
    output = emb_layer.forward(indices)
    
    print(f"输入形状: {indices.shape}")
    print(f"输出形状: {output.shape}")
    print(f"嵌入表形状: {emb_layer.weight.shape}")
    
    # 反向传播
    dout = np.random.randn(batch_size, seq_len, embedding_dim)
    emb_layer.backward(dout)
    print(f"梯度形状: {emb_layer.grad.shape}")
    print(f"梯度非零元素比例: {np.mean(emb_layer.grad != 0):.2%}")
    
    # 测试2：Skip-gram
    print("\n--- Skip-gram模型测试 ---")
    skipgram = SkipGram(vocab_size=1000, embedding_dim=32, neg_samples=5)
    
    # 模拟训练数据
    center_word = 100
    context_word = 250
    
    # 前馈
    loss, pos_score, neg_scores = skipgram.forward(center_word, context_word)
    
    print(f"中心词索引: {center_word}")
    print(f"上下文词索引: {context_word}")
    print(f"损失: {loss:.4f}")
    print(f"正样本分数: {pos_score:.4f}")
    print(f"负样本分数范围: [{neg_scores.min():.4f}, {neg_scores.max():.4f}]")
    
    # 测试3：CBOW
    print("\n--- CBOW模型测试 ---")
    cbow = CBOW(vocab_size=1000, embedding_dim=32, window_size=2, neg_samples=5)
    
    # 模拟上下文和中心词
    context_words = [50, 75, 300, 400]  # 4个上下文词
    center_word = 250
    
    loss_cbow = cbow.forward(context_words, center_word)
    
    print(f"上下文词索引: {context_words}")
    print(f"中心词索引: {center_word}")
    print(f"CBOW损失: {loss_cbow:.4f}")
    
    # 测试4：词嵌入相似度
    print("\n--- 词嵌入相似度测试 ---")
    skipgram2 = SkipGram(vocab_size=100, embedding_dim=16, neg_samples=3)
    
    # 测试几个词的相似度
    test_pairs = [(0, 1), (0, 2), (10, 20)]
    print(f"{'词对':>10} | {'余弦相似度':>12}")
    print("-" * 25)
    
    for w1, w2 in test_pairs:
        e1 = skipgram2.W_in[w1]
        e2 = skipgram2.W_in[w2]
        cosine_sim = np.dot(e1, e2) / (np.linalg.norm(e1) * np.linalg.norm(e2) + 1e-8)
        print(f"({w1:3d}, {w2:3d}) | {cosine_sim:12.4f}")
    
    # 测试5：Skip-gram训练模拟
    print("\n--- Skip-gram训练模拟 ---")
    skipgram3 = SkipGram(vocab_size=500, embedding_dim=16, neg_samples=5)
    
    initial_emb = skipgram3.W_in[10].copy()
    
    # 模拟几个训练步骤
    losses = []
    for epoch in range(100):
        # 随机采样一对词
        center = np.random.randint(0, 500)
        context = np.random.randint(0, 500)
        if center != context:
            loss, _, _ = skipgram3.forward(center, context)
            skipgram3.backward(center, context, loss)
            losses.append(loss)
    
    print(f"训练100步后的平均损失: {np.mean(losses):.4f}")
    print(f"训练后词10的嵌入变化: {np.linalg.norm(skipgram3.W_in[10] - initial_emb):.4f}")
    
    print("\nEmbedding层和Word2Vec测试完成！")
