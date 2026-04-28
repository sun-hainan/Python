"""
DDPM损失函数：简化损失与变分下界
DDPM Loss Functions: Simplified Loss and Variational Lower Bound

DDPM训练目标经历了从VLBO到简化MSE损失的演进。
核心思想：预测噪声比预测原始图像更有效。
"""

import numpy as np
from typing import Tuple, Optional, Callable


class DDPMLoss:
    """
    DDPM损失函数计算
    
    参数:
        T: 扩散步数
        loss_type: 损失类型 ('mse', 'vlb', 'hybrid')
        lambda_vlb: VLB损失的权重（用于hybrid）
    """
    
    def __init__(self, T: int = 1000, loss_type: str = 'mse', 
                 lambda_vlb: float = 0.001):
        self.T = T
        self.loss_type = loss_type
        self.lambda_vlb = lambda_vlb
        
        # 预计算调度参数
        self._compute_schedule()
    
    def _compute_schedule(self):
        """计算扩散调度参数"""
        # 线性beta调度
        self.betas = np.linspace(1e-4, 0.02, self.T)
        self.alphas = 1 - self.betas
        self.alphas_bar = np.cumprod(self.alphas)
        
        # 一些常用值
        self.sqrt_alphas_bar = np.sqrt(self.alphas_bar)
        self.sqrt_one_minus_alphas_bar = np.sqrt(1 - self.alphas_bar)
        self.sqrt_recip_alphas = np.sqrt(1 / self.alphas)
        self.sqrt_recip_alphas_bar = np.sqrt(1 / self.alphas_bar)
    
    def simplified_loss(self, epsilon_theta: np.ndarray, epsilon: np.ndarray,
                        x_t: np.ndarray, t: np.ndarray) -> float:
        """
        简化MSE损失（原始DDPM论文）
        
        L_simple = E_{t,x0,epsilon} || epsilon - epsilon_theta(x_t, t) ||^2
        
        参数:
            epsilon_theta: 预测的噪声
            epsilon: 真实的噪声
            x_t: 时间步t的图像
            t: 时间步
            
        返回:
            损失值
        """
        # 时间步权重（可选的加权策略）
        loss = (epsilon_theta - epsilon) ** 2
        
        # 保留维度用于均值计算
        while loss.ndim > 1:
            loss = np.mean(loss, axis=-1)
        
        return np.mean(loss)
    
    def vlb_loss(self, x_0: np.ndarray, epsilon: np.ndarray,
                 t: np.ndarray, epsilon_theta: np.ndarray,
                 model_vlb: Optional[Callable] = None) -> float:
        """
        变分下界损失（改进版DDPM）
        
        L_vlb = L_t-1 + L_0 + L_T
        
        其中：
        - L_T: 先验匹配（x_T与纯噪声的距离）
        - L_0: 最终重建损失
        - L_t-1: 重建损失（相邻时间步）
        
        参数:
            x_0: 原始图像
            epsilon: 添加的噪声
            t: 时间步
            epsilon_theta: 预测的噪声
            model_vlb: 用于计算p_theta(x_{t-1}|x_t)的模型
            
        返回:
            VLB损失
        """
        # 简化计算：只用重构损失的近似
        batch_size = len(t)
        
        # 计算x_t（需要x_0和epsilon）
        alpha_bar_t = self.alphas_bar[t].reshape(-1, 1, 1, 1)
        x_t = np.sqrt(alpha_bar_t) * x_0 + np.sqrt(1 - alpha_bar_t) * epsilon
        
        # L_t-1：预测x_{t-1}的损失
        # 简化：使用预测噪声的损失
        l_t_minus_1 = np.mean((epsilon_theta - epsilon) ** 2)
        
        # L_T: 先验（假设为0）
        l_T = 0.0
        
        # L_0: 最终步（简化）
        l_0 = l_t_minus_1
        
        return l_t_minus_1 + l_T + l_0
    
    def hybrid_loss(self, x_0: np.ndarray, epsilon: np.ndarray,
                    t: np.ndarray, epsilon_theta: np.ndarray,
                    model_vlb: Optional[Callable] = None) -> Tuple[float, dict]:
        """
        混合损失：MSE + lambda * VLB
        
        参数:
            x_0: 原始图像
            epsilon: 真实噪声
            t: 时间步
            epsilon_theta: 预测噪声
            model_vlb: VLB计算模型
            
        返回:
            (总损失, 损失分解字典)
        """
        loss_mse = self.simplified_loss(epsilon_theta, epsilon, x_0, t)
        
        if self.loss_type == 'hybrid' and model_vlb is not None:
            loss_vlb = self.vlb_loss(x_0, epsilon, t, epsilon_theta, model_vlb)
            loss_total = loss_mse + self.lambda_vlb * loss_vlb
        else:
            loss_vlb = 0.0
            loss_total = loss_mse
        
        return loss_total, {
            'mse': loss_mse,
            'vlb': loss_vlb,
            'total': loss_total
        }
    
    def weighted_loss(self, epsilon_theta: np.ndarray, epsilon: np.ndarray,
                      t: np.ndarray, weighting: str = 'uniform') -> float:
        """
        加权损失
        
        参数:
            epsilon_theta: 预测噪声
            epsilon: 真实噪声
            t: 时间步
            weighting: 加权策略 ('uniform', 'snr', 'inv_sn_r', 'uniform_v2')
            
        返回:
            加权损失
        """
        batch_size = len(t)
        
        # 计算SNR
        alpha_bar_t = self.alphas_bar[t]
        snr = alpha_bar_t / (1 - alpha_bar_t)
        
        if weighting == 'uniform':
            weights = np.ones_like(t, dtype=float)
        elif weighting == 'snr':
            weights = snr
        elif weighting == 'inv_snr':
            weights = 1 / (snr + 1e-8)
        elif weighting == 'uniform_v2':
            # Improved DDPM加权
            weights = (1 + snr) ** -0.5
        else:
            weights = np.ones_like(t, dtype=float)
        
        # 加权MSE
        loss = (epsilon_theta - epsilon) ** 2
        
        while loss.ndim > 1:
            loss = np.mean(loss, axis=-1)
        
        weighted_loss = loss * weights
        
        return np.mean(weighted_loss)


