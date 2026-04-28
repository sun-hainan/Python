"""
变分贝叶斯学习（Variational Bayes Learning）
Variational Bayes Learning

变分贝叶斯是一种将精确推断近似为优化问题的框架。
通过优化一个变分分布 q(z) 来逼近真实后验 p(z|x)。
"""

import numpy as np
from typing import Dict, List, Tuple, Callable, Optional
from collections import defaultdict


class VariationalBayes:
    """
    变分贝叶斯推断基类
    
    参数:
        model: 模型定义
    """
    
    def __init__(self, model: 'BayesianModel'):
        self.model = model
        self.q_params = {}  # 变分分布参数
        self.elbo_history = []
    
    def elbo(self) -> float:
        """
        计算证据下界(ELBO)
        
        ELBO = E_q[log p(x,z)] - E_q[log q(z)]
              = log p(x) - KL(q||p)
        
        返回:
            ELBO值
        """
        raise NotImplementedError
    
    def update(self):
        """更新变分参数"""
        raise NotImplementedError
    
    def fit(self, max_iter: int = 100, tol: float = 1e-6, verbose: bool = True):
        """
        运行变分推断
        
        参数:
            max_iter: 最大迭代次数
            tol: 收敛容差
            verbose: 是否打印
        """
        self.elbo_history = []
        elbo_prev = -np.inf
        
        for iteration in range(max_iter):
            self.update()
            elbo = self.elbo()
            self.elbo_history.append(elbo)
            
            if verbose and (iteration + 1) % 10 == 0:
                print(f"   迭代 {iteration + 1}, ELBO = {elbo:.4f}")
            
            if abs(elbo - elbo_prev) < tol:
                if verbose:
                    print(f"   收敛于第 {iteration + 1} 次迭代")
                break
            
            elbo_prev = elbo


class MeanFieldFactor:
    """
    平均场变分因子
    
    每个隐变量有自己的变分分布 q_i(z_i)
    q(z) = ∏_i q_i(z_i)
    
    参数:
        name: 变量名
        param_type: 参数类型 ('normal', 'beta', 'dirichlet', 'categorical')
    """
    
    def __init__(self, name: str, param_type: str = 'normal'):
        self.name = name
        self.param_type = param_type
        self.params = {}
    
    def initialize(self, init_params: Dict):
        """初始化参数"""
        self.params = init_params.copy()
    
    def expected_log_likelihood(self, other_params: Dict) -> float:
        """计算与其他因子的期望对数似然"""
        raise NotImplementedError
    
    def kl_divergence(self) -> float:
        """计算与先验的KL散度"""
        raise NotImplementedError


class VariationalNormal(MeanFieldFactor):
    """
    高斯变分分布 q(z) = N(mu, sigma^2)
    """
    
    def __init__(self, name: str, prior_mu: float = 0.0, prior_var: float = 1.0):
        super().__init__(name, 'normal')
        self.prior_mu = prior_mu
        self.prior_var = prior_var
    
    def initialize(self, init_params: Optional[Dict] = None):
        """初始化"""
        if init_params is None:
            self.params = {'mu': 0.0, 'log_var': 0.0}
        else:
            self.params = init_params
    
    @property
    def mu(self) -> float:
        return self.params['mu']
    
    @property
    def var(self) -> float:
        return np.exp(self.params['log_var'])
    
    def expected_value(self) -> float:
        """E_q[z]"""
        return self.mu
    
    def expected_squared(self) -> float:
        """E_q[z^2]"""
        return self.var + self.mu**2
    
    def kl(self) -> float:
        """
        KL(q||p) = log(sqrt(p_var / q_var)) - 0.5 + (q_var + (q_mu - p_mu)^2) / (2 * p_var)
        """
        q_var = self.var
        q_mu = self.mu
        p_var = self.prior_var
        p_mu = self.prior_mu
        
        kl = 0.5 * (np.log(p_var) - np.log(q_var) - 1 + q_var / p_var + (q_mu - p_mu)**2 / p_var)
        return kl


