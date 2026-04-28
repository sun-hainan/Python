"""
MCMC贝叶斯推断：Metropolis-Hastings与Gibbs采样
MCMC Bayesian Inference: Metropolis-Hastings and Gibbs Sampling

马尔可夫链蒙特卡洛(MCMC)方法通过构建马尔可夫链来近似复杂分布。
Metropolis-Hastings和Gibbs采样是最常用的两种MCMC算法。
"""

import numpy as np
from typing import Dict, List, Callable, Tuple, Optional
from collections import defaultdict
import random


class MetropolisHastings:
    """
    Metropolis-Hastings采样器
    
    参数:
        log_target: 目标分布的对数密度函数
        proposal: 提议分布函数 q(x_new | x_old)
        proposal_sample: 提议分布采样函数
        dim: 变量维度
    """
    
    def __init__(self, log_target: Callable, proposal: Callable, 
                 proposal_sample: Callable, dim: int):
        self.log_target = log_target  # 对数目标密度
        self.proposal = proposal  # 提议密度
        self.proposal_sample = proposal_sample  # 提议采样
        self.dim = dim  # 维度
    
    def sample(self, n_samples: int, burn_in: int = 1000, 
               initial: Optional[np.ndarray] = None) -> np.ndarray:
        """
        运行MCMC采样
        
        参数:
            n_samples: 目标样本数量
            burn_in: 预热期（燃烧期）
            initial: 初始点
            
        返回:
            采样轨迹数组 (n_samples, dim)
        """
        # 初始化
        if initial is None:
            current = np.random.randn(self.dim) * 0.1
        else:
            current = np.array(initial).copy()
        
        samples = []
        n_accepted = 0
        
        # 预热期
        for _ in range(burn_in):
            proposed = self.proposal_sample(current)
            
            # 计算接受率
            log_alpha = (self.log_target(proposed) + 
                        self.proposal(proposed, current) -
                        self.log_target(current) - 
                        self.proposal(current, proposed))
            
            alpha = min(1.0, np.exp(log_alpha))
            
            if np.random.rand() < alpha:
                current = proposed
                n_accepted += 1
        
        # 正式采样
        for _ in range(n_samples):
            proposed = self.proposal_sample(current)
            
            log_alpha = (self.log_target(proposed) + 
                        self.proposal(proposed, current) -
                        self.log_target(current) - 
                        self.proposal(current, proposed))
            
            alpha = min(1.0, np.exp(log_alpha))
            
            if np.random.rand() < alpha:
                current = proposed
                n_accepted += 1
            
            samples.append(current.copy())
        
        acceptance_rate = n_accepted / (burn_in + n_samples)
        
        return np.array(samples), acceptance_rate


class GaussianRandomWalk:
    """
    高斯随机游走提议分布
    
    参数:
        scale: 步长标准差
    """
    
    def __init__(self, scale: float = 0.5):
        self.scale = scale
    
    def sample(self, current: np.ndarray) -> np.ndarray:
        """从高斯随机游走采样"""
        return current + np.random.randn(len(current)) * self.scale
    
    def log_density(self, x_new: np.ndarray, x_old: np.ndarray) -> float:
        """高斯随机游走的对数密度（对称，所以返回0）"""
        return 0.0  # 对称提议，无需修正


class GibbsSampler:
    """
    Gibbs采样器：条件采样
    
    Gibbs采样是MH算法的特例，每步完全条件分布采样。
    
    参数:
        conditionals: 条件分布字典 {变量索引: 条件采样函数}
        initial: 初始点
    """
    
    def __init__(self, conditionals: Dict[int, Callable], initial: np.ndarray):
        self.conditionals = conditionals
        self.current = np.array(initial).copy()
        self.dim = len(initial)
    
    def sample(self, n_samples: int) -> np.ndarray:
        """
        运行Gibbs采样
        
        参数:
            n_samples: 样本数量
            
        返回:
            采样轨迹
        """
        samples = []
        
        for _ in range(n_samples):
            # 依次对每个变量采样
            for i in range(self.dim):
                if i in self.conditionals:
                    # 从条件分布采样
                    self.current[i] = self.conditionals[i](self.current)
            
            samples.append(self.current.copy())
        
        return np.array(samples)


