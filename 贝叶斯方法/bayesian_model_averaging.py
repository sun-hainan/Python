"""
贝叶斯模型平均（Bayesian Model Averaging, BMA）
Bayesian Model Averaging

BMA通过加权平均所有候选模型的预测来处理模型不确定性。
权重基于后验模型概率：P(M_k | D) ∝ P(D | M_k) * P(M_k)
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Callable
from abc import ABC, abstractmethod
from collections import defaultdict


class BayesianModel(ABC):
    """贝叶斯模型基类"""
    
    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray):
        """拟合模型"""
        pass
    
    @abstractmethod
    def log_marginal_likelihood(self) -> float:
        """计算对数边缘似然 log p(y | X, M)"""
        pass
    
    @abstractmethod
    def predict_log_proba(self, X: np.ndarray) -> np.ndarray:
        """预测对数概率"""
        pass
    
    @abstractmethod
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """预测概率"""
        pass


class BayesianModelAveraging:
    """
    贝叶斯模型平均
    
    参数:
        models: 模型列表
        prior_weights: 模型先验权重（可选）
    """
    
    def __init__(self, models: List[BayesianModel], 
                 prior_weights: Optional[np.ndarray] = None):
        self.models = models
        self.n_models = len(models)
        
        # 先验权重
        if prior_weights is None:
            self.prior_weights = np.ones(self.n_models) / self.n_models
        else:
            self.prior_weights = np.array(prior_weights)
            self.prior_weights = self.prior_weights / np.sum(self.prior_weights)
        
        # 后验权重
        self.posterior_weights = None
        self.log_marginal_liks = None
    
    def fit(self, X: np.ndarray, y: np.ndarray, verbose: bool = True) -> 'BayesianModelAveraging':
        """
        拟合并计算后验权重
        
        参数:
            X: 特征
            y: 目标
            verbose: 是否打印
        """
        # 拟合每个模型并计算边缘似然
        self.log_marginal_liks = np.zeros(self.n_models)
        
        for i, model in enumerate(self.models):
            model.fit(X, y)
            self.log_marginal_liks[i] = model.log_marginal_likelihood()
            
            if verbose:
                print(f"   模型 {i}: log p(y|M) = {self.log_marginal_liks[i]:.4f}")
        
        # 计算后验权重
        log_posterior = self.log_marginal_liks + np.log(self.prior_weights)
        log_posterior = log_posterior - np.max(log_posterior)  # 数值稳定性
        posterior = np.exp(log_posterior)
        self.posterior_weights = posterior / np.sum(posterior)
        
        if verbose:
            print("\n   后验模型概率:")
            for i, w in enumerate(self.posterior_weights):
                print(f"   P(M_{i} | D) = {w:.4f}")
        
        return self
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        BMA预测概率
        
        P(y=k | x, D) = sum_k P(M_k | D) * P(y=k | x, M_k)
        
        参数:
            X: 测试数据
            
        返回:
            加权平均概率
        """
        n_samples = len(X)
        n_classes = self.models[0].predict_proba(X).shape[1]
        
        weighted_proba = np.zeros((n_samples, n_classes))
        
        for i, (model, weight) in enumerate(zip(self.models, self.posterior_weights)):
            proba = model.predict_proba(X)
            weighted_proba += weight * proba
        
        # 归一化
        weighted_proba = weighted_proba / np.sum(weighted_proba, axis=1, keepdims=True)
        
        return weighted_proba
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """BMA预测类别"""
        proba = self.predict_proba(X)
        return np.argmax(proba, axis=1)