class VariationalBernoulli(MeanFieldFactor):
    """
    伯努利变分分布 q(z) = Bernoulli(phi)
    """
    
    def __init__(self, name: str, prior_pi: float = 0.5):
        super().__init__(name, 'bernoulli')
        self.prior_pi = prior_pi
    
    def initialize(self, init_params: Optional[Dict] = None):
        """初始化"""
        if init_params is None:
            self.params = {'logit_phi': 0.0}  # phi = sigmoid(0) = 0.5
        else:
            self.params = init_params
    
    @property
    def phi(self) -> float:
        """参数phi = sigmoid(logit_phi)"""
        logit = self.params['logit_phi']
        return 1 / (1 + np.exp(-logit))
    
    def expected_value(self) -> float:
        """E_q[z]"""
        return self.phi
    
    def kl(self) -> float:
        """KL(q||p)"""
        phi = self.phi
        pi = self.prior_pi
        
        # KL = phi * log(phi/pi) + (1-phi) * log((1-phi)/(1-pi))
        eps = 1e-10
        kl = phi * np.log((phi + eps) / (pi + eps))
        kl += (1 - phi) * np.log(((1 - phi) + eps) / ((1 - pi) + eps))
        return kl


class VariationalBayesLinearRegression(VariationalBayes):
    """
    贝叶斯线性回归的变分推断
    
    模型：
    y | X, w ~ N(Xw, sigma^2)
    w ~ N(0, alpha^2 * I)
    
    变分近似：q(w) = N(mu, diag(s))
    """
    
    def __init__(self, X: np.ndarray, y: np.ndarray,
                 alpha: float = 1.0, sigma: float = 1.0):
        # 创建模型
        model = BayesianLinearRegressionModel(X, y, alpha, sigma)
        super().__init__(model)
        
        self.X = X
        self.y = y
        self.n, self.d = X.shape
        self.alpha = alpha
        self.sigma = sigma
        
        # 初始化变分参数
        self.q_params = {
            'mu': np.zeros(self.d),
            'log_s': np.zeros(self.d)
        }
    
    def elbo(self) -> float:
        """计算ELBO"""
        mu = self.q_params['mu']
        s = np.exp(self.q_params['log_s'])
        
        # E[log p(y|X,w)]
        residuals = self.y - self.X @ mu
        eq_log_lik = -0.5 * self.n * np.log(2 * np.pi * self.sigma**2)
        eq_log_lik += -0.5 / self.sigma**2 * (
            np.sum(residuals**2) + np.trace(self.X.T @ self.X @ np.diag(s))
        )
        
        # E[log p(w)]
        eq_log_prior = -0.5 * self.d * np.log(2 * np.pi * self.alpha**2)
        eq_log_prior += -0.5 / self.alpha**2 * (np.sum(mu**2) + np.sum(s))
        
        # H(q)
        entropy = 0.5 * np.sum(1 + np.log(2 * np.pi * s))
        
        return eq_log_lik + eq_log_prior + entropy
    
    def update(self):
        """坐标上升更新"""
        mu = self.q_params['mu']
        s = np.exp(self.q_params['log_s'])
        
        XtX = self.X.T @ self.X
        XtX_diag = np.diag(XtX)
        
        # 更新mu
        Sigma_inv = np.diag(1 / s + 1e-10) + self.sigma**(-2) * XtX
        new_mu = self.sigma**(-2) * np.linalg.solve(
            Sigma_inv + 1e-6 * np.eye(self.d),
            self.X.T @ self.y
        )
        
        # 更新s
        new_s = 1 / (1 / self.alpha**2 + self.sigma**(-2) * XtX_diag)
        
        self.q_params['mu'] = new_mu
        self.q_params['log_s'] = np.log(new_s + 1e-10)
    
    def get_posterior(self) -> Tuple[np.ndarray, np.ndarray]:
        """获取后验近似"""
        return self.q_params['mu'], np.exp(self.q_params['log_s'])


