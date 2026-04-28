"""
Score重参数化技术
Score Renormalization Techniques

Score重参数化用于改善score matching的训练稳定性和样本质量。
包括各种归一化和正则化技术。
"""

import numpy as np
from typing import Callable, Optional, Tuple
from abc import ABC, abstractmethod


class ScoreRenormalization(ABC):
    """
    Score重参数化基类
    """
    
    @abstractmethod
    def apply(self, score: np.ndarray, x: np.ndarray, t: float) -> np.ndarray:
        """应用重参数化"""
        pass


class UnitNormRenormalization(ScoreRenormalization):
    """
    单位范数重参数化
    
    将score归一化到单位长度
    
    ||s_theta(x, t)|| = 1
    """
    
    def __init__(self, eps: float = 1e-6):
        self.eps = eps
    
    def apply(self, score: np.ndarray, x: np.ndarray, 
              t: float = None) -> np.ndarray:
        """
        应用单位范数重参数化
        
        参数:
            score: 原始score
            x: 输入（未使用）
            t: 时间步（未使用）
            
        返回:
            归一化后的score
        """
        norm = np.linalg.norm(score.flatten())
        if norm < self.eps:
            return score
        return score / norm


class SpectralNormalization:
    """
    谱归一化
    
    将网络参数矩阵的谱范数限制为1
    
    参数:
        n_power_iterations: 幂迭代次数
    """
    
    def __init__(self, n_power_iterations: int = 1):
        self.n_power_iterations = n_power_iterations
        self.u = None  # 奇异向量近似
    
    def normalize(self, W: np.ndarray) -> np.ndarray:
        """
        对权重矩阵进行谱归一化
        
        参数:
            W: 权重矩阵
            
        返回:
            归一化后的权重
        """
        W_flat = W.reshape(-1, W.shape[-1])
        
        if self.u is None:
            self.u = np.random.randn(W_flat.shape[0])
            self.u = self.u / np.linalg.norm(self.u)
        
        # 幂迭代求奇异值
        for _ in range(self.n_power_iterations):
            v = W_flat @ self.u
            v = v / (np.linalg.norm(v) + 1e-8)
            u_new = W_flat.T @ v
            u_new = u_new / (np.linalg.norm(u_new) + 1e-8)
            self.u = u_new
        
        sigma = np.dot(u_new, W_flat @ self.u)
        
        return W / sigma


class AdaptiveScoreScaling(ScoreRenormalization):
    """
    自适应Score缩放
    
    根据输入范数动态调整score的缩放
    
    s' = s / (||x|| + c)
    """
    
    def __init__(self, c: float = 1.0):
        self.c = c
    
    def apply(self, score: np.ndarray, x: np.ndarray, 
              t: float = None) -> np.ndarray:
        """
        应用自适应缩放
        
        参数:
            score: 原始score
            x: 输入数据
            t: 时间步
            
        返回:
            缩放后的score
        """
        x_norm = np.linalg.norm(x.flatten())
        scale = x_norm / (x_norm + self.c)
        return score * scale


class TemperatureScoreScaling(ScoreRenormalization):
    """
    温度缩放
    
    s' = s / temperature
    
    用于控制分布的锐度
    """
    
    def __init__(self, initial_temp: float = 1.0):
        self.temperature = initial_temp
    
    def apply(self, score: np.ndarray, x: np.ndarray, 
              t: float = None) -> np.ndarray:
        """应用温度缩放"""
        return score / self.temperature
    
    def update_temperature(self, new_temp: float):
        """更新温度"""
        self.temperature = new_temp


class LipschitzScoreRegularization:
    """
    Lipschitz正则化
    
    添加Lipschitz约束到score function
    
    ||s(x1) - s(x2)|| <= L ||x1 - x2||
    """
    
    def __init__(self, lip_coeff: float = 0.1):
        self.lip_coeff = lip_coeff
    
    def compute_penalty(self, score_net: Callable, 
                       x1: np.ndarray, x2: np.ndarray) -> float:
        """
        计算Lipschitz惩罚项
        
        参数:
            score_net: score网络
            x1, x2: 样本对
            
        返回:
            惩罚值
        """
        s1 = score_net(x1)
        s2 = score_net(x2)
        
        score_diff = np.linalg.norm(s1 - s2)
        x_diff = np.linalg.norm(x1 - x2)
        
        if x_diff < 1e-8:
            return 0.0
        
        violation = max(0, score_diff / x_diff - 1.0)
        
        return self.lip_coeff * violation


