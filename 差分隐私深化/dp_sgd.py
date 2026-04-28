# -*- coding: utf-8 -*-
"""
差分隐私随机梯度下降（DP-SGD）模块

本模块实现差分隐私随机梯度下降算法，是深度学习隐私保护的核心技术。
DP-SGD通过在梯度更新时添加高斯噪声并实施梯度裁剪来实现差分隐私。

核心思想：
1. 梯度裁剪：将每个样本的梯度裁剪到固定范数内
2. 噪声注入：向聚合梯度添加校准过的高斯噪声
3. 隐私会计：跟踪累积隐私损失

作者：算法实现
版本：1.0
"""

import numpy as np  # 数值计算库
from typing import Tuple, Optional, Callable  # 类型提示
from collections import defaultdict  # 字典默认工厂


class DPSGD:
    """
    差分隐私随机梯度下降优化器

    用于在训练机器学习模型时保护数据隐私。每一轮迭代都使用
    差分隐私机制保护梯度信息，并进行隐私会计跟踪。

    属性:
        clip_bound: 梯度裁剪范数上限C
        noise_multiplier: 噪声乘数σ/C（通常设为1.0或更高）
        epsilon: 隐私预算ε（目标）
        delta: 失败概率δ
        batch_size: 批处理大小
        noise_seed: 随机噪声种子（用于可重复性）
    """

    def __init__(self, clip_bound: float = 1.0, noise_multiplier: float = 1.0,
                 epsilon: float = 10.0, delta: float = 1e-5,
                 batch_size: int = 32, max_grad_norm: float = 1.0):
        """
        初始化DP-SGD优化器

        参数:
            clip_bound: 每样本梯度裁剪范数上限C
            noise_multiplier: 噪声乘数（σ/C比值）
            epsilon: 目标隐私预算ε
            delta: 目标失败概率δ
            batch_size: 训练批次大小
            max_grad_norm: 梯度最大范数（与clip_bound同义）
        """
        self.clip_bound = clip_bound if clip_bound > 0 else max_grad_norm
        self.noise_multiplier = noise_multiplier  # 噪声乘数μ = σ/C
        self.epsilon = epsilon  # 目标隐私预算
        self.delta = delta  # 失败概率
        self.batch_size = batch_size  # 批次大小
        self.privacy_budget_used = 0.0  # 已消耗隐私预算
        self.step_count = 0  # 训练步数计数

    def clip_gradients(self, per_sample_grads: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        对每样本梯度进行裁剪

        将每个样本的梯度向量裁剪到L2范数不超过clip_bound。

        参数:
            per_sample_grads: shape为(batch_size, model_dim)的每样本梯度数组

        返回:
            (裁剪后的梯度, 裁剪因子数组)
        """
        batch_size = per_sample_grads.shape[0]  # 批次大小
        clipped_grads = np.zeros_like(per_sample_grads)  # 初始化裁剪后梯度
        clip_factors = np.ones(batch_size)  # 初始化裁剪因子

        for i in range(batch_size):
            grad_norm = np.linalg.norm(per_sample_grads[i])  # 计算梯度L2范数
            if grad_norm > self.clip_bound:
                # 裁剪：缩放到clip_bound
                clip_factors[i] = self.clip_bound / grad_norm
                clipped_grads[i] = per_sample_grads[i] * clip_factors[i]
            else:
                clipped_grads[i] = per_sample_grads[i]

        return clipped_grads, clip_factors

    def add_noise_to_gradients(self, clipped_grads: np.ndarray) -> np.ndarray:
        """
        向裁剪后的梯度添加高斯噪声

        使用校准过的高斯噪声，标准差为 noise_multiplier * clip_bound。

        参数:
            clipped_grads: 裁剪后的梯度数组

        返回:
            添加噪声后的梯度数组
        """
        batch_size = clipped_grads.shape[0]  # 批次大小
        model_dim = clipped_grads.shape[1]  # 模型参数维度

        # 计算噪声标准差：σ = noise_multiplier * clip_bound
        noise_std = self.noise_multiplier * self.clip_bound

        # 生成高斯噪声
        noise = np.random.normal(0, noise_std, size=(batch_size, model_dim))

        # 添加噪声
        noisy_grads = clipped_grads + noise

        return noisy_grads

    def compute_noisy_gradient(self, per_sample_grads: np.ndarray) -> np.ndarray:
        """
        计算带隐私保护的梯度（核心方法）

        完整流程：裁剪 -> 聚合 -> 添加噪声

        参数:
            per_sample_grads: 每样本梯度数组

        返回:
            带噪声的聚合梯度
        """
        # 步骤1：裁剪每样本梯度
        clipped_grads, clip_factors = self.clip_gradients(per_sample_grads)

        # 步骤2：聚合梯度（求平均）
        aggregated_grad = np.mean(clipped_grads, axis=0)

        # 步骤3：添加高斯噪声
        noise_std = self.noise_multiplier * self.clip_bound / np.sqrt(self.batch_size)
        noise = np.random.normal(0, noise_std, size=aggregated_grad.shape)
        noisy_grad = aggregated_grad + noise

        return noisy_grad

    def compute_privacy_spent(self, num_steps: int) -> dict:
        """
        计算已消耗的隐私预算（基于RDP accountant）

        使用RDP（Rényi差分隐私）组合定理计算累积隐私损失。

        参数:
            num_steps: 训练步数（梯度更新次数）

        返回:
            包含隐私参数的字典
        """
        # 使用简单的RDP计算（高斯机制）
        # RDP for Gaussian mechanism with parameters (σ/C, q=1/batch_size)
        # 简化：使用RDP公式的闭式解

        q = 1.0 / self.batch_size  # 采样率
        sigma = self.noise_multiplier * self.clip_bound  # 噪声标准差

        # 计算α阶Rényi散度（使用α=2的特例）
        alpha = 2.0
        rdp_per_step = (alpha * q**2 * sigma**2) / (2 * (alpha - 1))

        # 组合k步的RDP
        total_rdp = num_steps * rdp_per_step

        # 从RDP转换到(zcdp)和(ε,δ)-DP
        # ZCDP ρ
        zcdp_rho = total_rdp

        # 转换到(ε, δ)-DP
        if self.delta > 0:
            eps_converted = np.sqrt(2 * zcdp_rho * np.log(1.25 / self.delta))
        else:
            eps_converted = float('inf')

        return {
            'num_steps': num_steps,
            'zcdp_rho': zcdp_rho,
            'eps_converted': eps_converted,
            'delta': self.delta,
            'noise_multiplier': self.noise_multiplier,
            'clip_bound': self.clip_bound
        }


def compute_gradients_for_model(model: np.ndarray, batch_x: np.ndarray,
                                 batch_y: np.ndarray,
                                 loss_func: Callable) -> np.ndarray:
    """
    计算模型在批数据上的每样本梯度（简化版）

    参数:
        model: 模型参数向量
        batch_x: 输入批次
        batch_y: 目标批次
        loss_func: 损失函数

    返回:
        每样本梯度数组
    """
    batch_size = batch_x.shape[0]  # 批次大小
    model_dim = len(model)  # 模型维度
    per_sample_grads = np.zeros((batch_size, model_dim))  # 初始化梯度数组

    for i in range(batch_size):
        # 数值梯度计算（简化版）
        grad = np.zeros(model_dim)  # 初始化梯度
        h = 1e-5  # 数值微分步长

        for j in range(model_dim):
            model_plus = model.copy()
            model_plus[j] += h
            loss_plus = loss_func(model_plus, batch_x[i:i+1], batch_y[i:i+1])

            model_minus = model.copy()
            model_minus[j] -= h
            loss_minus = loss_func(model_minus, batch_x[i:i+1], batch_y[i:i+1])

            grad[j] = (loss_plus - loss_minus) / (2 * h)

        per_sample_grads[i] = grad

    return per_sample_grads


def mse_loss(model: np.ndarray, x: np.ndarray, y: np.ndarray) -> float:
    """
    均方误差损失函数

    参数:
        model: 模型参数
        x: 输入数据
        y: 目标数据

    返回:
        损失值
    """
    pred = x.dot(model)  # 简单线性模型预测
    return np.mean((pred - y) ** 2)


def softmax_cross_entropy(model: np.ndarray, x: np.ndarray, y: np.ndarray) -> float:
    """
    Softmax交叉熵损失（简化分类场景）

    参数:
        model: 模型参数（包含权重和偏置）
        x: 输入特征
        y: 目标标签

    返回:
        损失值
    """
    n_classes = max(y) + 1  # 类别数
    logits = x.dot(model[:n_classes])  # 简化为线性分类器
    probs = np.exp(logits) / np.sum(np.exp(logits), axis=1, keepdims=True)
    one_hot = np.eye(n_classes)[y.astype(int)]
    loss = -np.mean(np.sum(one_hot * np.log(probs + 1e-10), axis=1))
    return loss


if __name__ == "__main__":
    print("=" * 60)
    print("差分隐私随机梯度下降（DP-SGD）测试")
    print("=" * 60)

    np.random.seed(42)  # 随机种子

    # 测试1：基本DP-SGD流程
    print("\n【测试1】DP-SGD基本流程")
    dp_sgd = DPSGD(clip_bound=1.0, noise_multiplier=1.0,
                   epsilon=8.0, delta=1e-5, batch_size=32)

    # 模拟每样本梯度（32个样本，10维模型）
    batch_size = 32
    model_dim = 10
    per_sample_grads = np.random.randn(batch_size, model_dim) * 0.5

    print(f"  模拟批次: {batch_size}样本, {model_dim}维模型")
    print(f"  梯度范数范围: [{np.linalg.norm(per_sample_grads, axis=1).min():.2f}, "
          f"{np.linalg.norm(per_sample_grads, axis=1).max():.2f}]")

    # 裁剪
    clipped_grads, clip_factors = dp_sgd.clip_gradients(per_sample_grads)
    avg_clip_factor = np.mean(clip_factors)
    print(f"  平均裁剪因子: {avg_clip_factor:.4f}")
    print(f"  被裁剪样本比例: {np.mean(clip_factors < 1.0):.2%}")

    # 添加噪声
    noisy_grad = dp_sgd.compute_noisy_gradient(per_sample_grads)
    print(f"  原始梯度均值: {np.mean(per_sample_grads):.6f}")
    print(f"  噪声梯度均值: {np.mean(noisy_grad):.6f}")
    print(f"  噪声梯度标准差: {np.std(noisy_grad):.6f}")

    # 测试2：隐私会计
    print("\n【测试2】隐私会计（隐私预算消耗）")
    total_steps = 100  # 总训练步数
    privacy_info = dp_sgd.compute_privacy_spent(total_steps)
    print(f"  总训练步数: {total_steps}")
    print(f"  ZCDP ρ: {privacy_info['zcdp_rho']:.4f}")
    print(f"  等效ε: {privacy_info['eps_converted']:.4f}")
    print(f"  目标ε: {dp_sgd.epsilon}")

    # 测试3：不同噪声乘数的影响
    print("\n【测试3】不同噪声乘数的影响")
    print(f"  {'μ(噪声乘数)':<15} {'σ(噪声标准差)':<15} {'ZCDP ρ':<12} {'等效ε':<12}")
    print(f"  {'-'*55}")
    for mu in [0.5, 1.0, 1.5, 2.0, 3.0]:
        dp = DPSGD(clip_bound=1.0, noise_multiplier=mu, batch_size=32)
        info = dp.compute_privacy_spent(100)
        sigma = mu * 1.0  # σ = μ * C
        print(f"  {mu:<15.1f} {sigma:<15.2f} {info['zcdp_rho']:<12.4f} {info['eps_converted']:<12.2f}")

    # 测试4：不同裁剪边界的影响
    print("\n【测试4】不同裁剪边界的影响")
    print(f"  {'C(裁剪边界)':<15} {'μ(噪声乘数)':<12} {'有效σ':<12}")
    print(f"  {'-'*40}")
    for clip_c in [0.5, 1.0, 2.0, 5.0]:
        dp = DPSGD(clip_bound=clip_c, noise_multiplier=1.0, batch_size=32)
        print(f"  {clip_c:<15.2f} {dp.noise_multiplier:<12.1f} {dp.noise_multiplier*clip_c:<12.2f}")

    # 测试5：梯度裁剪效果演示
    print("\n【测试5】梯度裁剪效果演示")
    # 生成极端梯度（某些样本梯度很大）
    extreme_grads = np.random.randn(32, 10)
    extreme_grads[:5] *= 10.0  # 前5个样本有极大梯度

    clipped, factors = dp_sgd.clip_gradients(extreme_grads)
    print(f"  原始梯度范数: 前5个={np.linalg.norm(extreme_grads[:5], axis=1).round(1)}")
    print(f"  裁剪后范数: 前5个={np.linalg.norm(clipped[:5], axis=1).round(1)}")
    print(f"  裁剪因子: 前5个={factors[:5].round(3)}")

    # 测试6：端到端训练模拟
    print("\n【测试6】端到端训练模拟")
    np.random.seed(42)
    n_samples = 1000
    n_features = 5
    n_epochs = 10
    batch_size = 32

    # 生成合成数据
    X = np.random.randn(n_samples, n_features)
    y = X.dot(np.random.randn(n_features)) + np.random.randn(n_samples) * 0.1

    # 初始化模型
    model = np.zeros(n_features)
    dp_sgd_train = DPSGD(clip_bound=1.0, noise_multiplier=1.2,
                         epsilon=8.0, delta=1e-5, batch_size=batch_size)

    print(f"  数据规模: {n_samples}样本, {n_features}特征")
    print(f"  训练轮数: {n_epochs}, 批次大小: {batch_size}")

    losses = []
    privacy_spent = []

    for epoch in range(n_epochs):
        # 打乱数据
        perm = np.random.permutation(n_samples)
        epoch_losses = []

        for i in range(0, n_samples, batch_size):
            batch_idx = perm[i:i+batch_size]
            if len(batch_idx) < batch_size:
                break

            batch_x = X[batch_idx]
            batch_y = y[batch_idx]

            # 计算梯度
            grads = compute_gradients_for_model(model, batch_x, batch_y, mse_loss)

            # DP-SGD更新
            noisy_grad = dp_sgd_train.compute_noisy_gradient(grads)
            model = model - 0.01 * noisy_grad  # 简化更新

            # 记录损失
            loss = mse_loss(model, batch_x, batch_y)
            epoch_losses.append(loss)
            dp_sgd_train.step_count += 1

        avg_loss = np.mean(epoch_losses)
        losses.append(avg_loss)

        # 每轮结束后计算隐私消耗
        if (epoch + 1) % 2 == 0:
            info = dp_sgd_train.compute_privacy_spent(dp_sgd_train.step_count)
            privacy_spent.append(info['eps_converted'])
            print(f"  Epoch {epoch+1:2d}: Loss={avg_loss:.4f}, 隐私ε消耗={info['eps_converted']:.4f}")

    print(f"\n  训练后模型参数: {model.round(3)}")
    print(f"  隐私预算总消耗: {dp_sgd_train.compute_privacy_spent(dp_sgd_train.step_count)['eps_converted']:.4f}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
