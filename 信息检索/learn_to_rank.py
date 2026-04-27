# -*- coding: utf-8 -*-

"""

算法实现：信息检索 / learn_to_rank



本文件实现 learn_to_rank 相关的算法功能。

"""



import random

from typing import List, Dict, Tuple





class PointwiseLTR:

    """Pointwise排序"""



    def __init__(self, features: List[str]):

        self.features = features

        self.weights = {f: random.uniform(-0.5, 0.5) for f in features}

        self.bias = random.uniform(-0.1, 0.1)



    def predict_score(self, doc_features: Dict[str, float]) -> float:

        """预测文档得分"""

        score = self.bias

        for feature in self.features:

            if feature in doc_features:

                score += self.weights[feature] * doc_features[feature]

        return score



    def rank(self, documents: List[Dict]) -> List[int]:

        """

        对文档排序



        参数：

            documents: [{'features': {...}, 'label': relevance}, ...]



        返回：排序后的文档索引

        """

        scored_docs = []

        for i, doc in enumerate(documents):

            score = self.predict_score(doc['features'])

            scored_docs.append((i, score, doc.get('label', 0)))



        # 按得分降序

        scored_docs.sort(key=lambda x: x[1], reverse=True)

        return [idx for idx, _, _ in scored_docs]





class PairwiseLTR:

    """Pairwise排序（RankNet风格）"""



    def __init__(self, features: List[str], learning_rate: float = 0.01):

        self.features = features

        self.weights = {f: 0.0 for f in features}

        self.bias = 0.0

        self.lr = learning_rate



    def sigmoid(self, x: float) -> float:

        """Sigmoid函数"""

        return 1.0 / (1.0 + 2.71828 ** (-x))



    def train(self, doc_pairs: List[Tuple[Dict, Dict, int]]):

        """

        训练



        参数：

            doc_pairs: [(doc1_features, doc2_features, label), ...]

                       label=1表示doc1应该排在doc2前面

        """

        for doc1_feat, doc2_feat, label in doc_pairs:

            # 计算分数

            s1 = sum(self.weights[f] * doc1_feat.get(f, 0) for f in self.features)

            s2 = sum(self.weights[f] * doc2_feat.get(f, 0) for f in self.features)



            # 计算概率

            prob = self.sigmoid(s1 - s2)



            # 梯度更新

            for f in self.features:

                grad = (label - prob) * (doc1_feat.get(f, 0) - doc2_feat.get(f, 0))

                self.weights[f] += self.lr * grad





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== Learning to Rank测试 ===\n")



    # 特征列表

    features = ["tfidf_score", "page_rank", "recency", "popularity"]



    # 训练数据

    train_data = [

        {'features': {"tfidf": 0.8, "page_rank": 0.6, "recency": 0.9, "popularity": 0.5}},

        {'features': {"tfidf": 0.3, "page_rank": 0.8, "recency": 0.2, "popularity": 0.7}},

    ]



    # Pointwise

    ltr = PointwiseLTR(features)



    print("Pointwise排序：")

    scores = [(i, ltr.predict_score(d['features'])) for i, d in enumerate(train_data)]

    scores.sort(key=lambda x: x[1], reverse=True)

    print(f"  排序结果: {[idx for idx, _ in scores]}")



    # Pairwise训练

    pairs = [

        ({"tfidf": 0.8}, {"tfidf": 0.3}, 1),

        ({"popularity": 0.7}, {"popularity": 0.5}, 1),

    ]



    ltr2 = PairwiseLTR(features)

    ltr2.train(pairs)



    print("\n训练后的权重：")

    for f, w in ltr2.weights.items():

        print(f"  {f}: {w:.3f}")



    print("\n说明：")

    print("  - Pointwise：简单但忽略文档对关系")

    print("  - Pairwise：常用，LambdaMART是代表")

    print("  - Listwise：直接优化NDCG，效果最好但最复杂")

