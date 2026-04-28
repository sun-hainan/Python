"""
分层贝叶斯模型（Hierarchical Bayesian Models）
Hierarchical Bayesian Models

分层贝叶斯模型是多层结构：
- Level 1: 数据模型 p(y | theta)
- Level 2: 先验 p(theta | phi)
- Level 3: 超先验 p(phi)

允许参数之间共享信息，实现"shrinkage"估计。
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Callable
from collections import defaultdict


class HierarchicalBayesianModel:
    """
    分层贝叶斯模型基类
    
    结构：
    - 数据层：y | theta ~ p(y | theta)
    - 参数层：theta | phi ~ p(theta | phi)
    - 超参数层：phi ~ p(phi)
    """
    
    def __init__(self):
        self.params = {}  # 层级参数
        self.hyperparams = {}  # 超参数
    
    def log_likelihood(self, theta: Dict) -> float:
        """数据对数似然 log p(y | theta)"""
        raise NotImplementedError
    
    def log_prior(self, theta: Dict, phi: Dict) -> float:
        """参数先验 log p(theta | phi)"""
        raise NotImplementedError
    
    def log_hyperprior(self, phi: Dict) -> float:
        """超先验 log p(phi)"""
        raise NotImplementedError
    
    def sample_posterior(self, n_samples: int) -> Tuple[List[Dict], List[Dict]]:
        """采样后验分布"""
        raise NotImplementedError


class NormalNormalHierarchical(HierarchicalBayesianModel):
    """
    正态-正态分层模型
    
    Level 1: y_j | mu_j, sigma_j^2 ~ N(mu_j, sigma_j^2)
    Level 2: mu_j | mu, tau^2 ~ N(mu, tau^2)
    Level 3: mu ~ flat, tau ~ half-Cauchy
    
    应用：多所学校成绩比较、meta分析等
    """
    
    def __init__(self, y: np.ndarray, sigma: np.ndarray):
        super().__init__()
        self.y = y  # 观测值
        self.sigma = sigma  # 已知标准差
        self.J = len(y)  # 组数
    
    def sample_posterior(self, n_samples: int, burn_in: int = 1000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Gibbs采样后验
        
        返回:
            (mu样本, tau样本)
        """
        mu_samples = []
        tau_samples = []
        
        # 初始值
        mu = np.mean(self.y)
        tau = np.std(self.y)
        
        for iteration in range(burn_in + n_samples):
            # 采样每个mu_j
            mu_j_samples = []
            for j in range(self.J):
                # 后验：mu_j | y, mu, tau ~ N(post_mean, post_var)
                post_var = 1 / (1 / tau**2 + 1 / self.sigma[j]**2)
                post_mean = post_var * (mu / tau**2 + self.y[j] / self.sigma[j]**2)
                mu_j = np.random.normal(post_mean, np.sqrt(post_var))
                mu_j_samples.append(mu_j)
            
            mu_j_samples = np.array(mu_j_samples)
            
            # 采样mu
            mu_var = tau**2 / self.J
            mu = np.random.normal(np.mean(mu_j_samples), np.sqrt(mu_var))
            
            # 采样tau（使用Metropolis-Hastings）
            tau_prop = tau * np.exp(np.random.randn() * 0.1)
            
            # 计算似然比
            def log_post(t):
                lp = 0
                for j in range(self.J):
                    lp += -0.5 * (mu_j_samples[j] - mu)**2 / t**2
                    lp += -np.log(t)
                return lp
            
            alpha = np.exp(log_post(tau_prop) - log_post(tau))
            if np.random.rand() < min(1, alpha):
                tau = tau_prop
            
            if iteration >= burn_in:
                mu_samples.append(mu)
                tau_samples.append(tau)
        
        return np.array(mu_samples), np.array(tau_samples)
    
    def posterior_mean(self, mu_samples: np.ndarray, tau_samples: np.ndarray) -> Tuple[float, float]:
        """后验均值"""
        return np.mean(mu_samples), np.mean(tau_samples)
    
    def shrunk_estimates(self, mu_samples: np.ndarray, tau_samples: np.ndarray) -> np.ndarray:
        """
        计算收缩估计
        
        每个组的均值被拉向全局均值
        """
        mu_mean = np.mean(mu_samples)
        
        shrunk = []
        for j in range(self.J):
            # 收缩因子
            w = tau_samples**2 / (tau_samples**2 + self.sigma[j]**2)
            w_mean = np.mean(w)
            
            # 收缩估计
            shrunk_j = w_mean * self.y[j] + (1 - w_mean) * mu_mean
            shrunk.append(shrunk_j)
        
        return np.array(shrunk)