class LinearRegressionBMA(BayesianModel):
    """
    贝叶斯线性回归（用于BMA）
    
    使用不同先验精度对应不同复杂度模型
    """
    
    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha  # 先验精度
    
    def fit(self, X: np.ndarray, y: np.ndarray):
        """拟合模型"""
        self.X = X
        self.y = y
        self.n, self.p = X.shape
        
        # 共轭先验下的后验
        self.beta_var = np.linalg.inv(X.T @ X + self.alpha * np.eye(self.p))
        self.beta_mean = self.beta_var @ X.T @ y
        
        # 残差
        residuals = y - X @ self.beta_mean
        self.sigma_sq = np.mean(residuals**2)
    
    def log_marginal_likelihood(self) -> float:
        """
        计算对数边缘似然（使用拉普拉斯近似）
        
        log p(y | X, alpha) ≈ -0.5 * y^T (I + alpha * X X^T)^-1 y - 0.5 * log|I + alpha * X X^T|
        """
        A = np.eye(self.n) + self.alpha * self.X @ self.X.T
        try:
            A_inv = np.linalg.inv(A + 1e-6 * np.eye(self.n))
        except:
            return -np.inf
        
        ll = -0.5 * self.y @ A_inv @ self.y
        ll -= 0.5 * np.log(np.linalg.det(A))
        
        return ll
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """预测（简化为回归输出）"""
        preds = X @ self.beta_mean
        return preds.reshape(-1, 1)
    
    def predict_log_proba(self, X: np.ndarray) -> np.ndarray:
        preds = X @ self.beta_mean
        return np.log(preds + 1e-10).reshape(-1, 1)


class DifferentSubsetModels:
    """
    不同特征子集的线性回归模型集合
    
    用于展示BMA如何平均不同复杂度模型
    """
    
    def __init__(self):
        self.models = []
    
    def create_subset_models(self, X: np.ndarray, y: np.ndarray,
                              max_features: int = 5) -> List[LinearRegressionBMA]:
        """创建不同特征数量的子集模型"""
        n_features = X.shape[1]
        models = []
        
        for k in range(1, min(max_features + 1, n_features + 1)):
            # 选择前k个特征
            X_subset = X[:, :k]
            
            model = LinearRegressionBMA(alpha=1.0)
            model.fit(X_subset, y)
            models.append(model)
        
        return models


class ModelComparison:
    """
    模型比较工具
    
    计算各模型的贝叶斯因子和后验概率
    """
    
    @staticmethod
    def bayes_factor(log_marginal_1: float, log_marginal_2: float) -> float:
        """
        计算贝叶斯因子
        
        BF_12 = p(D | M_1) / p(D | M_2) = exp(log_m1 - log_m2)
        """
        return np.exp(log_marginal_1 - log_marginal_2)
    
    @staticmethod
    def posterior_probabilities(log_marginals: np.ndarray,
                                 prior: Optional[np.ndarray] = None) -> np.ndarray:
        """
        计算后验概率
        
        参数:
            log_marginals: 各模型的对数边缘似然
            prior: 先验概率
            
        返回:
            后验概率
        """
        if prior is None:
            prior = np.ones(len(log_marginals)) / len(log_marginals)
        
        log_posterior = log_marginals + np.log(prior)
        log_posterior = log_posterior - np.max(log_posterior)
        posterior = np.exp(log_posterior)
        
        return posterior / np.sum(posterior)
    
    @staticmethod
    def interpret_bayes_factor(BF: float) -> str:
        """
        解释贝叶斯因子
        
        BF > 100: 极端证据支持M1
        30 < BF < 100: 非常强证据
        10 < BF < 30: 强证据
        3 < BF < 10: 中等证据
        1 < BF < 3: 弱证据
        BF ≈ 1: 无差异
        """
        if BF > 100:
            return "极端证据支持M1"
        elif BF > 30:
            return "非常强证据支持M1"
        elif BF > 10:
            return "强证据支持M1"
        elif BF > 3:
            return "中等证据支持M1"
        elif BF > 1:
            return "弱证据支持M1"
        elif BF > 0.33:
            return "弱证据支持M2"
        elif BF > 0.1:
            return "中等证据支持M2"
        elif BF > 0.03:
            return "强证据支持M2"
        elif BF > 0.01:
            return "非常强证据支持M2"
        else:
            return "极端证据支持M2"


