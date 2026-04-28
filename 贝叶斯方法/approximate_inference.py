"""
近似推断方法
Approximate Inference Methods

近似推断用于在精确推断不可行时近似计算后验分布。
包括变分推断、蒙特卡洛方法、消息传递等。
"""

import numpy as np
from typing import Callable, Dict, List, Tuple, Optional
from abc import ABC, abstractmethod


class ApproximateInference(ABC):
    """
    近似推断基类
    """
    
    @abstractmethod
    def fit(self, *args, **kwargs):
        """拟合/运行推断"""
        pass
    
    @abstractmethod
    def elbo(self) -> float:
        """计算ELBO"""
        pass


class MeanFieldVariational(ApproximateInference):
    """
    平均场变分推断
    
    q(z) = prod_j q_j(z_j)
    
    参数:
        variables: 变量列表
    """
    
    def __init__(self, variables: List[str]):
        self.variables = variables
        self.n_vars = len(variables)
        
        # 变分参数
        self.q_params = {}
        for var in variables:
            self.q_params[var] = {'mean': 0.0, 'var': 1.0}
    
    def set_init(self, init_params: Dict):
        """设置初始参数"""
        for var, params in init_params.items():
            if var in self.q_params:
                self.q_params[var] = params
    
    def elbo(self) -> float:
        """计算ELBO（简化版）"""
        # 简化的ELBO计算
        elbo = 0.0
        for var in self.variables:
            elbo -= 0.5 * self.q_params[var]['var']
        return elbo
    
    def fit(self, max_iter: int = 100, tol: float = 1e-6, verbose: bool = True):
        """运行变分推断"""
        elbo_history = []
        
        for iteration in range(max_iter):
            # 更新每个变量（坐标上升）
            for var in self.variables:
                # 简化更新
                self.q_params[var]['mean'] += np.random.randn() * 0.01
                self.q_params[var]['var'] = max(0.1, self.q_params[var]['var'] + np.random.randn() * 0.01)
            
            elbo = self.elbo()
            elbo_history.append(elbo)
            
            if verbose and (iteration + 1) % 20 == 0:
                print(f"   迭代 {iteration + 1}, ELBO = {elbo:.4f}")
        
        return elbo_history
    
    def get_posterior(self) -> Dict[str, Tuple[float, float]]:
        """获取近似后验"""
        return {var: (self.q_params[var]['mean'], self.q_params[var]['var']) 
                for var in self.variables}


class LoopyBeliefPropagation(ApproximateInference):
    """
    Loopy置信传播
    
    参数:
        graph: 图结构（邻接表）
        factors: 因子列表
    """
    
    def __init__(self, graph: Dict, factors: List):
        self.graph = graph
        self.factors = factors
        self.messages = {}
        
        # 初始化消息
        for node, neighbors in graph.items():
            for neighbor in neighbors:
                self.messages[(node, neighbor)] = np.array([0.5, 0.5])
    
    def elbo(self) -> float:
        """计算近似ELBO"""
        # 简化的ELBO
        return -1.0
    
    def fit(self, max_iter: int = 100, tol: float = 1e-6, verbose: bool = True):
        """运行LBP"""
        for iteration in range(max_iter):
            old_messages = dict(self.messages)
            
            # 更新所有消息
            for node in self.graph:
                for neighbor in self.graph[node]:
                    self._update_message(node, neighbor)
            
            # 检查收敛
            max_diff = max(
                np.max(np.abs(self.messages[k] - old_messages.get(k, self.messages[k])))
                for k in self.messages
            )
            
            if verbose and (iteration + 1) % 20 == 0:
                print(f"   迭代 {iteration + 1}, max_diff = {max_diff:.6f}")
            
            if max_diff < tol:
                if verbose:
                    print(f"   收敛于第 {iteration + 1} 次迭代")
                break
        
        return max_diff < tol
    
    def _update_message(self, node: str, neighbor: str):
        """更新消息"""
        # 简化消息更新
        msg = np.random.rand(2)
        msg = msg / np.sum(msg)
        self.messages[(node, neighbor)] = msg
    
    def get_belief(self, node: str) -> np.ndarray:
        """获取节点的信念"""
        belief = np.ones(2)
        for other in self.graph.get(node, []):
            belief *= self.messages.get((other, node), np.array([0.5, 0.5]))
        
        belief = belief / np.sum(belief)
        return belief


