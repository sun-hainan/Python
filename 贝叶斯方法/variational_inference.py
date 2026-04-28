"""
变分推断(Variational Inference)实现
Variational Inference: Mean Field Approximation and ELBO

变分推断通过优化一个近似分布来逼近后验分布。
核心思想是将推断问题转化为优化问题。
"""

import numpy as np
from typing import Dict, List, Callable, Tuple, Optional
from collections import defaultdict


class VariationalGaussian:
    """
    变分高斯分布
    
    参数:
        mu: 均值参数
        log_var: 对数方差参数
    """
    
    def __init__(self, mu: float = 0.0, log_var: float = 0.0):
        self.mu = mu  # 均值
        self.log_var = log_var  # 对数方差
    
    @property
    def var(self) -> float:
        """方差"""
        return np.exp(self.log_var)
    
    def sample(self) -> float:
        """从变分分布采样"""
        return self.mu + np.sqrt(self.var) * np.random.randn()
    
    def entropy(self) -> float:
        """高斯分布的熵"""
        return 0.5 * (1 + np.log(2 * np.pi * self.var))


class MeanFieldVI:
    """
    平均场变分推断
    
    平均场假设：近似后验可以分解为各隐变量的乘积
    q(z) = ∏_j q_j(z_j)
    
    参数:
        variables: 隐变量列表
        data: 观测数据
        model: 模型定义（似然函数和先验）
    """
    
    def __init__(self, variables: List[str], data: np.ndarray):
        self.variables = variables  # 隐变量列表
        self.data = data  # 观测数据
        self.n_vars = len(variables)
        self.q = {}  # 变分分布字典
        
        # 初始化变分参数
        for var in variables:
            self.q[var] = {'mu': 0.0, 'log_var': 0.0}
    
    def set_init_params(self, init_params: Dict[str, Dict]):
        """设置初始变分参数"""
        for var, params in init_params.items():
            if var in self.q:
                self.q[var]['mu'] = params.get('mu', 0.0)
                self.q[var]['log_var'] = params.get('log_var', 0.0)
    
    def elbo(self, model: 'BayesianModel') -> float:
        """
        计算证据下界(Evidence Lower Bound)
        
        ELBO = E_q[log p(x,z)] - E_q[log q(z)]
              = log p(x) - KL(q||p)
        
        参数:
            model: 贝叶斯模型
            
        返回:
            ELBO值
        """
        # 计算期望项 E_q[log p(x|z)]
        eq_log_pxz = model.expected_log_likelihood(self.q, self.data)
        
        # 计算期望项 E_q[log p(z)]
        eq_log_pz = self.expected_log_prior(model)
        
        # 计算熵项 H(q) = -E_q[log q(z)]
        entropy = self.variational_entropy()
        
        # ELBO = E_q[log p(x,z)] + H(q)
        elbo = eq_log_pxz + eq_log_pz + entropy
        
        return elbo
    
    def expected_log_prior(self, model: 'BayesianModel') -> float:
        """计算 E_q[log p(z)]"""
        total = 0.0
        
        for var in self.variables:
            mu = self.q[var]['mu']
            log_var = self.q[var]['log_var']
            var_val = np.exp(log_var)
            
            # 对于高斯先验，计算 E_q[log N(z|0, I)]
            total += model.prior_log_pdf(var, mu, var_val)
        
        return total
    
    def variational_entropy(self) -> float:
        """计算变分分布的熵"""
        total = 0.0
        
        for var in self.variables:
            log_var = self.q[var]['log_var']
            var_val = np.exp(log_var)
            
            # 高斯熵：0.5 * log(var) + const
            total += 0.5 * (1 + np.log(2 * np.pi * var_val))
        
        return total
    
    def update_q(self, var: str, model: 'BayesianModel'):
        """
        更新单个变量q的变分参数
        
        使用坐标上升更新：
        log q_j(z_j) ∝ E_{-q_j}[log p(x, z)]
        
        参数:
            var: 要更新的变量
            model: 贝叶斯模型
        """
        # 获取当前对其他变量的期望
        other_expectations = {}
        for other_var in self.variables:
            if other_var != var:
                other_expectations[other_var] = {
                    'mean': self.q[other_var]['mu'],
                    'var': np.exp(self.q[other_var]['log_var'])
                }
        
        # 计算最优更新的参数
        new_mu, new_log_var = model.optimal_variational_params(
            var, other_expectations, self.data
        )
        
        self.q[var]['mu'] = new_mu
        self.q[var]['log_var'] = new_log_var
    
    def fit(self, model: 'BayesianModel', max_iter: int = 100, 
            tol: float = 1e-6, verbose: bool = True) -> List[float]:
        """
        运行变分推断
        
        参数:
            model: 贝叶斯模型
            max_iter: 最大迭代次数
            tol: 收敛容差
            verbose: 是否打印进度
            
        返回:
            ELBO历史
        """
        elbo_history = []
        elbo_prev = -np.inf
        
        for iteration in range(max_iter):
            # 更新每个变量的变分分布
            for var in self.variables:
                self.update_q(var, model)
            
            # 计算ELBO
            elbo = self.elbo(model)
            elbo_history.append(elbo)
            
            # 检查收敛
            if abs(elbo - elbo_prev) < tol:
                if verbose:
                    print(f"   收敛于第 {iteration + 1} 次迭代")
                break
            
            elbo_prev = elbo
            
            if verbose and (iteration + 1) % 10 == 0:
                print(f"   迭代 {iteration + 1}, ELBO = {elbo:.4f}")
        
        return elbo_history
    
    def get_posterior(self) -> Dict[str, Tuple[float, float]]:
        """获取近似后验分布"""
        return {var: (self.q[var]['mu'], np.exp(self.q[var]['log_var'])) 
                for var in self.variables}


