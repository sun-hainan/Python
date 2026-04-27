# -*- coding: utf-8 -*-
"""
算法实现：25_深度学习核心算法 / gradient_clipping

本文件实现 gradient_clipping 相关的算法功能。
"""

import numpy as np


def clip_grad_by_norm(grad, max_norm):
    """
    按全局L2范数裁剪梯度
    clip_norm = max_norm / (||grad|| + eps)
    若 clip_norm < 1，则 grad *= clip_norm
    
    参数:
        grad: 梯度向量或矩阵（numpy数组）
        max_norm: 最大允许的L2范数值
    返回:
        clipped_grad: 裁剪后的梯度
        total_norm: 裁剪前的全局范数
    """
    eps = 1e-8
    total_norm = np.linalg.norm(grad)
    clip_coef = max_norm / (total_norm + eps)
    
    # 如果范数超过阈值，按比例缩放
    if clip_coef < 1:
        return grad * clip_coef, total_norm
    return grad, total_norm


def clip_grad_by_value(grad, clip_value):
    """
    按值裁剪：将梯度限制在[-clip_value, clip_value]范围内
    
    参数:
        grad: 梯度数组
        clip_value: 裁剪阈值
    返回:
        clipped_grad: 裁剪后的梯度
    """
    return np.clip(grad, -clip_value, clip_value)


class GradientClipper:
    """
    梯度裁剪封装类
    
    参数:
        clip_type: 裁剪方式 ('norm' 或 'value')
        clip_value: 裁剪阈值
    """
    
    def __init__(self, clip_type='norm', clip_value=1.0):
        self.clip_type = clip_type
        self.clip_value = clip_value
        self.history = []  # 记录历史梯度范数
    
    def clip(self, grad):
        """执行梯度裁剪"""
        if self.clip_type == 'norm':
            clipped, norm = clip_grad_by_norm(grad, self.clip_value)
            self.history.append(norm)
            return clipped
        elif self.clip_type == 'value':
            return clip_grad_by_value(grad, self.clip_value)
        else:
            raise ValueError(f"Unknown clip_type: {self.clip_type}")
    
    def detect_issue(self, grad):
        """
        检测梯度是否存在问题
        
        返回:
            issue: 'exploding', 'vanishing', 或 'normal'
            ratio: 问题严重程度（相对于阈值）
        """
        norm = np.linalg.norm(grad)
        
        if norm > 10 * self.clip_value:
            return 'exploding', norm / self.clip_value
        elif norm < 1e-7:
            return 'vanishing', 1e-7 / (norm + 1e-10)
        return 'normal', 1.0


# ============================
# 测试代码
# ============================

if __name__ == "__main__":
    np.random.seed(42)
    
    print("=" * 55)
    print("梯度裁剪测试")
    print("=" * 55)
    
    # 测试1：模拟梯度爆炸
    print("\n--- 模拟梯度爆炸场景 ---")
    exploding_grad = np.random.randn(1000) * 10  # 大范数梯度
    original_norm = np.linalg.norm(exploding_grad)
    print(f"原始梯度范数: {original_norm:.2f}")
    
    clipper = GradientClipper(clip_type='norm', clip_value=1.0)
    clipped_grad = clipper.clip(exploding_grad)
    clipped_norm = np.linalg.norm(clipped_grad)
    
    print(f"裁剪后梯度范数: {clipped_norm:.2f}")
    print(f"裁剪比例: {clipped_norm / original_norm:.4f}")
    
    issue, ratio = clipper.detect_issue(exploding_grad)
    print(f"检测结果: {issue}, ratio={ratio:.2f}")
    
    # 测试2：模拟梯度消失
    print("\n--- 模拟梯度消失场景 ---")
    vanishing_grad = np.random.randn(1000) * 1e-8
    original_norm = np.linalg.norm(vanishing_grad)
    print(f"原始梯度范数: {original_norm:.10f}")
    
    clipper2 = GradientClipper(clip_type='norm', clip_value=1.0)
    issue, ratio = clipper2.detect_issue(vanishing_grad)
    print(f"检测结果: {issue}, ratio={ratio:.2f}")
    
    # 测试3：值裁剪
    print("\n--- 值裁剪测试 ---")
    grad = np.array([0.5, 1.5, 2.5, 3.5, 4.5])
    clipped = clip_grad_by_value(grad, 2.0)
    print(f"原始: {grad}")
    print(f"裁剪后(阈值=2.0): {clipped}")
    
    # 测试4：模拟RNN训练中的梯度问题
    print("\n--- 模拟RNN训练（梯度裁剪必要性） ---")
    # RNN中由于链式法则，梯度可能指数级增长或衰减
    time_steps = 20
    grad_sequence = []
    current_grad = np.random.randn(10)
    
    for t in range(time_steps):
        # 模拟链式传播，梯度可能指数增长
        growth_factor = 1.2 if t < 10 else 0.8  # 前10步放大，后10步衰减
        current_grad = current_grad * growth_factor + np.random.randn(10) * 0.1
        grad_sequence.append(np.linalg.norm(current_grad))
    
    print("RNN各时间步梯度范数变化:")
    for i, norm in enumerate(grad_sequence):
        marker = " ⚠️爆炸" if norm > 10 else (" ⚠️消失" if norm < 0.1 else "")
        print(f"  Step {i+1:2d}: norm = {norm:.4f}{marker}")
    
    # 应用全局裁剪
    print("\n应用全局范数裁剪（max_norm=5.0）后:")
    for norm in grad_sequence:
        clipped_norm = min(norm, 5.0)
        print(f"  norm = {clipped_norm:.4f}")
    
    print("\n梯度裁剪测试完成！")
