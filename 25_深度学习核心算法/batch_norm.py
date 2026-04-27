# -*- coding: utf-8 -*-
"""
算法实现：25_深度学习核心算法 / batch_norm

本文件实现 batch_norm 相关的算法功能。
"""

import numpy as np


def batch_norm_forward(x, gamma, beta, eps=1e-8):
    """
    BatchNorm前馈传播
    
    参数:
        x: 输入 (batch_size, num_features)
        gamma: 缩放参数 (num_features,)
        beta: 平移参数 (num_features,)
        eps: 防止除零的小常数
    返回:
        out: 归一化输出
        cache: 反向传播需要的中间变量
    """
    batch_size, num_features = x.shape
    
    # 计算batch统计量
    mu = np.mean(x, axis=0)  # (num_features,) 均值
    var = np.var(x, axis=0)  # (num_features,) 方差
    
    # 标准化
    x_centered = x - mu
    x_normalized = x_centered / np.sqrt(var + eps)
    
    # 缩放和平移
    out = gamma * x_normalized + beta
    
    # 保存反向传播需要的中间变量
    cache = {
        'x': x,
        'x_centered': x_centered,
        'x_normalized': x_normalized,
        'mu': mu,
        'var': var,
        'gamma': gamma,
        'eps': eps,
        'batch_size': batch_size
    }
    
    return out, cache


def batch_norm_backward(dout, cache):
    """
    BatchNorm反向传播
    
    目标：计算损失L对以下参数的梯度：
    - d_beta: 损失对平移参数的梯度
    - d_gamma: 损失对缩放参数的梯度
    - d_x: 损失对输入x的梯度
    
    参数:
        dout: 损失对输出的梯度 (batch_size, num_features)
        cache: 前馈传播保存的中间变量
    返回:
        dx: 损失对输入的梯度
        dgamma: 损失对gamma的梯度
        dbeta: 损失对beta的梯度
    """
    x = cache['x']
    x_centered = cache['x_centered']
    x_normalized = cache['x_normalized']
    mu = cache['mu']
    var = cache['var']
    gamma = cache['gamma']
    eps = cache['eps']
    batch_size = cache['batch_size']
    
    # 对标准化后的值求导
    # out = gamma * x_normalized + beta
    d_standardized = dout * gamma  # (batch_size, num_features)
    
    # 对归一化过程求导
    # x_normalized = x_centered / sqrt(var + eps)
    d_x_centered = d_standardized / np.sqrt(var + eps)
    
    # 对方差求导
    # var = (1/N) * sum(x_centered^2)
    d_var = np.sum(d_standardized * x_centered * (-0.5) * (var + eps) ** (-1.5), axis=0)
    
    # 对均值求导
    # mu = (1/N) * sum(x - mu) = (1/N) * sum(x_centered)
    d_mu = -np.sum(d_x_centered, axis=0) - 2 / batch_size * np.sum(x_centered, axis=0) * d_var
    
    # 对输入x的梯度
    dx = d_x_centered + d_mu / batch_size + 2 * d_var * x_centered / batch_size
    
    # 对gamma和beta的梯度
    dgamma = np.sum(dout * x_normalized, axis=0)
    dbeta = np.sum(dout, axis=0)
    
    return dx, dgamma, dbeta


class BatchNorm1d:
    """
    1维BatchNorm层（全连接层后使用）
    
    参数:
        num_features: 特征维度（等于上一层输出维度）
        momentum: 移动平均动量（用于推理时统计量）
        eps: 防止除零
    """
    
    def __init__(self, num_features, momentum=0.9, eps=1e-8):
        self.num_features = num_features
        self.momentum = momentum
        self.eps = eps
        
        # 可学习参数：缩放gamma和平移beta
        self.gamma = np.ones(num_features)
        self.beta = np.zeros(num_features)
        
        # 推理时的移动平均统计量
        self.running_mean = np.zeros(num_features)
        self.running_var = np.ones(num_features)
        
        self.training = True
    
    def forward(self, x):
        """
        前馈传播
        
        参数:
            x: 输入 (batch_size, num_features)
        返回:
            out: 输出
        """
        if self.training:
            # 训练模式：使用batch统计量
            mu = np.mean(x, axis=0)
            var = np.var(x, axis=0)
            
            # 更新移动平均（用于推理）
            self.running_mean = self.momentum * self.running_mean + (1 - self.momentum) * mu
            self.running_var = self.momentum * self.running_var + (1 - self.momentum) * var * (x.shape[0] / (x.shape[0] - 1))
            
            # 标准化
            x_centered = x - mu
            x_normalized = x_centered / np.sqrt(var + self.eps)
            
            # 缩放平移
            out = self.gamma * x_normalized + self.beta
            
            # 保存中间变量
            self.cache = {
                'x': x,
                'x_centered': x_centered,
                'x_normalized': x_normalized,
                'mu': mu,
                'var': var
            }
        else:
            # 推理模式：使用移动平均统计量
            x_centered = x - self.running_mean
            x_normalized = x_centered / np.sqrt(self.running_var + self.eps)
            out = self.gamma * x_normalized + self.beta
            self.cache = None
        
        return out
    
    def backward(self, dout):
        """
        反向传播
        
        参数:
            dout: 损失对输出的梯度
        返回:
            dx: 损失对输入的梯度
        """
        if self.cache is None:
            raise RuntimeError("需要先执行前馈传播才能反向传播")
        
        cache = self.cache
        x = cache['x']
        x_centered = cache['x_centered']
        x_normalized = cache['x_normalized']
        mu = cache['mu']
        var = cache['var']
        batch_size = x.shape[0]
        
        # 计算d_standardized = dout * gamma
        d_standardized = dout * self.gamma
        
        # 对标准化求导
        d_x_centered = d_standardized / np.sqrt(var + self.eps)
        
        # 对方差求导
        d_var = np.sum(d_standardized * x_centered * (-0.5) * (var + self.eps) ** (-1.5), axis=0)
        
        # 对均值求导
        d_mu = -np.sum(d_x_centered, axis=0) - 2 / batch_size * np.sum(x_centered, axis=0) * d_var
        
        # 对输入x的梯度
        dx = d_x_centered + d_mu / batch_size + 2 * d_var * x_centered / batch_size
        
        # 对gamma和beta的梯度
        self.d_gamma = np.sum(dout * x_normalized, axis=0)
        self.d_beta = np.sum(dout, axis=0)
        
        return dx
    
    def update_params(self, lr=0.01):
        """更新参数（简化版）"""
        self.gamma -= lr * self.d_gamma
        self.beta -= lr * self.d_beta
    
    def eval(self):
        """切换到推理模式"""
        self.training = False
    
    def train(self):
        """切换到训练模式"""
        self.training = True