class BayesianLinearRegressionVI:
    """
    贝叶斯线性回归的变分推断
    
    模型：
    - y | X, w ~ N(Xw, sigma^2)
    - w ~ N(0, alpha^2 * I)
    
    变分近似：q(w) = N(w|mu, diag(s))
    """
    
    def __init__(self, X: np.ndarray, y: np.ndarray, 
                 alpha: float = 1.0, sigma: float = 1.0):
        self.X = X
        self.y = y
        self.n, self.d = X.shape
        self.alpha = alpha
        self.sigma = sigma
        
        # 初始化变分参数
        self.mu = np.zeros(d)
        self.s = np.ones(d)  # 方差的对角元素
    
    def expected_log_likelihood(self) -> float:
        """计算 E_q[log p(y|X,w)]"""
        # E_q[w^T X^T X w] = mu^T X^T X mu + tr(S X^T X)
        XtX = self.X.T @ self.X
        S = np.diag(self.s)
        
        term1 = self.mu @ XtX @ self.mu
        term2 = np.trace(S @ XtX)
        
        residuals = self.y - self.X @ self.mu
        eq_ll = -0.5 * self.n * np.log(2 * np.pi * self.sigma**2)
        eq_ll += -0.5 / self.sigma**2 * (np.sum(residuals**2) + term2)
        
        return eq_ll
    
    def expected_log_prior(self) -> float:
        """计算 E_q[log p(w)]"""
        alpha2 = self.alpha**2
        S = np.diag(self.s)
        
        eq_lp = -0.5 * self.d * np.log(2 * np.pi * alpha2)
        eq_lp += -0.5 / alpha2 * (np.sum(self.mu**2) + np.trace(S))
        
        return eq_lp
    
    def entropy(self) -> float:
        """变分分布的熵"""
        return 0.5 * np.sum(1 + np.log(2 * np.pi * self.s))
    
    def elbo(self) -> float:
        """计算ELBO"""
        return self.expected_log_likelihood() + self.expected_log_prior() + self.entropy()
    
    def update_mu(self):
        """更新均值参数"""
        S = np.diag(self.s)
        Sigma_inv = S + self.sigma**(-2) * self.X.T @ self.X + 1e-6 * np.eye(self.d)
        
        # 更新后的均值
        residuals = self.y - self.X @ self.mu
        new_mu = np.linalg.solve(
            Sigma_inv,
            self.sigma**(-2) * self.X.T @ self.y
        )
        self.mu = new_mu
    
    def update_s(self):
        """更新方差参数"""
        S_diag = np.zeros(self.d)
        
        for j in range(self.d):
            S_diag[j] = 1.0 / (1.0 / self.alpha**2 + self.sigma**(-2) * np.sum(self.X[:, j]**2) + 1e-6)
        
        self.s = S_diag
    
    def fit(self, max_iter: int = 100, tol: float = 1e-6, verbose: bool = True) -> List[float]:
        """
        运行变分推断
        
        参数:
            max_iter: 最大迭代次数
            tol: 收敛容差
            verbose: 是否打印
            
        返回:
            ELBO历史
        """
        elbo_history = []
        
        for iteration in range(max_iter):
            # 坐标上升更新
            self.update_mu()
            self.update_s()
            
            elbo = self.elbo()
            elbo_history.append(elbo)
            
            if verbose and (iteration + 1) % 10 == 0:
                print(f"   迭代 {iteration + 1}, ELBO = {elbo:.4f}")
        
        return elbo_history


