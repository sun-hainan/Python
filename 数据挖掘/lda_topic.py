# -*- coding: utf-8 -*-

"""

算法实现：数据挖掘 / lda_topic



本文件实现 lda_topic 相关的算法功能。

"""



import random

from typing import List, Dict, Tuple

import numpy as np





class LDAModel:

    """LDA主题模型"""



    def __init__(self, num_topics: int = 5, alpha: float = 0.1, beta: float = 0.01):

        """

        参数：

            num_topics: 主题数量

            alpha: 文档-主题Dirichlet先验

            beta: 主题-词Dirichlet先验

        """

        self.num_topics = num_topics

        self.alpha = alpha

        self.beta = beta



        self.vocab = []

        self.word_to_idx = {}

        self.documents = []



        # 统计量

        self.doc_topic_count = []  # 每个文档中每个主题的计数

        self.topic_word_count = []  # 每个主题中每个词的计数

        self.topic_total = []       # 每个主题的总词数



    def build_vocab(self, documents: List[List[str]]):

        """构建词汇表"""

        vocab_set = set()

        for doc in documents:

            vocab_set.update(doc)



        self.vocab = sorted(vocab_set)

        self.word_to_idx = {w: i for i, w in enumerate(self.vocab)}



    def fit(self, documents: List[List[str]], max_iter: int = 100):

        """

        训练LDA模型



        参数：

            documents: 分词后的文档列表

            max_iter: 最大迭代次数

        """

        self.documents = documents

        D = len(documents)

        V = len(self.vocab)



        # 初始化统计量

        self.doc_topic_count = [[0] * self.num_topics for _ in range(D)]

        self.topic_word_count = [[0] * V for _ in range(self.num_topics)]

        self.topic_total = [0] * self.num_topics



        # 随机初始化主题分配

        z = []  # z[d][n] = 文档d中第n个词的主题

        for d, doc in enumerate(documents):

            z_d = []

            for word in doc:

                if word in self.word_to_idx:

                    topic = random.randint(0, self.num_topics - 1)

                    z_d.append(topic)

                    w_idx = self.word_to_idx[word]

                    self.doc_topic_count[d][topic] += 1

                    self.topic_word_count[topic][w_idx] += 1

                    self.topic_total[topic] += 1

            z.append(z_d)



        # 吉布斯采样

        for iteration in range(max_iter):

            for d, doc in enumerate(documents):

                for n, word in enumerate(doc):

                    if word not in self.word_to_idx:

                        continue



                    topic = z[d][n]

                    w_idx = self.word_to_idx[word]



                    # 移除当前分配

                    self.doc_topic_count[d][topic] -= 1

                    self.topic_word_count[topic][w_idx] -= 1

                    self.topic_total[topic] -= 1



                    # 计算新主题的采样概率

                    probs = []

                    for k in range(self.num_topics):

                        # P(z=k | rest) ∝ (α + count(d,k)) * (β + count(k,w)) / (β*V + count(k,*))

                        p = (self.alpha + self.doc_topic_count[d][k]) * \

                            (self.beta + self.topic_word_count[k][w_idx]) / \

                            (self.beta * V + self.topic_total[k])

                        probs.append(p)



                    # 归一化

                    total = sum(probs)

                    probs = [p / total for p in probs]



                    # 采样新主题

                    new_topic = random.choices(range(self.num_topics), weights=probs)[0]

                    z[d][n] = new_topic



                    # 添加新分配

                    self.doc_topic_count[d][new_topic] += 1

                    self.topic_word_count[new_topic][w_idx] += 1

                    self.topic_total[new_topic] += 1



            if iteration % 20 == 0:

                print(f"  迭代 {iteration}/{max_iter}")



        return self



    def get_document_topics(self, doc_idx: int) -> Dict[int, float]:

        """获取文档的主题分布"""

        counts = self.doc_topic_count[doc_idx]

        total = sum(counts) + self.num_topics * self.alpha

        return {k: (self.alpha + counts[k]) / total

                for k in range(self.num_topics)}



    def get_topic_words(self, topic_idx: int, top_n: int = 10) -> List[Tuple[str, float]]:

        """获取某个主题的关键词"""

        counts = self.topic_word_count[topic_idx]

        total = self.topic_total[topic_idx] + len(self.vocab) * self.beta

        word_probs = [(self.vocab[i], (self.beta + counts[i]) / total)

                     for i in range(len(self.vocab))]

        word_probs.sort(key=lambda x: x[1], reverse=True)

        return word_probs[:top_n]





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== LDA主题模型测试 ===\n")



    # 简化文档

    documents = [

        "计算机 程序 设计 算法 数据 结构".split(),

        "金融 投资 银行 股票 市场".split(),

        "计算机 算法 人工智能 机器 学习".split(),

        "经济 政策 市场 投资 金融".split(),

        "人工智能 深度 学习 神经 网络".split(),

        "银行 存款 利率 金融 经济".split(),

    ]



    print(f"文档数: {len(documents)}")



    lda = LDAModel(num_topics=3, alpha=0.1, beta=0.01)

    lda.build_vocab(documents)

    lda.fit(documents, max_iter=50)



    print("\n主题词汇：")

    for k in range(3):

        words = lda.get_topic_words(k, top_n=5)

        print(f"  主题{k}: {[w[0] for w in words]}")



    print("\n文档主题分布：")

    for d, doc in enumerate(documents):

        topics = lda.get_document_topics(d)

        print(f"  文档{d} ({' '.join(doc[:3])}...): {topics}")



    print("\n说明：")

    print("  - LDA是无监督学习")

    print("  - 常用于：新闻分类、推荐系统、用户画像")

    print("  - 变分推断比吉布斯采样更快")

