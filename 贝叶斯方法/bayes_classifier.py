"""
贝叶斯分类器：生成模型视角
Bayesian Classifier: Generative Model Perspective

贝叶斯分类器是生成模型，通过建模 P(x|y) 和 P(y) 来进行分类。
与判别模型不同，生成模型可以生成新样本。
包含：判别分析（线性/二次）、朴素贝叶斯、生成式分类器框架。
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Callable
from abc import ABC, abstractmethod


class BayesianClassifier(ABC):
    """
    贝叶斯分类器基类（生成模型框架）
    
    分类原理：
    y* = argmax_y P(y|x) = argmax_y P(x|y) P(y)
    
    其中：
    - P(y) 是类先验
    - P(x|y) 是似然（类条件密度）
    - P(y|x) 是后验
    """
    
    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'BayesianClassifier':
        """训练分类器"""
        pass
    
    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测类别"""
        pass
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """预测后验概率"""
        log_proba = self.predict_log_proba(X)
        # softmax
        log_proba = log_proba - np.max(log_proba, axis=1, keepdims=True)
        proba = np.exp(log_proba)
        proba = proba / np.sum(proba, axis=1, keepdims=True)
        return proba
    
    @abstractmethod
    def predict_log_proba(self, X: np.ndarray) -> np.ndarray:
        """预测对数后验"""
        pass
    
    def generate(self, n_samples: int, class_label: int) -> np.ndarray:
        """
        从类条件分布生成样本（生成模型特有）
        
        参数:
            n_samples: 生成样本数
            class_label: 类别标签
            
        返回:
            生成样本
        """
        raise NotImplementedError("Subclass must implement generate()")


