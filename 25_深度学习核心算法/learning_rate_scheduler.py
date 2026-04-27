# -*- coding: utf-8 -*-
"""
算法实现：25_深度学习核心算法 / learning_rate_scheduler

本文件实现 learning_rate_scheduler 相关的算法功能。
"""

import numpy as np


class StepLR:
    """
    阶梯式学习率衰减
    
    参数:
        optimizer: 优化器
        step_size: 衰减周期（多少个epoch后衰减）
        gamma: 衰减倍率（默认0.1，即每次衰减为原来的1/10）
    """
    
    def __init__(self, optimizer, step_size, gamma=0.1):
        self.optimizer = optimizer
        self.step_size = step_size
        self.gamma = gamma
        self.current_step = 0
    
    def step(self):
        """执行一次调度（通常每个epoch调用一次）"""
        self.current_step += 1
        if self.current_step % self.step_size == 0:
            # 降低学习率
            self.optimizer.lr *= self.gamma
            return True  # 表示发生了衰减
        return False
    
    def get_lr(self):
        """获取当前学习率"""
        return self.optimizer.lr


class CosineAnnealingLR:
    """
    余弦退火学习率调度
    
    参数:
        optimizer: 优化器
        T_max: 最大迭代次数（一个完整周期的迭代数）
        eta_min: 最小学习率（默认0）
        warmup_epochs: 预热epoch数（可选）
    """
    
    def __init__(self, optimizer, T_max, eta_min=0.0, warmup_epochs=0):
        self.optimizer = optimizer
        self.T_max = T_max
        self.eta_min = eta_min
        self.warmup_epochs = warmup_epochs
        self.current_epoch = 0
        self.base_lr = optimizer.lr
    
    def step(self):
        """执行一次调度"""
        self.current_epoch += 1
        
        if self.current_epoch <= self.warmup_epochs:
            # Warmup阶段：线性增加学习率
            self.optimizer.lr = self.base_lr * self.current_epoch / self.warmup_epochs
        else:
            # 余弦退火阶段
            progress = (self.current_epoch - self.warmup_epochs) / (self.T_max - self.warmup_epochs)
            progress = min(progress, 1.0)
            
            # 余弦退火公式
            self.optimizer.lr = self.eta_min + (self.base_lr - self.eta_min) * \
                                (1 + np.cos(np.pi * progress)) / 2
    
    def get_lr(self):
        return self.optimizer.lr


class WarmupScheduler:
    """
    学习率预热调度器
    
    参数:
        optimizer: 优化器
        warmup_epochs: 预热epoch数
        target_lr: 预热的目标学习率
    """
    
    def __init__(self, optimizer, warmup_epochs, target_lr=None):
        self.optimizer = optimizer
        self.warmup_epochs = warmup_epochs
        self.target_lr = target_lr if target_lr else optimizer.lr
        self.base_lr = optimizer.lr
        self.current_epoch = 0
    
    def step(self):
        """执行一次调度"""
        self.current_epoch += 1
        
        if self.current_epoch <= self.warmup_epochs:
            # 线性预热
            self.optimizer.lr = self.base_lr * self.current_epoch / self.warmup_epochs
        else:
            # 预热结束后不再调整
            self.optimizer.lr = self.target_lr
    
    def get_lr(self):
        return self.optimizer.lr


class ExponentialLR:
    """
    指数学习率衰减
    
    参数:
        optimizer: 优化器
        gamma: 衰减系数（每个epoch乘以gamma）
    """
    
    def __init__(self, optimizer, gamma=0.95):
        self.optimizer = optimizer
        self.gamma = gamma
        self.current_epoch = 0
    
    def step(self):
        self.current_epoch += 1
        self.optimizer.lr *= self.gamma
    
    def get_lr(self):
        return self.optimizer.lr


class PolynomialLR:
    """
    多项式学习率衰减
    
    参数:
        optimizer: 优化器
        max_epochs: 总epoch数
        power: 多项式幂次（1为线性，2为二次）
    """
    
    def __init__(self, optimizer, max_epochs, power=1.0):
        self.optimizer = optimizer
        self.max_epochs = max_epochs
        self.power = power
        self.current_epoch = 0
        self.base_lr = optimizer.lr
    
    def step(self):
        self.current_epoch += 1
        progress = self.current_epoch / self.max_epochs
        progress = min(progress, 1.0)
        
        # 多项式衰减
        self.optimizer.lr = self.base_lr * (1 - progress) ** self.power
    
    def get_lr(self):
        return self.optimizer.lr


