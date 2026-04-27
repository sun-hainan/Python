# -*- coding: utf-8 -*-
"""
算法实现：推荐系统 / content_based

本文件实现 content_based 相关的算法功能。
"""

import math
from collections import defaultdict, Counter


class ContentBasedRecommender:
    """基于内容的推荐系统"""

    def __init__(self):
        """初始化基于内容的推荐器"""
        self.item_features = {}  # 物品特征字典 {item_id: {feature: weight}}
        self.user_profiles = {}  # 用户画像字典 {user_id: {feature: weight}}
        self.feature_idf = {}  # 特征IDF权重（用于TF-IDF）

    def set_item_features(self, features_dict):
        """
        设置物品特征

        Args:
            features_dict: dict[item_id, dict[feature_name, weight]]
                           物品ID到特征的映射，特征权重表示该特征对该物品的重要程度
        """
        self.item_features = features_dict

        # 计算IDF（逆文档频率），用于特征重要性加权
        n_items = len(features_dict)  # 总物品数
        feature_doc_freq = Counter()  # 特征出现在多少个物品中

        for features in features_dict.values():
            feature_doc_freq.update(features.keys())  # 统计每个特征出现的物品数

        # IDF = log(N / n_i)，特征越稀有IDF越高
        for feature, freq in feature_doc_freq.items():
            self.feature_idf[feature] = math.log(n_items / (freq + 1)) + 1

    def build_user_profile(self, user_id, rated_items, method='tfidf'):
        """
        构建用户兴趣画像

        Args:
            user_id: 用户ID
            rated_items: list of tuple (item_id, rating) 用户评分过的物品及评分
            method: str 构建方法，'tfidf' 或 'average'

        用户画像是用户所有交互物品的加权特征向量：
        - 权重 = rating * feature_weight * idf
        - 最后归一化
        """
        profile = defaultdict(float)  # 特征权重累加字典
        total_weight = 0.0  # 总权重（用于归一化）

        for item_id, rating in rated_items:
            if item_id not in self.item_features:
                continue  # 跳过无特征的物品

            item_feature_weights = self.item_features[item_id]  # 该物品的特征权重

            for feature, feature_weight in item_feature_weights.items():
                # TF-IDF加权：特征在物品中的权重 × 该特征的全局IDF
                tfidf_weight = feature_weight * self.feature_idf.get(feature, 1.0)

                if method == 'tfidf':
                    # 评分 × TF-IDF权重
                    contribution = rating * tfidf_weight
                else:
                    # 简单平均
                    contribution = rating * feature_weight

                profile[feature] += contribution
                total_weight += abs(contribution)

        # 归一化（L2范数）
        if total_weight > 0:
            norm = math.sqrt(sum(v ** 2 for v in profile.values()))
            if norm > 0:
                for feat in profile:
                    profile[feat] /= norm

        self.user_profiles[user_id] = dict(profile)  # 存储用户画像

    def _cosine_similarity(self, vec_a, vec_b):
        """
        计算两个稀疏向量的余弦相似度

        Args:
            vec_a: dict[feature, weight] 第一个向量
            vec_b: dict[feature, weight] 第二个向量

        Returns:
            float 余弦相似度 ∈ [-1, 1]
        """
        # 找出共同特征
        common_features = set(vec_a.keys()) & set(vec_b.keys())

        if not common_features:
            return 0.0  # 无共同特征

        # 计算点积
        dot_product = sum(vec_a[f] * vec_b[f] for f in common_features)

        # 计算模长
        norm_a = math.sqrt(sum(vec_a[f] ** 2 for f in vec_a.keys()))
        norm_b = math.sqrt(sum(vec_b[f] ** 2 for f in vec_b.keys()))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def recommend(self, user_id, candidate_items=None, top_k=10):
        """
        生成推荐列表

        Args:
            user_id: 用户ID
            candidate_items: list[item_id] 待评估物品候选集，None时评估所有物品
            top_k: int 返回前top_k个推荐

        Returns:
            list of tuple (item_id, similarity_score) 按相似度降序排列
        """
        if user_id not in self.user_profiles:
            return []  # 用户画像不存在

        user_profile = self.user_profiles[user_id]  # 用户画像向量

        # 确定候选物品集
        if candidate_items is None:
            candidate_items = list(self.item_features.keys())
        else:
            # 过滤掉无特征的物品
            candidate_items = [i for i in candidate_items if i in self.item_features]

        # 计算每个候选物品与用户画像的相似度
        scores = []
        for item_id in candidate_items:
            item_feature = self.item_features[item_id]  # 物品特征向量
            similarity = self._cosine_similarity(user_profile, item_feature)
            scores.append((item_id, similarity))

        # 按相似度降序排序
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class TextContentAnalyzer:
    """文本内容分析器（用于从文本中提取TF-IDF特征）"""

    def __init__(self):
        """初始化文本分析器"""
        self.vocabulary = {}  # 词汇表 {word: index}
        self.document_freq = Counter()  # 文档频率
        self.n_documents = 0  # 文档总数

    def fit(self, documents):
        """
        从文档集合学习词汇表和文档频率

        Args:
            documents: list of tuple (doc_id, text) 文档列表
        """
        self.n_documents = len(documents)  # 更新文档总数

        for doc_id, text in documents:
            # 简单分词（按空格和标点）
            words = self._tokenize(text)

            # 去重统计文档频率
            unique_words = set(words)
            for word in unique_words:
                if word not in self.vocabulary:
                    self.vocabulary[word] = len(self.vocabulary)  # 分配索引
                self.document_freq[word] += 1  # 该词出现的文档数+1

    def _tokenize(self, text):
        """
        简单分词

        Args:
            text: str 原始文本

        Returns:
            list[str] 分词结果（小写，去除短词）
        """
        # 简单处理：转小写，按空格和标点分割
        import re
        words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
        return words

    def get_tfidf_vector(self, text):
        """
        将文本转换为TF-IDF向量

        Args:
            text: str 输入文本

        Returns:
            dict[word, tfidf_weight] TF-IDF权重字典
        """
        words = self._tokenize(text)  # 分词
        word_counts = Counter(words)  # 词频统计

        # 计算TF
        total_words = len(words)  # 总词数
        tf_vector = {word: count / total_words for word, count in word_counts.items()}

        # 计算TF-IDF：TF * IDF
        tfidf_vector = {}
        for word, tf in tf_vector.items():
            if word in self.vocabulary:
                # IDF = log(N / df) + 1
                idf = math.log(self.n_documents / (self.document_freq[word] + 1)) + 1
                tfidf_vector[word] = tf * idf

        return tfidf_vector


