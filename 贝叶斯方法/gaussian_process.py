"""
高斯过程回归：核函数与预测
Gaussian Process Regression: Kernel Functions and Prediction

高斯过程是函数空间上的贝叶斯推断，提供了预测值的不确定性估计。
广泛应用于回归、分类和贝叶斯优化。
"""

import numpy as np
from typing import Callable, Tuple, Optional, List
from abc import ABC, abstractmethod


class Kernel(ABC):
    """核函数抽象基类"""
    
    @abstractmethod
    def __call__(self, x1: np.ndarray, x2: np.ndarray) -> float:
        """计算核函数 k(x1, x2)"""
        pass
    
    @abstractmethod
    def diag(self, X: np.ndarray) -> np.ndarray:
        """计算核函数对角线 k(x, x)"""
        pass


class RBFKernel(Kernel):
    """
    径向基函数核 / 高斯核 / SE核
    
    k(x1, x2) = exp(-||x1 - x2||^2 / (2 * l^2))
    
    参数:
        length_scale: 长度尺度l，控制函数的平滑程度
        variance: 方差，控制函数振幅
    """
    
    def __init__(self, length_scale: float = 1.0, variance: float = 1.0):
        self.length_scale = length_scale
        self.variance = variance
    
    def __call__(self, x1: np.ndarray, x2: np.ndarray) -> float:
        """RBF核计算"""
        diff = x1 - x2
        return self.variance * np.exp(-np.sum(diff**2) / (2 * self.length_scale**2))
    
    def diag(self, X: np.ndarray) -> np.ndarray:
        """对角线元素（等于variance）"""
        return np.full(len(X), self.variance)


class MaternKernel(Kernel):
    """
    Matern核函数
    
    k(x1, x2) = variance * f(|x1 - x2|)
    
    参数:
        length_scale: 长度尺度
        variance: 方差
        nu: Matern参数（常用1.5, 2.5, inf）
    """
    
    def __init__(self, length_scale: float = 1.0, variance: float = 1.0, nu: float = 2.5):
        self.length_scale = length_scale
        self.variance = variance
        self.nu = nu
    
    def __call__(self, x1: np.ndarray, x2: np.ndarray) -> float:
        """Matern核计算"""
        r = np.linalg.norm(x1 - x2)
        
        if self.nu == np.inf:
            # RBF核极限
            return self.variance * np.exp(-r**2 / (2 * self.length_scale**2))
        elif self.nu == 1.5:
            # 一次可导
            factor = np.sqrt(3) * r / self.length_scale
            return self.variance * (1 + factor) * np.exp(-factor)
        elif self.nu == 2.5:
            # 二次可导
            factor = np.sqrt(5) * r / self.length_scale
            return self.variance * (1 + factor + factor**2 / 3) * np.exp(-factor)
        else:
            raise ValueError(f"Unsupported nu: {self.nu}")
    
    def diag(self, X: np.ndarray) -> np.ndarray:
        """对角线元素"""
        return np.full(len(X), self.variance)


class LinearKernel(Kernel):
    """
    线性核函数
    
    k(x1, x2) = variance * x1^T x2
    
    参数:
        variance: 缩放参数
    """
    
    def __init__(self, variance: float = 1.0):
        self.variance = variance
    
    def __call__(self, x1: np.ndarray, x2: np.ndarray) -> float:
        """线性核计算"""
        return self.variance * np.dot(x1, x2)
    
    def diag(self, X: np.ndarray) -> np.ndarray:
        """对角线元素"""
        return self.variance * np.sum(X**2, axis=1)


class PeriodicKernel(Kernel):
    """
    周期核函数
    
    k(x1, x2) = variance * exp(-2 * sin^2(pi * |x1 - x2| / p) / l^2)
    
    参数:
        length_scale: 长度尺度l
        period: 周期p
        variance: 方差
    """
    
    def __init__(self, length_scale: float = 1.0, period: float = 1.0, variance: float = 1.0):
        self.length_scale = length_scale
        self.period = period
        self.variance = variance
    
    def __call__(self, x1: np.ndarray, x2: np.ndarray) -> float:
        """周期核计算"""
        r = np.linalg.norm(x1 - x2)
        sin_term = np.sin(np.pi * r / self.period)
        return self.variance * np.exp(-2 * sin_term**2 / self.length_scale**2)
    
    def diag(self, X: np.ndarray) -> np.ndarray:
        """对角线元素"""
        return np.full(len(X), self.variance)


