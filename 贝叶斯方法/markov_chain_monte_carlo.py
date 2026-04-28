"""
马尔可夫链蒙特卡洛(MCMC)基础：MH算法与Gibbs采样
MCMC Foundation: Metropolis-Hastings Algorithm and Gibbs Sampling

MCMC是构建马尔可夫链来从复杂分布抽样的通用方法。
Metropolis-Hastings是最基础的MCMC算法，Gibbs是其特例。
"""

import numpy as np
from typing import Callable, Tuple, Optional, List
from collections import defaultdict
import random


class MetropolisHastings:
    """
    Metropolis-Hastings采样器
    
    核心思想：
    1. 从提议分布 q(x'|x) 生成候选样本 x'
    2. 以概率 min(1, p(x')q(x|x') / (p(x)q(x'|x))) 接受
    
    参数:
        log_target: 目标分布的对数密度函数
        proposal: 提议分布的对数密度函数 log q(x'|x)
        proposal_sample: 提议分布采样函数
        dim: 变量维度
    """
    
    def __init__(self, log_target: Callable, proposal: Callable,
                 proposal_sample: Callable, dim: int):
        self.log_target = log_target
        self.proposal = proposal
        self.proposal_sample = proposal_sample
        self.dim = dim
        
        self.samples = []
        self.acceptance_count = 0
        self.total_count = 0
    
    def run(self, n_samples: int, burn_in: int = 1000,
            initial: Optional[np.ndarray] = None,
            thinning: int = 1) -> np.ndarray:
        """
        运行MCMC采样
        
        参数:
            n_samples: 目标样本数量
            burn_in: 燃烧期
            initial: 初始点
            thinning:  thinning因子，每隔thinning个样本采一个
            
        返回:
            样本数组 (n_samples, dim)
        """
        # 初始化
        if initial is None:
            current = np.random.randn(self.dim)
        else:
            current = np.array(initial, dtype=float)
        
        self.samples = []
        self.acceptance_count = 0
        self.total_count = 0
        
        # 预热期
        for _ in range(burn_in):
            current = self._step(current)
        
        # 正式采样
        collected = 0
        while collected < n_samples:
            current = self._step(current)
            
            if self.total_count % thinning == 0:
                self.samples.append(current.copy())
                collected += 1
        
        return np.array(self.samples)
    
    def _step(self, current: np.ndarray) -> np.ndarray:
        """执行一步MCMC"""
        # 提议
        proposed = self.proposal_sample(current)
        
        # 计算接受率
        log_alpha = (self.log_target(proposed) + 
                    self.proposal(proposed, current) -
                    self.log_target(current) -
                    self.proposal(current, proposed))
        
        alpha = min(1.0, np.exp(log_alpha))
        
        self.total_count += 1
        
        # 接受/拒绝
        if np.random.rand() < alpha:
            self.acceptance_count += 1
            return proposed
        else:
            return current
    
    @property
    def acceptance_rate(self) -> float:
        """接受率"""
        if self.total_count == 0:
            return 0.0
        return self.acceptance_count / self.total_count


class GibbsSampler:
    """
    Gibbs采样器
    
    Gibbs采样是MH算法的特例，每步从完全条件分布采样：
    x_i^(t+1) ~ p(x_i | x_-i^(t))
    
    优点：接受率100%
    缺点：需要能够从完全条件分布采样
    
    参数:
        conditionals: 条件分布字典 {维度: 条件采样函数}
    """
    
    def __init__(self, conditionals: Dict[int, Callable]):
        self.conditionals = conditionals
        self.dim = len(conditionals)
        self.samples = []
    
    def run(self, n_samples: int, initial: Optional[np.ndarray] = None,
            burn_in: int = 0) -> np.ndarray:
        """
        运行Gibbs采样
        
        参数:
            n_samples: 样本数量
            initial: 初始点
            burn_in: 燃烧期（可选）
        """
        if initial is None:
            current = np.random.randn(self.dim)
        else:
            current = np.array(initial, dtype=float)
        
        self.samples = []
        
        total_samples = n_samples + burn_in
        
        for t in range(total_samples):
            # 依次对每个变量采样
            for i in range(self.dim):
                current[i] = self.conditionals[i](current)
            
            # 燃烧期后开始记录
            if t >= burn_in:
                self.samples.append(current.copy())
        
        return np.array(self.samples)