class BayesianLinearRegressionModel:
    """贝叶斯线性回归模型"""
    
    def __init__(self, X: np.ndarray, y: np.ndarray, 
                 alpha: float, sigma: float):
        self.X = X
        self.y = y
        self.alpha = alpha
        self.sigma = sigma


class VariationalMixtureGaussians(VariationalBayes):
    """
    高斯混合模型的变分推断
    
    模型：
    - z_i ~ Categorical(pi)  隐变量
    - x_i | z_i=k ~ N(mu_k, Sigma_k)  观测
    - pi ~ Dirichlet(alpha)  混合权重
    - mu_k ~ N(mu_0, kappa_0^-1 * Sigma_k)  均值先验
    - Sigma_k ~ Wishart(S_0, nu_0)  协方差先验
    """
    
    def __init__(self, X: np.ndarray, n_components: int, 
                 alpha: float = 1.0, max_iter: int = 100):
        super().__init__(None)
        self.X = X
        self.n, self.d = X.shape
        self.K = n_components
        self.alpha_0 = alpha
        
        # 先验参数
        self.mu_0 = np.mean(X, axis=0)
        self.kappa_0 = 1.0
        self.S_0 = np.eye(self.d)
        self.nu_0 = self.d
        
        # 变分参数
        self.rho = np.random.rand(self.n, self.K)  # 混合权重（未归一化）
        self.rho = self.rho / np.sum(self.rho, axis=1, keepdims=True)
        
        # 初始化
        self._initialize_params()
    
    def _initialize_params(self):
        """初始化变分参数"""
        # 混合权重
        self.alpha_k = np.ones(self.K) * self.alpha_0  # Dirichlet参数
        
        # 均值
        self.mu_k = np.zeros((self.K, self.d))
        # 用K-Means初始化
        from sklearn.cluster import KMeans
        kmeans = KMeans(n_clusters=self.K, n_init=1, random_state=42)
        labels = kmeans.fit_predict(self.X)
        for k in range(self.K):
            self.mu_k[k] = np.mean(self.X[labels == k], axis=0)
        
        # 协方差
        self.L_k = [np.eye(self.d) for _ in range(self.K)]  # Wishart L矩阵
        self.nu_k = np.ones(self.K) * self.d  # Wishart自由度
    
    def _e_step(self):
        """E步：更新隐变量后验"""
        # 对每个样本计算其属于各成分的期望
        log_rho = np.zeros((self.n, self.K))
        
        for k in range(self.K):
            # log p(z_i=k | pi) + E[log p(x_i | z_i=k)]
            log_rho[:, k] += np.log(self.alpha_k[k] + 1e-10)
            log_rho[:, k] += self._log_predictive(self.X, k)
        
        # 归一化
        log_rho = log_rho - np.max(log_rho, axis=1, keepdims=True)
        self.rho = np.exp(log_rho)
        self.rho = self.rho / np.sum(self.rho, axis=1, keepdims=True)
    
    def _log_predictive(self, X: np.ndarray, k: int) -> np.ndarray:
        """对数预测分布 E[log N(x | mu_k, Sigma_k)]"""
        from scipy.stats import wishart
        from scipy.linalg import solve_triangular
        
        L = self.L_k[k]
        nu = self.nu_k[k]
        
        # Sigma_k^-1 = L L^T
        Sigma_inv = L.T @ L
        
        # |Sigma_k| = 1/|L|^2
        log_det = -2 * np.sum(np.log(np.diag(L)))
        
        n = len(X)
        log_p = np.zeros(n)
        
        for i in range(n):
            diff = X[i] - self.mu_k[k]
            # d/2 * log(2pi) - 1/2 * trace(L^{-1} (x-mu)(x-mu)^T) + nu/2 * log|L| - ...
            # 简化为: -0.5 * (x-mu)^T Sigma^-1 (x-mu)
            log_p[i] = -0.5 * diff @ Sigma_inv @ diff
        
        return log_p
    
    def _m_step(self):
        """M步：更新变分参数"""
        N_k = np.sum(self.rho, axis=0)  # 各成分的有效样本数
        
        # 更新混合权重 Dirichlet参数
        self.alpha_k = self.alpha_0 + N_k
        
        # 更新均值和协方差
        for k in range(self.K):
            # 加权均值
            self.mu_k[k] = np.sum(self.rho[:, k:k+1] * self.X, axis=0) / (N_k[k] + 1e-10)
            
            # 估计协方差（简化版）
            centered = self.X - self.mu_k[k]
            cov = (self.rho[:, k:k+1] * centered).T @ centered / (N_k[k] + 1e-10)
            self.L_k[k] = np.linalg.cholesky(cov + 1e-6 * np.eye(self.d))
            self.nu_k[k] = N_k[k]
    
    def elbo(self) -> float:
        """计算ELBO"""
        # 简化为重建误差 + KL散度
        elbo = 0.0
        
        # 重构误差（近似）
        for k in range(self.K):
            log_p = self._log_predictive(self.X, k)
            elbo += np.sum(self.rho[:, k] * log_p)
        
        # KL散度（简化）
        for k in range(self.K):
            elbo -= 0.5 * np.sum(self.rho[:, k])
        
        return elbo
    
    def update(self):
        """E步和M步"""
        self._e_step()
        self._m_step()
    
    def predict_proba(self, X_test: np.ndarray) -> np.ndarray:
        """预测样本属于各成分的概率"""
        log_p = np.zeros((len(X_test), self.K))
        for k in range(self.K):
            log_p[:, k] = self._log_predictive(X_test, k)
        
        # 加上混合权重
        log_p += np.log(self.alpha_k / np.sum(self.alpha_k))
        
        # 归一化
        log_p = log_p - np.max(log_p, axis=1, keepdims=True)
        p = np.exp(log_p)
        return p / np.sum(p, axis=1, keepdims=True)


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("变分贝叶斯学习测试")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 测试1：贝叶斯线性回归
    print("\n1. 贝叶斯线性回归变分推断:")
    
    n = 100
    d = 3
    X = np.column_stack([np.ones(n), np.random.randn(n, d - 1)])
    true_w = np.array([1.0, 2.0, -1.0])
    y = X @ true_w + np.random.randn(n) * 0.5
    
    vblr = VariationalBayesLinearRegression(X, y, alpha=1.0, sigma=0.5)
    vblr.fit(max_iter=50, verbose=True)
    
    mu, var = vblr.get_posterior()
    print(f"   估计权重: {mu}")
    print(f"   权重方差: {var}")
    print(f"   真实权重: {true_w}")
    
    # 测试2：ELBO收敛
    print("\n2. ELBO收敛曲线:")
    print(f"   初始ELBO: {vblr.elbo_history[0]:.4f}")
    print(f"   最终ELBO: {vblr.elbo_history[-1]:.4f}")
    
    # 测试3：高斯混合模型
    print("\n3. 高斯混合模型变分推断:")
    
    # 生成混合数据
    n1, n2 = 50, 50
    X1 = np.random.randn(n1, 2) + np.array([0, 0])
    X2 = np.random.randn(n2, 2) + np.array([3, 3])
    X_mix = np.vstack([X1, X2])
    
    vgmm = VariationalMixtureGaussians(X_mix, n_components=2, alpha=1.0)
    
    for i in range(30):
        vgmm.update()
        if (i + 1) % 10 == 0:
            print(f"   迭代 {i + 1}, ELBO = {vgmm.elbo():.4f}")
    
    # 预测
    probs = vgmm.predict_proba(X_mix[:5])
    print(f"   预测概率形状: {probs.shape}")
    print(f"   前5个样本预测:\n{probs[:5].round(3)}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
