# -*- coding: utf-8 -*-
"""
算法实现：联邦学习 / 07_horizontal_fl

本文件实现 07_horizontal_fl 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Dict, Optional, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class ClientConfig:
    """
    客户端配置数据类

    Attributes:
        client_id: 客户端唯一标识符
        data_size: 本地数据集大小
        model_dim: 模型参数维度
        learning_rate: 本地学习率
        local_epochs: 本地训练轮数
    """
    client_id: int
    data_size: int
    model_dim: int
    learning_rate: float = 0.01
    local_epochs: int = 5


class BaseClient(ABC):
    """
    客户端抽象基类

    定义横向联邦学习中客户端的标准接口,
    具体实现可根据任务需求定制。
    """

    def __init__(self, config: ClientConfig):
        """
        初始化客户端

        Args:
            config: 客户端配置
        """
        self.config = config
        self.client_id = config.client_id
        self.model_params = None  # 本地模型参数

    @abstractmethod
    def local_train(self, global_params: np.ndarray) -> np.ndarray:
        """
        本地训练接口

        Args:
            global_params: 从服务器接收的全局模型参数

        Returns:
            本地训练后的参数更新量
        """
        pass

    def receive_global_model(self, global_params: np.ndarray):
        """
        接收全局模型参数

        Args:
            global_params: 服务器下发的全局模型参数
        """
        self.model_params = global_params.copy()

    def send_update(self) -> np.ndarray:
        """
        发送本地更新到服务器

        Returns:
            本地模型参数的更新量
        """
        return self.model_params


class LinearRegressionClient(BaseClient):
    """
    线性回归客户端实现

    使用梯度下降进行本地模型训练
    """

    def __init__(
        self,
        config: ClientConfig,
        train_data: np.ndarray,
        train_labels: np.ndarray
    ):
        """
        初始化线性回归客户端

        Args:
            config: 客户端配置
            train_data: 本地训练数据特征
            train_labels: 本地训练数据标签
        """
        super().__init__(config)
        self.train_data = train_data
        self.train_labels = train_labels

    def local_train(self, global_params: np.ndarray) -> np.ndarray:
        """
        本地训练 - 线性回归梯度下降

        Args:
            global_params: 全局模型参数

        Returns:
            更新后的本地模型参数
        """
        self.receive_global_model(global_params)
        local_params = self.model_params.copy()
        lr = self.config.learning_rate
        epochs = self.config.local_epochs
        n_samples = len(self.train_labels)

        for _ in range(epochs):
            # 前向传播
            predictions = self.train_data @ local_params
            # 计算梯度
            errors = predictions - self.train_labels
            gradients = (1.0 / n_samples) * (self.train_data.T @ errors)
            # 更新
            local_params = local_params - lr * gradients

        self.model_params = local_params
        return local_params


class Server:
    """
    横向联邦学习服务器

    负责任务分发、模型聚合和客户端协调
    """

    def __init__(
        self,
        model_dim: int,
        aggregation_method: str = "fedavg"
    ):
        """
        初始化服务器

        Args:
            model_dim: 模型参数维度
            aggregation_method: 聚合方法,支持"fedavg","fedprox"
        """
        self.model_dim = model_dim
        self.global_params = self._initialize_params()
        self.aggregation_method = aggregation_method
        self.round_number = 0
        self.history = []

    def _initialize_params(self) -> np.ndarray:
        """
        初始化全局模型参数

        Returns:
            初始化的参数向量
        """
        return np.random.randn(self.model_dim) * np.sqrt(2.0 / self.model_dim)

    def select_clients(
        self,
        n_clients: int,
        selection_ratio: float = 1.0
    ) -> List[int]:
        """
        选择参与本轮训练的客户端

        Args:
            n_clients: 总客户端数
            selection_ratio: 选择比例

        Returns:
            被选中的客户端ID列表
        """
        n_selected = max(1, int(n_clients * selection_ratio))
        selected = np.random.choice(n_clients, n_selected, replace=False)
        return sorted(selected.tolist())

    def broadcast_model(
        self,
        selected_clients: List[BaseClient]
    ):
        """
        向选中的客户端广播全局模型

        Args:
            selected_clients: 被选中的客户端列表
        """
        for client in selected_clients:
            client.receive_global_model(self.global_params)

    def aggregate_updates(
        self,
        client_updates: List[np.ndarray],
        client_weights: List[float]
    ) -> np.ndarray:
        """
        聚合客户端更新

        Args:
            client_updates: 各客户端的更新列表
            client_weights: 各客户端的权重

        Returns:
            聚合后的全局参数
        """
        if self.aggregation_method == "fedavg":
            return self._fedavg_aggregate(client_updates, client_weights)
        elif self.aggregation_method == "fedprox":
            return self._fedavg_aggregate(client_updates, client_weights)
        else:
            return self._fedavg_aggregate(client_updates, client_weights)

    def _fedavg_aggregate(
        self,
        client_updates: List[np.ndarray],
        client_weights: List[float]
    ) -> np.ndarray:
        """
        FedAvg加权平均聚合

        Args:
            client_updates: 各客户端更新后的参数
            client_weights: 各客户端权重

        Returns:
            聚合后的全局参数
        """
        total_weight = sum(client_weights)
        normalized_weights = [w / total_weight for w in client_weights]

        aggregated = np.zeros_like(client_updates[0])
        for update, weight in zip(client_updates, normalized_weights):
            aggregated += weight * update

        return aggregated

    def update_global_model(self, new_params: np.ndarray):
        """
        更新全局模型参数

        Args:
            new_params: 新的全局参数
        """
        self.global_params = new_params
        self.round_number += 1

    def evaluate(self, test_data: np.ndarray, test_labels: np.ndarray) -> Dict:
        """
        评估全局模型

        Args:
            test_data: 测试数据特征
            test_labels: 测试数据标签

        Returns:
            评估指标字典
        """
        predictions = test_data @ self.global_params
        mse = np.mean((predictions - test_labels) ** 2)
        return {"mse": mse, "rmse": np.sqrt(mse)}


class HorizontalFederatedLearning:
    """
    横向联邦学习框架主类

    整合客户端和服务器,提供完整的训练流程
    """

    def __init__(
        self,
        clients: List[BaseClient],
        server: Server,
        client_weights: List[float] = None
    ):
        """
        初始化横向联邦学习框架

        Args:
            clients: 客户端列表
            server: 服务器实例
            client_weights: 各客户端权重
        """
        self.clients = clients
        self.server = server
        self.n_clients = len(clients)

        # 默认权重为等权重
        if client_weights is None:
            client_weights = [1.0 / self.n_clients] * self.n_clients
        self.client_weights = client_weights

    def train(
        self,
        n_rounds: int,
        client_selection_ratio: float = 1.0,
        test_data: np.ndarray = None,
        test_labels: np.ndarray = None,
        verbose: bool = True
    ) -> Dict:
        """
        执行联邦学习训练

        Args:
            n_rounds: 训练轮数
            client_selection_ratio: 每轮客户端选择比例
            test_data: 测试数据(可选)
            test_labels: 测试标签(可选)
            verbose: 是否打印训练进度

        Returns:
            训练历史记录
        """
        history = {
            "rounds": [],
            "test_mse": [] if test_data is not None else None,
            "client_participation": []
        }

        for round_idx in range(n_rounds):
            self.server.round_number = round_idx + 1

            # 1. 选择客户端
            selected_indices = self.server.select_clients(
                self.n_clients, client_selection_ratio
            )
            selected_clients = [self.clients[i] for i in selected_indices]
            selected_weights = [self.client_weights[i] for i in selected_indices]

            # 2. 广播全局模型
            self.server.broadcast_model(selected_clients)

            # 3. 本地训练
            client_updates = []
            for client in selected_clients:
                updated_params = client.local_train(self.server.global_params)
                client_updates.append(updated_params)

            # 4. 聚合更新
            aggregated_params = self.server.aggregate_updates(
                client_updates, selected_weights
            )
            self.server.update_global_model(aggregated_params)

            # 5. 评估(如果提供测试数据)
            if test_data is not None:
                metrics = self.server.evaluate(test_data, test_labels)
                history["test_mse"].append(metrics["mse"])

            history["rounds"].append(round_idx + 1)
            history["client_participation"].append(selected_indices)

            if verbose and (round_idx + 1) % 5 == 0:
                msg = f"轮次 {round_idx + 1}/{n_rounds}"
                if test_data is not None:
                    msg += f" | MSE: {metrics['mse']:.6f}"
                print(msg)

        return history

    def get_global_model(self) -> np.ndarray:
        """
        获取当前全局模型

        Returns:
            全局模型参数
        """
        return self.server.global_params


def create_horizontal_fl_scenario(
    n_clients: int,
    model_dim: int,
    data_per_client: int,
    test_size: int,
    seed: int = 42
) -> Tuple[HorizontalFederatedLearning, np.ndarray, np.ndarray]:
    """
    创建横向联邦学习场景

    辅助函数,用于快速创建测试场景

    Args:
        n_clients: 客户端数量
        model_dim: 模型维度
        data_per_client: 每客户端数据量
        test_size: 测试集大小
        seed: 随机种子

    Returns:
        (框架实例, 测试数据, 测试标签)
    """
    np.random.seed(seed)

    # 生成真实模型参数
    w_true = np.random.randn(model_dim) * 0.5

    # 生成测试数据
    X_test = np.random.randn(test_size, model_dim)
    y_test = X_test @ w_true + np.random.randn(test_size) * 0.1

    # 创建客户端
    clients = []
    client_weights = []

    for i in range(n_clients):
        # 模拟各客户端的非IID数据
        noise_scale = 0.1 + 0.2 * (i / n_clients)
        X = np.random.randn(data_per_client, model_dim)
        y = X @ w_true + np.random.randn(data_per_client) * noise_scale

        config = ClientConfig(
            client_id=i,
            data_size=data_per_client,
            model_dim=model_dim,
            learning_rate=0.1,
            local_epochs=5
        )

        client = LinearRegressionClient(config, X, y)
        clients.append(client)
        client_weights.append(float(data_per_client))

    # 创建服务器
    server = Server(model_dim, aggregation_method="fedavg")

    # 创建框架
    framework = HorizontalFederatedLearning(clients, server, client_weights)

    return framework, X_test, y_test


if __name__ == "__main__":
    print("=" * 60)
    print("横向联邦学习框架演示")
    print("=" * 60)

    # 创建场景
    framework, X_test, y_test = create_horizontal_fl_scenario(
        n_clients=5,
        model_dim=10,
        data_per_client=200,
        test_size=500,
        seed=42
    )

    # 训练
    history = framework.train(
        n_rounds=20,
        client_selection_ratio=1.0,
        test_data=X_test,
        test_labels=y_test,
        verbose=True
    )

    print("\n" + "=" * 60)
    print("训练完成!")
    print(f"最终MSE: {history['test_mse'][-1]:.6f}")
    print(f"全局模型维度: {len(framework.get_global_model())}")
    print("=" * 60)
