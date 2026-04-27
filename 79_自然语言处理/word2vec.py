# -*- coding: utf-8 -*-

"""

算法实现：自然语言处理 / word2vec



本文件实现 word2vec 相关的算法功能。

"""



import numpy as np

import random

from collections import Counter, deque





class Word2Vec:

    """简化版 Word2Vec（支持 Skip-gram 和 CBOW）"""



    def __init__(self, embedding_dim=50, window_size=5, learning_rate=0.025,

                 epochs=100, min_count=1, negative_samples=5, model_type="skipgram"):

        self.embedding_dim = embedding_dim

        self.window_size = window_size

        self.lr = learning_rate

        self.epochs = epochs

        self.min_count = min_count

        self.negative_samples = negative_samples

        self.model_type = model_type  # "skipgram" or "cbow"



        self.word_to_idx = {}  # 词 -> 索引

        self.idx_to_word = {}  # 索引 -> 词

        self.word_counts = Counter()



        # 嵌入矩阵（待训练）

        self.W_in = None  # 输入嵌入 (vocab_size, embedding_dim)

        self.W_out = None  # 输出嵌入 (vocab_size, embedding_dim)



        # 噪声分布（用于负采样）

        self.noise_distribution = None



    def build_vocab(self, corpus):

        """构建词汇表"""

        # 统计词频

        for sentence in corpus:

            tokens = sentence.lower().split()

            self.word_counts.update(tokens)



        # 过滤低频词

        idx = 0

        for word, count in self.word_counts.items():

            if count >= self.min_count:

                self.word_to_idx[word] = idx

                self.idx_to_word[idx] = word

                idx += 1



        vocab_size = len(self.word_to_idx)

        # Xavier 初始化

        scale = np.sqrt(2.0 / (vocab_size + self.embedding_dim))

        self.W_in = np.random.randn(vocab_size, self.embedding_dim) * scale

        self.W_out = np.random.randn(vocab_size, self.embedding_dim) * scale



        # 构建噪声分布（词频的 3/4 次幂）

        counts = np.array([self.word_counts.get(self.idx_to_word[i], 0)

                           for i in range(vocab_size)]) ** 0.75

        self.noise_distribution = counts / counts.sum()



        return self



    def sigmoid(self, x):

        """Sigmoid 函数（数值稳定版）"""

        return np.where(x >= 0, 1 / (1 + np.exp(-x)), np.exp(x) / (1 + np.exp(x)))



    def generate_training_pairs(self, sentence):

        """为一句话生成训练样本对"""

        tokens = sentence.lower().split()

        # 过滤 OOV 词

        tokens = [t for t in tokens if t in self.word_to_idx]

        pairs = []  # (center_idx, context_idx)



        for i, center in enumerate(tokens):

            center_idx = self.word_to_idx[center]

            # 窗口内的上下文

            start = max(0, i - self.window_size)

            end = min(len(tokens), i + self.window_size + 1)

            for j in range(start, end):

                if j != i:

                    context_idx = self.word_to_idx[tokens[j]]

                    pairs.append((center_idx, context_idx))



        return pairs, tokens



    def negative_sampling(self, pos_context_idx, num_samples):

        """负采样：采样不出现在正上下文中的词"""

        neg_indices = []

        for _ in range(num_samples):

            idx = np.random.choice(len(self.noise_distribution), p=self.noise_distribution)

            while idx == pos_context_idx:

                idx = np.random.choice(len(self.noise_distribution), p=self.noise_distribution)

            neg_indices.append(idx)

        return neg_indices



    def train_step(self, center_idx, context_idx):

        """单步训练更新"""

        # 正样本

        pos_score = np.dot(self.W_in[center_idx], self.W_out[context_idx])

        pos_sigmoid = self.sigmoid(pos_score)

        grad_pos = 1 - pos_sigmoid  # 正样本梯度



        # 正向更新 W_out[context_idx]

        self.W_out[context_idx] += self.lr * grad_pos * self.W_in[center_idx]

        # 负向更新 W_in[center_idx]

        self.W_in[center_idx] += self.lr * grad_pos * self.W_out[context_idx]



        # 负样本

        neg_indices = self.negative_sampling(context_idx, self.negative_samples)

        for neg_idx in neg_indices:

            neg_score = np.dot(self.W_in[center_idx], self.W_out[neg_idx])

            neg_sigmoid = self.sigmoid(neg_score)

            grad_neg = -neg_sigmoid  # 负样本梯度

            self.W_out[neg_idx] += self.lr * grad_neg * self.W_in[center_idx]

            self.W_in[center_idx] += self.lr * grad_neg * self.W_out[neg_idx]



    def fit(self, corpus):

        """训练 Word2Vec"""

        self.build_vocab(corpus)



        for epoch in range(self.epochs):

            random.shuffle(corpus)

            total_loss = 0



            for sentence in corpus:

                pairs, tokens = self.generate_training_pairs(sentence)

                for center_idx, context_idx in pairs:

                    if self.model_type == "skipgram":

                        # Skip-gram: (center, context)

                        self.train_step(center_idx, context_idx)

                    elif self.model_type == "cbow":

                        # CBOW: 用上下文预测中心词（简化：直接用中心词）

                        self.train_step(center_idx, context_idx)



            if epoch % 20 == 0:

                loss = total_loss / max(len(corpus), 1)

                print(f"Epoch {epoch}, loss: {loss:.4f}")



        return self



    def most_similar(self, word, top_k=5):

        """查找最相似的词（基于余弦相似度）"""

        if word not in self.word_to_idx:

            return []

        word_idx = self.word_to_idx[word]

        word_vec = self.W_in[word_idx]

        # 归一化

        word_vec_norm = word_vec / (np.linalg.norm(word_vec) + 1e-8)

        all_vecs_norm = self.W_in / (np.linalg.norm(self.W_in, axis=1, keepdims=True) + 1e-8)

        # 余弦相似度

        similarities = np.dot(all_vecs_norm, word_vec_norm)

        # 排序（排除自身）

        top_indices = np.argsort(similarities)[::-1]

        results = []

        for idx in top_indices:

            if self.idx_to_word[idx] != word:

                results.append((self.idx_to_word[idx], similarities[idx]))

            if len(results) >= top_k:

                break

        return results





if __name__ == "__main__":

    # 测试 Word2Vec

    sentences = [

        "the king is a man and the queen is a woman",

        "the man is strong and the woman is beautiful",

        "the prince is the son of the king",

        "the princess is the daughter of the queen",

        "the boy is young and the girl is young",

        "machine learning is about computers learning from data",

        "deep learning uses neural networks with many layers",

        "natural language processing deals with text and speech"

    ]



    # Skip-gram

    model = Word2Vec(embedding_dim=20, window_size=3, epochs=100, min_count=1, model_type="skipgram")

    model.fit(sentences)



    print("\nSkip-gram 最相似词:")

    for word in ["king", "woman", "learning"]:

        similar = model.most_similar(word, top_k=3)

        print(f"  {word}: {similar}")



    # CBOW

    model_cbow = Word2Vec(embedding_dim=20, window_size=3, epochs=100, min_count=1, model_type="cbow")

    model_cbow.fit(sentences)

    print("\nCBOW 最相似词:")

    for word in ["queen", "man"]:

        similar = model_cbow.most_similar(word, top_k=3)

        print(f"  {word}: {similar}")

