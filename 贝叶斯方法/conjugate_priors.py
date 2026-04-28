"""
共轭先验与指数族分布
Conjugate Priors and Exponential Family

共轭先验是贝叶斯推断中的重要概念。
当先验与似然共轭时，后验与先验具有相同的函数形式，简化计算。
指数族分布具有闭式共轭先验。
"""

import numpy as np
from typing import Tuple, Optional, Dict, Callable
from scipy import special


class ExponentialFamily:
    """
    指数族分布基类
    
    形式：p(x|theta) = h(x) * exp(eta(theta) * T(x) - A(theta))
    
    参数:
        natural_params: 自然参数 eta
        sufficient_stats: 充分统计量 T(x)
        log_partition: 对数配分函数 A(eta)
        base_measure: 基础测度 h(x)
    """
    
    def __init__(self, natural_params: np.ndarray, 
                 base_measure: Callable = None):
        self.natural_params = natural_params
        self.base_measure = base_measure or (lambda x: 1.0)
        self._verify_params()
    
    def _verify_params(self):
        """验证参数维度"""
        pass
    
    def log_pdf(self, x: np.ndarray) -> float:
        """
        计算对数概率密度
        
        log p(x|eta) = eta^T * T(x) - A(eta) + log h(x)
        """
        eta = self.natural_params
        T_x = self.sufficient_statistics(x)
        A_eta = self.log_partition(eta)
        h_x = self.base_measure(x)
        
        return np.dot(eta, T_x) - A_eta + np.log(h_x + 1e-10)
    
    def pdf(self, x: np.ndarray) -> float:
        """概率密度"""
        return np.exp(self.log_pdf(x))
    
    def sufficient_statistics(self, x: np.ndarray) -> np.ndarray:
        """充分统计量"""
        raise NotImplementedError
    
    def log_partition(self, eta: np.ndarray) -> float:
        """对数配分函数"""
        raise NotImplementedError


class BernoulliConjugate(ExponentialFamily):
    """
    伯努利分布的共轭先验：Beta-Bernoulli
    
    似然：x ~ Bernoulli(p)
    先验：p ~ Beta(alpha, beta)
    后验：p | x ~ Beta(alpha + x, beta + 1 - x)
    """
    
    def __init__(self, alpha: float = 1.0, beta: float = 1.0):
        self.alpha = alpha
        self.beta = beta
        # Beta分布的自然参数
        eta1 = alpha - 1
        eta2 = beta - 1
        super().__init__(natural_params=np.array([eta1, eta2]))
    
    def sufficient_statistics(self, x: np.ndarray) -> np.ndarray:
        """充分统计量: [x, 1-x]"""
        return np.array([x, 1 - x])
    
    def log_partition(self, eta: np.ndarray) -> float:
        """
        对数配分函数：A(eta) = log B(alpha, beta)
                              = log Gamma(alpha) + log Gamma(beta) - log Gamma(alpha+beta)
        """
        alpha = eta[0] + 1
        beta = eta[1] + 1
        
        return (special.gammaln(alpha) + special.gammaln(beta) - 
                special.gammaln(alpha + beta))
    
    def posterior_update(self, data: np.ndarray) -> 'BernoulliConjugate':
        """
        更新后验
        
        参数:
            data: 伯努利数据 (0或1)
            
        返回:
            后验Beta分布
        """
        n_success = np.sum(data)
        n_trials = len(data)
        n_failures = n_trials - n_success
        
        return BernoulliConjugate(
            alpha=self.alpha + n_success,
            beta=self.beta + n_failures
        )
    
    def posterior_mean(self) -> float:
        """后验均值"""
        return self.alpha / (self.alpha + self.beta)
    
    def posterior_mode(self) -> float:
        """后验众数"""
        if self.alpha > 1 and self.beta > 1:
            return (self.alpha - 1) / (self.alpha + self.beta - 2)
        return self.posterior_mean()


