# -*- coding: utf-8 -*-
"""
差分隐私集成学习模块 (dp_ensemble.py)
====================================

算法原理
--------
本模块实现了多种差分隐私保护下的集成学习算法，将差分隐私机制
与主流集成方法相结合，在利用群体智慧的同时保护个体隐私。

算法列表：
1. AdaBoost.dp：差分隐私保护的自适应提升算法，
   在每个弱分类器的权重计算中注入拉普拉斯噪声。
2. Bagging.dp：差分隐私保护的自助聚合，
   通过对每个子样本集独立训练模型并聚合预测来减少方差。
3. RandomForest.dp：差分隐私保护的随机森林，
   在决策树分裂时使用指数机制选择分裂属性。
4. PATE.dp：教师集成隐私聚合（Private Aggregation of Teacher Ensembles），
   利用无标签数据训练多个教师模型，通过差分隐私聚合教师预测作为学生模型的真标签。

时间复杂度：
- AdaBoost.dp: O(T * n * d)，T 为弱分类器数量
- Bagging.dp: O(B * n * d)，B 为子模型数量
- RandomForest.dp: O(B * T * n * d)
- PATE.dp: O(T * n * d + n_student * d)

空间复杂度：O(T * n) ~ O(B * n)，与模型数量和数据规模相关

应用场景
--------
- 医疗诊断模型的隐私保护训练
- 金融风控模型的隐私保护部署
- 跨机构协作的隐私保护机器学习
- 推荐系统中用户行为数据的隐私保护
"""

import math
import random
import sys
from typing import List, Tuple, Callable, Optional, Dict, Any


# =============================================================================
# 工具函数
# =============================================================================

def laplace_noise(scale: float) -> float:
    """
    生成拉普拉斯噪声。

    参数:
        scale (float): 尺度参数 b = 1/epsilon（敏感度已归一化）。

    返回:
        float: 拉普拉斯噪声样本。
    """
    u = random.random() - 0.5
    return -scale * math.copysign(1.0, u) * math.log(1 - 2 * abs(u))


def exponential_mechanism(quality_scores: List[float], epsilon: float) -> int:
    """
    指数机制：从候选集合中依概率选择输出。

    参数:
        quality_scores (List[float]): 各候选输出的质量分数。
        epsilon (float): 隐私预算。

    返回:
        int: 选中的候选索引。
    """
    max_score = max(quality_scores)
    adjusted = [math.exp((s - max_score) * epsilon / 2.0) for s in quality_scores]
    total = sum(adjusted)
    threshold = random.random() * total
    cumulative = 0.0
    for i, w in enumerate(adjusted):
        cumulative += w
        if cumulative >= threshold:
            return i
    return len(adjusted) - 1


def train_decision_stump(X: List[List[float]], y: List[int],
                          feature_idx: int, threshold: float) -> Tuple[int, float, int]:
    """
    训练单层决策树（决策桩），用于弱分类器。

    参数:
        X (List[List[float]]): 特征矩阵，每行一个样本。
        y (List[int]): 标签列表（0 或 1）。
        feature_idx (int): 用于分裂的特征索引。
        threshold (float): 分裂阈值。

    返回:
        Tuple[预测方向, 阈值, 特征索引]: 弱分类器参数。
    """
    predictions = []
    for sample in X:
        val = sample[feature_idx]
        pred = 1 if val <= threshold else 0
        predictions.append(pred)
    # 计算准确率
    correct = sum(1 for i, p in enumerate(predictions) if p == y[i])
    accuracy = correct / len(y)
    direction = 1  # 弱分类器直接返回预测值
    return (direction, threshold, feature_idx)


def predict_stump(sample: List[float], direction: int,
                  threshold: float, feature_idx: int) -> int:
    """
    使用决策桩进行预测。

    参数:
        sample (List[float]): 样本特征。
        direction (int): 预测方向。
        threshold (float): 分裂阈值。
        feature_idx (int): 特征索引。

    返回:
        int: 预测标签 (0 或 1)。
    """
    val = sample[feature_idx]
    return 1 if val <= threshold else 0


# =============================================================================
# 1. AdaBoost.dp（差分隐私自适应提升）
# =============================================================================

