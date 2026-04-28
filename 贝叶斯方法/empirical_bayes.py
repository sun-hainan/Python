"""
经验贝叶斯方法
Empirical Bayes

经验贝叶斯通过从数据中估计超参数，而不是完全主观地指定。
核心思想是用边缘似然的最大化来估计先验参数。
"""

import numpy as np
from typing import Tuple, Optional, Callable, List
from scipy.optimize import minimize_scalar, minimize
from scipy.special import gammaln, digamma, logsumexp


class EmpiricalBayes:
    """
    经验贝叶斯基类
    
    经验贝叶斯方法通过最大化边缘似然：
    p(x | theta) = integral p(x | w) p(w | theta) dw
    然后用估计的 theta_hat 进行推断。
    """
    
    def __init__(self):
        self.estimated_params = None
    
    def marginal_likelihood(self, params) -> float:
        """
        计算边缘对数似然
        
        参数:
            params: 超参数
            
        返回:
            log p(x | params)
        """
        raise NotImplementedError
    
    def estimate_params(self, data, verbose: bool = True):
        """
        估计超参数
        
        参数:
            data: 观测数据
            verbose: 是否打印
        """
        raise NotImplementedError


class EmpiricalBayesNormal:
    """
    正态分布的经验贝叶斯
    
    观测模型：x_i ~ N(mu, sigma^2)
    先验：mu ~ N(mu_0, tau_0^2)
    
    估计 mu_0 和 tau_0^2
    """
    
    def __init__(self):
        self.mu_0 = None
        self.tau_0_sq = None
        self.sigma_sq = None
    
    def fit(self, observations: np.ndarray, sigma_sq: Optional[float] = None):
        """
        估计超参数
        
        参数:
            observations: 观测数据
            sigma_sq: 已知噪声方差
        """
        n = len(observations)
        x_bar = np.mean(observations)
        
        if sigma_sq is None:
            # 同时估计sigma
            self.sigma_sq = np.var(observations)
        else:
            self.sigma_sq = sigma_sq
        
        # 估计tau_0^2（使用矩估计）
        sample_var = np.var(observations)
        
        # tau_0^2 = sample_var - sigma^2/n
        self.tau_0_sq = max(sample_var - self.sigma_sq / n, 1e-6)
        
        # mu_0 = x_bar
        self.mu_0 = x_bar
        
        return self
    
    def posterior_mean(self, x: float) -> float:
        """
        计算后验均值
        
        参数:
            x: 观测值
            
        返回:
            E[mu | x]
        """
        # 后验均值是观测值和先验均值的加权平均
        n = 1  # 这里是单次观测
        
        weight = self.tau_0_sq / (self.tau_0_sq + self.sigma_sq / n)
        posterior_mean = weight * x + (1 - weight) * self.mu_0
        
        return posterior_mean
    
    def marginal_likelihood(self, observations: np.ndarray) -> float:
        """
        计算边缘对数似然
        
        参数:
            observations: 观测数据
            
        返回:
            log p(x | mu_0, tau_0_sq, sigma_sq)
        """
        n = len(observations)
        
        # 边缘分布是 t-分布
        # log p(x) = -n/2 * log(2*pi) - 1/2 * sum(log(sigma^2 + tau_0^2))
        #           - 1/2 * sum((x_i - mu_0)^2 / (sigma^2 + tau_0^2))
        
        var_total = self.sigma_sq + self.tau_0_sq
        
        log_lik = -n / 2 * np.log(2 * np.pi)
        log_lik += -0.5 * n * np.log(var_total)
        log_lik += -0.5 * np.sum((observations - self.mu_0)**2) / var_total
        
        return log_lik