class NoiseConditionedRenormalization:
    """
    噪声条件归一化 (NCR)
    
    根据噪声级别自适应调整归一化
    
    参数:
        sigma_min: 最小sigma
        sigma_max: 最大sigma
    """
    
    def __init__(self, sigma_min: float = 0.01, sigma_max: float = 1.0):
        self.sigma_min = sigma_min
        self.sigma_max = sigma_max
    
    def apply(self, score: np.ndarray, x: np.ndarray, 
              sigma: float) -> np.ndarray:
        """
        应用噪声条件归一化
        
        s' = s * sigma
        
        参数:
            score: 原始score
            x: 输入
            sigma: 噪声级别
            
        返回:
            归一化后的score
        """
        # 缩放
        scaled_score = score * sigma
        
        # 归一化
        norm = np.linalg.norm(scaled_score.flatten())
        if norm < 1e-8:
            return scaled_score
        
        return scaled_score / norm
    
    def get_sigma_schedule(self, n_steps: int) -> np.ndarray:
        """获取sigma调度"""
        return np.geomspace(self.sigma_max, self.sigma_min, n_steps)


class FlowScoreMatching:
    """
    流匹配Score重参数化
    
    用于连续正规化流(CNF)的score
    """
    
    def __init__(self, model: Callable):
        self.model = model
    
    def compute_divergence(self, x: np.ndarray, 
                          t: float) -> np.ndarray:
        """
        计算速度场的散度
        
        参数:
            x: 位置
            t: 时间
            
        返回:
            散度
        """
        # 简化的散度计算
        eps = 1e-5
        div = np.zeros_like(x)
        
        x_flat = x.flatten()
        div_flat = np.zeros_like(x_flat)
        
        for i in range(len(x_flat)):
            x_plus = x_flat.copy()
            x_minus = x_flat.copy()
            x_plus[i] += eps
            x_minus[i] -= eps
            
            s_plus = self.model(x_plus.reshape(x.shape), t)
            s_minus = self.model(x_minus.reshape(x.shape), t)
            
            div_flat[i] = (np.sum(s_plus) - np.sum(s_minus)) / (2 * eps)
        
        return div_flat.reshape(x.shape)
    
    def score_matching_loss(self, x: np.ndarray, 
                           t: float, 
                           target_score: np.ndarray) -> float:
        """
        修正的score matching损失
        
        L = ||s(x,t) - target||^2 + lambda * ||div(s(x,t))||^2
        """
        pred_score = self.model(x, t)
        
        # 主要损失
        main_loss = np.mean((pred_score - target_score) ** 2)
        
        # 散度惩罚
        div = self.compute_divergence(x, t)
        div_loss = np.mean(div ** 2)
        
        return main_loss + 0.1 * div_loss