class CombinedScheduler:
    """
    组合调度器：先warmup，再执行主调度器
    
    参数:
        warmup_epochs: 预热epoch数
        main_scheduler: 主调度器
    """
    
    def __init__(self, warmup_epochs, main_scheduler):
        self.warmup_epochs = warmup_epochs
        self.main_scheduler = main_scheduler
        self.current_epoch = 0
    
    def step(self):
        self.current_epoch += 1
        
        if self.current_epoch <= self.warmup_epochs:
            # Warmup阶段
            self.main_scheduler.optimizer.lr *= 1.1  # 简化的warmup
        else:
            # 调用主调度器
            self.main_scheduler.current_epoch = self.current_epoch - self.warmup_epochs
            self.main_scheduler.step()
    
    def get_lr(self):
        return self.main_scheduler.optimizer.lr


# ============================
# 模拟优化器（用于测试）
# ============================

class MockOptimizer:
    """模拟优化器（仅用于学习率调度测试）"""
    def __init__(self, lr=0.1):
        self.lr = lr


# ============================
# 测试代码
# ============================

if __name__ == "__main__":
    print("=" * 55)
    print("学习率调度器测试")
    print("=" * 55)
    
    # 测试1：StepLR
    print("\n--- StepLR（每3个epoch衰减一半）---")
    opt = MockOptimizer(lr=0.1)
    scheduler = StepLR(opt, step_size=3, gamma=0.5)
    
    lr_history = [opt.lr]
    for epoch in range(1, 16):
        scheduler.step()
        lr_history.append(opt.lr)
        if scheduler.current_step % scheduler.step_size == 0:
            print(f"  Epoch {epoch}: 学习率 = {opt.lr:.6f}")
    
    # 测试2：CosineAnnealingLR
    print("\n--- CosineAnnealingLR（20 epochs，余弦退火）---")
    opt2 = MockOptimizer(lr=0.1)
    scheduler2 = CosineAnnealingLR(opt2, T_max=20, eta_min=0.001)
    
    for epoch in range(1, 21):
        scheduler2.step()
        if epoch <= 5 or epoch == 20:
            print(f"  Epoch {epoch:2d}: 学习率 = {opt2.lr:.6f}")
    
    # 测试3：CosineAnnealingLR with Warmup
    print("\n--- CosineAnnealing + Warmup（5 epoch预热）---")
    opt3 = MockOptimizer(lr=0.1)
    scheduler3 = CosineAnnealingLR(opt3, T_max=20, eta_min=0.001, warmup_epochs=5)
    
    for epoch in range(1, 21):
        scheduler3.step()
        if epoch <= 7 or epoch == 20:
            print(f"  Epoch {epoch:2d}: 学习率 = {opt3.lr:.6f}")
    
    # 测试4：对比不同调度器
    print("\n--- 不同调度器学习率曲线对比 ---")
    print(f"{'Epoch':>5} | {'Step(γ=0.5)':>12} | {'Cosine':>10} | {'Exp(γ=0.9)':>10} | {'Poly(p=2)':>10}")
    print("-" * 60)
    
    opt_s = MockOptimizer(lr=0.1)
    opt_c = MockOptimizer(lr=0.1)
    opt_e = MockOptimizer(lr=0.1)
    opt_p = MockOptimizer(lr=0.1)
    
    sched_s = StepLR(opt_s, step_size=5, gamma=0.5)
    sched_c = CosineAnnealingLR(opt_c, T_max=30, eta_min=0.0001)
    sched_e = ExponentialLR(opt_e, gamma=0.9)
    sched_p = PolynomialLR(opt_p, max_epochs=30, power=2.0)
    
    for epoch in range(1, 31):
        sched_s.step()
        sched_c.step()
        sched_e.step()
        sched_p.step()
        
        if epoch in [1, 5, 10, 15, 20, 25, 30]:
            print(f"{epoch:5d} | {opt_s.lr:12.6f} | {opt_c.lr:10.6f} | {opt_e.lr:10.6f} | {opt_p.lr:10.6f}")
    
    # 测试5：WarmupScheduler
    print("\n--- WarmupScheduler（10 epoch预热）---")
    opt_w = MockOptimizer(lr=0.01)
    scheduler_w = WarmupScheduler(opt_w, warmup_epochs=10, target_lr=0.1)
    
    for epoch in range(1, 16):
        scheduler_w.step()
        if epoch <= 12:
            print(f"  Epoch {epoch:2d}: 学习率 = {opt_w.lr:.6f}")
    
    print("\n学习率调度器测试完成！")