class LinearDiscriminantAnalysis(BayesianClassifier):
    """
    线性判别分析 (LDA)
    
    假设所有类别共享同一协方差矩阵：
    x | y=c ~ N(mu_c, Sigma)  其中 Sigma 共享
    
    决策边界是线性的。
    
    参数:
        priors: 类先验
    """
    
    def __init__(self, priors: Optional[np.ndarray] = None):
        self.priors = priors  # 类先验
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'LinearDiscriminantAnalysis':
        """训练LDA"""
        X = np.array(X)
        y = np.array(y)
        
        self.classes = np.unique(y)
        self.n_classes = len(self.classes)
        self.n_features = X.shape[1]
        
        # 计算类均值
        self.means = np.zeros((self.n_classes, self.n_features))
        for i, c in enumerate(self.classes):
            self.means[i] = np.mean(X[y == c], axis=0)
        
        # 计算共享协方差矩阵（加权平均）
        self.cov = np.zeros((self.n_features, self.n_features))
        for i, c in enumerate(self.classes):
            X_c = X[y == c]
            centered = X_c - self.means[i]
            self.cov += np.sum(y == c) * (centered.T @ centered)
        self.cov = self.cov / (len(y) - self.n_classes)
        
        # 确保协方差矩阵正定
        self.cov = self.cov + 1e-6 * np.eye(self.n_features)
        self.cov_inv = np.linalg.inv(self.cov)
        
        # 类先验
        if self.priors is None:
            self.priors = np.array([np.mean(y == c) for c in self.classes])
        
        self.log_priors = np.log(self.priors + 1e-10)
        
        return self
    
    def _log_likelihood(self, x: np.ndarray, class_idx: int) -> float:
        """计算类条件对数似然"""
        diff = x - self.means[class_idx]
        # 高斯对数密度：-0.5 * (x-mu)^T Sigma^-1 (x-mu) - 0.5 * log|Sigma|
        ll = -0.5 * diff @ self.cov_inv @ diff
        ll += -0.5 * np.log(np.linalg.det(self.cov))
        ll += -self.n_features / 2 * np.log(2 * np.pi)
        return ll
    
    def predict_log_proba(self, X: np.ndarray) -> np.ndarray:
        """预测对数后验"""
        X = np.array(X)
        n_samples = X.shape[0]
        
        log_proba = np.zeros((n_samples, self.n_classes))
        
        for i in range(self.n_classes):
            log_proba[:, i] = self.log_priors[i] + \
                             np.array([self._log_likelihood(x, i) for x in X])
        
        return log_proba
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测类别"""
        log_proba = self.predict_log_proba(X)
        return self.classes[np.argmax(log_proba, axis=1)]
    
    def generate(self, n_samples: int, class_label: int) -> np.ndarray:
        """从类条件分布生成样本"""
        class_idx = np.where(self.classes == class_label)[0][0]
        
        # 从 N(mu_c, Sigma) 采样
        L = np.linalg.cholesky(self.cov)
        samples = self.means[class_idx] + L @ np.random.randn(self.n_features, n_samples)
        
        return samples.T


class QuadraticDiscriminantAnalysis(BayesianClassifier):
    """
    二次判别分析 (QDA)
    
    每个类别有独立的协方差矩阵：
    x | y=c ~ N(mu_c, Sigma_c)
    
    决策边界是二次的。
    """
    
    def __init__(self, priors: Optional[np.ndarray] = None):
        self.priors = priors
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'QuadraticDiscriminantAnalysis':
        """训练QDA"""
        X = np.array(X)
        y = np.array(y)
        
        self.classes = np.unique(y)
        self.n_classes = len(self.classes)
        self.n_features = X.shape[1]
        
        self.means = np.zeros((self.n_classes, self.n_features))
        self.covs = []  # 每个类的协方差
        self.cov_invs = []
        self.cov_dets = []
        
        for i, c in enumerate(self.classes):
            X_c = X[y == c]
            self.means[i] = np.mean(X_c, axis=0)
            
            cov_c = np.cov(X_c.T) + 1e-6 * np.eye(self.n_features)
            self.covs.append(cov_c)
            self.cov_invs.append(np.linalg.inv(cov_c))
            self.cov_dets.append(np.linalg.det(cov_c))
        
        if self.priors is None:
            self.priors = np.array([np.mean(y == c) for c in self.classes])
        
        self.log_priors = np.log(self.priors + 1e-10)
        
        return self
    
    def _log_likelihood(self, x: np.ndarray, class_idx: int) -> float:
        """计算对数似然"""
        diff = x - self.means[class_idx]
        cov_inv = self.cov_invs[class_idx]
        cov_det = self.cov_dets[class_idx]
        
        ll = -0.5 * diff @ cov_inv @ diff
        ll += -0.5 * np.log(cov_det)
        ll += -self.n_features / 2 * np.log(2 * np.pi)
        return ll
    
    def predict_log_proba(self, X: np.ndarray) -> np.ndarray:
        """预测对数后验"""
        X = np.array(X)
        n_samples = X.shape[0]
        
        log_proba = np.zeros((n_samples, self.n_classes))
        
        for i in range(self.n_classes):
            log_proba[:, i] = self.log_priors[i] + \
                             np.array([self._log_likelihood(x, i) for x in X])
        
        return log_proba
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测类别"""
        log_proba = self.predict_log_proba(X)
        return self.classes[np.argmax(log_proba, axis=1)]
    
    def generate(self, n_samples: int, class_label: int) -> np.ndarray:
        """生成样本"""
        class_idx = np.where(self.classes == class_label)[0][0]
        
        L = np.linalg.cholesky(self.covs[class_idx])
        samples = self.means[class_idx] + L @ np.random.randn(self.n_features, n_samples)
        
        return samples.T