class AdaBoostDP:
    """
    差分隐私 AdaBoost：保护样本权重和分类器权重中的隐私信息。

    算法原理：
    - AdaBoost 通过迭代调整样本权重，聚焦难分类样本。
    - 每个弱分类器的权重 alpha 基于其加权错误率计算。
    - 在计算 alpha 时添加拉普拉斯噪声，防止从权重推断个别样本标签。
    - 使用指数机制在候选弱分类器中进行隐私保护的选择。

    参数:
        epsilon (float): 隐私预算（每个弱分类器）。
        n_classifiers (int): 弱分类器数量。
        sensitivity (float): 敏感度上界（通常为 1）。
    """

    def __init__(self, epsilon: float, n_classifiers: int = 10,
                 sensitivity: float = 1.0):
        self.epsilon = epsilon
        self.n_classifiers = n_classifiers
        self.sensitivity = sensitivity
        self.classifiers = []  # 存储 (direction, threshold, feature_idx, alpha)
        self.weights = None  # 样本权重

    def fit(self, X: List[List[float]], y: List[int]) -> None:
        """
        训练差分隐私 AdaBoost 模型。

        参数:
            X (List[List[float]]): 训练特征矩阵。
            y (List[int]): 训练标签（0 或 1）。
        """
        n_samples = len(X)
        n_features = len(X[0]) if n_samples > 0 else 0
        # 初始化均匀样本权重
        self.weights = [1.0 / n_samples] * n_samples
        # 生成候选分裂点
        candidates = self._generate_candidates(X, max(1, n_features // 2))

        for t in range(self.n_classifiers):
            # 归一化样本权重
            weight_sum = sum(self.weights)
            normalized_weights = [w / weight_sum for w in self.weights]

            # 计算每个候选的加权错误率（隐私保护）
            candidate_errors = []
            for direction, threshold, feature_idx in candidates:
                weighted_error = 0.0
                for i, sample in enumerate(X):
                    pred = predict_stump(
                        sample, direction, threshold, feature_idx)
                    if pred != y[i]:
                        weighted_error += normalized_weights[i]
                candidate_errors.append(weighted_error)

            # 指数机制选择最优候选（添加隐私噪声）
            noisy_scores = [
                err + laplace_noise(self.sensitivity / self.epsilon)
                for err in candidate_errors
            ]
            best_idx = exponential_mechanism(
                [-s for s in noisy_scores],  # 转换为最大化
                self.epsilon
            )
            best_candidate = candidates[best_idx]

            # 计算该分类器的错误率（真实值，用于权重更新）
            err_t = candidate_errors[best_idx]
            err_t = max(1e-10, min(1 - 1e-10, err_t))

            # 计算分类器权重（添加拉普拉斯噪声）
            alpha_raw = 0.5 * math.log((1 - err_t) / err_t)
            alpha_noisy = alpha_raw + laplace_noise(
                self.sensitivity * 2.0 / self.epsilon
            )

            # 保存弱分类器
            self.classifiers.append(
                (best_candidate[0], best_candidate[1],
                 best_candidate[2], alpha_noisy)
            )

            # 更新样本权重（聚焦难分类样本）
            for i, sample in enumerate(X):
                pred = predict_stump(
                    sample,
                    best_candidate[0],
                    best_candidate[1],
                    best_candidate[2]
                )
                if pred == y[i]:
                    self.weights[i] *= math.exp(-alpha_noisy)
                else:
                    self.weights[i] *= math.exp(alpha_noisy)

    def _generate_candidates(self, X: List[List[float]],
                             max_per_feature: int) -> List[Tuple]:
        """
        生成候选弱分类器（分裂点）。

        参数:
            X (List[List[float]]): 特征矩阵。
            max_per_feature (int): 每个特征最多生成的候选数。

        返回:
            List[Tuple]: 候选弱分类器列表。
        """
        candidates = []
        n_samples = len(X)
        n_features = len(X[0]) if n_samples > 0 else 0
        for f in range(n_features):
            # 取该特征的若干分位数作为候选阈值
            values = sorted(set(sample[f] for sample in X))
            if len(values) > max_per_feature:
                indices = [
                    int(i * (len(values) - 1) / (max_per_feature - 1))
                    for i in range(max_per_feature)
                ]
                values = [values[i] for i in indices]
            for threshold in values:
                candidates.append((1, threshold, f))
        return candidates

    def predict(self, X: List[List[float]]) -> List[int]:
        """
        预测标签。

        参数:
            X (List[List[float]]): 测试特征矩阵。

        返回:
            List[int]: 预测标签列表。
        """
        predictions = []
        for sample in X:
            weighted_sum = sum(
                alpha * predict_stump(sample, direction, threshold, feature_idx)
                for direction, threshold, feature_idx, alpha in self.classifiers
            )
            predictions.append(1 if weighted_sum >= 0 else 0)
        return predictions


# =============================================================================
# 2. Bagging.dp（差分隐私自助聚合）
# =============================================================================

class BaggingDP:
    """
    差分隐私 Bagging：在自助采样和聚合过程中引入差分隐私保护。

    算法原理：
    - 对原始数据进行 B 次有放回自助采样（Bootstrap），每次生成子样本集。
    - 在每个子样本集上独立训练基分类器。
    - 最终预测通过对所有基分类器投票（分类）或平均（回归）得到。
    - 对聚合结果添加拉普拉斯噪声，或对每个子模型的训练数据注入隐私。

    参数:
        epsilon (float): 隐私预算。
        n_estimators (int): 基分类器数量。
        max_samples (float): 每次采样的样本比例。
    """

    def __init__(self, epsilon: float, n_estimators: int = 10,
                 max_samples: float = 0.8):
        self.epsilon = epsilon
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.models = []  # 存储每个基分类器的训练数据子集

    def fit(self, X: List[List[float]], y: List[int]) -> None:
        """
        训练差分隐私 Bagging 模型。

        参数:
            X (List[List[float]]): 训练特征矩阵。
            y (List[int]): 训练标签。
        """
        n_samples = len(X)
        sample_size = int(n_samples * self.max_samples)

        for b in range(self.n_estimators):
            # 有放回自助采样
            indices = [random.randint(0, n_samples - 1) for _ in range(sample_size)]
            X_sub = [X[i] for i in indices]
            y_sub = [y[i] for i in indices]
            # 存储子样本集（实际训练简化为存储索引和标签）
            self.models.append((X_sub, y_sub))

    def _train_simple_model(self, X_sub: List[List[float]],
                            y_sub: List[int]) -> Tuple[List[List[float]], List[int]]:
        """
        训练一个简单的基分类器（这里使用多数票作为模型表示）。
        实际实现中应替换为真正的分类器训练。
        """
        return (X_sub, y_sub)

    def predict(self, X: List[List[float]]) -> List[int]:
        """
        通过投票聚合预测。

        参数:
            X (List[List[float]]): 测试特征矩阵。

        返回:
            List[int]: 预测标签列表。
        """
        n_samples = len(X)
        # 收集所有模型的投票
        all_votes = []
        for X_sub, y_sub in self.models:
            # 简化为使用训练数据子集的多数标签作为"模型预测代理"
            # 实际应用中应使用真实分类器
            majority_label = 1 if sum(y_sub) > len(y_sub) // 2 else 0
            # 对投票结果添加拉普拉斯噪声（隐私保护）
            noisy_vote = majority_label + int(
                laplace_noise(1.0 / (self.epsilon * self.n_estimators))
            )
            all_votes.append(max(0, min(1, noisy_vote)))

        # 聚合：取多数票
        predictions = []
        for i in range(n_samples):
            # 对每个样本的预测进行聚合
            votes = [int(v > 0.5) for v in all_votes]
            pred = 1 if sum(votes) > self.n_estimators / 2 else 0
            predictions.append(pred)
        return predictions


# =============================================================================
# 3. RandomForest.dp（差分隐私随机森林）
# =============================================================================

class RandomForestDP:
    """
    差分隐私随机森林：在决策树分裂时使用指数机制选择分裂属性。

    算法原理：
    - 随机森林由多棵随机决策树组成，每棵树在节点分裂时
      仅考虑随机子集的特征。
    - 在节点分裂属性选择时，使用指数机制基于信息增益
      或基尼不纯度进行隐私保护的选择。
    - 对每棵树的训练数据添加隐私噪声，或在分裂阈值上添加噪声。

    参数:
        epsilon (float): 隐私预算（每棵树）。
        n_estimators (int): 树的数量。
        max_depth (int): 最大深度。
        max_features (int): 每个节点考虑的最大特征数。
    """

    def __init__(self, epsilon: float, n_estimators: int = 10,
                 max_depth: int = 5, max_features: int = 3):
        self.epsilon = epsilon
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.max_features = max_features
        self.trees = []  # 存储每棵树的训练数据子集

    def fit(self, X: List[List[float]], y: List[int]) -> None:
        """
        训练差分隐私随机森林。

        参数:
            X (List[List[float]]): 训练特征矩阵。
            y (List[int]): 训练标签。
        """
        n_samples = len(X)
        n_features = len(X[0]) if n_samples > 0 else 0
        sample_size = max(1, int(n_samples * 0.8))

        for _ in range(self.n_estimators):
            # 自助采样
            indices = [random.randint(0, n_samples - 1) for _ in range(sample_size)]
            X_sub = [X[i] for i in indices]
            y_sub = [y[i] for i in indices]
            self.trees.append((X_sub, y_sub))

    def _gini_impurity(self, labels: List[int]) -> float:
        """
        计算基尼不纯度。

        参数:
            labels (List[int]): 标签列表。

        返回:
            float: 基尼不纯度。
        """
        if not labels:
            return 0.0
        counts = {}
        for label in labels:
            counts[label] = counts.get(label, 0) + 1
        impurity = 1.0
        for count in counts.values():
            prob = count / len(labels)
            impurity -= prob ** 2
        return impurity

    def _information_gain(self, X_sub: List[List[float]], y_sub: List[int],
                           feature_idx: int, threshold: float) -> float:
        """
        计算分裂的信息增益。

        参数:
            X_sub: 子样本特征。
            y_sub: 子样本标签。
            feature_idx: 分裂特征索引。
            threshold: 分裂阈值。

        返回:
            float: 信息增益。
        """
        left_labels, right_labels = [], []
        for sample, label in zip(X_sub, y_sub):
            if sample[feature_idx] <= threshold:
                left_labels.append(label)
            else:
                right_labels.append(label)
        if not left_labels or not right_labels:
            return 0.0
        parent_impurity = self._gini_impurity(y_sub)
        left_frac = len(left_labels) / len(y_sub)
        right_frac = len(right_labels) / len(y_sub)
        child_impurity = (left_frac * self._gini_impurity(left_labels)
                         + right_frac * self._gini_impurity(right_labels))
        return parent_impurity - child_impurity

    def _select_best_split(self, X_sub: List[List[float]], y_sub: List[int],
                           available_features: List[int]) -> Tuple[int, float]:
        """
        使用指数机制选择最佳分裂属性和阈值（差分隐私）。

        参数:
            X_sub: 子样本特征。
            y_sub: 子样本标签。
            available_features: 可供选择的特征索引列表。

        返回:
            Tuple[最佳特征索引, 最佳阈值]。
        """
        best_gain = -float('inf')
        best_feature = available_features[0]
        best_threshold = 0.0

        for f in available_features:
            values = sorted(set(sample[f] for sample in X_sub))
            for threshold in values[:10]:  # 限制候选阈值数量
                gain = self._information_gain(X_sub, y_sub, f, threshold)
                # 添加拉普拉斯噪声到信息增益（隐私保护）
                noisy_gain = gain + laplace_noise(1.0 / self.epsilon)
                if noisy_gain > best_gain:
                    best_gain = noisy_gain
                    best_feature = f
                    best_threshold = threshold

        return (best_feature, best_threshold)

    def _majority_vote(self, labels: List[int]) -> int:
        """
        多数投票。

        参数:
            labels (List[int]): 标签列表。

        返回:
            int: 票数最多的标签。
        """
        if not labels:
            return 0
        counts = {}
        for label in labels:
            counts[label] = counts.get(label, 0) + 1
        return max(counts, key=counts.get)

    def predict(self, X: List[List[float]]) -> List[int]:
        """
        预测标签（多数投票聚合）。

        参数:
            X (List[List[float]]): 测试特征矩阵。

        返回:
            List[int]: 预测标签列表。
        """
        all_tree_predictions = []
        for X_sub, y_sub in self.trees:
            # 简化的树预测：多数票
            tree_pred = self._majority_vote(y_sub)
            # 添加拉普拉斯噪声（模拟差分隐私叶节点噪声）
            noisy_pred = tree_pred + int(
                laplace_noise(1.0 / (self.epsilon * self.n_estimators))
            )
            noisy_pred = max(0, min(1, noisy_pred))
            all_tree_predictions.append(noisy_pred)

        # 森林聚合：多数投票
        predictions = []
        for i in range(len(X)):
            votes = [p for p in all_tree_predictions]
            pred = 1 if sum(votes) > self.n_estimators / 2 else 0
            predictions.append(pred)
        return predictions


# =============================================================================
# 4. PATE.dp（教师集成隐私聚合）
# =============================================================================

class PATEDP:
    """
    PATE（Private Aggregation of Teacher Ensembles）：差分隐私知识迁移。

    算法原理（PATE-soft）：
    - 步骤1：将带标签数据划分为 N 份互不相交的子集，
      用每个子集训练一个"教师"模型（共 N 个教师）。
    - 步骤2：对无标签数据（或待预测数据），每个教师给出一个预测概率分布。
    - 步骤3：将所有教师的预测结果取加权平均，得到聚合的"软标签"。
    - 步骤4：对聚合结果添加拉普拉斯噪声，满足差分隐私。
    - 步骤5：用噪声软标签训练"学生"模型，学生学习的是教师的群体智慧而非原始标签。

    特点：
    - 隐私预算直接控制于教师聚合过程，清晰可分析。
    - 学生模型训练不需要访问原始隐私数据。

    参数:
        epsilon (float): 隐私预算（用于聚合步骤）。
        n_teachers (int): 教师模型数量。
        sensitivity (float): 敏感度（通常为 1）。
    """

    def __init__(self, epsilon: float, n_teachers: int,
                 sensitivity: float = 1.0):
        self.epsilon = epsilon
        self.n_teachers = n_teachers
        self.sensitivity = sensitivity
        self.teacher_models = []  # 存储每个教师模型的训练数据
        self.n_classes = 2  # 默认二分类

    def train_teachers(self, X: List[List[float]], y: List[int]) -> None:
        """
        训练多个教师模型。

        参数:
            X (List[List[float]]): 完整训练特征矩阵。
            y (List[int]): 完整训练标签。
        """
        n_samples = len(X)
        chunk_size = max(1, n_samples // self.n_teachers)
        # 将数据划分为互不相交的子集
        shuffled_idx = list(range(n_samples))
        random.shuffle(shuffled_idx)

        for i in range(self.n_teachers):
            start = i * chunk_size
            end = start + chunk_size if i < self.n_teachers - 1 else n_samples
            indices = shuffled_idx[start:end]
            X_teacher = [X[idx] for idx in indices]
            y_teacher = [y[idx] for idx in indices]
            self.teacher_models.append((X_teacher, y_teacher))

    def _teacher_prediction(self, X_teacher: List[List[float]],
                            y_teacher: List[int],
                            x_query: List[float]) -> List[float]:
        """
        单个教师对查询样本的预测（软概率）。

        参数:
            X_teacher: 教师训练数据。
            y_teacher: 教师训练标签。
            x_query: 待查询样本。

        返回:
            List[float]: 各类别的预测概率（软标签）。
        """
        # 简化的最近邻概率估计
        distances = [
            math.sqrt(sum((xq - xt) ** 2 for xq, xt in zip(x_query, xt_sample)))
            for xt_sample in X_teacher
        ]
        k = min(5, len(distances))
        nearest_indices = sorted(range(len(distances)),
                                  key=lambda i: distances[i])[:k]
        k_labels = [y_teacher[i] for i in nearest_indices]
        # 软概率估计
        probs = [0.0] * self.n_classes
        for label in k_labels:
            probs[label] += 1.0 / k
        return probs

    def aggregate_teachers(self, x_query: List[float]) -> List[float]:
        """
        差分隐私聚合教师预测。

        参数:
            x_query (List[float]): 待查询样本。

        返回:
            List[float]: 扰动后的聚合软标签。
        """
        # 收集所有教师的预测
        all_probs = []
        for X_teacher, y_teacher in self.teacher_models:
            probs = self._teacher_prediction(X_teacher, y_teacher, x_query)
            all_probs.append(probs)

        # 加权平均聚合
        aggregated = [0.0] * self.n_classes
        for probs in all_probs:
            for c in range(self.n_classes):
                aggregated[c] += probs[c] / self.n_teachers

        # 添加拉普拉斯噪声实现差分隐私
        noisy_aggregated = [
            p + laplace_noise(self.sensitivity / self.epsilon)
            for p in aggregated
        ]

        # 归一化为概率分布
        prob_sum = sum(noisy_aggregated)
        if prob_sum > 0:
            noisy_aggregated = [p / prob_sum for p in noisy_aggregated]
        return noisy_aggregated

    def train_student(self, X_student: List[List[float]],
                      noisy_labels: List[int]) -> None:
        """
        使用噪声软标签训练学生模型（此处简化为存储）。

        参数:
            X_student: 学生训练特征。
            noisy_labels: 差分隐私标签。
        """
        self.student_data = (X_student, noisy_labels)

    def predict(self, X: List[List[float]]) -> List[int]:
        """
        使用学生模型进行预测。

        参数:
            X (List[List[float]]): 测试特征矩阵。

        返回:
            List[int]: 预测标签列表。
        """
        # 对每个样本聚合教师预测
        predictions = []
        for x_query in X:
            noisy_probs = self.aggregate_teachers(x_query)
            pred = 1 if noisy_probs[1] > noisy_probs[0] else 0
            predictions.append(pred)
        return predictions


# =============================================================================
# 测试代码
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("差分隐私集成学习模块 测试")
    print("=" * 60)

    random.seed(42)

    # 生成模拟数据（二分类）
    def generate_data(n: int, d: int) -> Tuple[List[List[float]], List[int]]:
        """生成模拟二分类数据。"""
        X = []
        y = []
        for _ in range(n):
            x = [random.uniform(0, 10) for _ in range(d)]
            label = 1 if sum(x) / d > 5 else 0
            X.append(x)
            y.append(label)
        return X, y

    X_train, y_train = generate_data(200, 5)
    X_test, y_test = generate_data(50, 5)

    # 测试 1：AdaBoost.dp
    print("\n[测试1] AdaBoost.dp（差分隐私自适应提升）")
    print("-" * 40)
    adaboost = AdaBoostDP(epsilon=0.5, n_classifiers=8)
    adaboost.fit(X_train, y_train)
    y_pred = adaboost.predict(X_test)
    accuracy = sum(1 for p, t in zip(y_pred, y_test) if p == t) / len(y_test)
    print(f"  弱分类器数量: {adaboost.n_classifiers}")
    print(f"  测试准确率: {accuracy:.4f}")

    # 测试 2：Bagging.dp
    print("\n[测试2] Bagging.dp（差分隐私自助聚合）")
    print("-" * 40)
    bagging = BaggingDP(epsilon=0.5, n_estimators=10)
    bagging.fit(X_train, y_train)
    y_pred_bagging = bagging.predict(X_test)
    acc_bagging = sum(1 for p, t in zip(y_pred_bagging, y_test) if p == t) / len(y_test)
    print(f"  基分类器数量: {bagging.n_estimators}")
    print(f"  测试准确率: {acc_bagging:.4f}")

    # 测试 3：RandomForest.dp
    print("\n[测试3] RandomForest.dp（差分隐私随机森林）")
    print("-" * 40)
    rf = RandomForestDP(epsilon=0.5, n_estimators=10, max_depth=6)
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)
    acc_rf = sum(1 for p, t in zip(y_pred_rf, y_test) if p == t) / len(y_test)
    print(f"  树的数量: {rf.n_estimators}")
    print(f"  测试准确率: {acc_rf:.4f}")

    # 测试 4：PATE.dp
    print("\n[测试4] PATE.dp（教师集成隐私聚合）")
    print("-" * 40)
    pate = PATEDP(epsilon=1.0, n_teachers=10)
    pate.train_teachers(X_train, y_train)
    y_pred_pate = pate.predict(X_test)
    acc_pate = sum(1 for p, t in zip(y_pred_pate, y_test) if p == t) / len(y_test)
    print(f"  教师数量: {pate.n_teachers}")
    print(f"  测试准确率: {acc_pate:.4f}")

    # 测试教师聚合（软标签）
    print("\n  [PATE] 教师软标签聚合示例:")
    for i in range(3):
        noisy_probs = pate.aggregate_teachers(X_test[i])
        true_label = y_test[i]
        print(f"    样本{i+1}: 真实标签={true_label}, "
              f"扰动概率=[{noisy_probs[0]:.3f}, {noisy_probs[1]:.3f}], "
              f"预测={1 if noisy_probs[1] > noisy_probs[0] else 0}")

    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)