class DDPM Trainer:
    """
    DDPM训练器
    
    参数:
        model: 去噪模型
        loss_fn: 损失函数
        optimizer: 优化器（简化实现）
    """
    
    def __init__(self, model, loss_fn: DDPMLoss, lr: float = 1e-4):
        self.model = model
        self.loss_fn = loss_fn
        self.lr = lr
        
        # 模拟优化器状态
        self.step_count = 0
    
    def train_step(self, x_0: np.ndarray, 
                   schedule: 'DiffusionSchedule') -> dict:
        """
        单步训练
        
        参数:
            x_0: 原始图像 (B, C, H, W)
            schedule: 扩散调度
            
        返回:
            损失字典
        """
        batch_size = len(x_0)
        T = self.loss_fn.T
        
        # 采样时间步
        t = np.random.randint(0, T, size=batch_size)
        
        # 采样噪声
        epsilon = np.random.randn(*x_0.shape)
        
        # 计算x_t
        alpha_bar_t = schedule.alpha_bars[t].reshape(batch_size, 1, 1, 1)
        x_t = np.sqrt(alpha_bar_t) * x_0 + np.sqrt(1 - alpha_bar_t) * epsilon
        
        # 预测噪声
        epsilon_theta = self.model.predict_noise(x_t, t)
        
        # 计算损失
        loss = self.loss_fn.simplified_loss(epsilon_theta, epsilon, x_t, t)
        
        # 模拟梯度更新
        self.step_count += 1
        
        return {
            'loss': loss,
            't_mean': np.mean(t)
        }
    
    def compute_loss_landscape(self, x_0: np.ndarray, 
                               schedule: 'DiffusionSchedule',
                               t_values: np.ndarray) -> np.ndarray:
        """
        计算损失景观（用于可视化）
        
        参数:
            x_0: 原始图像
            schedule: 扩散调度
            t_values: 要评估的时间步
            
        返回:
            各时间步的损失数组
        """
        losses = np.zeros(len(t_values))
        
        for i, t in enumerate(t_values):
            t_batch = np.array([t] * len(x_0))
            epsilon = np.random.randn(*x_0.shape)
            
            alpha_bar_t = schedule.alpha_bars[t]
            x_t = np.sqrt(alpha_bar_t) * x_0 + np.sqrt(1 - alpha_bar_t) * epsilon
            
            epsilon_theta = self.model.predict_noise(x_t, t)
            
            losses[i] = self.loss_fn.simplified_loss(epsilon_theta, epsilon, x_t, t_batch)
        
        return losses


