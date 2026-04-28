"""
Score匹配：Sliced Score Matching
Score Matching: Sliced Score Matching

Score匹配是一类无需计算归一化常数的分布估计方法。
核心思想：学习对数密度的梯度（score function）∇_x log p(x)。
Sliced Score Matching通过随机投影降低计算复杂度。
"""

import numpy as np
from typing import Callable, Tuple, Optional
from functools import partial


class ScoreNetwork:
    """
    Score网络
    
    学习score function: s_theta(x) ≈ ∇_x log p(x)
    
    参数:
        network: 基础神经网络
    """
    
    def __init__(self, network_fn: Callable):
        self.network = network_fn
    
    def __call__(self, x: np.ndarray, t: Optional[float] = None) -> np.ndarray:
        """
        计算score
        
        参数:
            x: 输入数据
            t: 可选的时间步（用于扩散模型）
            
        返回:
            score向量 ∇_x log p(x)
        """
        return self.network(x, t)


class SlicedScoreMatching:
    """
    Sliced Score Matching
    
    通过随机投影计算score匹配损失：
    L = E_{v~N(0,I)} E_{x~p} [v^T J_theta(x) v + 0.5 ||s_theta(x)||^2]
    
    其中J是score network的雅可比矩阵。
    
    参数:
        score_net: Score网络
        n_projections: 投影数量
    """
    
    def __init__(self, score_net: ScoreNetwork, n_projections: int = 1):
        self.score_net = score_net
        self.n_projections = n_projections
    
    def hutchinson_trace(self, x: np.ndarray, 
                         rademacher: bool = True) -> float:
        """
        使用Hutchinson's trace estimator计算 Tr(J s_theta(x))
        
        参数:
            x: 输入数据
            rademacher: 使用Rademacher vs Gaussian随机向量
            
        返回:
            迹估计
        """
        dim = np.prod(x.shape) if x.ndim > 1 else len(x)
        
        if rademacher:
            # Rademacher随机向量
            v = np.random.choice([-1, 1], size=x.shape)
        else:
            # Gaussian随机向量
            v = np.random.randn(*x.shape)
        
        # 计算v^T J s_theta(x)
        # 近似：使用有限差分
        eps = 1e-5
        s_plus = self.score_net(x + eps * v)
        s_minus = self.score_net(x - eps * v)
        
        hvp = (s_plus - s_minus) / (2 * eps)
        
        return np.sum(v * hvp)
    
    def sliced_loss(self, x: np.ndarray) -> float:
        """
        计算Sliced Score Matching损失
        
        L = E_p[sum_i lambda_i(x)] + 0.5 * E_p[||s_theta(x)||^2]
        
        参数:
            x: 数据样本
            
        返回:
            损失值
        """
        score = self.score_net(x)
        
        # 迹项
        trace = 0.0
        for _ in range(self.n_projections):
            trace += self.hutchinson_trace(x)
        
        trace /= self.n_projections
        
        # L2项
        l2_term = 0.5 * np.sum(score ** 2)
        
        return trace + l2_term
    
    def compute_divergence(self, x: np.ndarray, 
                          method: str = 'autodiff') -> float:
        """
        计算散度 div(s_theta(x))
        
        参数:
            x: 输入
            method: 计算方法 ('autodiff', 'finite_diff', 'hutchinson')
            
        返回:
            散度值
        """
        if method == 'finite_diff':
            eps = 1e-5
            div = 0.0
            for i in np.ndindex(x.shape):
                x_plus = x.copy()
                x_plus[i] += eps
                x_minus = x.copy()
                x_minus[i] -= eps
                
                s_plus = self.score_net(x_plus)
                s_minus = self.score_net(x_minus)
                
                div += (s_plus[i] - s_minus[i]) / (2 * eps)
        
        elif method == 'hutchinson':
            v = np.random.randn(*x.shape)
            s = self.score_net(x)
            
            # 近似
            eps = 1e-5
            s_eps = self.score_net(x + eps * v)
            
            div = np.sum(v * (s_eps - s) / eps)
        
        else:
            # 简化的autodiff近似
            score = self.score_net(x)
            div = np.sum(score) * 0.1  # 占位
        
        return div


