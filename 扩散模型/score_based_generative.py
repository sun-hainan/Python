"""
Score-Based生成模型
Score-Based Generative Models

Score-Based模型通过学习数据分布的score function ∇_x log p(x) 来生成样本。
等价于学习能量模型的梯度，可以看作扩散模型的连续极限。
"""

import numpy as np
from typing import Callable, Tuple, Optional, List
from abc import ABC, abstractmethod


class ScoreBasedModel:
    """
    Score-Based生成模型基类
    
    核心思想：
    1. 学习 score(x) = ∇_x log p(x)
    2. 使用 Langevin MCMC 从 p(x) 采样
    """
    
    def __init__(self, score_net: Callable):
        self.score_net = score_net
    
    def __call__(self, x: np.ndarray, t: Optional[float] = None) -> np.ndarray:
        """计算score"""
        return self.score_net(x, t)


class NoiseConditionedScoreNetwork:
    """
    噪声条件Score网络 (NCSN)
    
    对多个噪声级别分别预测score
    s_theta(x, sigma) ≈ ∇_x log p_sigma(x)
    
    参数:
        sigmas: 噪声级别数组
        network: 基础网络
    """
    
    def __init__(self, sigmas: np.ndarray, network: Callable):
        self.sigmas = sigmas
        self.network = network
        self.n_levels = len(sigmas)
    
    def __call__(self, x: np.ndarray, sigma: float) -> np.ndarray:
        """
        计算给定噪声级别下的score
        
        参数:
            x: 输入
            sigma: 噪声级别
            
        返回:
            score向量
        """
        # 通过网络预测
        score = self.network(x, sigma)
        return score
    
    def annealed_score(self, x: np.ndarray) -> np.ndarray:
        """
        退火score（对多个噪声级别加权）
        
        参数:
            x: 输入
            
        返回:
            加权score
        """
        weighted_score = np.zeros_like(x)
        
        for sigma in self.sigmas:
            # 添加对应级别的噪声
            x_noisy = x + np.random.randn(*x.shape) * sigma
            
            # 预测score
            score = self.network(x_noisy, sigma)
            
            # 权重
            weight = 1.0 / sigma**2
            
            weighted_score += weight * score
        
        return weighted_score / len(self.sigmas)


class AnnealedLangevinDynamics:
    """
    退火Langevin动力学采样
    
    从粗到细的多噪声级别采样
    每个级别执行Langevin采样，然后逐渐降低噪声
    
    参数:
        score_net: Score网络
        sigmas: 噪声级别（从大到小）
    """
    
    def __init__(self, score_net: ScoreNetwork, sigmas: np.ndarray,
                 step_size: float = 0.0001, n_steps_per_level: int = 100):
        self.score_net = score_net
        self.sigmas = sigmas  # 从大到小
        self.step_size = step_size
        self.n_steps = n_steps_per_level
    
    def sample(self, initial: Optional[np.ndarray] = None,
               shape: Tuple = (1,)) -> np.ndarray:
        """
        运行退火Langevin采样
        
        参数:
            initial: 初始点
            shape: 如果无初始点，生成此形状的初始点
            
        返回:
            采样结果
        """
        if initial is None:
            x = np.random.randn(*shape)
        else:
            x = initial.copy()
        
        trajectory = [x]
        
        # 从最粗糙的噪声开始
        for sigma in self.sigmas:
            # 使用固定步长的Langevin采样
            for _ in range(self.n_steps):
                # 计算score
                score = self.score_net(x, sigma)
                
                # Langevin更新
                noise = np.random.randn(*x.shape)
                x = x + self.step_size * score + np.sqrt(2 * self.step_size) * noise
                
                trajectory.append(x)
        
        return np.array(trajectory)
    
    def sample_single_trajectory(self, shape: Tuple) -> np.ndarray:
        """
        单条采样轨迹
        
        参数:
            shape: 采样形状
            
        返回:
            最终采样
        """
        x = np.random.randn(*shape)
        
        for sigma in self.sigmas:
            for _ in range(self.n_steps):
                score = self.score_net(x, sigma)
                noise = np.random.randn(*x.shape)
                
                x = x + self.step_size * score + np.sqrt(2 * self.step_size) * noise
        
        return x