class BayesianLinearRegression:
    """
    贝叶斯线性回归：使用MCMC推断后验
    
    模型：y = X @ w + epsilon, epsilon ~ N(0, sigma^2)
    先验：w ~ N(0, alpha^2 * I)
    """
    
    def __init__(self, X: np.ndarray, y: np.ndarray, 
                 alpha: float = 1.0, sigma: float = 1.0):
        self.X = X  # 设计矩阵 (n, d)
        self.y = y  # 目标值 (n,)
        self.n, self.d = X.shape
        self.alpha = alpha  # 先验精度
        self.sigma = sigma  # 噪声标准差
    
    def log_posterior(self, w: np.ndarray) -> float:
        """
        计算后验的对数密度（未归一化）
        
        参数:
            w: 权重向量
            
        返回:
            对数后验密度
        """
        # 先验：w ~ N(0, alpha^2 * I)
        log_prior = -0.5 * np.sum(w**2) / self.alpha**2
        
        # 似然：y | X, w ~ N(Xw, sigma^2 * I)
        residuals = self.y - self.X @ w
        log_lik = -0.5 * np.sum(residuals**2) / self.sigma**2
        
        return log_prior + log_lik
    
    def sample_posterior(self, n_samples: int, burn_in: int = 1000) -> np.ndarray:
        """
        使用Metropolis-Hastings采样后验
        
        参数:
            n_samples: 样本数量
            burn_in: 燃烧期
            
        返回:
            后验样本 (n_samples, d)
        """
        # 提议分布：高斯随机游走
        proposal = GaussianRandomWalk(scale=0.1)
        
        def proposal_sample(w):
            return proposal.sample(w)
        
        def proposal_log(w_new, w_old):
            return proposal.log_density(w_new, w_old)
        
        # 创建MH采样器
        mh = MetropolisHastings(
            log_target=self.log_posterior,
            proposal=proposal_log,
            proposal_sample=proposal_sample,
            dim=self.d
        )
        
        samples, acc_rate = mh.sample(n_samples, burn_in)
        print(f"   接受率: {acc_rate:.2%}")
        
        return samples


