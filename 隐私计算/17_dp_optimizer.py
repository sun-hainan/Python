# -*- coding: utf-8 -*-
"""
算法实现：隐私计算 / 17_dp_optimizer

本文件实现 17_dp_optimizer 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Optional
from abc import ABC, abstractmethod


class PrivacyAccountant:
    """
    隐私会计

    追踪训练过程中的隐私消耗
    """

    def __init__(self, target_epsilon: float, target_delta: float, sigma: float):
        """
        初始化

        Args:
            target_epsilon: 目标ε
            target_delta: 目标δ
            sigma: 噪声乘数
        """
        self.target_epsilon = target_epsilon
        self.target_delta = target_delta
        self.sigma = sigma
        self.epoch_count = 0
        self.sample_rate = 0.0

    def compute_epsilon(self, steps: int) -> float:
        """
        计算当前ε

        使用RDP(Rényi差分隐私)

        Args:
            steps: 步数

        Returns:
            当前ε
        """
        # 简化的ε计算
        # 实际使用强组合定理
        q = self.sample_rate
        epochs = steps / self.sample_rate if self.sample_rate > 0 else steps

        # DP-SGD的ε近似
        epsilon = (epochs * q * q * self.sigma * self.sigma) / (2 * self.target_delta)

        return min(epsilon, self.target_epsilon)

    def step(self):
        """更新步数"""
        self.epoch_count += 1


class GradientClipper:
    """
    梯度裁剪

    将梯度范数裁剪到指定阈值
    """

    def __init__(self, clip_norm: float = 1.0):
        """
        初始化

        Args:
            clip_norm: 裁剪范数阈值
        """
        self.clip_norm = clip_norm

    def clip(self, gradient: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        裁剪梯度

        Args:
            gradient: 原始梯度

        Returns:
            (裁剪后的梯度, 裁剪比率)
        """
        grad_norm = np.linalg.norm(gradient)

        if grad_norm > self.clip_norm:
            clip_factor = self.clip_norm / grad_norm
            clipped_gradient = gradient * clip_factor
        else:
            clip_factor = 1.0
            clipped_gradient = gradient

        return clipped_gradient, clip_factor


class DPSGDOptimizer:
    """
    差分隐私SGD优化器

    实现:
    1. 梯度裁剪
    2. 添加高斯噪声
    3. 隐私会计
    """

    def __init__(
        self,
        lr: float,
        sigma: float,
        clip_norm: float = 1.0,
        noise_accumulator: Optional[PrivacyAccountant] = None
    ):
        """
        初始化DP-SGD

        Args:
            lr: 学习率
            sigma: 噪声标准差乘数
            clip_norm: 裁剪阈值
            noise_accumulator: 隐私会计
        """
        self.lr = lr
        self.sigma = sigma
        self.clipper = GradientClipper(clip_norm)
        self.privacy_accountant = noise_accumulator
        self.iteration_count = 0

    def step(self, gradient: np.ndarray, batch_size: int) -> np.ndarray:
        """
        执行一步优化

        Args:
            gradient: 原始梯度
            batch_size: 批次大小

        Returns:
            加噪后的梯度
        """
        # 1. 裁剪梯度
        clipped_gradient, _ = self.clipper.clip(gradient)

        # 2. 添加高斯噪声
        sensitivity = self.clipper.clip_norm / batch_size
        noise = np.random.normal(0, self.sigma * sensitivity, gradient.shape)
        noisy_gradient = clipped_gradient + noise

        # 3. 更新
        self.iteration_count += 1

        return noisy_gradient


class DPAdamOptimizer:
    """
    差分隐私Adam优化器

    结合Adam优化器和差分隐私
    """

    def __init__(
        self,
        lr: float = 0.001,
        sigma: float = 1.0,
        clip_norm: float = 1.0,
        beta1: float = 0.9,
        beta2: float = 0.999,
        eps: float = 1e-8
    ):
        """
        初始化DP-Adam

        Args:
            lr: 学习率
            sigma: 噪声乘数
            clip_norm: 裁剪阈值
            beta1: 一阶矩衰减
            beta2: 二阶矩衰减
            eps: 数值稳定项
        """
        self.lr = lr
        self.sigma = sigma
        self.clip_norm = clip_norm
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.clipper = GradientClipper(clip_norm)

        self.m = None  # 一阶矩
        self.v = None  # 二阶矩
        self.t = 0     # 时间步

    def step(self, gradient: np.ndarray, batch_size: int) -> np.ndarray:
        """
        执行一步优化

        Args:
            gradient: 原始梯度
            batch_size: 批次大小

        Returns:
            更新后的参数
        """
        self.t += 1

        # 初始化矩估计
        if self.m is None:
            self.m = np.zeros_like(gradient)
        if self.v is None:
            self.v = np.zeros_like(gradient)

        # 裁剪梯度
        clipped_gradient, _ = self.clipper.clip(gradient)

        # 添加噪声
        sensitivity = self.clip_norm / batch_size
        noise = np.random.normal(0, self.sigma * sensitivity, gradient.shape)
        noisy_gradient = clipped_gradient + noise

        # 更新矩估计
        self.m = self.beta1 * self.m + (1 - self.beta1) * noisy_gradient
        self.v = self.beta2 * self.v + (1 - self.beta2) * (noisy_gradient ** 2)

        # 偏差校正
        m_hat = self.m / (1 - self.beta1 ** self.t)
        v_hat = self.v / (1 - self.beta2 ** self.t)

        # 参数更新
        update = self.lr * m_hat / (np.sqrt(v_hat) + self.eps)

        return update


