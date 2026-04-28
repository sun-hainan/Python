"""
贝叶斯优化：EI采集函数与高斯过程
Bayesian Optimization: Expected Improvement Acquisition and Gaussian Process

贝叶斯优化用于优化黑盒函数，通过代理模型(高斯过程)建模目标函数，
并使用采集函数决定下一步采样的位置。
"""

import numpy as np
from typing import Callable, Tuple, Optional, List
from collections import defaultdict


class GaussianProcess:
    """
    高斯过程回归
    
    参数:
        kernel: 核函数
        noise: 观测噪声方差
    """
    
    def __init__(self, kernel: Callable, noise: float = 1e-6):
        self.kernel = kernel  # 核函数 k(x, x')
        self.noise = noise  # 噪声方差
        self.X_train = None  # 训练数据
        self.y_train = None
        self.K = None  # 协方差矩阵
        self.K_inv = None  # 协方差矩阵的逆
    
    def fit(self, X: np.ndarray, y: np.ndarray):
        """
        训练高斯过程
        
        参数:
            X: 训练输入 (n, d)
            y: 训练输出 (n,)
        """
        self.X_train = np.array(X)
        self.y_train = np.array(y)
        n = len(y)
        
        # 构建协方差矩阵
        self.K = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                self.K[i, j] = self.kernel(X[i], X[j])
        
        # 加入噪声
        self.K = self.K + self.noise * np.eye(n)
        
        # 计算逆矩阵
        self.K_inv = np.linalg.inv(self.K)
    
    def predict(self, X_test: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        预测均值和方差
        
        参数:
            X_test: 测试点 (m, d)
            
        返回:
            (均值, 方差)
        """
        X_test = np.array(X_test)
        n_train = len(self.y_train)
        m = len(X_test)
        
        # 计算测试点与训练点之间的协方差
        k_star = np.zeros((m, n_train))
        for i in range(m):
            for j in range(n_train):
                k_star[i, j] = self.kernel(X_test[i], self.X_train[j])
        
        # 预测均值
        alpha = self.K_inv @ self.y_train
        mu = k_star @ alpha
        
        # 预测方差
        k_star_star = np.zeros(m)
        for i in range(m):
            k_star_star[i] = self.kernel(X_test[i], X_test[i])
        
        var = k_star_star - np.sum(k_star @ self.K_inv * k_star, axis=1)
        var = np.maximum(var, 0)  # 数值稳定性
        
        return mu, var
    
    def predict_single(self, x: np.ndarray) -> Tuple[float, float]:
        """预测单个点"""
        mu, var = self.predict(x.reshape(1, -1))
        return float(mu), float(var)


class RBFKernel:
    """
    径向基函数(RBF)核 / 高斯核
    
    k(x, x') = exp(-||x - x'||^2 / (2 * l^2))
    
    参数:
        length_scale: 长度尺度参数l
    """
    
    def __init__(self, length_scale: float = 1.0):
        self.length_scale = length_scale
    
    def __call__(self, x1: np.ndarray, x2: np.ndarray) -> float:
        """计算核函数值"""
        diff = x1 - x2
        return np.exp(-np.sum(diff**2) / (2 * self.length_scale**2))


class ExpectedImprovement:
    """
    期望改进量(Expected Improvement)采集函数
    
    EI(x) = E[max(0, f_best - f(x))]
    
    参数:
        y_best: 当前最优观测值
        xi: 探索参数（鼓励探索）
    """
    
    def __init__(self, y_best: float, xi: float = 0.01):
        self.y_best = y_best  # 当前最优
        self.xi = xi  # 探索参数
    
    def evaluate(self, mu: float, var: float) -> float:
        """
        计算期望改进量
        
        参数:
            mu: 预测均值
            var: 预测方差
            
        返回:
            EI值
        """
        if var < 1e-10:
            return 0.0
        
        sigma = np.sqrt(var)
        
        # 标准化改进量
        z = (self.y_best - mu - self.xi) / sigma
        
        # EI = (y_best - mu - xi) * Phi(z) + sigma * phi(z)
        from scipy.stats import norm
        phi = norm.pdf(z)  # 标准正态密度
        Phi = norm.cdf(z)  # 标准正态累积分布
        
        ei = (self.y_best - mu - self.xi) * Phi + sigma * phi
        
        return max(0.0, ei)
    
    def evaluate_batch(self, X: np.ndarray, gp: GaussianProcess) -> np.ndarray:
        """
        批量计算EI
        
        参数:
            X: 测试点 (m, d)
            gp: 高斯过程模型
            
        返回:
            EI值数组 (m,)
        """
        mu, var = gp.predict(X)
        ei_values = np.array([self.evaluate(m, v) for m, v in zip(mu, var)])
        return ei_values


class BayesianOptimizer:
    """
    贝叶斯优化器
    
    参数:
        obj_func: 目标函数（最小化）
        bounds: 变量边界 (d, 2) 数组
        kernel: 核函数
        n_initial: 初始采样点数
        noise: 观测噪声
    """
    
    def __init__(self, obj_func: Callable, bounds: np.ndarray, 
                 kernel: Optional[RBFKernel] = None,
                 n_initial: int = 5, noise: float = 1e-6):
        self.obj_func = obj_func  # 目标函数
        self.bounds = bounds  # (d, 2): 下界和上界
        self.d = bounds.shape[0]  # 维度
        self.noise = noise
        
        # 核函数
        if kernel is None:
            self.kernel = RBFKernel(length_scale=1.0)
        else:
            self.kernel = kernel
        
        # 高斯过程
        self.gp = GaussianProcess(self.kernel, noise)
        
        # 数据存储
        self.X_data = []
        self.y_data = []
        self.n_initial = n_initial
        
        # 采集函数
        self.acquisition = None
    
    def _random_sample(self) -> np.ndarray:
        """在边界内随机采样"""
        return np.random.uniform(self.bounds[:, 0], self.bounds[:, 1])
    
    def _get_best(self) -> float:
        """获取当前最优值"""
        return np.min(self.y_data)
    
    def _optimize_acquisition(self, n_candidates: int = 100) -> np.ndarray:
        """
        优化采集函数找到下一个采样点
        
        参数:
            n_candidates: 候选点数量
            
        返回:
            下一个采样点
        """
        # 生成候选点
        candidates = np.zeros((n_candidates, self.d))
        for d in range(self.d):
            candidates[:, d] = np.random.uniform(
                self.bounds[d, 0], self.bounds[d, 1], n_candidates
            )
        
        # 计算采集函数值
        ei_values = self.acquisition.evaluate_batch(candidates, self.gp)
        
        # 选择最优
        best_idx = np.argmax(ei_values)
        return candidates[best_idx]
    
    def _observe(self, x: np.ndarray) -> float:
        """评估目标函数"""
        return self.obj_func(x)
    
    def suggest(self) -> np.ndarray:
        """
        建议下一个采样点
        
        返回:
            建议的点
        """
        if len(self.X_data) < self.n_initial:
            # 随机采样
            return self._random_sample()
        else:
            # 优化采集函数
            return self._optimize_acquisition()
    
    def observe(self, x: np.ndarray) -> float:
        """
        观察点x的目标值并更新
        
        参数:
            x: 采样点
            
        返回:
            观测值
        """
        y = self._observe(x)
        
        self.X_data.append(x)
        self.y_data.append(y)
        
        # 重新训练高斯过程
        self.gp.fit(np.array(self.X_data), np.array(self.y_data))
        
        # 更新采集函数
        self.acquisition = ExpectedImprovement(self._get_best())
        
        return y
    
    def run(self, n_iterations: int, verbose: bool = True) -> Tuple[List, List]:
        """
        运行贝叶斯优化
        
        参数:
            n_iterations: 总迭代次数
            verbose: 是否打印
            
        返回:
            (X历史, y历史)
        """
        # 初始采样
        if verbose:
            print("   初始采样阶段...")
        
        for _ in range(self.n_initial):
            x = self._random_sample()
            self.observe(x)
            if verbose:
                print(f"   x = {x}, y = {self.y_data[-1]:.4f}")
        
        # 优化循环
        if verbose:
            print("\n   贝叶斯优化阶段...")
        
        for i in range(n_iterations - self.n_initial):
            # 建议下一个点
            x_next = self.suggest()
            
            # 观察
            y_next = self.observe(x_next)
            
            if verbose:
                print(f"   迭代 {i + 1}: x = {x_next}, y = {y_next:.4f}, "
                      f"最优 = {self._get_best():.4f}")
        
        return self.X_data, self.y_data


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("贝叶斯优化测试")
    print("=" * 60)
    
    # 测试1：高斯过程拟合
    print("\n1. 高斯过程拟合:")
    
    np.random.seed(42)
    
    # 生成训练数据
    X_train = np.array([[0.0], [1.0], [2.0], [3.0], [4.0]])
    y_train = np.sin(X_train.flatten()) + 0.1 * np.random.randn(5)
    
    # 训练GP
    gp = GaussianProcess(RBFKernel(length_scale=1.0), noise=0.01)
    gp.fit(X_train, y_train)
    
    # 预测
    X_test = np.linspace(0, 4, 100).reshape(-1, 1)
    mu, var = gp.predict(X_test)
    
    print(f"   预测均值范围: [{mu.min():.4f}, {mu.max():.4f}]")
    print(f"   预测方差范围: [{var.min():.6f}, {var.max():.6f}]")
    
    # 测试2：期望改进量计算
    print("\n2. 期望改进量(EI)计算:")
    
    y_best = 0.5  # 当前最优
    ei = ExpectedImprovement(y_best, xi=0.01)
    
    # 不同均值和方差下的EI
    test_cases = [
        (0.8, 0.1),
        (0.3, 0.5),
        (0.1, 1.0),
        (0.5, 0.2),
    ]
    
    for mu, var in test_cases:
        ei_val = ei.evaluate(mu, var)
        print(f"   mu={mu:.1f}, var={var:.1f} -> EI={ei_val:.4f}")
    
    # 测试3：贝叶斯优化最小化函数
    print("\n3. 贝叶斯优化示例:")
    
    def objective(x):
        """测试函数：一维Rosenbrock"""
        x = x[0]
        return (1 - x)**2 + 100 * (x**2 - 1)**2
    
    bounds = np.array([[-2.0, 2.0]])
    
    optimizer = BayesianOptimizer(
        obj_func=objective,
        bounds=bounds,
        kernel=RBFKernel(length_scale=0.5),
        n_initial=3,
        noise=0.01
    )
    
    X_history, y_history = optimizer.run(n_iterations=10, verbose=True)
    
    print(f"\n   最优解: x = {X_history[np.argmin(y_history)]}")
    print(f"   最优值: y = {min(y_history):.6f}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