class EmpiricalBayesGaussianMixture:
    """
    高斯混合模型的经验贝叶斯（EM算法）
    
    使用EM算法最大化边缘似然来估计混合参数。
    
    参数:
        n_components: 成分数量
        max_iter: 最大迭代次数
    """
    
    def __init__(self, n_components: int, max_iter: int = 100):
        self.K = n_components
        self.max_iter = max_iter
        
        self.weights = None  # 混合权重 pi_k
        self.means = None  # 均值 mu_k
        self.vars = None  # 方差 sigma_k^2
    
    def fit(self, X: np.ndarray, verbose: bool = True):
        """
        拟合模型
        
        参数:
            X: 数据 (n, d)
        """
        X = np.array(X)
        n, d = X.shape
        
        # 初始化
        np.random.seed(42)
        self.weights = np.ones(self.K) / self.K
        self.means = X[np.random.choice(n, self.K, replace=False)]
        self.vars = np.ones((self.K, d)) * np.var(X)
        
        for iteration in range(self.max_iter):
            # E步：计算隐变量后验
            responsibilities = self._e_step(X)
            
            # M步：更新参数
            self._m_step(X, responsibilities)
            
            if verbose and (iteration + 1) % 10 == 0:
                ll = self._log_likelihood(X)
                print(f"   迭代 {iteration + 1}, 边缘对数似然: {ll:.4f}")
        
        return self
    
    def _e_step(self, X: np.ndarray) -> np.ndarray:
        """E步：计算后验概率"""
        n = len(X)
        responsibilities = np.zeros((n, self.K))
        
        for k in range(self.K):
            diff = X - self.means[k]
            log_prob = -0.5 * np.sum(diff**2 / self.vars[k], axis=1)
            log_prob += -0.5 * np.sum(np.log(2 * np.pi * self.vars[k]))
            log_prob += np.log(self.weights[k])
            responsibilities[:, k] = log_prob
        
        # 归一化
        responsibilities = responsibilities - logsumexp(responsibilities, axis=1, keepdims=True)
        responsibilities = np.exp(responsibilities)
        
        return responsibilities
    
    def _m_step(self, X: np.ndarray, responsibilities: np.ndarray):
        """M步：更新参数"""
        n = len(X)
        
        # 更新权重
        Nk = np.sum(responsibilities, axis=0)
        self.weights = Nk / n
        
        # 更新均值
        for k in range(self.K):
            self.means[k] = np.sum(responsibilities[:, k:k+1] * X, axis=0) / (Nk[k] + 1e-10)
        
        # 更新方差
        for k in range(self.K):
            diff = X - self.means[k]
            self.vars[k] = np.sum(responsibilities[:, k:k+1] * diff**2, axis=0) / (Nk[k] + 1e-10)
    
    def _log_likelihood(self, X: np.ndarray) -> float:
        """计算边缘对数似然"""
        n = len(X)
        ll = 0.0
        
        for i in range(n):
            xi = X[i]
            log_probs = []
            
            for k in range(self.K):
                diff = xi - self.means[k]
                log_prob = -0.5 * np.sum(diff**2 / self.vars[k])
                log_prob += -0.5 * np.sum(np.log(2 * np.pi * self.vars[k]))
                log_prob += np.log(self.weights[k])
                log_probs.append(log_prob)
            
            ll += logsumexp(log_probs)
        
        return ll
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """预测成分概率"""
        return self._e_step(X)


class EmpiricalBayesHierarchical:
    """
    分层模型的经验贝叶斯
    
    观测：y_j | theta_j ~ N(theta_j, sigma_j^2)
    先验：theta_j | mu, tau ~ N(mu, tau^2)
    超先验：mu ~ flat, tau ~ half-Cauchy
    
    估计 mu 和 tau
    """
    
    def __init__(self):
        self.mu_hat = None
        self.tau_hat = None
        self.sigma_sq = None
    
    def fit(self, y: np.ndarray, sigma_sq: np.ndarray, verbose: bool = True):
        """
        估计超参数
        
        参数:
            y: 观测值 (J,)
            sigma_sq: 观测方差 (J,)
        """
        J = len(y)
        self.sigma_sq = sigma_sq
        
        def neg_marginal_lik(log_tau):
            """负边缘对似然（作为tau的函数）"""
            tau_sq = np.exp(2 * log_tau)
            
            # 边缘均值和方差
            w = sigma_sq / (sigma_sq + tau_sq)
            
            # 似然部分
            ll = -0.5 * np.sum(np.log(sigma_sq + tau_sq))
            ll += -0.5 * np.sum(w * (y - np.mean(y))**2 / (sigma_sq + tau_sq))
            ll += -J / 2 * np.log(2 * np.pi)
            
            return -ll
        
        # 优化tau
        result = minimize_scalar(neg_marginal_lik, bounds=(-5, 5), method='bounded')
        log_tau_hat = result.x
        self.tau_hat = np.exp(log_tau_hat)
        
        # 估计mu
        tau_sq = self.tau_hat**2
        w = sigma_sq / (sigma_sq + tau_sq)
        self.mu_hat = np.sum(w * y) / np.sum(w)
        
        if verbose:
            print(f"   估计 mu: {self.mu_hat:.4f}")
            print(f"   估计 tau: {self.tau_hat:.4f}")
        
        return self
    
    def posterior_mean(self, y_j: float, sigma_j_sq: float) -> float:
        """
        计算第j个参数的收缩估计
        
        参数:
            y_j: 观测值
            sigma_j_sq: 观测方差
            
        返回:
            收缩后的估计
        """
        tau_sq = self.tau_hat**2
        
        # 收缩权重
        w = tau_sq / (tau_sq + sigma_j_sq)
        
        # 收缩估计
        theta_hat = w * y_j + (1 - w) * self.mu_hat
        
        return theta_hat