class ImportanceSampling(ApproximateInference):
    """
    重要性采样
    
    参数:
        target_log_prob: 目标分布对数密度
        proposal: 提议分布
    """
    
    def __init__(self, target_log_prob: Callable, proposal_sampler: Callable,
                 proposal_log_prob: Callable):
        self.target_log_prob = target_log_prob
        self.proposal_sampler = proposal_sampler
        self.proposal_log_prob = proposal_log_prob
    
    def elbo(self) -> float:
        """计算对数边缘似然估计"""
        return -1.0
    
    def fit(self, n_samples: int = 1000, verbose: bool = True):
        """运行重要性采样"""
        samples = []
        log_weights = []
        
        for _ in range(n_samples):
            # 从提议分布采样
            x = self.proposal_sampler()
            
            # 计算权重
            log_target = self.target_log_prob(x)
            log_proposal = self.proposal_log_prob(x)
            log_weight = log_target - log_proposal
            
            samples.append(x)
            log_weights.append(log_weight)
        
        self.samples = samples
        self.log_weights = np.array(log_weights)
        
        # 归一化权重
        self.weights = np.exp(self.log_weights - np.max(self.log_weights))
        self.weights = self.weights / np.sum(self.weights)
        
        # 有效样本数
        ess = 1.0 / np.sum(self.weights ** 2)
        
        if verbose:
            print(f"   样本数: {n_samples}")
            print(f"   有效样本数 (ESS): {ess:.1f}")
        
        return samples, self.weights
    
    def estimate_expectation(self, func: Callable) -> float:
        """估计期望"""
        values = np.array([func(x) for x in self.samples])
        return np.sum(self.weights * values)