class BayesianOccamWindow:
    """
    贝叶斯奥卡姆窗口
    
    用于识别最优复杂度模型，排除过于复杂或过于简单的模型
    """
    
    def __init__(self, models: List, log_marginals: np.ndarray):
        self.models = models
        self.log_marginals = log_marginals
        self.posterior_probs = ModelComparison.posterior_probabilities(log_marginals)
    
    def best_models(self, threshold: float = 0.01) -> List[Tuple[int, float]]:
        """
        返回累积概率达到阈值的模型
        
        参数:
            threshold: 累积后验概率阈值
            
        返回:
            [(模型索引, 后验概率), ...]
        """
        # 按后验概率排序
        sorted_indices = np.argsort(self.posterior_probs)[::-1]
        
        selected = []
        cumsum = 0.0
        
        for idx in sorted_indices:
            prob = self.posterior_probs[idx]
            if cumsum >= threshold:
                break
            selected.append((idx, prob))
            cumsum += prob
        
        return selected
    
    def complexity_penalty(self, model_idx: int, n_params: int) -> float:
        """
        计算复杂度惩罚
        
        近似：复杂度惩罚 ≈ 0.5 * n_params * log(n)
        """
        n = 100  # 假设样本数
        return 0.5 * n_params * np.log(n)


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("贝叶斯模型平均(BMA)测试")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 生成数据
    n = 100
    p = 5
    
    X = np.random.randn(n, p)
    X[:, 0] = 1.0  # 截距
    
    true_beta = np.array([2.0, 1.5, 0.0, 0.0, 0.0])  # 只有前两个特征有贡献
    y = X @ true_beta + np.random.randn(n) * 0.5
    
    # 测试1：不同特征子集模型
    print("\n1. 不同特征子集模型:")
    
    subset_models = []
    for k in range(1, p + 1):
        X_k = X[:, :k]
        
        model = LinearRegressionBMA(alpha=1.0)
        model.fit(X_k, y)
        
        ll = model.log_marginal_likelihood()
        subset_models.append((k, model, ll))
        
        print(f"   前{k}个特征: log p(y|X) = {ll:.4f}")
    
    # 测试2：计算后验权重
    print("\n2. 模型后验概率:")
    
    log_marginals = np.array([m[2] for m in subset_models])
    posterior = ModelComparison.posterior_probabilities(log_marginals)
    
    for k, _, ll in subset_models:
        bf_12 = ModelComparison.bayes_factor(ll, log_marginals[0])
        print(f"   k={k}: P(M|D) = {posterior[k-1]:.4f}, BF vs k=1: {bf_12:.2f}")
    
    # 测试3：BMA预测
    print("\n3. 贝叶斯模型平均预测:")
    
    models_list = [m[1] for m in subset_models]
    bma = BayesianModelAveraging(models_list)
    bma.fit(X, y, verbose=False)
    
    print(f"   后验权重分布:")
    for i, w in enumerate(bma.posterior_weights):
        print(f"   k={i+1}: {w:.4f}")
    
    # 测试4：模型比较
    print("\n4. 模型比较（贝叶斯因子）:")
    
    for i in range(len(log_marginals)):
        for j in range(i + 1, len(log_marginals)):
            BF = ModelComparison.bayes_factor(log_marginals[i], log_marginals[j])
            interp = ModelComparison.interpret_bayes_factor(BF)
            print(f"   M{i+1} vs M{j+1}: BF = {BF:.2f} -> {interp}")
    
    # 测试5：奥卡姆窗口
    print("\n5. 贝叶斯奥卡姆窗口:")
    
    ow = BayesianOccamWindow(subset_models, log_marginals)
    best = ow.best_models(threshold=0.99)
    
    print(f"   包含99%后验概率的模型:")
    for idx, prob in best:
        k = idx + 1
        n_params = k
        print(f"   k={k}: P={prob:.4f}, 复杂度惩罚≈{ow.complexity_penalty(idx, n_params):.2f}")
    
    # 测试6：预测不确定性
    print("\n6. BMA预测 vs 单模型预测:")
    
    X_test = np.random.randn(5, p)
    X_test[:, 0] = 1.0
    
    # BMA预测（加权平均）
    bma_preds = []
    for i, model in enumerate(models_list):
        X_test_subset = X_test[:, :i+1]
        pred = model.predict_proba(X_test_subset).flatten()
        bma_preds.append(pred)
    
    # 计算BMA加权平均
    bma_final = np.zeros(5)
    for i, (pred, w) in enumerate(zip(bma_preds, bma.posterior_weights)):
        bma_final += w * pred
    
    # 单模型（k=2，最优模型）
    single_pred = models_list[1].predict_proba(X_test[:, :2]).flatten()
    
    print(f"   真实值: {(X_test @ true_beta)[:3].round(2)}")
    print(f"   BMA预测: {bma_final[:3].round(2)}")
    print(f"   单模型(k=2)预测: {single_pred[:3].round(2)}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