class FiniteDifferenceSM:
    """
    有限差分Score Matching
    
    简化版本：通过有限差分近似score
    """
    
    def __init__(self, log_prob_fn: Callable, eps: float = 1e-5):
        """
        参数:
            log_prob_fn: 对数概率密度函数
            eps: 有限差分步长
        """
        self.log_prob = log_prob_fn
        self.eps = eps
    
    def compute_score(self, x: np.ndarray) -> np.ndarray:
        """
        有限差分近似score
        
        ∇_x log p(x) ≈ [log p(x+eps) - log p(x-eps)] / (2*eps)
        
        参数:
            x: 输入点
            
        返回:
            score估计
        """
        score = np.zeros_like(x)
        
        flat_x = x.flatten()
        flat_score = np.zeros_like(flat_x)
        
        for i in range(len(flat_x)):
            x_plus = flat_x.copy()
            x_minus = flat_x.copy()
            
            x_plus[i] += self.eps
            x_minus[i] -= self.eps
            
            log_prob_plus = self.log_prob(x_plus.reshape(x.shape))
            log_prob_minus = self.log_prob(x_minus.reshape(x.shape))
            
            flat_score[i] = (log_prob_plus - log_prob_minus) / (2 * self.eps)
        
        return flat_score.reshape(x.shape)


class DenoisingScoreMatching:
    """
    去噪Score Matching
    
    直接从带噪声的数据学习score
    L = E_{sigma} E_{x+sigma} [||s_theta(x+sigma, sigma) - ∇_{x+sigma} log p(x+sigma|sigma)||^2]
    
    参数:
        score_net: Score网络
    """
    
    def __init__(self, score_net: ScoreNetwork):
        self.score_net = score_net
    
    def loss(self, x_noisy: np.ndarray, sigma: float) -> float:
        """
        计算去噪score matching损失
        
        参数:
            x_noisy: 带噪图像
            sigma: 噪声标准差
            
        返回:
            损失值
        """
        # 真实的score：∇_{x_noisy} log N(x_noisy|x, sigma^2) = -(x_noisy - x) / sigma^2
        # 但我们不知道原始x，所以简化为：
        score_target = -x_noisy / sigma**2  # 近似
        
        # 预测的score
        score_pred = self.score_net(x_noisy, sigma)
        
        return np.mean((score_pred - score_target) ** 2)
    
    def noise_conditional_loss(self, x_clean: np.ndarray, 
                               sigmas: np.ndarray) -> float:
        """
        多噪声级别的条件损失
        
        参数:
            x_clean: 干净图像
            sigmas: 噪声级别数组
            
        返回:
            加权损失
        """
        total_loss = 0.0
        
        for sigma in sigmas:
            # 添加噪声
            noise = np.random.randn(*x_clean.shape) * sigma
            x_noisy = x_clean + noise
            
            # 计算损失
            loss = self.loss(x_noisy, sigma)
            
            # 加权
            weight = 1.0 / sigma**2
            total_loss += weight * loss
        
        return total_loss / len(sigmas)


class SongEBM:
    """
    基于Energy-Based Model的Score Matching (NCSN)
    
    来自Song Yang等人的"Generative Modeling by Estimating Gradients of the Data Distribution"
    
    参数:
        sigma_min: 最小噪声级别
        sigma_max: 最大噪声级别
        score_net: Score网络
    """
    
    def __init__(self, score_net: ScoreNetwork, 
                 sigma_min: float = 0.01, sigma_max: float = 1.0):
        self.score_net = score_net
        self.sigma_min = sigma_min
        self.sigma_max = sigma_max
        
        # 噪声级别（几何级数）
        self.sigmas = np.geomspace(sigma_min, sigma_max, 10)
    
    def annealed_loss(self, x: np.ndarray) -> float:
        """
        退火损失
        
        L = sum_{i} lambda(sigma_i) * E_{x~N(x, sigma_i^2)} 
            [||sigma_i * s_theta(x, sigma_i) + (x - mu)/sigma_i||^2]
            
        参数:
            x: 数据样本
            
        返回:
            损失值
        """
        total_loss = 0.0
        
        for sigma in self.sigmas:
            # 添加噪声
            noise = np.random.randn(*x.shape) * sigma
            x_noisy = x + noise
            
            # 预测score（乘以sigma）
            sigma_s = self.score_net(x_noisy, sigma) * sigma
            
            # 目标：-(x_noisy - x) / sigma = -noise / sigma
            target = -noise / sigma
            
            # 损失
            loss = np.mean((sigma_s - target) ** 2)
            
            # 权重
            total_loss += loss
        
        return total_loss / len(self.sigmas)