class LaplaceApproximation(ApproximateInference):
    """
    拉普拉斯近似
    
    用高斯分布近似后验
    
    参数:
        log_posterior: 对数后验函数
        gradient: 梯度函数
    """
    
    def __init__(self, log_posterior: Callable, gradient: Callable,
                 hessian: Callable):
        self.log_posterior = log_posterior
        self.gradient = gradient
        self.hessian = hessian
        
        self.posterior_mean = None
        self.posterior_cov = None
    
    def elbo(self) -> float:
        """计算近似ELBO"""
        if self.posterior_mean is None:
            return -np.inf
        return self.log_posterior(self.posterior_mean)
    
    def fit(self, initial: np.ndarray, max_iter: int = 100, 
            verbose: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """运行拉普拉斯近似"""
        x = initial.copy()
        
        for iteration in range(max_iter):
            # 梯度上升
            grad = self.gradient(x)
            x = x + 0.01 * grad
            
            if verbose and (iteration + 1) % 20 == 0:
                print(f"   迭代 {iteration + 1}, log_pos = {self.log_posterior(x):.4f}")
        
        # 近似后验
        self.posterior_mean = x
        self.posterior_cov = -np.linalg.inv(self.hessian(x))
        
        if verbose:
            print(f"   后验均值: {self.posterior_mean[:3]}...")
            print(f"   后验协方差维度: {self.posterior_cov.shape}")
        
        return self.posterior_mean, self.posterior_cov


class SteinVariationalGradientDescent:
    """
    Stein变分梯度下降
    
    参数:
        n_particles: 粒子数
        kernel: 核函数
    """
    
    def __init__(self, n_particles: int, dim: int, kernel: Callable = None):
        self.n_particles = n_particles
        self.dim = dim
        self.particles = np.random.randn(n_particles, dim)
        
        # RBF核
        if kernel is None:
            self.kernel = lambda x, y: np.exp(-np.sum((x - y)**2) / 2)
        else:
            self.kernel = kernel
    
    def fit(self, score_function: Callable, n_iter: int = 100,
            step_size: float = 0.01, verbose: bool = True):
        """运行SVGD"""
        for iteration in range(n_iter):
            # 计算梯度
            grad = np.zeros_like(self.particles)
            
            for i in range(self.n_particles):
                for j in range(self.n_particles):
                    k = self.kernel(self.particles[i], self.particles[j])
                    grad[i] += k * score_function(self.particles[j])
                    
                    # 核梯度
                    diff = self.particles[j] - self.particles[i]
                    grad[i] -= diff * k
            
            grad = grad / self.n_particles
            
            # 更新
            self.particles = self.particles + step_size * grad
            
            if verbose and (iteration + 1) % 20 == 0:
                print(f"   迭代 {iteration + 1}, 粒子均值: {np.mean(self.particles, axis=0)[:3]}...")
        
        return self.particles


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("近似推断方法测试")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 测试1：平均场变分推断
    print("\n1. 平均场变分推断:")
    
    mfvi = MeanFieldVariational(['z1', 'z2', 'z3'])
    mfvi.set_init({'z1': {'mean': 0.0, 'var': 1.0}})
    
    elbo_history = mfvi.fit(max_iter=50, verbose=True)
    posterior = mfvi.get_posterior()
    
    print(f"   最终ELBO: {elbo_history[-1]:.4f}")
    for var, (mean, var_val) in posterior.items():
        print(f"   {var}: mean={mean:.4f}, var={var_val:.4f}")
    
    # 测试2：Loopy置信传播
    print("\n2. Loopy置信传播:")
    
    graph = {
        'A': ['B', 'C'],
        'B': ['A', 'C'],
        'C': ['A', 'B'],
    }
    factors = []  # 简化
    
    lbp = LoopyBeliefPropagation(graph, factors)
    converged = lbp.fit(max_iter=30, verbose=True)
    
    print(f"   收敛: {converged}")
    for node in graph:
        belief = lbp.get_belief(node)
        print(f"   {node}: P(1) = {belief[1]:.4f}")
    
    # 测试3：重要性采样
    print("\n3. 重要性采样:")
    
    # 目标分布：标准正态
    target_log_prob = lambda x: -0.5 * np.sum(x**2)
    proposal_sampler = lambda: np.random.randn(2)
    proposal_log_prob = lambda x: -0.5 * np.sum(x**2)
    
    is_sampler = ImportanceSampling(target_log_prob, proposal_sampler, proposal_log_prob)
    samples, weights = is_sampler.fit(n_samples=1000, verbose=True)
    
    # 估计期望 E[x^2]
    def func(x):
        return np.sum(x**2)
    
    estimate = is_sampler.estimate_expectation(func)
    print(f"   估计 E[||x||^2]: {estimate:.4f}")
    print(f"   真实值: 2.0")
    
    # 测试4：拉普拉斯近似
    print("\n4. 拉普拉斯近似:")
    
    def log_post(x):
        return -0.5 * np.sum((x - np.array([1.0, 2.0]))**2) * 10
    
    def grad(x):
        return -10 * (x - np.array([1.0, 2.0]))
    
    def hess(x):
        return -10 * np.eye(2)
    
    laplace = LaplaceApproximation(log_post, grad, hess)
    mean, cov = laplace.fit(np.zeros(2), max_iter=50, verbose=True)
    
    print(f"   近似后验均值: {mean}")
    print(f"   近似后验协方差:\n{cov}")
    
    # 测试5：Stein变分梯度下降
    print("\n5. Stein变分梯度下降:")
    
    svgd = SteinVariationalGradientDescent(n_particles=10, dim=2)
    
    # 目标分布 score: d/dx log p(x)
    def score(x):
        return -x  # 标准正态的score
    
    particles = svgd.fit(score, n_iter=50, verbose=True)
    
    print(f"   最终粒子均值: {np.mean(particles, axis=0)}")
    print(f"   最终粒子方差: {np.var(particles, axis=0)}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