class SimpleBayesianModel:
    """简化贝叶斯模型接口"""
    
    def __init__(self, prior_mean: float = 0.0, prior_var: float = 1.0):
        self.prior_mean = prior_mean
        self.prior_var = prior_var
    
    def expected_log_likelihood(self, q: Dict, data: np.ndarray) -> float:
        """计算 E_q[log p(x|z)]"""
        return 0.0
    
    def prior_log_pdf(self, var: str, mean: float, var_val: float) -> float:
        """计算先验的对数密度"""
        # N(var|0, prior_var) 的对数
        return -0.5 * (mean**2 + var_val) / self.prior_var - 0.5 * np.log(2 * np.pi * self.prior_var)
    
    def optimal_variational_params(self, var: str, other_exp: Dict, data: np.ndarray) -> Tuple[float, float]:
        """计算最优变分参数"""
        # 对于简单模型
        return 0.0, 0.0


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("变分推断测试")
    print("=" * 60)
    
    # 测试1：简单模型的变分推断
    print("\n1. 简单模型的平均场变分推断:")
    
    np.random.seed(42)
    n = 100
    true_mu = 3.0
    data = np.random.randn(n) + true_mu
    
    # 变分推断：估计均值
    class NormalMeanModel:
        """估计正态分布均值的简单模型"""
        
        def expected_log_likelihood(self, q, data):
            mu = q['mu']['mu']
            var = np.exp(q['mu']['log_var'])
            n = len(data)
            return -0.5 * n * np.log(2 * np.pi) - 0.5 * n * var - 0.5 * np.sum((data - mu)**2) - 0.5 * n * var
        
        def prior_log_pdf(self, var, mean, var_val):
            return -0.5 * (mean**2 + var_val) - 0.5 * np.log(2 * np.pi)
        
        def optimal_variational_params(self, var, other_exp, data):
            n = len(data)
            # 后验均值和方差
            new_var = 1.0 / (1.0 + n)
            new_mu = new_var * np.sum(data)
            return new_mu, np.log(new_var)
    
    model = NormalMeanModel()
    vi = MeanFieldVI(['mu'], data)
    elbo_history = vi.fit(model, max_iter=50, verbose=True)
    
    print(f"   估计均值: {vi.q['mu']['mu']:.4f}")
    print(f"   估计方差: {np.exp(vi.q['mu']['log_var']):.4f}")
    
    # 测试2：贝叶斯线性回归
    print("\n2. 贝叶斯线性回归变分推断:")
    np.random.seed(42)
    d = 3
    n = 100
    X = np.column_stack([np.ones(n), np.random.randn(n, d - 1)])
    true_w = np.array([1.0, 2.0, -1.0])
    y = X @ true_w + np.random.randn(n) * 0.5
    
    vi_lr = BayesianLinearRegressionVI(X, y, alpha=1.0, sigma=0.5)
    elbo_history = vi_lr.fit(max_iter=50, verbose=True)
    
    print(f"   估计权重: {vi_lr.mu}")
    print(f"   估计权重方差: {vi_lr.s}")
    
    print("\n3. ELBO收敛曲线:")
    print(f"   初始ELBO: {elbo_history[0]:.4f}")
    print(f"   最终ELBO: {elbo_history[-1]:.4f}")
    print(f"   ELBO变化: {elbo_history[-1] - elbo_history[0]:.4f}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
