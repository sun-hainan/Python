"""
贝叶斯曲线拟合
Bayesian Curve Fitting

贝叶斯方法通过在函数空间上定义先验，然后计算后验预测分布。
相比点估计，提供完整的不确定性量化。
"""

import numpy as np
from typing import Tuple, Optional, Callable
from abc import ABC, abstractmethod


class BayesianCurveFitter:
    """
    贝叶斯曲线拟合基类
    
    参数:
        alpha: 先验精度
        beta: 噪声精度
    """
    
    def __init__(self, alpha: float = 1.0, beta: float = 1.0):
        self.alpha = alpha
        self.beta = beta
    
    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray):
        """拟合模型"""
        pass
    
    @abstractmethod
    def predict(self, X_test: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        预测后验均值和方差
        
        返回:
            (均值, 方差)
        """
        pass
    
    def rmse(self, X_test: np.ndarray, y_test: np.ndarray) -> float:
        """计算测试集RMSE"""
        mu, _ = self.predict(X_test)
        return np.sqrt(np.mean((mu - y_test)**2))


class LinearBasisCurveFitter(BayesianCurveFitter):
    """
    基于线性基函数的贝叶斯曲线拟合
    
    模型：y = w^T phi(x) + epsilon
    先验：w ~ N(0, alpha^-1 * I)
    
    参数:
        basis_funcs: 基函数列表 phi_j(x)
        alpha: 先验精度
        beta: 噪声精度
    """
    
    def __init__(self, basis_funcs: list, alpha: float = 1.0, beta: float = 1.0):
        super().__init__(alpha, beta)
        self.basis_funcs = basis_funcs
        self.n_basis = len(basis_funcs)
        
        self.posterior_mean = None
        self.posterior_cov = None
    
    def _compute_design_matrix(self, X: np.ndarray) -> np.ndarray:
        """
        计算设计矩阵 Phi
        
        参数:
            X: 输入点 (n,)
            
        返回:
            设计矩阵 (n, n_basis)
        """
        n = len(X)
        Phi = np.zeros((n, self.n_basis))
        
        for i, x in enumerate(X):
            for j, phi in enumerate(self.basis_funcs):
                Phi[i, j] = phi(x)
        
        return Phi
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'LinearBasisCurveFitter':
        """
        贝叶斯拟合
        
        参数:
            X: 训练输入 (n,)
            y: 训练目标 (n,)
        """
        X = np.array(X)
        y = np.array(y)
        
        # 设计矩阵
        Phi = self._compute_design_matrix(X)
        
        # 先验精度矩阵
        alpha_I = self.alpha * np.eye(self.n_basis)
        
        # 后验协方差：Sigma = (beta * Phi^T Phi + alpha * I)^-1
        cov_inv = self.beta * Phi.T @ Phi + alpha_I
        self.posterior_cov = np.linalg.inv(cov_inv + 1e-6 * np.eye(self.n_basis))
        
        # 后验均值：mu = beta * Sigma * Phi^T * y
        self.posterior_mean = self.beta * self.posterior_cov @ Phi.T @ y
        
        return self
    
    def predict(self, X_test: np.ndarray, return_cov: bool = False) -> Tuple[np.ndarray, np.ndarray]:
        """
        预测
        
        参数:
            X_test: 测试点 (m,)
            return_cov: 是否返回完整协方差矩阵
            
        返回:
            (均值, 方差) 或 (均值, 协方差矩阵)
        """
        Phi_test = self._compute_design_matrix(X_test)
        
        # 预测均值
        mu = Phi_test @ self.posterior_mean
        
        # 预测方差
        # var(y*) = phi(x*)^T Sigma phi(x*) + beta^-1
        var = np.sum(Phi_test @ self.posterior_cov * Phi_test, axis=1) + 1.0 / self.beta
        
        if return_cov:
            cov = Phi_test @ self.posterior_cov @ Phi_test.T + (1.0 / self.beta) * np.eye(len(X_test))
            return mu, cov
        else:
            return mu, var
    
    def sample_posterior(self, X_test: np.ndarray, n_samples: int = 10) -> np.ndarray:
        """
        从后验预测分布采样
        
        参数:
            X_test: 测试点
            n_samples: 样本数量
            
        返回:
            采样数组 (n_samples, n_test)
        """
        # 采样权重
        w_samples = np.random.multivariate_normal(
            self.posterior_mean, self.posterior_cov, n_samples
        )
        
        # 计算函数值
        Phi_test = self._compute_design_matrix(X_test)
        f_samples = w_samples @ Phi_test.T
        
        # 添加噪声
        y_samples = f_samples + np.random.randn(n_samples, len(X_test)) / np.sqrt(self.beta)
        
        return y_samples


class PolynomialBasis:
    """多项式基函数"""
    
    @staticmethod
    def monomials(degree: int) -> list:
        """生成单项式基函数列表"""
        return [lambda x, d=i: x**d for i in range(degree + 1)]
    
    @staticmethod
    def legendre(degree: int) -> list:
        """Legendre多项式基"""
        from scipy.special import legendre
        funcs = []
        for i in range(degree + 1):
            L = legendre(i)
            funcs.append(lambda x, L=L: L(x))
        return funcs


class GaussianBasis:
    """高斯基函数"""
    
    @staticmethod
    def create(mus: np.ndarray, sigma: float = 1.0) -> list:
        """
        创建高斯基函数
        
        参数:
            mus: 基函数中心点
            sigma: 标准差
        """
        return [lambda x, mu=m, s=sigma: np.exp(-(x - mu)**2 / (2 * s**2)) 
                for m in mus]


class SinusoidBasis:
    """正弦基函数"""
    
    @staticmethod
    def fourier(frequencies: list) -> list:
        """Fourier基"""
        funcs = [lambda x: 1.0]  # 直流分量
        
        for freq in frequencies:
            funcs.append(lambda x, f=freq: np.sin(2 * np.pi * f * x))
            funcs.append(lambda x, f=freq: np.cos(2 * np.pi * f * x))
        
        return funcs


class BayesianSplineFitter(BayesianCurveFitter):
    """
    贝叶斯样条曲线拟合
    
    使用B样条基函数。
    
    参数:
        knots: 节点位置
        order: 样条阶数
        alpha: 先验精度
        beta: 噪声精度
    """
    
    def __init__(self, knots: np.ndarray, order: int = 3, 
                 alpha: float = 1.0, beta: float = 1.0):
        super().__init__(alpha, beta)
        self.knots = knots
        self.order = order
        self.n_basis = len(knots) + order - 1
        
        self.posterior_mean = None
        self.posterior_cov = None
    
    def _bspline_basis(self, x: float, i: int, k: int, t: np.ndarray) -> float:
        """
        计算B样条基函数值
        
        参数:
            x: 位置
            i: 基函数索引
            k: 阶数
            t: 节点向量
        """
        if k == 0:
            return 1.0 if t[i] <= x < t[i + 1] else 0.0
        
        denom1 = t[i + k] - t[i] if t[i + k] != t[i] else 1.0
        denom2 = t[i + k + 1] - t[i + 1] if t[i + k + 1] != t[i + 1] else 1.0
        
        c1 = 0.0
        if denom1 != 0:
            c1 = (x - t[i]) / denom1 * self._bspline_basis(x, i, k - 1, t)
        
        c2 = 0.0
        if denom2 != 0:
            c2 = (t[i + k + 1] - x) / denom2 * self._bspline_basis(x, i + 1, k - 1, t)
        
        return c1 + c2
    
    def _compute_design_matrix(self, X: np.ndarray) -> np.ndarray:
        """计算B样条设计矩阵"""
        # 扩展节点向量
        t = np.concatenate([
            [self.knots[0]] * self.order,
            self.knots,
            [self.knots[-1]] * self.order
        ])
        
        n = len(X)
        Phi = np.zeros((n, self.n_basis))
        
        for i, x in enumerate(X):
            for j in range(self.n_basis):
                Phi[i, j] = self._bspline_basis(x, j, self.order, t)
        
        return Phi
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'BayesianSplineFitter':
        """拟合"""
        X = np.array(X)
        y = np.array(y)
        
        Phi = self._compute_design_matrix(X)
        
        cov_inv = self.beta * Phi.T @ Phi + self.alpha * np.eye(self.n_basis)
        self.posterior_cov = np.linalg.inv(cov_inv + 1e-6 * np.eye(self.n_basis))
        self.posterior_mean = self.beta * self.posterior_cov @ Phi.T @ y
        
        return self
    
    def predict(self, X_test: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """预测"""
        Phi_test = self._compute_design_matrix(X_test)
        
        mu = Phi_test @ self.posterior_mean
        var = np.sum(Phi_test @ self.posterior_cov * Phi_test, axis=1) + 1.0 / self.beta
        
        return mu, var


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("贝叶斯曲线拟合测试")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 生成非线性函数数据
    def true_function(x):
        return np.sin(2 * np.pi * x) + 0.3 * np.sin(4 * np.pi * x)
    
    n_train = 20
    X_train = np.linspace(0, 1, n_train)
    y_train = true_function(X_train) + 0.1 * np.random.randn(n_train)
    
    # 测试1：多项式基函数
    print("\n1. 多项式基函数贝叶斯曲线拟合:")
    
    poly_degree = 10
    basis = PolynomialBasis.monomials(poly_degree)
    
    fitter_poly = LinearBasisCurveFitter(basis, alpha=0.01, beta=100)
    fitter_poly.fit(X_train, y_train)
    
    X_test = np.linspace(0, 1, 100)
    mu, var = fitter_poly.predict(X_test)
    std = np.sqrt(var)
    
    print(f"   预测均值范围: [{mu.min():.4f}, {mu.max():.4f}]")
    print(f"   预测标准差范围: [{std.min():.4f}, {std.max():.4f}]")
    print(f"   测试RMSE: {fitter_poly.rmse(X_test, true_function(X_test)):.4f}")
    
    # 测试2：高斯基函数
    print("\n2. 高斯基函数贝叶斯曲线拟合:")
    
    n_basis = 15
    mus = np.linspace(0, 1, n_basis)
    gauss_basis = GaussianBasis.create(mus, sigma=0.1)
    
    fitter_gauss = LinearBasisCurveFitter(gauss_basis, alpha=1.0, beta=50)
    fitter_gauss.fit(X_train, y_train)
    
    mu_g, var_g = fitter_gauss.predict(X_test)
    std_g = np.sqrt(var_g)
    
    print(f"   预测均值范围: [{mu_g.min():.4f}, {mu_g.max():.4f}]")
    print(f"   测试RMSE: {fitter_gauss.rmse(X_test, true_function(X_test)):.4f}")
    
    # 测试3：从后验采样
    print("\n3. 后验预测采样:")
    
    samples = fitter_poly.sample_posterior(X_test, n_samples=5)
    print(f"   采样形状: {samples.shape}")
    print(f"   样本1均值: {np.mean(samples[0]):.4f}")
    
    # 测试4：Fourier基
    print("\n4. Fourier基函数曲线拟合:")
    
    freqs = [1, 2, 3, 4]
    fourier_basis = SinusoidBasis.fourier(freqs)
    
    fitter_fourier = LinearBasisCurveFitter(fourier_basis, alpha=1.0, beta=50)
    fitter_fourier.fit(X_train, y_train)
    
    mu_f, var_f = fitter_fourier.predict(X_test)
    print(f"   Fourier基函数数量: {len(fourier_basis)}")
    print(f"   测试RMSE: {fitter_fourier.rmse(X_test, true_function(X_test)):.4f}")
    
    # 测试5：不确定性量化
    print("\n5. 不确定性量化示例:")
    
    # 训练点附近和远离训练点的预测比较
    x_near = 0.25
    x_far = 0.75
    
    _, var_near = fitter_poly.predict(np.array([x_near]))
    _, var_far = fitter_poly.predict(np.array([x_far]))
    
    print(f"   x={x_near} 处的预测方差: {var_near[0]:.4f}")
    print(f"   x={x_far} 处的预测方差: {var_far[0]:.4f}")
    print(f"   远离数据区域的方差更大: {var_far[0] > var_near[0]}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
