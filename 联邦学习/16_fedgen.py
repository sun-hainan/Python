# -*- coding: utf-8 -*-
"""
算法实现：联邦学习 / 16_fedgen

本文件实现 16_fedgen 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Dict


class GenerativeModel:
    """
    生成模型(简化版)

    使用随机生成模拟GAN/VAE
    """

    def __init__(self, latent_dim: int, output_dim: int):
        """
        初始化生成器

        Args:
            latent_dim: 潜在空间维度
            output_dim: 输出维度
        """
        self.latent_dim = latent_dim
        self.output_dim = output_dim
        # 简化的生成器参数
        self.generator_params = np.random.randn(latent_dim + output_dim) * 0.1

    def generate(self, n_samples: int) -> np.ndarray:
        """
        生成样本

        Args:
            n_samples: 生成数量

        Returns:
            生成的样本
        """
        # 从潜在空间采样
        z = np.random.randn(n_samples, self.latent_dim)
        # 简化的生成: 线性变换 + 非线性
        samples = z @ self.generator_params[:self.latent_dim].T + self.generator_params[self.latent_dim:]
        # 添加非线性
        samples = np.tanh(samples)
        return samples

    def update(self, fake_samples: np.ndarray, real_samples: np.ndarray, lr: float = 0.01):
        """
        更新生成器

        简化: 使生成的样本分布接近真实样本

        Args:
            fake_samples: 生成的样本
            real_samples: 真实样本
            lr: 学习率
        """
        # 简化: 使均值和方差接近
        fake_mean = np.mean(fake_samples, axis=0)
        real_mean = np.mean(real_samples, axis=0)

        fake_std = np.std(fake_samples, axis=0) + 1e-8
        real_std = np.std(real_samples, axis=0) + 1e-8

        # 调整生成器参数
        mean_diff = real_mean - fake_mean
        std_diff = np.log(real_std / fake_std)

        self.generator_params[:self.latent_dim] += lr * mean_diff[:self.latent_dim]
        self.generator_params[self.latent_dim:] += lr * std_diff


class FedGenClient:
    """FedGen客户端"""

    def __init__(
        self,
        client_id: int,
        train_data: np.ndarray,
        train_labels: np.ndarray,
        n_classes: int
    ):
        """初始化客户端"""
        self.client_id = client_id
        self.train_data = train_data
        self.train_labels = train_labels
        self.n_classes = n_classes
        self.model_params = None
        self.class_indices = self._compute_class_indices()

    def _compute_class_indices(self) -> Dict[int, np.ndarray]:
        """计算每类的样本索引"""
        indices = {}
        for c in range(self.n_classes):
            indices[c] = np.where(self.train_labels == c)[0]
        return indices

    def get_class_distribution(self) -> Dict[int, int]:
        """获取类别分布"""
        return {c: len(indices) for c, indices in self.class_indices.items()}

    def initialize_model(self, dim: int, seed: int = 42):
        """初始化本地模型"""
        np.random.seed(seed + self.client_id)
        self.model_params = np.random.randn(dim) * np.sqrt(2.0 / dim)

    def local_train(
        self,
        global_params: np.ndarray,
        generator: GenerativeModel,
        local_epochs: int,
        learning_rate: float,
        augmentation_ratio: float = 0.5
    ) -> np.ndarray:
        """
        本地训练(使用生成数据增强)

        Args:
            global_params: 全局模型参数
            generator: 全局生成器
            local_epochs: 本地训练轮数
            learning_rate: 学习率
            augmentation_ratio: 增强比例

        Returns:
            更新后的模型参数
        """
        local_params = global_params.copy()
        n_samples = len(self.train_labels)

        # 从生成器合成数据
        n_synthetic = int(n_samples * augmentation_ratio)
        synthetic_data = generator.generate(n_synthetic)
        synthetic_labels = np.random.randint(0, self.n_classes, n_synthetic)

        # 合并真实数据和合成数据
        augmented_data = np.vstack([self.train_data, synthetic_data])
        augmented_labels = np.concatenate([self.train_labels, synthetic_labels])

        for _ in range(local_epochs):
            predictions = augmented_data @ local_params
            errors = predictions - augmented_labels
            gradients = (1.0 / len(augmented_labels)) * (augmented_data.T @ errors)
            local_params = local_params - learning_rate * gradients

        return local_params

    def compute_class_gradient(
        self,
        params: np.ndarray,
        target_class: int,
        learning_rate: float
    ) -> np.ndarray:
        """
        计算特定类别的梯度(用于指导生成器)

        Args:
            params: 模型参数
            target_class: 目标类别
            learning_rate: 学习率

        Returns:
            类别特定梯度
        """
        indices = self.class_indices.get(target_class, np.array([]))
        if len(indices) == 0:
            return np.zeros_like(params)

        data = self.train_data[indices]
        labels = self.train_labels[indices]

        predictions = data @ params
        errors = predictions - labels
        gradients = (1.0 / len(indices)) * (data.T @ errors)

        return gradients


def fedgen_server_aggregate(
    client_params_list: List[np.ndarray],
    client_weights: List[float]
) -> np.ndarray:
    """服务器聚合"""
    total_weight = sum(client_weights)
    normalized_weights = [w / total_weight for w in client_weights]

    global_params = np.zeros_like(client_params_list[0])
    for params, weight in zip(client_params_list, normalized_weights):
        global_params += weight * params

    return global_params


def run_fedgen_fl(
    n_clients: int,
    model_dim: int,
    n_classes: int,
    n_rounds: int,
    local_epochs: int,
    learning_rate: float,
    data_per_client: int = 100,
    test_size: int = 500,
    seed: int = 42
) -> Dict:
    """运行FedGen"""
    np.random.seed(seed)

    w_true = np.random.randn(model_dim) * 0.5

    # 创建非均衡的类别分布
    client_data_list = []
    client_weights = []

    for i in range(n_clients):
        X = np.random.randn(data_per_client, model_dim)
        # 模拟标签不均衡
        if i % 3 == 0:
            # 这个客户端主要有一类数据
            y = np.zeros(data_per_client, dtype=int)
            y[:data_per_client // 2] = i % n_classes
        else:
            y = np.random.randint(0, n_classes, data_per_client)

        y = X @ w_true + np.random.randn(data_per_client) * 0.1
        client_data_list.append((X, y))
        client_weights.append(float(data_per_client))

    X_test = np.random.randn(test_size, model_dim)
    y_test = X_test @ w_true + np.random.randn(test_size) * 0.1

    global_params = np.random.randn(model_dim) * np.sqrt(2.0 / model_dim)

    # 初始化生成器
    generator = GenerativeModel(latent_dim=10, output_dim=model_dim)

    history = {"rounds": [], "test_mse": [], "generator_updates": 0}

    print("FedGen联邦学习 (数据增强)")

    for round_idx in range(n_rounds):
        client_updates = []

        for i, (data, labels) in enumerate(client_data_list):
            client = FedGenClient(i, data, labels.astype(int), n_classes)
            client.initialize_model(model_dim)

            # 本地训练(使用生成数据增强)
            updated_params = client.local_train(
                global_params, generator, local_epochs, learning_rate, augmentation_ratio=0.3
            )
            client_updates.append(updated_params)

        # 聚合
        global_params = fedgen_server_aggregate(client_updates, client_weights)

        # 更新生成器(从所有客户端聚合)
        for i, (data, labels) in enumerate(client_data_list):
            client = FedGenClient(i, data, labels.astype(int), n_classes)
            client.initialize_model(model_dim)

            # 使用客户端数据更新生成器
            fake_samples = generator.generate(min(50, len(data)))
            client_data_subset = data[:min(50, len(data))]
            generator.update(fake_samples, client_data_subset, lr=0.01)

        history["generator_updates"] += 1

        # 评估
        mse = np.mean((X_test @ global_params - y_test) ** 2)

        history["rounds"].append(round_idx + 1)
        history["test_mse"].append(mse)

        if (round_idx + 1) % 5 == 0 or round_idx == 0:
            print(f"轮次 {round_idx + 1}/{n_rounds} | MSE: {mse:.6f}")

    return {"final_params": global_params, "history": history}


if __name__ == "__main__":
    print("=" * 60)
    print("联邦学习 - FedGen (联邦生成模型) 演示")
    print("=" * 60)

    result = run_fedgen_fl(
        n_clients=5,
        model_dim=10,
        n_classes=3,
        n_rounds=20,
        local_epochs=5,
        learning_rate=0.1,
        data_per_client=200,
        test_size=500,
        seed=42
    )

    print("\n" + "=" * 60)
    print(f"最终MSE: {result['history']['test_mse'][-1]:.6f}")
    print("=" * 60)
