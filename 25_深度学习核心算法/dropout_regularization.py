# -*- coding: utf-8 -*-
"""
算法实现：25_深度学习核心算法 / dropout_regularization

本文件实现 dropout_regularization 相关的算法功能。
"""

import numpy as np


# ============================
# Dropout
# ============================

def dropout_forward(x, dropout_rate, training=True):
    """
    Dropout前馈传播
    
    参数:
        x: 输入
        dropout_rate: 丢弃概率（0-1之间）
        training: 是否在训练模式（True时应用dropout）
    返回:
        out: 输出
        mask: 丢弃掩码（训练时需要保存用于反向传播）
    """
    if training:
        # 训练时：随机丢弃部分神经元
        # mask中True表示保留，False表示丢弃
        mask = np.random.rand(*x.shape) > dropout_rate
        out = x * mask
        # Inverted Dropout：缩放保留的神经元以保持期望和不变
        out = out / (1 - dropout_rate)
    else:
        # 推理时：保留所有神经元（不做dropout）
        mask = None
        out = x
    
    return out, mask


def dropout_backward(dout, mask, dropout_rate):
    """
    Dropout反向传播
    
    参数:
        dout: 损失对输出的梯度
        mask: 前馈时生成的掩码
        dropout_rate: 丢弃概率
    返回:
        dx: 损失对输入的梯度
    """
    # 反向传播时，只有mask中为True的位置有梯度
    dx = dout * mask
    # Inverted Dropout的梯度也需要缩放
    dx = dx / (1 - dropout_rate)
    return dx


class Dropout:
    """
    Dropout层
    
    参数:
        dropout_rate: 丢弃概率（默认0.5）
    """
    
    def __init__(self, dropout_rate=0.5):
        self.dropout_rate = dropout_rate
        self.mask = None
        self.training = True
    
    def forward(self, x):
        """前馈传播"""
        if self.training:
            self.mask = np.random.rand(*x.shape) > self.dropout_rate
            out = x * self.mask
            out = out / (1 - self.dropout_rate)  # Inverted Dropout
        else:
            self.mask = None
            out = x
        return out
    
    def backward(self, dout):
        """反向传播"""
        if self.mask is None:
            raise RuntimeError("需要先执行前馈传播")
        dx = dout * self.mask
        dx = dx / (1 - self.dropout_rate)
        return dx
    
    def eval(self):
        """切换到推理模式"""
        self.training = False
    
    def train(self):
        """切换到训练模式"""
        self.training = True


# ============================
# L1/L2正则化
# ============================

def l1_regularization(weights, lambda_reg):
    """
    L1正则化：lambda * sum(|w|)
    会产生稀疏权重（很多w变成0）
    
    参数:
        weights: 权重矩阵
        lambda_reg: 正则化系数
    返回:
        reg_loss: 正则化损失
        reg_grad: 正则化对权重的梯度
    """
    reg_loss = lambda_reg * np.sum(np.abs(weights))
    reg_grad = lambda_reg * np.sign(weights)
    return reg_loss, reg_grad


def l2_regularization(weights, lambda_reg):
    """
    L2正则化：lambda * sum(w^2) / 2
    会让权重趋向于小值，但不会变成0
    
    参数:
        weights: 权重矩阵
        lambda_reg: 正则化系数
    返回:
        reg_loss: 正则化损失
        reg_grad: 正则化对权重的梯度
    """
    reg_loss = lambda_reg * np.sum(weights ** 2) / 2
    reg_grad = lambda_reg * weights
    return reg_loss, reg_grad


def elastic_net_regularization(weights, lambda_l1=0.01, lambda_l2=0.01):
    """
    Elastic Net：结合L1和L2正则化
    loss = lambda_l1 * |w| + lambda_l2 * w^2 / 2
    """
    l1_loss, l1_grad = l1_regularization(weights, lambda_l1)
    l2_loss, l2_grad = l2_regularization(weights, lambda_l2)
    return l1_loss + l2_loss, l1_grad + l2_grad


class RegularizedOptimizer:
    """
    带正则化的优化器（演示如何在训练中加入正则化）
    
    参数:
        optimizer: 基础优化器
        lambda_l1: L1正则化系数
        lambda_l2: L2正则化系数
    """
    
    def __init__(self, optimizer, lambda_l1=0.0, lambda_l2=0.0):
        self.optimizer = optimizer
        self.lambda_l1 = lambda_l1
        self.lambda_l2 = lambda_l2
    
    def step_with_reg(self, weights):
        """
        带正则化的参数更新
        
        参数:
            weights: 权重（需要包含grad属性）
        """
        # 计算正则化梯度
        if self.lambda_l2 > 0:
            reg_grad = self.lambda_l2 * weights.data
            weights.grad = weights.grad + reg_grad
        
        if self.lambda_l1 > 0:
            reg_grad = self.lambda_l1 * np.sign(weights.data)
            weights.grad = weights.grad + reg_grad
        
        # 调用优化器更新
        self.optimizer.step()