class GenerativeClassifierWrapper:
    """
    生成式分类器包装器
    
    将任何类条件密度估计器包装成贝叶斯分类器。
    
    参数:
        density_estimator: 密度估计器
        classes: 类别标签
    """
    
    def __init__(self, density_estimator: Callable, classes: np.ndarray):
        self.density_estimator = density_estimator  # 估计 P(x|y)
        self.classes = classes
        self.class_prior = None
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'GenerativeClassifierWrapper':
        """训练"""
        X = np.array(X)
        y = np.array(y)
        
        # 估计类先验
        self.class_prior = np.array([np.mean(y == c) for c in self.classes])
        self.log_prior = np.log(self.class_prior + 1e-10)
        
        # 为每个类别拟合密度估计器
        self.densities = {}
        for i, c in enumerate(self.classes):
            X_c = X[y == c]
            self.densities[c] = self.density_estimator(X_c)
        
        return self
    
    def predict_log_proba(self, X: np.ndarray) -> np.ndarray:
        """预测对数后验"""
        X = np.array(X)
        n_samples = X.shape[0]
        
        log_proba = np.zeros((n_samples, len(self.classes)))
        
        for i, c in enumerate(self.classes):
            # log P(y) + log P(x|y)
            log_proba[:, i] = self.log_prior[i]
            for j in range(n_samples):
                log_proba[j, i] += self.densities[c].log_pdf(X[j])
        
        return log_proba
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测"""
        log_proba = self.predict_log_proba(X)
        return self.classes[np.argmax(log_proba, axis=1)]


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("贝叶斯分类器（生成模型）测试")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 生成测试数据
    print("\n1. 线性判别分析 (LDA):")
    
    n = 100
    # 类别1：高斯分布
    X1 = np.random.randn(n, 2) + np.array([0, 0])
    # 类别2：高斯分布
    X2 = np.random.randn(n, 2) + np.array([2, 2])
    X = np.vstack([X1, X2])
    y = np.array([0] * n + [1] * n)
    
    # LDA
    lda = LinearDiscriminantAnalysis()
    lda.fit(X, y)
    
    y_pred = lda.predict(X)
    accuracy = np.mean(y_pred == y)
    print(f"   训练准确率: {accuracy:.2%}")
    print(f"   类先验: {lda.priors}")
    print(f"   共享协方差矩阵范数: {np.linalg.norm(lda.cov):.4f}")
    
    # 测试生成
    gen_samples = lda.generate(5, class_label=0)
    print(f"   生成样本形状: {gen_samples.shape}")
    
    # QDA
    print("\n2. 二次判别分析 (QDA):")
    
    qda = QuadraticDiscriminantAnalysis()
    qda.fit(X, y)
    
    y_pred_qda = qda.predict(X)
    accuracy_qda = np.mean(y_pred_qda == y)
    print(f"   训练准确率: {accuracy_qda:.2%}")
    
    # 不同协方差矩阵
    print(f"   类别0协方差范数: {np.linalg.norm(qda.covs[0]):.4f}")
    print(f"   类别1协方差范数: {np.linalg.norm(qda.covs[1]):.4f}")
    
    # 概率预测
    print("\n3. 后验概率预测:")
    proba = lda.predict_proba(np.array([[0.5, 0.5], [2.5, 2.5]]))
    print(f"   点[0.5,0.5]后验: {proba[0]}")
    print(f"   点[2.5,2.5]后验: {proba[1]}")
    
    # 不同形状的类别
    print("\n4. 非线性可分数据（QDA优势）:")
    
    # 类别1：圆形
    angle = np.random.uniform(0, 2 * np.pi, n)
    X1_circle = np.column_stack([np.cos(angle), np.sin(angle)]) * 2 + np.array([0, 0])
    # 类别2：外环
    X2_ring = np.column_stack([np.cos(angle), np.sin(angle)]) * 4 + np.array([0, 0])
    X_circle = np.vstack([X1_circle, X2_ring])
    y_circle = np.array([0] * n + [1] * n)
    
    # LDA（线性边界效果差）
    lda_c = LinearDiscriminantAnalysis()
    lda_c.fit(X_circle, y_circle)
    acc_lda = np.mean(lda_c.predict(X_circle) == y_circle)
    
    # QDA（二次边界效果好）
    qda_c = QuadraticDiscriminantAnalysis()
    qda_c.fit(X_circle, y_circle)
    acc_qda = np.mean(qda_c.predict(X_circle) == y_circle)
    
    print(f"   LDA准确率: {acc_lda:.2%}")
    print(f"   QDA准确率: {acc_qda:.2%}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