class DPAdaGradOptimizer:
    """
    差分隐私AdaGrad优化器
    """

    def __init__(
        self,
        lr: float = 0.01,
        sigma: float = 1.0,
        clip_norm: float = 1.0,
        eps: float = 1e-8
    ):
        """
        初始化DP-AdaGrad

        Args:
            lr: 学习率
            sigma: 噪声乘数
            clip_norm: 裁剪阈值
            eps: 数值稳定项
        """
        self.lr = lr
        self.sigma = sigma
        self.clip_norm = clip_norm
        self.eps = eps
        self.clipper = GradientClipper(clip_norm)

        self.G = None  # 累积梯度平方

    def step(self, gradient: np.ndarray, batch_size: int) -> np.ndarray:
        """
        执行一步优化

        Args:
            gradient: 原始梯度
            batch_size: 批次大小

        Returns:
            更新后的参数
        """
        # 初始化累积
        if self.G is None:
            self.G = np.zeros_like(gradient)

        # 裁剪梯度
        clipped_gradient, _ = self.clipper.clip(gradient)

        # 添加噪声
        sensitivity = self.clip_norm / batch_size
        noise = np.random.normal(0, self.sigma * sensitivity, gradient.shape)
        noisy_gradient = clipped_gradient + noise

        # 更新累积
        self.G += noisy_gradient ** 2

        # 参数更新
        update = self.lr * noisy_gradient / (np.sqrt(self.G) + self.eps)

        return update


class DPSGDTrainer:
    """
    差分隐私SGD训练器

    完整的隐私保护训练循环
    """

    def __init__(
        self,
        model_dim: int,
        optimizer: DPSGDOptimizer,
        privacy_accountant: PrivacyAccountant = None
    ):
        """
        初始化训练器

        Args:
            model_dim: 模型维度
            optimizer: DP优化器
            privacy_accountant: 隐私会计
        """
        self.model_dim = model_dim
        self.optimizer = optimizer
        self.privacy_accountant = privacy_accountant
        self.model_params = np.random.randn(model_dim) * 0.01
        self.train_history = []

    def train_step(
        self,
        data: np.ndarray,
        labels: np.ndarray,
        batch_size: int
    ) -> float:
        """
        执行一个训练步骤

        Args:
            data: 训练数据
            labels: 标签
            batch_size: 批次大小

        Returns:
            损失值
        """
        # 随机选择批次
        indices = np.random.choice(len(data), batch_size, replace=False)
        batch_data = data[indices]
        batch_labels = labels[indices]

        # 计算梯度
        predictions = batch_data @ self.model_params
        errors = predictions - batch_labels
        gradients = (1.0 / batch_size) * (batch_data.T @ errors)

        # 使用DP优化器更新
        update = self.optimizer.step(gradients, batch_size)
        self.model_params = self.model_params - update

        # 计算损失
        loss = np.mean(errors ** 2)

        return loss

    def train(
        self,
        train_data: np.ndarray,
        train_labels: np.ndarray,
        n_epochs: int,
        batch_size: int,
        verbose: bool = True
    ) -> List[float]:
        """
        训练模型

        Args:
            train_data: 训练数据
            train_labels: 训练标签
            n_epochs: 训练轮数
            batch_size: 批次大小
            verbose: 是否打印进度

        Returns:
            训练历史
        """
        n_samples = len(train_data)
        steps_per_epoch = n_samples // batch_size

        for epoch in range(n_epochs):
            epoch_losses = []

            for step in range(steps_per_epoch):
                loss = self.train_step(train_data, train_labels, batch_size)
                epoch_losses.append(loss)

            avg_loss = np.mean(epoch_losses)
            self.train_history.append(avg_loss)

            if verbose and (epoch + 1) % 5 == 0:
                msg = f"Epoch {epoch + 1}/{n_epochs}, Loss: {avg_loss:.4f}"
                if self.privacy_accountant:
                    epsilon = self.privacy_accountant.compute_epsilon(
                        self.optimizer.iteration_count
                    )
                    msg += f", ε: {epsilon:.4f}"
                print(f"   {msg}")

        return self.train_history


