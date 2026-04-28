"""
朴素贝叶斯分类器实现
Naive Bayes Classifier Implementation

朴素贝叶斯是基于贝叶斯定理的生成分类器，假设特征条件独立。
包含高斯朴素贝叶斯、多项朴素贝叶斯、伯努利朴素贝叶斯三种常见变体。
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import math


class GaussianNaiveBayes:
    """
    高斯朴素贝叶斯
    
    假设每个类别的特征服从独立高斯分布：
    P(x|y) = ∏_j N(x_j | mu_{yj}, sigma^2_{yj})
    
    参数:
        alpha: 拉普拉斯平滑参数
    """
    
    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha  # 平滑参数
        self.classes = None  # 类别列表
        self.n_classes = 0  # 类别数量
        self.n_features = 0  # 特征数量
        self.class_prior = None  # 类先验 P(y)
        self.theta = None  # 每个类别的特征均值
        self.var = None  # 每个类别的特征方差
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'GaussianNaiveBayes':
        """
        训练高斯朴素贝叶斯
        
        参数:
            X: 训练数据 (n_samples, n_features)
            y: 标签 (n_samples,)
            
        返回:
            self
        """
        X = np.array(X)
        y = np.array(y)
        
        self.n_features = X.shape[1]
        self.classes = np.unique(y)
        self.n_classes = len(self.classes)
        
        # 初始化参数
        self.class_prior = np.zeros(self.n_classes)
        self.theta = np.zeros((self.n_classes, self.n_features))
        self.var = np.zeros((self.n_classes, self.n_features))
        
        for i, c in enumerate(self.classes):
            # 该类别的样本
            X_c = X[y == c]
            
            # 类先验（加上平滑）
            self.class_prior[i] = (len(X_c) + self.alpha) / (len(y) + self.n_classes * self.alpha)
            
            # 均值
            self.theta[i] = np.mean(X_c, axis=0)
            
            # 方差（加上平滑避免零方差）
            self.var[i] = np.var(X_c, axis=0) + 1e-6
        
        return self
    
    def _log_likelihood(self, x: np.ndarray, class_idx: int) -> float:
        """
        计算对数似然 log P(x|y)
        
        参数:
            x: 样本特征
            class_idx: 类别索引
            
        返回:
            对数似然值
        """
        # 高斯分布对数密度
        log_lik = -0.5 * np.sum(
            np.log(2 * np.pi * self.var[class_idx]) + 
            (x - self.theta[class_idx])**2 / self.var[class_idx]
        )
        return log_lik
    
    def predict_log_proba(self, X: np.ndarray) -> np.ndarray:
        """
        预测对数概率
        
        参数:
            X: 测试数据 (n_samples, n_features)
            
        返回:
            对数概率 (n_samples, n_classes)
        """
        X = np.array(X)
        n_samples = X.shape[0]
        
        log_proba = np.zeros((n_samples, self.n_classes))
        
        for i in range(self.n_classes):
            # log P(y) + log P(x|y)
            log_proba[:, i] = np.log(self.class_prior[i] + 1e-10) + \
                             np.array([self._log_likelihood(x, i) for x in X])
        
        # 归一化（减去最大值提高数值稳定性）
        log_proba = log_proba - np.max(log_proba, axis=1, keepdims=True)
        
        return log_proba
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        预测概率
        
        参数:
            X: 测试数据
            
        返回:
            概率 (n_samples, n_classes)
        """
        log_proba = self.predict_log_proba(X)
        
        # softmax归一化
        proba = np.exp(log_proba)
        proba = proba / np.sum(proba, axis=1, keepdims=True)
        
        return proba
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        预测类别
        
        参数:
            X: 测试数据
            
        返回:
            类别标签
        """
        log_proba = self.predict_log_proba(X)
        return self.classes[np.argmax(log_proba, axis=1)]


class MultinomialNaiveBayes:
    """
    多项朴素贝叶斯
    
    适用于离散特征（如词频）的分类问题。
    P(x|y) 服从多项分布。
    
    参数:
        alpha: 平滑参数
    """
    
    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'MultinomialNaiveBayes':
        """
        训练多项朴素贝叶斯
        
        参数:
            X: 词频矩阵 (n_samples, n_features)
            y: 标签
        """
        X = np.array(X)
        y = np.array(y)
        
        self.classes = np.unique(y)
        self.n_classes = len(self.classes)
        self.n_features = X.shape[1]
        
        # 类先验
        self.class_log_prior = np.zeros(self.n_classes)
        
        # 每个类别的特征对数似然
        self.feature_log_prob = np.zeros((self.n_classes, self.n_features))
        
        for i, c in enumerate(self.classes):
            X_c = X[y == c]
            
            # 类先验
            self.class_log_prior[i] = np.log(len(X_c) / len(y))
            
            # 特征似然（多项分布参数）
            # P(x_j|y) = (count(x_j,y) + alpha) / (sum(count(y)) + alpha * n_features)
            feature_count = np.sum(X_c, axis=0)
            total_count = np.sum(feature_count)
            
            self.feature_log_prob[i] = np.log(
                (feature_count + self.alpha) / 
                (total_count + self.alpha * self.n_features)
            )
        
        return self
    
    def predict_log_proba(self, X: np.ndarray) -> np.ndarray:
        """预测对数概率"""
        return self.class_log_prior + X @ self.feature_log_prob.T
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """预测概率"""
        log_proba = self.predict_log_proba(X)
        log_proba = log_proba - np.max(log_proba, axis=1, keepdims=True)
        proba = np.exp(log_proba)
        return proba / np.sum(proba, axis=1, keepdims=True)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测类别"""
        log_proba = self.predict_log_proba(X)
        return self.classes[np.argmax(log_proba, axis=1)]