class LangevinSampler:
    """
    Langevin动力学采样
    
    使用score function进行MCMC采样
    x_{t+1} = x_t + epsilon * s_theta(x_t) + sqrt(2*epsilon) * z_t
    
    参数:
        score_net: Score网络
        step_size: 步长
    """
    
    def __init__(self, score_net: ScoreNetwork, step_size: float = 0.01):
        self.score_net = score_net
        self.step_size = step_size
    
    def sample(self, n_steps: int, initial: Optional[np.ndarray] = None,
               temperature: float = 1.0) -> np.ndarray:
        """
        运行Langevin采样
        
        参数:
            n_steps: 采样步数
            initial: 初始点
            temperature: 温度（>1增加探索）
            
        返回:
            采样轨迹
        """
        if initial is None:
            x = np.random.randn(1, 2)  # 简化的2D采样
        else:
            x = initial.copy()
        
        samples = [x.copy()]
        
        for _ in range(n_steps):
            # 计算score
            score = self.score_net(x)
            
            # 更新
            noise = np.random.randn(*x.shape)
            x = x + self.step_size * score + np.sqrt(2 * self.step_size * temperature) * noise
            
            samples.append(x.copy())
        
        return np.array(samples)


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Score匹配测试")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 测试1：简单高斯分布的Score
    print("\n1. 高斯分布的Score Function:")
    
    # 真实的score: ∇_x log N(x|mu, sigma^2) = -(x - mu) / sigma^2
    
    def true_log_prob(x, mu=0.0, sigma=1.0):
        return -0.5 * (x - mu)**2 / sigma**2 - 0.5 * np.log(2 * np.pi * sigma**2)
    
    def true_score(x, mu=0.0, sigma=1.0):
        return -(x - mu) / sigma**2
    
    fdm = FiniteDifferenceSM(true_log_prob, eps=1e-5)
    
    x_test = np.array([[1.0], [2.0], [0.0]])
    
    for x in x_test:
        score_true = true_score(x)
        score_est = fdm.compute_score(x)
        print(f"   x={x[0]:.1f}: 真实score={score_true[0]:.4f}, 估计score={score_est[0]:.4f}")
    
    # 测试2：Score网络
    print("\n2. Score网络:")
    
    def mock_network(x, t=None):
        """模拟的score网络"""
        return -x * 0.5 + np.random.randn(*x.shape) * 0.1
    
    score_net = ScoreNetwork(mock_network)
    
    x = np.random.randn(4, 3, 8, 8)
    score = score_net(x)
    print(f"   输入形状: {x.shape}")
    print(f"   Score形状: {score.shape}")
    
    # 测试3：Sliced Score Matching
    print("\n3. Sliced Score Matching:")
    
    class SimpleScoreNet:
        def __init__(self):
            self.params = np.random.randn(10) * 0.1
        
        def __call__(self, x, t=None):
            return x * 0.3 + np.mean(self.params)
    
    simple_net = SimpleScoreNet()
    score_net = ScoreNetwork(simple_net)
    
    ssm = SlicedScoreMatching(score_net, n_projections=1)
    
    x = np.random.randn(8, 5)
    loss = ssm.sliced_loss(x)
    print(f"   输入形状: {x.shape}")
    print(f"   Sliced SM损失: {loss:.6f}")
    
    # 测试4：去噪Score Matching
    print("\n4. 去噪Score Matching:")
    
    dsm = DenoisingScoreMatching(score_net)
    
    x_clean = np.random.randn(4, 10)
    x_noisy = x_clean + np.random.randn(4, 10) * 0.5
    sigma = 0.5
    
    loss = dsm.loss(x_noisy, sigma)
    print(f"   干净数据形状: {x_clean.shape}")
    print(f"   噪声级别: {sigma}")
    print(f"   去噪SM损失: {loss:.6f}")
    
    # 测试5：NCSN退火损失
    print("\n5. NCSN退火Score Matching:")
    
    ebm = SongEBM(score_net, sigma_min=0.01, sigma_max=1.0)
    
    print(f"   噪声级别: {ebm.sigmas}")
    
    x = np.random.randn(4, 10)
    loss = ebm.annealed_loss(x)
    print(f"   退火损失: {loss:.6f}")
    
    # 测试6：Langevin采样
    print("\n6. Langevin动力学采样:")
    
    class GaussianScoreNet:
        def __call__(self, x, t=None):
            return -x  # N(0,1)的score
    
    langevin = LangevinSampler(GaussianScoreNet(), step_size=0.1)
    
    samples = langevin.sample(n_steps=100)
    print(f"   采样轨迹形状: {samples.shape}")
    print(f"   最后样本均值: {samples[-1].mean():.4f}")
    print(f"   最后样本方差: {samples[-1].var():.4f}")
    
    # 测试7：散度计算
    print("\n7. Score散度计算:")
    
    div = ssm.compute_divergence(x, method='finite_diff')
    print(f"   散度估计: {div:.6f}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