class RandomWalkProposal:
    """
    随机游走提议分布
    
    q(x'|x) = N(x, sigma^2 * I)
    
    参数:
        scale: 步长标准差
    """
    
    def __init__(self, scale: float = 0.5):
        self.scale = scale
    
    def sample(self, current: np.ndarray) -> np.ndarray:
        """生成提议"""
        return current + np.random.randn(len(current)) * self.scale
    
    def log_density(self, proposed: np.ndarray, current: np.ndarray) -> float:
        """提议密度（对称，返回0）"""
        return 0.0  # 对称提议


class IndependentProposal:
    """
    独立提议分布
    
    q(x'|x) = g(x')，与当前状态无关
    
    参数:
        sample_func: 采样函数
        log_density_func: 对数密度函数
    """
    
    def __init__(self, sample_func: Callable, log_density_func: Callable):
        self.sample = sample_func
        self.log_density = log_density_func


class HamiltonianMonteCarlo:
    """
    哈密顿蒙特卡洛 (HMC)
    
    利用梯度信息进行更高效的采样。
    
    参数:
        log_target: 目标分布对数密度
        grad_log_target: 梯度对数密度
        epsilon: 步长
        L: 步数
    """
    
    def __init__(self, log_target: Callable, grad_log_target: Callable,
                 epsilon: float = 0.01, L: int = 10):
        self.log_target = log_target
        self.grad_log_target = grad_log_target
        self.epsilon = epsilon
        self.L = L
    
    def run(self, n_samples: int, dim: int,
            burn_in: int = 1000) -> np.ndarray:
        """运行HMC"""
        samples = []
        current = np.random.randn(dim)
        
        for _ in range(burn_in + n_samples):
            current = self._step(current)
            
            if _ >= burn_in:
                samples.append(current.copy())
        
        return np.array(samples)
    
    def _leapfrog(self, q: np.ndarray, p: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Leapfrog积分器"""
        for _ in range(self.L):
            # 半步动量
            p_half = p + 0.5 * self.epsilon * self.grad_log_target(q)
            # 全步位置
            q = q + self.epsilon * p_half
            # 半步动量
            p = p_half + 0.5 * self.epsilon * self.grad_log_target(q)
        
        return q, -p  # 翻转动量（对称）
    
    def _step(self, q: np.ndarray) -> np.ndarray:
        """一步HMC"""
        # 采样动量
        p = np.random.randn(len(q))
        
        # 提议
        q_new, p_new = self._leapfrog(q, p)
        
        # 计算接受率
        log_alpha = (self.log_target(q_new) - self.log_target(q) -
                    0.5 * np.sum(p_new**2) + 0.5 * np.sum(p**2))
        
        alpha = min(1.0, np.exp(log_alpha))
        
        if np.random.rand() < alpha:
            return q_new
        else:
            return q


class MCMCDiagnostics:
    """MCMC诊断工具"""
    
    @staticmethod
    def autocorrelation(samples: np.ndarray, max_lag: int = 50) -> np.ndarray:
        """
        计算自相关函数
        
        参数:
            samples: 样本序列 (n_samples, dim) 或 (n_samples,)
            max_lag: 最大滞后
            
        返回:
            自相关数组
        """
        if samples.ndim == 1:
            samples = samples.reshape(-1, 1)
        
        n = len(samples)
        mean = np.mean(samples, axis=0)
        var = np.var(samples, axis=0)
        
        acf = np.zeros((max_lag + 1, samples.shape[1]))
        acf[0] = 1.0
        
        for lag in range(1, max_lag + 1):
            cov = np.mean((samples[:-lag] - mean) * (samples[lag:] - mean), axis=0)
            with np.errstate(divide='ignore', invalid='ignore'):
                acf[lag] = cov / var
                acf[lag] = np.where(var > 0, acf[lag], 0)
        
        return acf
    
    @staticmethod
    def effective_sample_size(samples: np.ndarray) -> float:
        """
        估计有效样本量(ESS)
        
        参数:
            samples: 样本序列
            
        返回:
            ESS估计值
        """
        acf = MCMCDiagnostics.autocorrelation(samples)
        
        # 找到截断点（ACF首次变负）
        n = len(samples)
        for i in range(1, len(acf)):
            if acf[i] < 0:
                n = i
                break
        
        # ESS = n / (1 + 2 * sum(acf))
        ess = n / (1 + 2 * np.sum(acf[1:n]))
        
        return max(1, ess)


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("MCMC基础算法测试")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 测试1：MH采样二元高斯
    print("\n1. Metropolis-Hastings采样二元高斯分布:")
    
    mean = np.array([0.0, 0.0])
    cov = np.array([[1.0, 0.7], [0.7, 1.0]])
    
    def log_target(x):
        diff = x - mean
        return -0.5 * diff @ np.linalg.inv(cov) @ diff
    
    proposal = RandomWalkProposal(scale=0.5)
    
    mh = MetropolisHastings(
        log_target=log_target,
        proposal=proposal.log_density,
        proposal_sample=proposal.sample,
        dim=2
    )
    
    samples = mh.run(n_samples=5000, burn_in=2000)
    
    print(f"   接受率: {mh.acceptance_rate:.2%}")
    print(f"   样本均值: {np.mean(samples, axis=0)}")
    print(f"   样本协方差:\n{np.cov(samples.T)}")
    
    # 测试2：Gibbs采样混合分布
    print("\n2. Gibbs采样双峰分布:")
    
    def conditional_x(y):
        """P(x|y) ~ N(mix_mean, mix_var)"""
        mix_mean = 5.0 if y > 0.5 else -5.0
        return mix_mean + np.random.randn() * 0.5
    
    def conditional_y(x):
        """P(y|x) ~ Bernoulli(sigmoid(x))"""
        p = 1 / (1 + np.exp(-x))
        return 1 if np.random.rand() < p else 0
    
    gibbs = GibbsSampler({0: conditional_x, 1: conditional_y})
    gibbs_samples = gibbs.run(n_samples=3000, burn_in=1000)
    
    print(f"   x均值: {np.mean(gibbs_samples[:, 0]):.2f}")
    print(f"   y=1比例: {np.mean(gibbs_samples[:, 1]):.2f}")
    
    # 测试3：HMC采样
    print("\n3. Hamiltonian Monte Carlo采样:")
    
    def log_target_hmc(x):
        return -0.5 * np.sum(x**2)
    
    def grad_log_target(x):
        return -x
    
    hmc = HamiltonianMonteCarlo(log_target_hmc, grad_log_target, 
                                epsilon=0.1, L=10)
    hmc_samples = hmc.run(n_samples=3000, dim=2, burn_in=1000)
    
    print(f"   HMC样本均值: {np.mean(hmc_samples, axis=0)}")
    print(f"   HMC样本协方差:\n{np.cov(hmc_samples.T)}")
    
    # 测试4：诊断工具
    print("\n4. MCMC诊断:")
    
    diag = MCMCDiagnostics()
    
    # 计算自相关
    acf = diag.autocorrelation(samples[:, 0], max_lag=30)
    print(f"   滞后5自相关: {acf[5]:.4f}")
    print(f"   滞后10自相关: {acf[10]:.4f}")
    
    # 有效样本量
    ess = diag.effective_sample_size(samples[:, 0])
    print(f"   有效样本量: {ess:.1f} / {len(samples)}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