class EmpiricalBayesBeta:
    """
    Beta-Binomial模型的经验贝叶斯
    
    观测：x ~ Binomial(n, p)
    先验：p ~ Beta(alpha, beta)
    
    使用边缘似然最大化估计 alpha 和 beta
    """
    
    def __init__(self):
        self.alpha_hat = None
        self.beta_hat = None
    
    def fit(self, successes: np.ndarray, trials: np.ndarray, verbose: bool = True):
        """
        估计超参数
        
        参数:
            successes: 成功次数数组
            trials: 试验次数数组
        """
        successes = np.array(successes)
        trials = np.array(trials)
        
        def neg_marginal_lik(log_params):
            """负边缘对数似然"""
            alpha, beta = np.exp(log_params[0]), np.exp(log_params[1])
            
            # 边缘似然：Beta-Binomial分布
            # log p(x | alpha, beta) = log C(n, x) + B(x+alpha, n-x+beta) - B(alpha, beta)
            
            ll = np.sum(gammaln(trials + 1) - gammaln(successes + 1) - gammaln(trials - successes + 1))
            ll += np.sum(gammaln(successes + alpha) + gammaln(trials - successes + beta) - gammaln(trials + alpha + beta))
            ll += np.sum(gammaln(alpha + beta) - gammaln(alpha) - gammaln(beta))
            
            return -ll
        
        # 优化
        from scipy.optimize import minimize
        result = minimize(neg_marginal_lik, x0=[1.0, 1.0], method='Nelder-Mead')
        
        self.alpha_hat, self.beta_hat = np.exp(result.x)
        
        if verbose:
            print(f"   估计 alpha: {self.alpha_hat:.4f}")
            print(f"   估计 beta: {self.beta_hat:.4f}")
        
        return self
    
    def posterior_mean(self, x: int, n: int) -> float:
        """
        计算后验均值
        
        参数:
            x: 成功次数
            n: 试验次数
        """
        return (x + self.alpha_hat) / (n + self.alpha_hat + self.beta_hat)


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("经验贝叶斯方法测试")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 测试1：正态分布经验贝叶斯
    print("\n1. 正态分布经验贝叶斯:")
    
    # 模拟多所学校考试成绩
    true_mu = 100.0  # 真实平均分
    true_tau = 10.0  # 学校间标准差
    sigma = 5.0  # 每所学校内部标准差
    
    n_schools = 10
    n_students = 30
    
    # 每所学校的观测均值
    school_means = np.random.normal(true_mu, true_tau, n_schools)
    # 每所学校的观测
    observations = school_means + np.random.normal(0, sigma / np.sqrt(n_students), n_schools)
    
    eb = EmpiricalBayesNormal()
    eb.fit(observations)
    
    print(f"   真实全局均值: {true_mu:.2f}")
    print(f"   估计全局均值: {eb.mu_0:.2f}")
    print(f"   边缘对数似然: {eb.marginal_likelihood(observations):.4f}")
    
    # 收缩效果
    print("\n2. 收缩估计效果:")
    for i in range(min(5, n_schools)):
        shrunk = eb.posterior_mean(observations[i])
        print(f"   学校{i}: 观测={observations[i]:.2f}, 收缩估计={shrunk:.2f}")
    
    # 测试2：分层模型的经验贝叶斯
    print("\n3. 分层模型经验贝叶斯:")
    
    J = 20
    sigma_sq = np.random.uniform(1, 10, J)
    theta_true = np.random.normal(0, 2, J)
    y = theta_true + np.random.normal(0, np.sqrt(sigma_sq))
    
    eb_hier = EmpiricalBayesHierarchical()
    eb_hier.fit(y, sigma_sq)
    
    print("   收缩估计示例:")
    for j in range(min(5, J)):
        shrunk = eb_hier.posterior_mean(y[j], sigma_sq[j])
        print(f"   组{j}: 观测={y[j]:.2f}, 收缩={shrunk:.2f}")
    
    # 测试3：Beta-Binomial经验贝叶斯
    print("\n4. Beta-Binomial经验贝叶斯:")
    
    # 模拟多个硬币实验
    n_experiments = 10
    trials = np.random.randint(20, 100, n_experiments)
    true_p = np.random.beta(3, 7, n_experiments)  # 真实成功率
    successes = np.random.binomial(trials, true_p)
    
    eb_beta = EmpiricalBayesBeta()
    eb_beta.fit(successes, trials)
    
    print("   硬币实验后验均值:")
    for i in range(min(5, n_experiments)):
        post_mean = eb_beta.posterior_mean(successes[i], trials[i])
        print(f"   硬币{i}: 观测={successes[i]}/{trials[i]}, 后验均值={post_mean:.3f}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