class BinomialBetaHierarchical(HierarchicalBayesianModel):
    """
    二项-贝塔分层模型
    
    Level 1: x_j | n_j, p_j ~ Binomial(n_j, p_j)
    Level 2: p_j | alpha, beta ~ Beta(alpha, beta)
    Level 3: alpha, beta ~ p(alpha, beta) (经验贝叶斯估计)
    """
    
    def __init__(self, successes: np.ndarray, trials: np.ndarray):
        super().__init__()
        self.x = successes
        self.n = trials
        self.J = len(successes)
    
    def estimate_hyperparams(self) -> Tuple[float, float]:
        """
        估计超参数（使用矩估计）
        
        返回:
            (alpha, beta) 估计
        """
        # 样本比例
        p_hat = self.x / self.n
        
        # 计算均值和方差
        p_bar = np.mean(p_hat)
        s_sq = np.var(p_hat)
        
        # Beta矩估计
        if p_bar * (1 - p_bar) <= s_sq:
            s_sq = p_bar * (1 - p_bar) * 0.99
        
        alpha = p_bar * (p_bar * (1 - p_bar) / s_sq - 1)
        beta = (1 - p_bar) * (p_bar * (1 - p_bar) / s_sq - 1)
        
        alpha = max(0.1, alpha)
        beta = max(0.1, beta)
        
        self.hyperparams = {'alpha': alpha, 'beta': beta}
        
        return alpha, beta
    
    def posterior_mean(self, alpha: Optional[float] = None, 
                       beta: Optional[float] = None) -> np.ndarray:
        """
        计算后验均值
        
        参数:
            alpha, beta: 如果为None，使用估计值
            
        返回:
            各组后验均值
        """
        if alpha is None:
            alpha = self.hyperparams.get('alpha', 1.0)
        if beta is None:
            beta = self.hyperparams.get('beta', 1.0)
        
        # Beta后验：p_j | x_j, alpha, beta ~ Beta(x_j + alpha, n_j - x_j + beta)
        post_mean = (self.x + alpha) / (self.n + alpha + beta)
        
        return post_mean


class PoissonGammaHierarchical(HierarchicalBayesianModel):
    """
    泊松-伽马分层模型
    
    Level 1: y_j | lambda_j ~ Poisson(lambda_j)
    Level 2: lambda_j | r, mu ~ Gamma(r, r/mu) (均值mu，形状r)
    Level 3: r, mu ~ p(r, mu) (经验贝叶斯)
    
    应用：保险索赔计数、疾病发病率等
    """
    
    def __init__(self, y: np.ndarray):
        super().__init__()
        self.y = y  # 观测计数
        self.J = len(y)
    
    def estimate_hyperparams(self) -> Tuple[float, float]:
        """
        估计超参数
        
        返回:
            (r, mu)
        """
        y_bar = np.mean(self.y)
        var_y = np.var(self.y)
        
        # 矩估计
        if var_y > y_bar:
            mu = y_bar
            r = y_bar**2 / (var_y - y_bar)
        else:
            mu = y_bar
            r = y_bar  # fallback
        
        r = max(0.1, r)
        
        self.hyperparams = {'r': r, 'mu': mu}
        
        return r, mu
    
    def posterior_mean(self, r: Optional[float] = None,
                       mu: Optional[float] = None) -> np.ndarray:
        """
        计算后验均值
        
        返回:
            各组lambda的后验均值
        """
        if r is None:
            r = self.hyperparams.get('r', 1.0)
        if mu is None:
            mu = self.hyperparams.get('mu', np.mean(self.y))
        
        # Gamma后验：lambda_j | y_j ~ Gamma(y_j + r, 1 + 1/mu)
        # 后验均值 = (y_j + r) / (1 + 1/mu) = (y_j + r) * mu / (1 + mu)
        post_mean = (self.y + r) * mu / (1 + mu)
        
        return post_mean
    
    def shrunk_estimates(self) -> np.ndarray:
        """
        计算收缩估计
        
        类似于James-Stein估计
        """
        r = self.hyperparams.get('r', 1.0)
        mu = self.hyperparams.get('mu', np.mean(self.y))
        
        # 收缩因子
        shrinkage = r / (self.y + r)
        
        # 收缩估计
        shrunk = shrinkage * mu + (1 - shrinkage) * self.y
        
        return shrunk


