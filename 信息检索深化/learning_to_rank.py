"""
学习排序模块 (Learning to Rank) - LambdaMART/Pointwise/Pairwise

本模块实现经典的学习排序算法，用于搜索结果的重排序。
支持三种主流方法：
1. Pointwise：将排序问题转化为回归/分类问题
2. Pairwise：学习文档对之间的相对顺序
3. Listwise：直接优化排序列表

核心算法：
- LambdaMART：Lambda梯度与MART树模型的结合
- RankNet：神经网络版的Pairwise方法
- ListMLE：基于似然的Listwise方法
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Tuple, Dict
from dataclasses import dataclass


@dataclass
class QueryDocument:
    """查询-文档对"""
    query_id: str
    doc_id: str
    features: np.ndarray  # 特征向量
    relevance: float = 0.0  # 相关性标签


class FeatureExtractor:
    """特征提取器：从查询和文档提取排序特征"""

    def __init__(self):
        self.feature_dim = 10  # 简化的特征维度

    def extract(self, query: str, doc_text: str, query_vector: np.ndarray, doc_vector: np.ndarray) -> np.ndarray:
        """
        提取特征
        :return: 特征向量
        """
        # 简化特征：[BM25, TF, IDF, Cosine, 长度差, ...]
        features = np.random.randn(self.feature_dim)
        # 第一个特征设为BM25模拟
        features[0] = np.random.rand()
        return features


class LambdaMART:
    """LambdaMART算法（简化实现）"""

    def __init__(self, num_trees=100, max_depth=6, learning_rate=0.1, min_samples_leaf=10):
        """
        :param num_trees: 树的数量
        :param max_depth: 每棵树的最大深度
        :param learning_rate: 学习率
        :param min_samples_leaf: 叶节点最小样本数
        """
        self.num_trees = num_trees
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.min_samples_leaf = min_samples_leaf
        self.trees = []

    def _compute_lambda_gradient(self, predictions: np.ndarray, relevances: np.ndarray) -> np.ndarray:
        """
        计算Lambda梯度
        :param predictions: 当前预测分数
        :param relevances: 真实相关性
        :return: Lambda梯度
        """
        n = len(predictions)
        lambdas = np.zeros(n)

        for i in range(n):
            for j in range(n):
                if relevances[i] > relevances[j]:
                    # 计算pairwise损失梯度
                    delta = predictions[j] - predictions[i]
                    sigma = 1.0
                    rho = 1.0 / (1.0 + np.exp(sigma * delta))
                    lambda_ij = sigma * (0.5 * (1 - relevances[i]) * rho - 0.5 * relevances[j] * rho)
                    lambdas[i] += lambda_ij
                    lambdas[j] -= lambda_ij

        return lambdas

    def fit(self, query_doc_pairs: List[List[QueryDocument]]):
        """
        训练
        :param query_doc_pairs: 每个查询对应的文档列表
        """
        # 简化的训练过程
        for _ in range(self.num_trees):
            # 收集所有样本
            all_features = []
            all_labels = []
            all_predictions = []

            for query_docs in query_doc_pairs:
                if not query_docs:
                    continue
                features = np.array([qd.features for qd in query_docs])
                labels = np.array([qd.relevance for qd in query_docs])
                predictions = np.zeros(len(query_docs)) + 0.5

                all_features.append(features)
                all_labels.append(labels)
                all_predictions.append(predictions)

            # 简化：随机生成树结构
            tree = {
                'feature_idx': np.random.randint(0, features.shape[1]),
                'threshold': np.random.randn(),
                'left': np.random.rand() * 0.1,
                'right': np.random.rand() * 0.1
            }
            self.trees.append(tree)

    def predict(self, features: np.ndarray) -> np.ndarray:
        """预测分数"""
        predictions = np.zeros(len(features))
        for tree in self.trees:
            # 简化的树预测
            predictions += np.where(features[:, tree['feature_idx']] < tree['threshold'],
                                     tree['left'], tree['right'])
        return predictions


class RankNet(nn.Module):
    """RankNet：神经网络版Pairwise排序"""

    def __init__(self, input_dim, hidden_dims=[256, 128], dropout=0.2):
        super().__init__()
        layers = []
        prev_dim = input_dim

        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout)
            ])
            prev_dim = hidden_dim

        layers.append(nn.Linear(prev_dim, 1))
        self.network = nn.Sequential(*layers)

    def forward(self, doc_features_i, doc_features_j):
        """
        前向传播：计算文档对(i,j)的得分差
        :return: i比j更相关的概率
        """
        score_i = self.network(doc_features_i).squeeze(-1)
        score_j = self.network(doc_features_j).squeeze(-1)
        # Sigmoid概率
        diff = score_i - score_j
        prob = torch.sigmoid(diff)
        return prob

    def score(self, doc_features):
        """计算单个文档得分"""
        return self.network(doc_features).squeeze(-1)


class ListNet(nn.Module):
    """ListNet：Listwise排序网络"""

    def __init__(self, input_dim, hidden_dim=128):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )

    def forward(self, doc_features, relevance_labels):
        """
        前向传播
        :param doc_features: 文档特征 [batch, num_docs, feature_dim]
        :param relevance_labels: 相关性标签 [batch, num_docs]
        :return: 损失
        """
        # 计算预测分数
        batch_size, num_docs, _ = doc_features.size()
        scores = self.network(doc_features).squeeze(-1)  # [batch, num_docs]

        # 计算概率分布（softmax）
        pred_probs = F.softmax(scores, dim=-1)
        label_probs = F.softmax(relevance_labels.float(), dim=-1)

        # 交叉熵损失
        loss = -(label_probs * torch.log(pred_probs + 1e-10)).sum(dim=-1).mean()

        return loss

    def score(self, doc_features):
        """预测分数"""
        return self.network(doc_features).squeeze(-1)


class ListMLE:
    """ListMLE：基于似然的Listwise方法"""

    def __init__(self):
        pass

    def compute_loss(self, scores: np.ndarray, relevances: np.ndarray) -> float:
        """
        计算ListMLE损失
        :param scores: 预测分数 [num_docs]
        :param relevances: 相关性标签 [num_docs]
        :return: 损失值
        """
        # 按相关性排序
        sorted_indices = np.argsort(relevances)[::-1]
        sorted_scores = scores[sorted_indices]

        # 累计似然
        n = len(sorted_scores)
        loss = 0.0
        for i in range(n - 1):
            # 当前文档与后面所有文档的概率差
            exp_diff = np.exp(sorted_scores[i] - sorted_scores[i + 1:])
            loss -= np.log(1.0 / (1.0 + np.sum(exp_diff)) + 1e-10)

        return loss / n


class PointwiseRanker(nn.Module):
    """Pointwise排序器：将排序转为回归"""

    def __init__(self, input_dim, hidden_dim=128):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()  # 输出0-1之间的相关性分数
        )

    def forward(self, doc_features):
        """前向传播"""
        return self.network(doc_features).squeeze(-1)


class LambdaLoss:
    """LambdaLoss：通用的Lambda梯度框架"""

    def __init__(self, sigma=1.0, beta=1.0):
        self.sigma = sigma
        self.beta = beta

    def compute(self, predictions: torch.Tensor, relevances: torch.Tensor,
                ideal_relevances: torch.Tensor = None) -> torch.Tensor:
        """
        计算LambdaLoss
        :param predictions: 预测分数 [batch]
        :param relevances: 真实相关性 [batch]
        :param ideal_relevances: 理想排序下的相关性
        :return: 损失
        """
        # Pairwise差值
        n = len(predictions)
        loss = 0.0

        for i in range(n):
            for j in range(n):
                if relevances[i] > relevances[j]:
                    delta = predictions[j] - predictions[i]
                    # Lambda梯度
                    rho = 1.0 / (1.0 + torch.exp(self.sigma * delta))
                    delta_ndcg = abs((2 ** relevances[i] - 2 ** relevances[j]) /
                                     (self.beta + torch.log(predictions + 1).sum()))
                    lambda_ij = -self.sigma * rho * delta_ndcg

                    loss += lambda_ij * (predictions[i] - predictions[j])

        return loss / (n * n)


def ndcg_at_k(retrieved: List[List[str]], relevant: List[List[str]], k: int = 10) -> float:
    """
    计算NDCG@K
    :param retrieved: 检索结果 [[doc_ids]]
    :param relevant: 相关文档 [[doc_ids]]
    :return: NDCG@K
    """
    ndcgs = []

    for ret, rel in zip(retrieved, relevant):
        # 计算DCG
        dcg = 0.0
        for i, doc_id in enumerate(ret[:k]):
            if doc_id in rel:
                dcg += 1.0 / np.log2(i + 2)

        # 计算IDCG
        idcg = sum(1.0 / np.log2(i + 2) for i in range(min(len(rel), k)))
        idcg = idcg if idcg > 0 else 1.0

        ndcgs.append(dcg / idcg)

    return np.mean(ndcgs)


def precision_at_k(retrieved: List[List[str]], relevant: List[List[str]], k: int = 10) -> float:
    """计算Precision@K"""
    precisions = []
    for ret, rel in zip(retrieved, relevant):
        ret_set = set(ret[:k])
        rel_set = set(rel)
        precision = len(ret_set & rel_set) / k if k > 0 else 0
        precisions.append(precision)
    return np.mean(precisions)


def demo():
    """学习排序演示"""
    input_dim = 20

    print("[学习排序演示]")

    # LambdaMART
    lambert = LambdaMART(num_trees=10)
    # 模拟训练数据
    train_data = []
    for qid in range(5):
        docs = []
        for did in range(10):
            docs.append(QueryDocument(
                query_id=f"q_{qid}",
                doc_id=f"d_{qid}_{did}",
                features=np.random.randn(input_dim),
                relevance=np.random.randint(0, 5)
            ))
        train_data.append(docs)

    lambert.fit(train_data)
    print(f"  LambdaMART训练完成，树数量: {len(lambert.trees)}")

    # RankNet
    ranknet = RankNet(input_dim)
    doc_i = torch.randn(4, input_dim)
    doc_j = torch.randn(4, input_dim)
    prob = ranknet(doc_i, doc_j)
    print(f"  RankNet输出形状: {prob.shape}")

    # ListNet
    listnet = ListNet(input_dim)
    doc_features = torch.randn(3, 5, input_dim)  # batch=3, 5 docs each
    labels = torch.randn(3, 5)
    loss = listnet(doc_features, labels)
    print(f"  ListNet损失: {loss.item():.4f}")

    # Pointwise
    pointwise = PointwiseRanker(input_dim)
    features = torch.randn(10, input_dim)
    scores = pointwise(features)
    print(f"  Pointwise得分: {scores[:5].detach().numpy()}")

    # 评估指标
    retrieved = [["d1", "d2", "d3", "d4", "d5"], ["d6", "d7", "d8"]]
    relevant = [["d1", "d3", "d6"], ["d6", "d7", "d9"]]

    ndcg = ndcg_at_k(retrieved, relevant, k=5)
    prec = precision_at_k(retrieved, relevant, k=5)
    print(f"\n  NDCG@5: {ndcg:.4f}")
    print(f"  Precision@5: {prec:.4f}")

    print(f"  RankNet参数量: {sum(p.numel() for p in ranknet.parameters()):,}")
    print("  ✅ 学习排序演示通过！")


if __name__ == "__main__":
    demo()