# ============================
# 测试代码
# ============================

if __name__ == "__main__":
    np.random.seed(42)
    
    print("=" * 55)
    print("BatchNorm测试")
    print("=" * 55)
    
    # 测试1：前馈传播
    print("\n--- 前馈传播测试 ---")
    batch_size = 32
    num_features = 64
    
    x = np.random.randn(batch_size, num_features) * 2 + 1  # 非标准正态分布
    
    gamma = np.ones(num_features)
    beta = np.zeros(num_features)
    
    out, cache = batch_norm_forward(x, gamma, beta)
    
    print(f"输入均值: {x.mean(axis=0).mean():.4f}, 方差: {x.var(axis=0).mean():.4f}")
    print(f"输出均值: {out.mean(axis=0).mean():.4f}, 方差: {out.var(axis=0).mean():.4f}")
    print(f"输出范围: [{out.min():.4f}, {out.max():.4f}]")
    
    # 测试2：反向传播
    print("\n--- 反向传播测试 ---")
    dout = np.random.randn(batch_size, num_features)
    
    dx, dgamma, dbeta = batch_norm_backward(dout, cache)
    
    print(f"输入梯度形状: {dx.shape}")
    print(f"gamma梯度范围: [{dgamma.min():.4f}, {dgamma.max():.4f}]")
    print(f"beta梯度范围: [{dbeta.min():.4f}, {dbeta.max():.4f}]")
    
    # 梯度检验：使用数值梯度验证
    print("\n--- 梯度检验（数值梯度对比）---")
    h = 1e-5
    x_test = np.random.randn(batch_size, num_features) * 2
    gamma_test = np.ones(num_features)
    beta_test = np.zeros(num_features)
    
    out_test, cache_test = batch_norm_forward(x_test, gamma_test, beta_test)
    dout_test = np.ones((batch_size, num_features))
    
    dx_analytic, dgamma_analytic, dbeta_analytic = batch_norm_backward(dout_test, cache_test)
    
    # 对gamma计算数值梯度
    dgamma_numeric = np.zeros_like(dgamma_analytic)
    for i in range(num_features):
        gamma_plus = gamma_test.copy()
        gamma_plus[i] += h
        out_plus, _ = batch_norm_forward(x_test, gamma_plus, beta_test)
        dgamma_numeric[i] = np.sum(out_plus - out_test) / h
    
    print(f"gamma梯度误差: {np.abs(dgamma_analytic - dgamma_numeric).max():.8f}")
    
    # 测试3：BatchNorm1d层
    print("\n--- BatchNorm1d层测试 ---")
    bn = BatchNorm1d(num_features=64, momentum=0.9)
    
    # 训练模式
    x_train = np.random.randn(64, 64)
    out_train = bn.forward(x_train)
    print(f"训练模式输出均值: {out_train.mean(axis=0).mean():.6f}")
    print(f"训练模式输出方差: {out_train.var(axis=0).mean():.4f}")
    
    # 反向传播
    dout_train = np.random.randn(64, 64)
    dx_train = bn.backward(dout_train)
    print(f"反向传播输入梯度形状: {dx_train.shape}")
    
    # 推理模式
    bn.eval()
    x_test = np.random.randn(32, 64)
    out_test = bn.forward(x_test)
    print(f"推理模式输出均值: {out_test.mean(axis=0).mean():.6f}")
    print(f"推理模式输出方差: {out_test.var(axis=0).mean():.4f}")
    
    # 测试4：训练 vs 推理差异
    print("\n--- 训练 vs 推理模式对比 ---")
    bn2 = BatchNorm1d(num_features=32, momentum=0.9)
    
    print(f"初始running_mean: {bn2.running_mean.mean():.6f}")
    print(f"初始running_var: {bn2.running_var.mean():.6f}")
    
    # 多次前馈更新running统计量
    for i in range(5):
        x_batch = np.random.randn(16, 32) * (i + 1)
        out_batch = bn2.forward(x_batch)
    
    print(f"5个batch后running_mean: {bn2.running_mean.mean():.6f}")
    print(f"5个batch后running_var: {bn2.running_var.mean():.4f}")
    
    print("\nBatchNorm测试完成！")