class ImprovedDDPMLoss:
    """
    改进DDPM损失（Improved DDPM论文）
    
    关键改进：
    1. 协变量位移加权
    2. 梯度截断/正则化
    """
    
    def __init__(self, T: int = 1000):
        self.T = T
        self._compute_schedule()
    
    def _compute_schedule(self):
        """计算调度"""
        self.betas = np.linspace(1e-4, 0.02, self.T)
        self.alphas = 1 - self.betas
        self.alphas_bar = np.cumprod(self.alphas)
    
    def c_skip(self, t: np.ndarray) -> np.ndarray:
        """
        计算跳连接系数
        
        c_skip(t) = sigma^2_q(x_0|x_t) / sigma^2_q(x_t|x_0)
        """
        return self.alphas_bar[t]
    
    def c_out(self, t: np.ndarray) -> np.ndarray:
        """
        计算输出系数
        
        c_out(t) = sigma_q(x_t|x_0) * c_skip(t)
        """
        return np.sqrt(1 - self.alphas_bar[t]) * self.alphas_bar[t]
    
    def c_in(self, t: np.ndarray) -> np.ndarray:
        """
        计算输入系数
        
        c_in(t) = 1 - c_skip(t) = 1 - alpha_bar_t
        """
        return 1 - self.alphas_bar[t]
    
    def c_noise(self, t: np.ndarray) -> np.ndarray:
        """噪声编码系数"""
        return np.log(t + 1) / np.log(self.T)


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("DDPM损失函数测试")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 测试1：基础损失计算
    print("\n1. 简化MSE损失:")
    
    loss_fn = DDPMLoss(T=1000, loss_type='mse')
    
    # 模拟数据
    epsilon_theta = np.random.randn(4, 3, 32, 32) * 0.5
    epsilon = np.random.randn(4, 3, 32, 32) * 0.5
    x_t = np.random.randn(4, 3, 32, 32)
    t = np.array([100, 300, 500, 800])
    
    loss = loss_fn.simplified_loss(epsilon_theta, epsilon, x_t, t)
    print(f"   MSE损失: {loss:.6f}")
    
    # 测试2：加权损失
    print("\n2. 不同加权策略:")
    
    for weighting in ['uniform', 'snr', 'inv_snr', 'uniform_v2']:
        loss_w = loss_fn.weighted_loss(epsilon_theta, epsilon, t, weighting)
        print(f"   {weighting}: {loss_w:.6f}")
    
    # 测试3：VLB损失
    print("\n3. 变分下界损失:")
    
    x_0 = np.random.randn(4, 3, 32, 32)
    vlb_loss = loss_fn.vlb_loss(x_0, epsilon, t, epsilon_theta)
    print(f"   VLB损失: {vlb_loss:.6f}")
    
    # 测试4：混合损失
    print("\n4. 混合损失 (MSE + VLB):")
    
    loss_fn_hybrid = DDPMLoss(T=1000, loss_type='hybrid', lambda_vlb=0.001)
    
    total_loss, loss_dict = loss_fn_hybrid.hybrid_loss(x_0, epsilon, t, epsilon_theta)
    print(f"   总损失: {loss_dict['total']:.6f}")
    print(f"   MSE部分: {loss_dict['mse']:.6f}")
    print(f"   VLB部分: {loss_dict['vlb']:.6f}")
    
    # 测试5：训练器
    print("\n5. DDPM训练器:")
    
    class MockModel:
        def predict_noise(self, x_t, t):
            return np.random.randn(*x_t.shape) * 0.3
    
    model = MockModel()
    trainer = Trainer(model, loss_fn, lr=1e-4)
    
    x_0_batch = np.random.randn(8, 3, 32, 32)
    
    class MockSchedule:
        def __init__(self):
            self.alpha_bars = np.cumprod(np.linspace(0.9999, 0.98, 1000))
    
    schedule = MockSchedule()
    
    for i in range(3):
        result = trainer.train_step(x_0_batch, schedule)
        print(f"   Step {i+1}: loss={result['loss']:.6f}")
    
    # 测试6：改进DDPM损失系数
    print("\n6. 改进DDPM损失系数:")
    
    improved_loss = ImprovedDDPMLoss(T=1000)
    
    t_test = np.array([0, 100, 500, 999])
    
    print("   t\t\tc_skip\t\tc_out\t\tc_in")
    for t in t_test:
        c_skip = improved_loss.c_skip(np.array([t]))[0]
        c_out = improved_loss.c_out(np.array([t]))[0]
        c_in = improved_loss.c_in(np.array([t]))[0]
        print(f"   {t}\t\t{c_skip:.4f}\t\t{c_out:.4f}\t\t{c_in:.4f}")
    
    # 测试7：损失景观
    print("\n7. 损失景观分析:")
    
    t_values = np.array([10, 50, 100, 200, 500, 800, 990])
    losses = trainer.compute_loss_landscape(x_0_batch, schedule, t_values)
    
    for t, l in zip(t_values, losses):
        print(f"   t={t}: 损失={l:.6f}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


class Trainer(DDPMLoss):
    """简化的训练器类（用于测试）"""
    
    def __init__(self, model, loss_fn, lr):
        self.model = model
        self.loss_fn = loss_fn
        self.lr = lr
        self.step_count = 0