class NormalConjugate(ExponentialFamily):
    """
    正态分布的共轭先验：Normal-Normal
    
    似然：x_i ~ N(mu, sigma^2) 或 x_i ~ N(mu, sigma^2) with known sigma
    先验：mu ~ N(mu_0, sigma_0^2)
    后验：mu | x ~ N(mu_n, sigma_n^2)
    
    参数:
        prior_mu: 先验均值
        prior_var: 先验方差
        likelihood_var: 似然方差
    """
    
    def __init__(self, prior_mu: float = 0.0, prior_var: float = 1.0,
                 likelihood_var: float = 1.0):
        self.prior_mu = prior_mu
        self.prior_var = prior_var
        self.likelihood_var = likelihood_var
        
        # 自然参数
        eta1 = prior_mu / prior_var
        eta2 = -1 / (2 * prior_var)
        super().__init__(natural_params=np.array([eta1, eta2]))
    
    def sufficient_statistics(self, x: np.ndarray) -> np.ndarray:
        """充分统计量: [sum(x), sum(x^2)]"""
        return np.array([np.sum(x), np.sum(x**2)])
    
    def log_partition(self, eta: np.ndarray) -> float:
        """对数配分函数"""
        eta1, eta2 = eta
        return eta1**2 / (4 * eta2) - 0.5 * np.log(-2 * eta2)
    
    def posterior_update(self, data: np.ndarray) -> 'NormalConjugate':
        """
        更新后验
        
        参数:
            data: 观测数据
            
        返回:
            后验Normal分布
        """
        n = len(data)
        x_bar = np.mean(data)
        
        # 后验方差
        posterior_var = 1 / (1 / self.prior_var + n / self.likelihood_var)
        
        # 后验均值
        posterior_mu = posterior_var * (
            self.prior_mu / self.prior_var + 
            n * x_bar / self.likelihood_var
        )
        
        return NormalConjugate(
            prior_mu=posterior_mu,
            prior_var=posterior_var,
            likelihood_var=self.likelihood_var
        )
    
    def posterior_mean(self) -> float:
        """后验均值"""
        return self.prior_mu
    
    def posterior_predictive(self, n_new: int = 1) -> Tuple[float, float]:
        """
        后验预测分布
        
        返回:
            (均值, 方差)
        """
        # 预测均值
        pred_mean = self.prior_mu
        
        # 预测方差
        pred_var = self.likelihood_var + self.prior_var
        
        return pred_mean, pred_var


class PoissonConjugate(ExponentialFamily):
    """
    泊松分布的共轭先验：Gamma-Poisson
    
    似然：x ~ Poisson(lambda)
    先验：lambda ~ Gamma(alpha, beta)
    后验：lambda | x ~ Gamma(alpha + sum(x), beta + n)
    """
    
    def __init__(self, alpha: float = 1.0, beta: float = 1.0):
        self.alpha = alpha
        self.beta = beta
        
        # 自然参数
        eta = np.log(beta)
        super().__init__(natural_params=np.array([alpha, eta]))
    
    def sufficient_statistics(self, x: np.ndarray) -> np.ndarray:
        """充分统计量: [sum(x), n]"""
        return np.array([np.sum(x), len(x)])
    
    def log_partition(self, eta: np.ndarray) -> float:
        """对数配分函数"""
        alpha, log_beta = eta
        return alpha * log_beta - special.gammaln(alpha)
    
    def posterior_update(self, data: np.ndarray) -> 'PoissonConjugate':
        """
        更新后验
        
        参数:
            data: 泊松计数数据
        """
        sum_data = np.sum(data)
        n = len(data)
        
        return PoissonConjugate(
            alpha=self.alpha + sum_data,
            beta=self.beta + n
        )
    
    def posterior_mean(self) -> float:
        """后验均值 E[lambda]"""
        return self.alpha / self.beta
    
    def posterior_mode(self) -> float:
        """后验众数 (alpha-1)/beta"""
        if self.alpha >= 1:
            return (self.alpha - 1) / self.beta
        return self.posterior_mean()


class DirichletMultinomialConjugate:
    """
    狄利克雷-多项式共轭
    
    似然：(x_1,...,x_K) ~ Multinomial(n, p)
    先验：p ~ Dirichlet(alpha)
    后验：p | x ~ Dirichlet(alpha + x)
    
    参数:
        alpha: Dirichlet参数
    """
    
    def __init__(self, alpha: np.ndarray):
        self.alpha = np.array(alpha, dtype=float)
        self.K = len(alpha)
    
    def posterior_update(self, counts: np.ndarray) -> 'DirichletMultinomialConjugate':
        """
        更新后验
        
        参数:
            counts: 各类的计数
        """
        return DirichletMultinomialConjugate(self.alpha + counts)
    
    def posterior_mean(self) -> np.ndarray:
        """后验均值"""
        alpha_sum = np.sum(self.alpha)
        return self.alpha / alpha_sum
    
    def posterior_mode(self) -> np.ndarray:
        """后验众数"""
        alpha_positive = np.maximum(self.alpha - 1, 0)
        if np.sum(alpha_positive) == 0:
            return self.posterior_mean()
        return alpha_positive / np.sum(alpha_positive)
    
    def log_marginal_likelihood(self, data: np.ndarray) -> float:
        """
        计算边缘似然的对数
        
        log p(data | alpha) = log B(alpha + x) - log B(alpha)
        
        参数:
            data: 计数数组
        """
        alpha_new = self.alpha + data
        return (special.gammaln(alpha_new) - special.gammaln(self.alpha)).sum() - \
               special.gammaln(np.sum(alpha_new)) + special.gammaln(np.sum(self.alpha))