class GaussianMixtureModel:
    """
    高斯混合模型的Gibbs采样推断
    
    模型：
    - z_i ~ Categorical(pi)  混合成分
    - x_i | z_i=k ~ N(mu_k, Sigma_k)  观测模型
    """
    
    def __init__(self, X: np.ndarray, n_components: int, 
                 alpha: float = 1.0):
        self.X = X  # 数据 (n, d)
        self.n, self.d = X.shape
        self.K = n_components  # 成分数
        self.alpha = alpha  # Dirichlet先验参数
        
        # 初始化参数
        self.pi = np.ones(self.K) / self.K  # 混合权重
        self.mu = X[np.random.choice(self.n, self.K, replace=False)]  # 均值
        self.Sigma = [np.eye(self.d) for _ in range(self.K)]  # 协方差
    
    def sample_z(self) -> np.ndarray:
        """采样隐变量z（成分标签）"""
        z = np.zeros(self.n, dtype=int)
        
        for i in range(self.n):
            # 计算每个成分的后验概率
            probs = np.zeros(self.K)
            for k in range(self.K):
                diff = self.X[i] - self.mu[k]
                log_prob = -0.5 * diff @ np.linalg.inv(self.Sigma[k]) @ diff
                log_prob += -0.5 * np.log(np.linalg.det(self.Sigma[k]))
                probs[k] = np.exp(log_prob) * self.pi[k]
            
            probs = probs / np.sum(probs)
            z[i] = np.random.choice(self.K, p=probs)
        
        return z
    
    def update_params(self, z: np.ndarray):
        """根据隐变量更新参数"""
        for k in range(self.K):
            # 属于成分k的样本
            indices = np.where(z == k)[0]
            n_k = len(indices)
            
            if n_k > 0:
                # 更新混合权重
                self.pi[k] = np.random.beta(self.alpha + n_k, 
                                            self.K * self.alpha + self.n - n_k)
                
                # 更新均值和协方差
                X_k = self.X[indices]
                self.mu[k] = np.mean(X_k, axis=0) + np.random.randn(self.d) * 0.1
                self.Sigma[k] = np.eye(self.d)
            else:
                self.pi[k] = 0.01
                self.mu[k] = np.random.randn(self.d)
                self.Sigma[k] = np.eye(self.d)
    
    def fit(self, n_iterations: int) -> Tuple[np.ndarray, List]:
        """
        运行Gibbs采样拟合GMM
        
        参数:
            n_iterations: 迭代次数
            
        返回:
            (样本轨迹, 对数后验历史)
        """
        log_posteriors = []
        
        for t in range(n_iterations):
            # 采样隐变量
            z = self.sample_z()
            
            # 更新参数
            self.update_params(z)
            
            # 计算对数后验（近似）
            log_post = self._log_posterior(z)
            log_posteriors.append(log_post)
            
            if (t + 1) % 10 == 0:
                print(f"   迭代 {t+1}/{n_iterations}, log p(z|X) ≈ {log_post:.2f}")
        
        return z, log_posteriors
    
    def _log_posterior(self, z: np.ndarray) -> float:
        """计算隐变量z的对数后验（近似）"""
        log_p = 0.0
        
        for i in range(self.n):
            k = z[i]
            diff = self.X[i] - self.mu[k]
            log_p += -0.5 * diff @ np.linalg.inv(self.Sigma[k]) @ diff
        
        return log_p


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("MCMC贝叶斯推断测试")
    print("=" * 60)
    
    # 测试1：简单高斯分布采样
    print("\n1. Metropolis-Hastings采样高斯分布:")
    mean_true = np.array([0.0, 0.0])
    cov_true = np.array([[1.0, 0.5], [0.5, 1.0]])
    
    def log_target(x):
        diff = x - mean_true
        return -0.5 * diff @ np.linalg.inv(cov_true) @ diff
    
    proposal = GaussianRandomWalk(scale=0.5)
    
    mh = MetropolisHastings(
        log_target=log_target,
        proposal=lambda x, y: 0.0,
        proposal_sample=proposal.sample,
        dim=2
    )
    
    samples, acc_rate = mh.sample(10000, burn_in=2000)
    print(f"   接受率: {acc_rate:.2%}")
    print(f"   样本均值: {np.mean(samples, axis=0)}")
    print(f"   样本协方差:\n{np.cov(samples.T)}")
    
    # 测试2：贝叶斯线性回归
    print("\n2. 贝叶斯线性回归（MH采样）:")
    np.random.seed(42)
    n = 100
    X = np.column_stack([np.ones(n), np.random.randn(n, 2)])
    true_w = np.array([1.0, 2.0, -1.0])
    y = X @ true_w + np.random.randn(n) * 0.5
    
    blr = BayesianLinearRegression(X, y, alpha=1.0, sigma=0.5)
    posterior_samples = blr.sample_posterior(5000, burn_in=2000)
    
    print(f"   后验均值: {np.mean(posterior_samples, axis=0)}")
    print(f"   后验标准差: {np.std(posterior_samples, axis=0)}")
    
    # 测试3：GMM的Gibbs采样
    print("\n3. GMM的Gibbs采样:")
    np.random.seed(42)
    
    # 生成混合数据
    n1 = 50
    n2 = 50
    X1 = np.random.randn(n1, 2) + np.array([0, 0])
    X2 = np.random.randn(n2, 2) + np.array([3, 3])
    X = np.vstack([X1, X2])
    
    gmm = GaussianMixtureModel(X, n_components=2)
    z_final, log_posts = gmm.fit(n_iterations=50)
    
    print(f"   估计的混合权重: {gmm.pi}")
    print(f"   估计的均值:\n{np.array(gmm.mu)}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