class PATEBasedTraining:
    """
    基于PATE的隐私保护训练

    使用教师集合聚合来生成隐私保护的伪标签
    """

    def __init__(self, n_teachers: int, epsilon: float):
        """
        初始化

        Args:
            n_teachers: 教师数量
            epsilon: 隐私预算
        """
        self.n_teachers = n_teachers
        self.epsilon = epsilon
        self.noise_scale = 1.0 / epsilon
        self.teachers = []

    def train_teachers(
        self,
        data: np.ndarray,
        labels: np.ndarray,
        n_classes: int
    ) -> None:
        """
        训练教师模型

        Args:
            data: 训练数据
            labels: 标签
            n_classes: 类别数
        """
        # 分割数据给各教师
        chunk_size = len(data) // self.n_teachers

        for i in range(self.n_teachers):
            start = i * chunk_size
            end = (i + 1) * chunk_size if i < self.n_teachers - 1 else len(data)

            teacher_data = data[start:end]
            teacher_labels = labels[start:end]

            # 训练简单模型
            params = np.random.randn(data.shape[1], n_classes) * 0.01
            lr = 0.1

            for _ in range(50):
                logits = teacher_data @ params
                probs = np.exp(logits) / np.sum(np.exp(logits), axis=1, keepdims=True)
                gradients = teacher_data.T @ (probs - np.eye(n_classes)[teacher_labels.astype(int)]) / len(teacher_labels)
                params = params - lr * gradients

            self.teachers.append(params)

    def aggregate_predictions(self, data: np.ndarray) -> np.ndarray:
        """
        聚合教师预测

        Args:
            data: 数据

        Returns:
            聚合后的预测
        """
        # 聚合logits
        aggregated_logits = np.zeros((len(data), self.teachers[0].shape[1]))

        for teacher_params in self.teachers:
            logits = data @ teacher_params
            aggregated_logits += logits

        # 添加拉普拉斯噪声
        noise = np.random.laplace(0, self.noise_scale, aggregated_logits.shape)
        noisy_logits = aggregated_logits + noise

        return np.argmax(noisy_logits, axis=1)


def dp_optimizer_demo():
    """
    差分隐私优化器演示
    """

    print("差分隐私优化器演示")
    print("=" * 60)

    np.random.seed(42)

    # 1. 基础DP-SGD
    print("\n1. DP-SGD优化器")
    model_dim = 10
    batch_size = 32

    optimizer = DPSGDOptimizer(
        lr=0.1,
        sigma=1.0,
        clip_norm=1.0
    )

    # 模拟梯度
    gradient = np.random.randn(model_dim)
    update = optimizer.step(gradient, batch_size)

    print(f"   原始梯度范数: {np.linalg.norm(gradient):.4f}")
    print(f"   更新向量范数: {np.linalg.norm(update):.4f}")

    # 2. DP-Adam
    print("\n2. DP-Adam优化器")
    dp_adam = DPAdamOptimizer(lr=0.001, sigma=1.0, clip_norm=1.0)

    for i in range(5):
        gradient = np.random.randn(model_dim)
        update = dp_adam.step(gradient, batch_size)
        print(f"   步骤{i+1}: 更新范数={np.linalg.norm(update):.4f}")

    # 3. 完整训练循环
    print("\n3. DP-SGD完整训练")
    model_dim = 5
    n_samples = 200
    batch_size = 32

    train_data = np.random.randn(n_samples, model_dim)
    true_w = np.array([1, -2, 0.5, 3, -1])
    train_labels = train_data @ true_w + np.random.randn(n_samples) * 0.1

    accountant = PrivacyAccountant(target_epsilon=1.0, target_delta=1e-5, sigma=1.0)
    optimizer = DPSGDOptimizer(lr=0.1, sigma=1.0, clip_norm=1.0)
    trainer = DPSGDTrainer(model_dim, optimizer, accountant)

    history = trainer.train(train_data, train_labels, n_epochs=20, batch_size=32)

    print(f"   初始损失: {history[0]:.4f}")
    print(f"   最终损失: {history[-1]:.4f}")

    # 4. PATE训练
    print("\n4. PATE隐私保护训练")
    pate = PATEBasedTraining(n_teachers=5, epsilon=1.0)

    X = np.random.randn(100, 5)
    y = np.random.randint(0, 3, 100)

    pate.train_teachers(X, y, n_classes=3)

    # 聚合预测
    pseudo_labels = pate.aggregate_predictions(X)
    agreement = np.mean(pseudo_labels == y)
    print(f"   教师预测一致率: {agreement:.4f}")


if __name__ == "__main__":
    dp_optimizer_demo()

    print("\n" + "=" * 60)
    print("差分隐私优化器演示完成!")
    print("=" * 60)