class HierarchicalLinearRegression(HierarchicalBayesianModel):
    """
    分层线性回归
    
    Level 1: y_i | x_i, beta_j[i], sigma^2 ~ N(x_i^T beta_j[i], sigma^2)
    Level 2: beta_j ~ N(mu_beta, Sigma_beta)
    Level 3: mu_beta, Sigma_beta ~ p(mu_beta, Sigma_beta)
    
    其中j[i]是样本i所属的组
    """
    
    def __init__(self, X: np.ndarray, y: np.ndarray, groups: np.ndarray):
        super().__init__()
        self.X = X  # (n, p)
        self.y = y  # (n,)
        self.groups = groups  # 组标签
        self.n, self.p = X.shape
        self.unique_groups = np.unique(groups)
        self.J = len(self.unique_groups)
    
    def estimate_group_effects(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        估计各组的回归系数
        
        返回:
            (组系数, 收缩后的系数)
        """
        # 各组的索引
        group_indices = [np.where(self.groups == g)[0] for g in self.unique_groups]
        
        # 各组的OLS估计
        beta_ols = np.zeros((self.J, self.p))
        for j, idx in enumerate(group_indices):
            X_j = self.X[idx]
            y_j = self.y[idx]
            beta_ols[j] = np.linalg.lstsq(X_j, y_j, rcond=None)[0]
        
        # 经验贝叶斯收缩
        beta_bar = np.mean(beta_ols, axis=0)
        S_beta = np.cov(beta_ols.T)
        
        # 估计噪声方差
        residuals = []
        for j, idx in enumerate(group_indices):
            X_j = self.X[idx]
            y_j = self.y[idx]
            residuals.extend(y_j - X_j @ beta_ols[j])
        sigma_sq = np.var(residuals)
        
        # James-Stein类型收缩
        # 收缩估计 = X_bar + shrinkage * (X_j - X_bar)
        shrinkage = np.trace(S_beta) / (np.trace(S_beta) + sigma_sq)
        beta_shrunk = beta_bar + shrinkage * (beta_ols - beta_bar)
        
        return beta_ols, beta_shrunk


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("分层贝叶斯模型测试")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 测试1：正态-正态分层模型
    print("\n1. 正态-正态分层模型（多学校效应）:")
    
    J = 8  # 学校数量
    sigma = np.array([10, 10, 10, 10, 10, 10, 10, 10])  # 每校标准误
    
    # 真实参数
    true_mu = 100.0  # 全局均值
    true_tau = 15.0  # 学校间标准差
    
    # 每校观测均值
    mu_j = np.random.normal(true_mu, true_tau, J)
    y = mu_j + np.random.normal(0, sigma)
    
    model = NormalNormalHierarchical(y, sigma)
    mu_samples, tau_samples = model.sample_posterior(n_samples=5000, burn_in=2000)
    
    mu_mean, tau_mean = model.posterior_mean(mu_samples, tau_samples)
    shrunk = model.shrunk_estimates(mu_samples, tau_samples)
    
    print(f"   真实全局均值: {true_mu:.2f}")
    print(f"   估计全局均值: {mu_mean:.2f}")
    print(f"   估计组间标准差: {tau_mean:.2f}")
    
    print("\n   收缩效果:")
    for j in range(J):
        print(f"   学校{j}: 观测={y[j]:.1f}, 收缩估计={shrunk[j]:.2f}")
    
    # 测试2：二项-贝塔分层模型
    print("\n2. 二项-贝塔分层模型（多硬币实验）:")
    
    J = 15
    trials = np.random.randint(20, 100, J)
    true_p = np.random.beta(2, 8, J)  # 偏向低成功率
    successes = np.random.binomial(trials, true_p)
    
    model2 = BinomialBetaHierarchical(successes, trials)
    alpha_est, beta_est = model2.estimate_hyperparams()
    
    print(f"   估计超参数: alpha={alpha_est:.3f}, beta={beta_est:.3f}")
    
    post_means = model2.posterior_mean()
    
    print("\n   估计效果:")
    for j in range(min(8, J)):
        raw_rate = successes[j] / trials[j]
        print(f"   硬币{j}: 观测={successes[j]}/{trials[j]}={raw_rate:.2f}, "
              f"后验均值={post_means[j]:.3f}")
    
    # 测试3：泊松-伽马分层模型
    print("\n3. 泊松-伽马分层模型（保险索赔）:")
    
    J = 12
    lambda_true = np.random.gamma(5, 20, J)  # 真实lambda
    y_poisson = np.random.poisson(lambda_true)  # 观测计数
    
    model3 = PoissonGammaHierarchical(y_poisson)
    r_est, mu_est = model3.estimate_hyperparams()
    
    print(f"   估计超参数: r={r_est:.3f}, mu={mu_est:.3f}")
    
    post_means = model3.posterior_mean()
    shrunk = model3.shrunk_estimates()
    
    print("\n   收缩效果:")
    for j in range(min(8, J)):
        print(f"   保单{j}: 观测={y_poisson[j]}, "
              f"后验均值={post_means[j]:.2f}, 收缩={shrunk[j]:.2f}")
    
    # 测试4：分层线性回归
    print("\n4. 分层线性回归:")
    
    n = 100
    J = 5
    groups = np.random.choice(J, n)
    
    X = np.column_stack([np.ones(n), np.random.randn(n, 2)])
    true_beta = np.array([[5.0, 1.0, 2.0]] * J) + np.random.randn(J, 3) * 0.5
    y_hier = np.array([X[i] @ true_beta[groups[i]] for i in range(n)])
    y_hier += np.random.randn(n) * 0.5
    
    model4 = HierarchicalLinearRegression(X, y_hier, groups)
    beta_ols, beta_shrunk = model4.estimate_group_effects()
    
    print(f"   组数: {J}")
    print(f"   特征数: 3")
    print(f"   OLS系数形状: {beta_ols.shape}")
    print(f"   收缩后系数形状: {beta_shrunk.shape}")
    
    print("\n   各组系数:")
    for j in range(min(3, J)):
        print(f"   组{j} OLS: {beta_ols[j].round(2)}")
        print(f"   组{j} 收缩: {beta_shrunk[j].round(2)}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