class ConjugatePriorRegistry:
    """
    共轭先验注册表
    
    用于查找给定似然的共轭先验
    """
    
    _registry = {
        'bernoulli': BernoulliConjugate,
        'binomial': BernoulliConjugate,  # Beta先验
        'normal_known_var': NormalConjugate,
        'normal_known_precision': NormalConjugate,
        'poisson': PoissonConjugate,
        'multinomial': DirichletMultinomialConjugate,
        'categorical': DirichletMultinomialConjugate,
    }
    
    @classmethod
    def get_conjugate(cls, likelihood_name: str, **kwargs):
        """
        获取共轭先验
        
        参数:
            likelihood_name: 似然名称
            **kwargs: 先验参数
            
        返回:
            共轭先验实例
        """
        if likelihood_name not in cls._registry:
            raise ValueError(f"Unknown likelihood: {likelihood_name}")
        
        return cls._registry[likelihood_name](**kwargs)


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("共轭先验与指数族测试")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 测试1：Beta-Bernoulli共轭
    print("\n1. Beta-Bernoulli共轭:")
    
    # 硬币实验
    true_p = 0.7
    n_flips = 100
    flips = (np.random.rand(n_flips) < true_p).astype(int)
    
    # 先验 Beta(1, 1)
    prior = BernoulliConjugate(alpha=1.0, beta=1.0)
    
    # 后验
    posterior = prior.posterior_update(flips)
    
    print(f"   先验: Alpha={prior.alpha:.1f}, Beta={prior.beta:.1f}")
    print(f"   后验: Alpha={posterior.alpha:.1f}, Beta={posterior.beta:.1f}")
    print(f"   真实p={true_p:.2f}, 后验均值={posterior.posterior_mean():.4f}")
    
    # 测试2：Normal-Normal共轭
    print("\n2. Normal-Normal共轭:")
    
    true_mu = 5.0
    sigma = 2.0
    n = 50
    data = np.random.normal(true_mu, sigma, n)
    
    # 先验 N(0, 10^2)
    prior = NormalConjugate(prior_mu=0.0, prior_var=100.0, likelihood_var=sigma**2)
    
    # 后验
    posterior = prior.posterior_update(data)
    
    print(f"   先验: mu={prior.prior_mu:.2f}, var={prior.prior_var:.2f}")
    print(f"   后验: mu={posterior.prior_mu:.4f}, var={posterior.prior_var:.4f}")
    print(f"   真实mu={true_mu:.2f}, 后验均值={posterior.posterior_mean():.4f}")
    
    # 后验预测
    pred_mean, pred_var = posterior.posterior_predictive()
    print(f"   后验预测分布: mean={pred_mean:.4f}, var={pred_var:.4f}")
    
    # 测试3：Gamma-Poisson共轭
    print("\n3. Gamma-Poisson共轭:")
    
    true_lambda = 10.0
    n_observations = 30
    counts = np.random.poisson(true_lambda, n_observations)
    
    # 先验 Gamma(1, 1)
    prior = PoissonConjugate(alpha=1.0, beta=1.0)
    
    # 后验
    posterior = prior.posterior_update(counts)
    
    print(f"   观测和: {np.sum(counts)}")
    print(f"   先验: alpha={prior.alpha:.1f}, beta={prior.beta:.1f}")
    print(f"   后验: alpha={posterior.alpha:.1f}, beta={posterior.beta:.1f}")
    print(f"   真实lambda={true_lambda:.2f}, 后验均值={posterior.posterior_mean():.4f}")
    
    # 测试4：Dirichlet-Multinomial共轭
    print("\n4. Dirichlet-Multinomial共轭:")
    
    K = 4
    true_probs = np.array([0.3, 0.4, 0.2, 0.1])
    n_trials = 1000
    
    # 多项分布采样
    counts = np.random.multinomial(n_trials, true_probs)
    
    # 先验 Dirichlet(1,1,1,1)
    prior = DirichletMultinomialConjugate(alpha=np.ones(K))
    
    # 后验
    posterior = prior.posterior_update(counts)
    
    print(f"   真实概率: {true_probs}")
    print(f"   后验均值: {posterior.posterior_mean().round(3)}")
    print(f"   后验众数: {posterior.posterior_mode().round(3)}")
    
    # 边缘似然
    log_ml = posterior.log_marginal_likelihood(counts)
    print(f"   边缘对数似然: {log_ml:.4f}")
    
    # 测试5：共轭先验注册表
    print("\n5. 共轭先验注册表:")
    
    for name in ['bernoulli', 'normal_known_var', 'poisson', 'multinomial']:
        conjugate = ConjugatePriorRegistry.get_conjugate(name)
        print(f"   {name}: {conjugate.__name__}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