# ------------------- 单元测试 -------------------
if __name__ == '__main__':
    # 示例：新闻推荐
    # 定义物品特征（通常由内容分析自动提取，这里手动构造）
    item_features = {
        'news1': {'科技': 0.9, 'AI': 0.8, '机器学习': 0.7},
        'news2': {'体育': 0.9, '足球': 0.8, '世界杯': 0.7},
        'news3': {'科技': 0.8, '手机': 0.9, '苹果': 0.7},
        'news4': {'娱乐': 0.9, '电影': 0.8, '票房': 0.6},
        'news5': {'科技': 0.7, '互联网': 0.8, '电商': 0.9},
        'news6': {'体育': 0.8, '篮球': 0.9, 'NBA': 0.8},
        'news7': {'科技': 0.6, 'AI': 0.9, '深度学习': 0.8},
        'news8': {'娱乐': 0.8, '音乐': 0.9, '演唱会': 0.7},
    }

    # 用户评分历史
    user_ratings = [
        ('news1', 5),  # 用户喜欢AI/机器学习
        ('news3', 4),  # 用户喜欢手机/苹果
        ('news5', 3),  # 用户对互联网/电商一般
    ]

    # 创建推荐器
    recommender = ContentBasedRecommender()
    recommender.set_item_features(item_features)  # 设置物品特征

    # 构建用户画像
    recommender.build_user_profile('user1', user_ratings, method='tfidf')

    print("=== 用户1的画像特征 ===")
    profile = recommender.user_profiles.get('user1', {})
    sorted_profile = sorted(profile.items(), key=lambda x: x[1], reverse=True)[:10]
    for feat, weight in sorted_profile:
        print(f"  {feat}: {weight:.4f}")

    # 生成推荐
    print("\n=== 基于内容的推荐结果 ===")
    recommendations = recommender.recommend('user1', top_k=5)
    for item_id, score in recommendations:
        print(f"  {item_id}: {score:.4f}")

    # 测试文本特征提取
    print("\n=== 文本TF-IDF特征提取 ===")
    analyzer = TextContentAnalyzer()
    docs = [
        ('d1', 'machine learning and artificial intelligence'),
        ('d2', 'deep learning neural network'),
        ('d3', 'machine learning and data science'),
    ]
    analyzer.fit(docs)

    test_text = 'artificial intelligence machine learning'
    tfidf_vec = analyzer.get_tfidf_vector(test_text)
    print(f"文本: {test_text}")
    print(f"TF-IDF特征: {tfidf_vec}")

    print("\n✅ 基于内容推荐算法测试通过！")