class BernoulliNaiveBayes:
    """
    伯努利朴素贝叶斯
    
    适用于二元特征（如词是否出现）分类。
    P(x_j|y) 服从伯努利分布。
    
    参数:
        alpha: 平滑参数
    """
    
    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'BernoulliNaiveBayes':
        """训练伯努利朴素贝叶斯"""
        X = np.array(X)
        y = np.array(y)
        
        self.classes = np.unique(y)
        self.n_classes = len(self.classes)
        self.n_features = X.shape[1]
        
        self.class_log_prior = np.zeros(self.n_classes)
        self.feature_prob = np.zeros((self.n_classes, self.n_features))  # P(x_j=1|y)
        
        for i, c in enumerate(self.classes):
            X_c = X[y == c]
            
            self.class_log_prior[i] = np.log(len(X_c) / len(y))
            
            # 计算 P(x_j=1|y)
            self.feature_prob[i] = (np.sum(X_c, axis=0) + self.alpha) / \
                                   (len(X_c) + 2 * self.alpha)
        
        return self
    
    def _log_likelihood(self, x: np.ndarray, class_idx: int) -> float:
        """计算对数似然"""
        # 对于伯努利分布
        # log P(x|y) = sum_j [ x_j * log(p_j) + (1-x_j) * log(1-p_j) ]
        p = self.feature_prob[class_idx]
        return np.sum(x * np.log(p + 1e-10) + (1 - x) * np.log(1 - p + 1e-10))
    
    def predict_log_proba(self, X: np.ndarray) -> np.ndarray:
        """预测对数概率"""
        n_samples = X.shape[0]
        log_proba = np.zeros((n_samples, self.n_classes))
        
        for i in range(self.n_classes):
            for j in range(n_samples):
                log_proba[j, i] = self.class_log_prior[i] + self._log_likelihood(X[j], i)
        
        return log_proba
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """预测概率"""
        log_proba = self.predict_log_proba(X)
        log_proba = log_proba - np.max(log_proba, axis=1, keepdims=True)
        proba = np.exp(log_proba)
        return proba / np.sum(proba, axis=1, keepdims=True)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测类别"""
        log_proba = self.predict_log_proba(X)
        return self.classes[np.argmax(log_proba, axis=1)]


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("朴素贝叶斯分类器测试")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 测试1：高斯朴素贝叶斯
    print("\n1. 高斯朴素贝叶斯分类:")
    
    # 生成样本数据：两个类别的高斯分布
    n_samples = 100
    X1 = np.random.randn(n_samples, 2) + np.array([0, 0])
    X2 = np.random.randn(n_samples, 2) + np.array([3, 3])
    X = np.vstack([X1, X2])
    y = np.array([0] * n_samples + [1] * n_samples)
    
    gnb = GaussianNaiveBayes(alpha=1.0)
    gnb.fit(X, y)
    
    # 预测
    y_pred = gnb.predict(X)
    accuracy = np.mean(y_pred == y)
    print(f"   训练准确率: {accuracy:.2%}")
    print(f"   类先验: {gnb.class_prior}")
    print(f"   类别0均值: {gnb.theta[0]}")
    print(f"   类别1均值: {gnb.theta[1]}")
    
    # 测试2：多项朴素贝叶斯（文本分类模拟）
    print("\n2. 多项朴素贝叶斯（词频分类）:")
    
    # 模拟词频矩阵
    X_text = np.array([
        [3, 0, 1],  # 文档1
        [0, 2, 1],  # 文档2
        [1, 1, 3],  # 文档3
        [2, 1, 0],  # 文档4
        [0, 3, 1],  # 文档5
        [1, 0, 2],  # 文档6
    ])
    y_text = np.array([0, 0, 1, 1, 0, 1])
    
    mnb = MultinomialNaiveBayes(alpha=1.0)
    mnb.fit(X_text, y_text)
    
    y_pred_text = mnb.predict(X_text)
    accuracy_text = np.mean(y_pred_text == y_text)
    print(f"   训练准确率: {accuracy_text:.2%}")
    print(f"   预测: {y_pred_text}")
    
    # 测试3：伯努利朴素贝叶斯
    print("\n3. 伯努利朴素贝叶斯（二元特征）:")
    
    X_binary = np.array([
        [1, 0, 1],
        [1, 1, 0],
        [0, 1, 1],
        [0, 0, 1],
        [1, 1, 1],
        [0, 1, 0],
    ])
    y_binary = np.array([0, 0, 1, 1, 0, 1])
    
    bnb = BernoulliNaiveBayes(alpha=1.0)
    bnb.fit(X_binary, y_binary)
    
    y_pred_binary = bnb.predict(X_binary)
    accuracy_binary = np.mean(y_pred_binary == y_binary)
    print(f"   训练准确率: {accuracy_binary:.2%}")
    print(f"   预测概率形状: {bnb.predict_proba(X_binary).shape}")
    
    # 测试4：概率预测
    print("\n4. 概率预测示例:")
    proba = gnb.predict_proba(np.array([[0.5, 0.5]]))
    print(f"   样本[0.5, 0.5]的概率: {proba[0]}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