class ConditionalScoreModel:
    """
    条件Score模型
    
    学习条件score: s_theta(x|y) = ∇_x log p(x|y)
    
    参数:
        base_score_net: 基础score网络
    """
    
    def __init__(self, base_score_net: Callable):
        self.base_score_net = base_score_net
    
    def __call__(self, x: np.ndarray, y: np.ndarray, 
                t: Optional[float] = None) -> np.ndarray:
        """
        计算条件score
        
        参数:
            x: 输入
            y: 条件
            t: 时间步
        """
        # 简化的条件score计算
        base_score = self.base_score_net(x, t)
        
        # 假设y通过某种方式影响score
        cond_effect = y * 0.1
        
        return base_score + cond_effect


class EnergyBasedModel:
    """
    基于能量模型 (EBM)
    
    p(x) ∝ exp(-E(x))
    
    参数:
        energy_fn: 能量函数 E(x)
    """
    
    def __init__(self, energy_fn: Callable):
        self.energy_fn = energy_fn
    
    def score(self, x: np.ndarray) -> np.ndarray:
        """
        计算score: -∇_x E(x)
        
        参数:
            x: 输入
            
        返回:
            score向量
        """
        # 有限差分近似
        eps = 1e-5
        score = np.zeros_like(x)
        
        flat_x = x.flatten()
        flat_score = np.zeros_like(flat_x)
        
        for i in range(len(flat_x)):
            x_plus = flat_x.copy()
            x_minus = flat_x.copy()
            
            x_plus[i] += eps
            x_minus[i] -= eps
            
            E_plus = self.energy_fn(x_plus.reshape(x.shape))
            E_minus = self.energy_fn(x_minus.reshape(x.shape))
            
            # score = -∇_x E(x)
            flat_score[i] = -(E_plus - E_minus) / (2 * eps)
        
        return flat_score.reshape(x.shape)
    
    def langevin_sample(self, n_steps: int, step_size: float = 0.01,
                       initial: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Langevin采样
        
        x_{t+1} = x_t - step_size * ∇_x E(x_t) + sqrt(2*step_size) * z_t
        
        参数:
            n_steps: 采样步数
            step_size: 步长
            initial: 初始点
        """
        if initial is None:
            x = np.random.randn(2)  # 简化的2D
        else:
            x = initial.copy()
        
        samples = [x]
        
        for _ in range(n_steps):
            energy_grad = self.score(x)
            noise = np.random.randn(*x.shape)
            
            x = x - step_size * energy_grad + np.sqrt(2 * step_size) * noise
            samples.append(x)
        
        return np.array(samples)


class ContrastiveDivergence:
    """
    对比散度 (Contrastive Divergence, CD-k)
    
    用于训练EBM的近似算法
    
    参数:
        ebm: 能量模型
        k: k步Gibbs采样
    """
    
    def __init__(self, ebm: EnergyBasedModel, k: int = 1, lr: float = 0.01):
        self.ebm = ebm
        self.k = k
        self.lr = lr
    
    def train_step(self, x_data: np.ndarray, 
                   params: dict) -> Tuple[dict, np.ndarray]:
        """
        单步训练
        
        参数:
            x_data: 数据样本
            params: 模型参数
            
        返回:
            (梯度, 负样本)
        """
        # 计算正梯度
        positive_grad = self._compute_gradient(x_data, params)
        
        # 用Gibbs采样获得负样本
        x_neg = self._gibbs_sample(x_data)
        
        # 计算负梯度
        negative_grad = self._compute_gradient(x_neg, params)
        
        # 梯度更新
        grad = positive_grad - negative_grad
        params = self._update_params(params, grad)
        
        return params, x_neg
    
    def _compute_gradient(self, x: np.ndarray, params: dict) -> np.ndarray:
        """计算能量梯度"""
        # 简化
        return np.random.randn(*x.shape) * 0.1
    
    def _gibbs_sample(self, x: np.ndarray) -> np.ndarray:
        """k步Gibbs采样"""
        x_sample = x.copy()
        
        for _ in range(self.k):
            # 采样新状态
            x_sample = x_sample + np.random.randn(*x_sample.shape) * 0.5
        
        return x_sample
    
    def _update_params(self, params: dict, grad: np.ndarray) -> dict:
        """更新参数"""
        return params


class JointScoreMatching:
    """
    联合Score匹配
    
    同时匹配数据分布和噪声扰动分布的score
    
    参数:
        data_score_net: 数据score网络
        noise_score_net: 噪声score网络
    """
    
    def __init__(self, data_score_net: Callable, noise_score_net: Callable):
        self.data_score_net = data_score_net
        self.noise_score_net = noise_score_net
    
    def loss(self, x_data: np.ndarray, sigma: float) -> float:
        """
        联合Score匹配损失
        
        参数:
            x_data: 数据样本
            sigma: 噪声级别
            
        返回:
            损失值
        """
        # 添加噪声
        x_noisy = x_data + np.random.randn(*x_data.shape) * sigma
        
        # 数据score
        s_data = self.data_score_net(x_data, sigma)
        
        # 噪声score
        s_noise = self.noise_score_net(x_noisy, sigma)
        
        # 损失：匹配噪声扰动分布的score
        loss = np.mean((s_data + (x_noisy - x_data) / sigma**2) ** 2)
        
        return loss


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Score-Based生成模型测试")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 模拟score网络
    class MockScoreNet:
        def __call__(self, x, sigma=None):
            # 假设数据服从 N(0,1)，score = -x
            return -x
    
    score_net = ScoreBasedModel(MockScoreNet())
    
    # 测试1：基础Score计算
    print("\n1. Score计算:")
    
    x = np.array([1.0, 2.0, -1.0])
    score = score_net(x)
    print(f"   x = {x}")
    print(f"   score = {score}")
    print(f"   真实score (N(0,1)) = {-x}")
    
    # 测试2：噪声条件Score网络
    print("\n2. 噪声条件Score网络 (NCSN):")
    
    sigmas = np.array([1.0, 0.5, 0.1, 0.01])
    ncscore = NoiseConditionedScoreNetwork(sigmas, MockScoreNet())
    
    for sigma in sigmas:
        x = np.random.randn(3)
        x_noisy = x + np.random.randn(3) * sigma
        score = ncscore(x_noisy, sigma)
        print(f"   sigma={sigma:.2f}: ||score||={np.linalg.norm(score):.4f}")
    
    # 测试3：退火Langevin动力学
    print("\n3. 退火Langevin动力学采样:")
    
    # 从大到小的噪声
    sigmas_anneal = np.array([1.0, 0.5, 0.1, 0.01])
    
    ald = AnnealedLangevinDynamics(score_net, sigmas_anneal, 
                                   step_size=0.01, n_steps_per_level=10)
    
    final_sample = ald.sample_single_trajectory(shape=(2,))
    print(f"   最终采样: {final_sample}")
    
    # 测试4：EBM和Langevin采样
    print("\n4. 基于能量模型 (EBM):")
    
    def energy_fn(x):
        # 双势阱能量
        return ((x**2 - 1)**2).sum()
    
    ebm = EnergyBasedModel(energy_fn)
    
    x_test = np.array([0.0, 0.0])
    score = ebm.score(x_test.reshape(1, -1))
    print(f"   x = {x_test}")
    print(f"   score = {score.flatten()}")
    print(f"   能量 = {energy_fn(x_test)}")
    
    # 测试5：Langevin采样轨迹
    print("\n5. Langevin采样轨迹:")
    
    samples = ebm.langevin_sample(n_steps=50, step_size=0.1)
    print(f"   采样点数: {len(samples)}")
    print(f"   最后5个点:\n{samples[-5:]}")
    
    # 测试6：对比散度
    print("\n6. 对比散度训练:")
    
    cd = ContrastiveDivergence(ebm, k=1)
    
    x_data = np.random.randn(4, 2)
    params = {'w': np.random.randn(10, 2) * 0.1}
    
    params, x_neg = cd.train_step(x_data, params)
    print(f"   正样本均值: {x_data.mean(axis=0)}")
    print(f"   负样本均值: {x_neg.mean(axis=0)}")
    
    # 测试7：条件Score模型
    print("\n7. 条件Score模型:")
    
    cond_score = ConditionalScoreModel(MockScoreNet())
    
    x = np.array([1.0, 2.0])
    y = np.array([0.5, -0.5])
    
    score = cond_score(x, y)
    print(f"   x = {x}, y = {y}")
    print(f"   条件score = {score}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


class ScoreNetwork:
    """简化的Score网络接口"""
    def __init__(self, net_fn):
        self.network = net_fn
    
    def __call__(self, x, sigma=None):
        return self.network(x, sigma)