# ============================
# 测试代码
# ============================

if __name__ == "__main__":
    np.random.seed(42)
    
    print("=" * 55)
    print("Dropout和正则化测试")
    print("=" * 55)
    
    # 测试1：Dropout前馈
    print("\n--- Dropout前馈传播 ---")
    x = np.ones((8, 10))  # 全1输入
    dropout_rate = 0.3
    
    print(f"输入（全部为1）: {x.shape}")
    print(f"丢弃率: {dropout_rate}")
    
    # 训练模式
    out_train, mask = dropout_forward(x, dropout_rate, training=True)
    print(f"\n训练模式:")
    print(f"  保留比例: {np.mean(mask):.2%}")
    print(f"  输出均值: {out_train.mean():.4f}")
    print(f"  输出方差: {out_train.var():.4f}")
    
    # 推理模式
    out_eval, _ = dropout_forward(x, dropout_rate, training=False)
    print(f"\n推理模式:")
    print(f"  输出均值: {out_eval.mean():.4f}")
    print(f"  输出: {out_eval[0]}")
    
    # 测试2：Dropout反向传播
    print("\n--- Dropout反向传播 ---")
    dout = np.ones_like(out_train)
    dx = dropout_backward(dout, mask, dropout_rate)
    print(f"输入梯度形状: {dx.shape}")
    print(f"梯度中非零比例: {np.mean(dx != 0):.2%}")
    
    # 测试3：L1 vs L2正则化
    print("\n--- L1 vs L2正则化对比 ---")
    weights = np.array([2.0, -1.0, 0.5, -0.3, 0.0])
    lambda_reg = 0.1
    
    l1_loss, l1_grad = l1_regularization(weights, lambda_reg)
    l2_loss, l2_grad = l2_regularization(weights, lambda_reg)
    
    print(f"权重: {weights}")
    print(f"\nL1正则化 (λ={lambda_reg}):")
    print(f"  损失: {l1_loss:.4f}")
    print(f"  梯度: {l1_grad}")
    
    print(f"\nL2正则化 (λ={lambda_reg}):")
    print(f"  损失: {l2_loss:.4f}")
    print(f"  梯度: {l2_grad}")
    
    # 测试4：正则化对权重的影响
    print("\n--- 正则化权重衰减效果 ---")
    print(f"{'λ':>6} | {'L1损失':>10} | {'L2损失':>10} | {'L1梯度和':>10} | {'L2梯度和':>10}")
    print("-" * 60)
    
    for lam in [0.001, 0.01, 0.1, 0.5, 1.0]:
        w = np.random.randn(100) * 2
        l1_loss, l1_grad = l1_regularization(w, lam)
        l2_loss, l2_grad = l2_regularization(w, lam)
        print(f"{lam:6.3f} | {l1_loss:10.4f} | {l2_loss:10.4f} | {np.sum(np.abs(l1_grad)):10.4f} | {np.sum(np.abs(l2_grad)):10.4f}")
    
    # 测试5：Dropout层
    print("\n--- Dropout层测试 ---")
    dropout = Dropout(dropout_rate=0.5)
    
    # 训练模式
    x_train = np.random.randn(64, 128)
    out_train = dropout.forward(x_train)
    print(f"训练模式输出方差: {out_train.var():.4f} (输入方差: {x_train.var():.4f})")
    
    # 反向传播
    dout = np.random.randn(64, 128)
    dx = dropout.backward(dout)
    print(f"反向传播完成，梯度形状: {dx.shape}")
    
    # 推理模式
    dropout.eval()
    out_eval = dropout.forward(x_train)
    print(f"推理模式输出方差: {out_eval.var():.4f}")
    
    # 测试6：Elastic Net
    print("\n--- Elastic Net正则化 ---")
    weights = np.array([1.0, -0.5, 0.3, -0.1, 0.05])
    en_loss, en_grad = elastic_net_regularization(weights, lambda_l1=0.1, lambda_l2=0.1)
    
    l1_loss, l1_grad = l1_regularization(weights, 0.1)
    l2_loss, l2_grad = l2_regularization(weights, 0.1)
    
    print(f"权重: {weights}")
    print(f"Elastic Net损失: {en_loss:.4f} (L1+L2 = {l1_loss + l2_loss:.4f})")
    print(f"Elastic Net梯度: {en_grad.round(4)}")
    
    print("\nDropout和正则化测试完成！")