class CompoundKernel(Kernel):
    """
    组合核函数
    
    通过加法和乘法组合基本核函数构建复杂核。
    """
    
    def __init__(self, kernel1: Kernel, kernel2: Kernel, operation: str = 'add'):
        self.kernel1 = kernel1
        self.kernel2 = kernel2
        self.operation = operation  # 'add' 或 'mult'
    
    def __call__(self, x1: np.ndarray, x2: np.ndarray) -> float:
        """组合核计算"""
        if self.operation == 'add':
            return self.kernel1(x1, x2) + self.kernel2(x1, x2)
        elif self.operation == 'mult':
            return self.kernel1(x1, x2) * self.kernel2(x1, x2)
        else:
            raise ValueError(f"Unknown operation: {self.operation}")
    
    def diag(self, X: np.ndarray) -> np.ndarray:
        """对角线元素"""
        if self.operation == 'add':
            return self.kernel1.diag(X) + self.kernel2.diag(X)
        elif self.operation == 'mult':
            return self.kernel1.diag(X) * self.kernel2.diag(X)


class GaussianProcessRegressor:
    """
    高斯过程回归器
    
    参数:
        kernel: 核函数
        noise: 观测噪声标准差
        optimizer: 是否优化超参数
    """
    
    def __init__(self, kernel: Kernel, noise: float = 1e-6, optimizer: bool = False):
        self.kernel = kernel
        self.noise = noise
        self.optimizer = optimizer
        
        self.X_train = None
        self.y_train = None
        self.K = None
        self.K_inv = None
        self.alpha = None
        self.is_fitted = False
    
    def _build_cov_matrix(self, X1: np.ndarray, X2: Optional[np.ndarray] = None) -> np.ndarray:
        """
        构建协方差矩阵
        
        参数:
            X1: 输入点 (n1, d)
            X2: 输入点 (n2, d)，None时X2=X1
            
        返回:
            协方差矩阵 (n1, n2)
        """
        if X2 is None:
            n1 = len(X1)
            K = np.zeros((n1, n1))
            for i in range(n1):
                for j in range(n1):
                    K[i, j] = self.kernel(X1[i], X1[j])
            return K
        else:
            n1, n2 = len(X1), len(X2)
            K = np.zeros((n1, n2))
            for i in range(n1):
                for j in range(n2):
                    K[i, j] = self.kernel(X1[i], X2[j])
            return K
    
    def fit(self, X: np.ndarray, y: np.ndarray):
        """
        训练高斯过程
        
        参数:
            X: 训练输入 (n, d)
            y: 训练目标 (n,)
        """
        self.X_train = np.array(X)
        self.y_train = np.array(y)
        n = len(y)
        
        # 构建协方差矩阵
        self.K = self._build_cov_matrix(X)
        self.K = self.K + self.noise**2 * np.eye(n)
        
        # 计算逆矩阵和alpha
        try:
            self.K_inv = np.linalg.inv(self.K)
        except np.linalg.LinAlgError:
            # 数值不稳定时添加小正则化
            self.K = self.K + 1e-6 * np.eye(n)
            self.K_inv = np.linalg.inv(self.K)
        
        self.alpha = self.K_inv @ self.y_train
        self.is_fitted = True
        
        # 可选：优化超参数
        if self.optimizer:
            self._optimize_hyperparameters()
    
    def _optimize_hyperparameters(self):
        """使用梯度下降优化核超参数"""
        # 简化版本：随机搜索
        best_ll = self._log_marginal_likelihood()
        
        for _ in range(20):
            # 扰动超参数
            if isinstance(self.kernel, RBFKernel):
                self.kernel.length_scale *= np.random.uniform(0.8, 1.2)
                self.kernel.variance *= np.random.uniform(0.8, 1.2)
            
            ll = self._log_marginal_likelihood()
            if ll > best_ll:
                best_ll = ll
            else:
                # 恢复
                if isinstance(self.kernel, RBFKernel):
                    self.kernel.length_scale /= np.random.uniform(0.8, 1.2)
                    self.kernel.variance /= np.random.uniform(0.8, 1.2)
    
    def _log_marginal_likelihood(self) -> float:
        """计算对数边缘似然"""
        n = len(self.y_train)
        
        # 重新计算K
        K = self._build_cov_matrix(self.X_train)
        K = K + self.noise**2 * np.eye(n)
        
        try:
            K_inv = np.linalg.inv(K + 1e-6 * np.eye(n))
        except:
            return -np.inf
        
        # log p(y|X) = -0.5 * y^T K^-1 y - 0.5 * log|K| - n/2 * log(2pi)
        ll = -0.5 * self.y_train @ K_inv @ self.y_train
        ll += -0.5 * np.log(np.linalg.det(K + 1e-6 * np.eye(n)))
        ll += -n / 2 * np.log(2 * np.pi)
        
        return ll
    
    def predict(self, X_test: np.ndarray, return_std: bool = False) -> Tuple[np.ndarray, np.ndarray]:
        """
        预测
        
        参数:
            X_test: 测试点 (m, d)
            return_std: 是否返回标准差
            
        返回:
            (均值, 标准差) 或 (均值,)
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit() first.")
        
        X_test = np.array(X_test)
        
        # 计算测试点与训练点的协方差
        K_star = self._build_cov_matrix(X_test, self.X_train)  # (m, n)
        
        # 预测均值
        mu = K_star @ self.alpha
        
        # 预测方差
        k_star_star = np.array([self.kernel(x, x) for x in X_test])
        var = k_star_star - np.sum(K_star @ self.K_inv * K_star, axis=1)
        var = np.maximum(var, 0)  # 数值稳定性
        
        if return_std:
            return mu, np.sqrt(var)
        else:
            return mu
    
    def sample_prior(self, X: np.ndarray, n_samples: int = 1) -> np.ndarray:
        """
        从先验分布采样函数
        
        参数:
            X: 采样点 (m, d)
            n_samples: 样本数量
            
        返回:
            函数样本 (n_samples, m)
        """
        K = self._build_cov_matrix(X)
        
        # Cholesky分解
        L = np.linalg.cholesky(K + 1e-6 * np.eye(len(X)))
        
        samples = L @ np.random.randn(len(X), n_samples)
        return samples.T
    
    def sample_posterior(self, X: np.ndarray, n_samples: int = 1) -> np.ndarray:
        """
        从后验分布采样函数
        
        参数:
            X: 采样点 (m, d)
            n_samples: 样本数量
            
        返回:
            函数样本 (n_samples, m)
        """
        mu, std = self.predict(X, return_std=True)
        
        samples = mu + std[:, np.newaxis] * np.random.randn(len(X), n_samples)
        return samples.T


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("高斯过程回归测试")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 生成训练数据
    X_train = np.array([[0.0], [1.0], [2.0], [3.0], [4.0], [5.0], [6.0]])
    y_train = np.sin(X_train.flatten()) + 0.1 * np.random.randn(7)
    
    # 测试不同核函数
    print("\n1. RBF核高斯过程:")
    gp_rbf = GaussianProcessRegressor(RBFKernel(length_scale=1.0, variance=1.0))
    gp_rbf.fit(X_train, y_train)
    
    X_test = np.linspace(-1, 7, 50).reshape(-1, 1)
    mu, std = gp_rbf.predict(X_test, return_std=True)
    
    print(f"   预测范围: [{mu.min():.4f}, {mu.max():.4f}]")
    print(f"   不确定性范围: [{std.min():.4f}, {std.max():.4f}]")
    
    print("\n2. Matern 2.5核高斯过程:")
    gp_matern = GaussianProcessRegressor(MaternKernel(length_scale=1.0, nu=2.5))
    gp_matern.fit(X_train, y_train)
    mu_m, std_m = gp_matern.predict(X_test, return_std=True)
    print(f"   预测范围: [{mu_m.min():.4f}, {mu_m.max():.4f}]")
    
    print("\n3. 组合核（线性+RBF）:")
    kernel_compound = CompoundKernel(LinearKernel(variance=0.1), 
                                     RBFKernel(length_scale=0.5), operation='add')
    gp_compound = GaussianProcessRegressor(kernel_compound)
    gp_compound.fit(X_train, y_train)
    mu_c, std_c = gp_compound.predict(X_test, return_std=True)
    print(f"   预测范围: [{mu_c.min():.4f}, {mu_c.max():.4f}]")
    
    print("\n4. 从后验采样:")
    samples = gp_rbf.sample_posterior(X_test, n_samples=3)
    print(f"   采样形状: {samples.shape}")
    
    print("\n5. 对数边缘似然:")
    ll = gp_rbf._log_marginal_likelihood()
    print(f"   RBF核 log p(y|X) = {ll:.4f}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