class MixupScoreAugmentation:
    """
    Mixup数据增强
    
    在score matching中混合样本
    """
    
    def __init__(self, alpha: float = 0.2):
        self.alpha = alpha
    
    def mixup(self, x1: np.ndarray, x2: np.ndarray, 
             score1: np.ndarray, score2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Mixup变换
        
        x~ = lambda * x1 + (1-lambda) * x2
        s~ = lambda * s1 + (1-lambda) * s2
        
        参数:
            x1, x2: 输入样本
            score1, score2: 对应的score
            
        返回:
            (混合样本, 混合score)
        """
        lam = np.random.beta(self.alpha, self.alpha)
        
        x_mix = lam * x1 + (1 - lam) * x2
        score_mix = lam * score1 + (1 - lam) * score2
        
        return x_mix, score_mix


class ScoreRegularizer:
    """
    Score正则化器
    
    组合多种正则化技术
    """
    
    def __init__(self, config: dict = None):
        config = config or {}
        
        self.unit_norm = config.get('unit_norm', False)
        self.adaptive_scale = config.get('adaptive_scale', False)
        self.lipschitz = config.get('lipschitz', False)
        self.lip_coeff = config.get('lip_coeff', 0.1)
        
        self.unit_norm_renorm = UnitNormRenormalization()
        self.adaptive_renorm = AdaptiveScoreScaling()
        self.lip_reg = LipschitzScoreRegularization(lip_coeff=self.lip_coeff)
    
    def regularize(self, score: np.ndarray, x: np.ndarray,
                  t: float = None, score_net: Callable = None) -> np.ndarray:
        """
        应用正则化
        
        参数:
            score: 原始score
            x: 输入
            t: 时间步
            score_net: score网络（用于Lipschitz惩罚）
            
        返回:
            正则化后的score
        """
        reg_score = score
        
        if self.unit_norm:
            reg_score = self.unit_norm_renorm.apply(reg_score, x, t)
        
        if self.adaptive_scale:
            reg_score = self.adaptive_renorm.apply(reg_score, x, t)
        
        return reg_score


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Score重参数化技术测试")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 模拟score网络
    class MockScoreNet:
        def __call__(self, x, t=None):
            return x * 0.1 + np.random.randn(*x.shape) * 0.01
    
    score_net = MockScoreNet()
    
    # 测试1：单位范数归一化
    print("\n1. 单位范数归一化:")
    
    un_renorm = UnitNormRenormalization(eps=1e-6)
    
    scores = [np.array([[1.0, 2.0], [3.0, 4.0]]),
              np.array([[0.1, 0.2], [0.3, 0.4]])]
    
    for s in scores:
        s_renorm = un_renorm.apply(s, None, None)
        print(f"   原始范数: {np.linalg.norm(s):.4f}, 重参数化后: {np.linalg.norm(s_renorm):.4f}")
    
    # 测试2：自适应缩放
    print("\n2. 自适应Score缩放:")
    
    adapt_renorm = AdaptiveScoreScaling(c=1.0)
    
    x = np.array([[10.0, 20.0], [30.0, 40.0]])
    score = x * 0.05
    
    s_scaled = adapt_renorm.apply(score, x, None)
    print(f"   x范数: {np.linalg.norm(x):.4f}")
    print(f"   缩放后score范数: {np.linalg.norm(s_scaled):.4f}")
    
    # 测试3：温度缩放
    print("\n3. 温度缩放:")
    
    temp_scaling = TemperatureScoreScaling(initial_temp=1.0)
    
    score = np.random.randn(5, 5)
    
    for temp in [0.5, 1.0, 2.0, 5.0]:
        temp_scaling.update_temperature(temp)
        s_temp = temp_scaling.apply(score, None, None)
        print(f"   T={temp}: score范数={np.linalg.norm(s_temp):.4f}")
    
    # 测试4：Lipschitz正则化
    print("\n4. Lipschitz正则化:")
    
    lip_reg = LipschitzScoreRegularization(lip_coeff=0.1)
    
    x1 = np.random.randn(1, 10)
    x2 = x1 + np.random.randn(1, 10) * 0.1
    
    penalty = lip_reg.compute_penalty(score_net, x1, x2)
    print(f"   Lipschitz惩罚: {penalty:.6f}")
    
    # 测试5：噪声条件归一化
    print("\n5. 噪声条件归一化:")
    
    ncr = NoiseConditionedRenormalization(sigma_min=0.01, sigma_max=1.0)
    
    sigmas = [0.01, 0.1, 0.5, 1.0]
    score = np.random.randn(5, 5)
    x = np.random.randn(5, 5)
    
    for sigma in sigmas:
        s_ncr = ncr.apply(score, x, sigma)
        print(f"   sigma={sigma:.2f}: 归一化score范数={np.linalg.norm(s_ncr):.4f}")
    
    # 测试6：谱归一化
    print("\n6. 谱归一化:")
    
    spec_norm = SpectralNormalization(n_power_iterations=1)
    
    W = np.random.randn(64, 128)
    W_normalized = spec_norm.normalize(W)
    
    # 验证谱范数为1
    spectral_norm = np.linalg.svd(W_normalized, compute_uv=False)[0]
    print(f"   原始权重谱范数: {np.linalg.svd(W, compute_uv=False)[0]:.4f}")
    print(f"   归一化后谱范数: {spectral_norm:.4f}")
    
    # 测试7：组合正则化
    print("\n7. 组合Score正则化:")
    
    reg_config = {
        'unit_norm': True,
        'adaptive_scale': True,
        'lipschitz': True,
        'lip_coeff': 0.1
    }
    
    regularizer = ScoreRegularizer(reg_config)
    
    score = np.random.randn(4, 8)
    x = np.random.randn(4, 8)
    
    s_reg = regularizer.regularize(score, x, t=0.5)
    print(f"   正则化前范数: {np.linalg.norm(score):.4f}")
    print(f"   正则化后范数: {np.linalg.norm(s_reg):.4f}")
    
    # 测试8：Mixup增强
    print("\n8. Mixup数据增强:")
    
    mixup = MixupScoreAugmentation(alpha=0.2)
    
    x1 = np.array([[1.0, 2.0], [3.0, 4.0]])
    x2 = np.array([[5.0, 6.0], [7.0, 8.0]])
    s1 = np.array([[0.1, 0.2], [0.3, 0.4]])
    s2 = np.array([[0.5, 0.6], [0.7, 0.8]])
    
    x_mix, s_mix = mixup.mixup(x1, x2, s1, s2)
    print(f"   x1: {x1.flatten()[:4]}")
    print(f"   x2: {x2.flatten()[:4]}")
    print(f"   x_mix: {x_mix.flatten()[:4]}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
