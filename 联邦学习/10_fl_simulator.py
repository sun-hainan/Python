# -*- coding: utf-8 -*-
"""
算法实现：联邦学习 / 10_fl_simulator

本文件实现 10_fl_simulator 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Dict, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import time


class ClientStatus(Enum):
    """客户端状态枚举"""
    IDLE = "idle"           # 空闲,等待任务
    TRAINING = "training"   # 正在训练
    UPLOADING = "uploading" # 上传更新
    DOWNLOADING = "downloading"  # 下载模型
    FAILED = "failed"       # 训练失败


@dataclass
class ClientState:
    """
    客户端状态快照

    Attributes:
        client_id: 客户端ID
        status: 当前状态
        data_size: 本地数据量
        last_train_round: 最后参与训练的轮次
        local_loss: 最近一次本地损失
        train_time: 训练耗时(秒)
    """
    client_id: int
    status: ClientStatus = ClientStatus.IDLE
    data_size: int = 0
    last_train_round: int = 0
    local_loss: float = 0.0
    train_time: float = 0.0


@dataclass
class RoundResult:
    """
    单轮训练结果

    Attributes:
        round_number: 轮次编号
        selected_clients: 参与本轮的客户端ID列表
        global_loss: 全局损失
        global_mse: 全局MSE
        communication_cost: 本轮通信开销(bytes)
        elapsed_time: 本轮耗时(秒)
    """
    round_number: int
    selected_clients: List[int]
    global_loss: float
    global_mse: float
    communication_cost: float
    elapsed_time: float


class FederatedClient:
    """
    联邦学习客户端

    封装本地数据、本地模型和训练逻辑
    """

    def __init__(
        self,
        client_id: int,
        train_data: np.ndarray,
        train_labels: np.ndarray,
        model_dim: int,
        learning_rate: float = 0.01,
        local_epochs: int = 5
    ):
        """
        初始化联邦学习客户端

        Args:
            client_id: 客户端唯一标识符
            train_data: 本地训练数据特征
            train_labels: 本地训练数据标签
            model_dim: 模型参数维度
            learning_rate: 学习率
            local_epochs: 本地训练轮数
        """
        self.client_id = client_id
        self.train_data = train_data
        self.train_labels = train_labels
        self.data_size = len(train_labels)
        self.model_dim = model_dim
        self.learning_rate = learning_rate
        self.local_epochs = local_epochs

        self.model_params = None
        self.status = ClientStatus.IDLE
        self.local_loss = 0.0
        self.train_time = 0.0

    def initialize_params(self, seed: int = 42):
        """
        初始化本地模型参数

        Args:
            seed: 随机种子
        """
        np.random.seed(seed + self.client_id)
        self.model_params = np.random.randn(self.model_dim) * np.sqrt(
            2.0 / self.model_dim
        )

    def receive_global_model(self, global_params: np.ndarray):
        """
        接收全局模型参数

        Args:
            global_params: 服务器下发的全局模型参数
        """
        self.model_params = global_params.copy()

    def local_train(self) -> Tuple[np.ndarray, float]:
        """
        执行本地训练

        Returns:
            (更新后的参数, 本地训练损失)
        """
        start_time = time.time()
        self.status = ClientStatus.TRAINING

        local_params = self.model_params.copy()
        n_samples = self.data_size

        for _ in range(self.local_epochs):
            # 前向传播
            predictions = self.train_data @ local_params
            # 计算损失
            loss = np.mean((predictions - self.train_labels) ** 2)
            # 计算梯度
            errors = predictions - self.train_labels
            gradients = (1.0 / n_samples) * (self.train_data.T @ errors)
            # 更新
            local_params = local_params - self.learning_rate * gradients

        self.model_params = local_params
        self.local_loss = loss
        self.train_time = time.time() - start_time
        self.status = ClientStatus.IDLE

        return local_params, loss

    def get_update(self) -> np.ndarray:
        """
        获取本地模型更新量

        Returns:
            模型参数更新量(新参数 - 旧参数)
        """
        # 返回更新量供服务器聚合
        return self.model_params

    def get_state(self) -> ClientState:
        """
        获取客户端状态快照

        Returns:
            客户端状态对象
        """
        return ClientState(
            client_id=self.client_id,
            status=self.status,
            data_size=self.data_size,
            local_loss=self.local_loss,
            train_time=self.train_time
        )


class FederatedSimulator:
    """
    联邦学习模拟器

    核心组件,管理多客户端的联邦学习训练流程
    """

    def __init__(
        self,
        clients: List[FederatedClient],
        aggregation_method: str = "fedavg",
        seed: int = 42
    ):
        """
        初始化模拟器

        Args:
            clients: 客户端列表
            aggregation_method: 聚合方法,"fedavg","fedprox","trimmed_mean"
            seed: 随机种子
        """
        self.clients = clients
        self.n_clients = len(clients)
        self.aggregation_method = aggregation_method
        self.seed = seed

        np.random.seed(seed)

        # 获取模型维度(假设所有客户端相同)
        self.model_dim = clients[0].model_dim

        # 初始化全局模型
        self.global_params = np.random.randn(self.model_dim) * np.sqrt(
            2.0 / self.model_dim
        )

        # 计算客户端权重(基于数据量)
        self.client_weights = [c.data_size for c in clients]
        total = sum(self.client_weights)
        self.client_weights = [w / total for w in self.client_weights]

        # 训练历史
        self.round_results: List[RoundResult] = []

        # 通信统计
        self.total_communication = 0.0

        # 客户端状态追踪
        self.client_states = {c.client_id: c.get_state() for c in clients}

    def select_clients(
        self,
        selection_ratio: float = 1.0,
        strategy: str = "random"
    ) -> List[int]:
        """
        选择参与本轮的客户端

        Args:
            selection_ratio: 选择比例
            strategy: 选择策略,"random"(随机),"sequential"(顺序),"adaptive"(自适应)

        Returns:
            被选中的客户端ID列表
        """
        n_selected = max(1, int(self.n_clients * selection_ratio))

        if strategy == "random":
            indices = np.random.choice(self.n_clients, n_selected, replace=False)
        elif strategy == "sequential":
            indices = list(range(n_selected))
        else:
            indices = np.random.choice(self.n_clients, n_selected, replace=False)

        return sorted(indices.tolist())

    def broadcast_to_clients(self, selected_ids: List[int]):
        """
        向选中的客户端广播全局模型

        Args:
            selected_ids: 选中的客户端ID列表
        """
        for client in self.clients:
            if client.client_id in selected_ids:
                client.receive_global_model(self.global_params)

    def aggregate_updates(
        self,
        client_updates: List[np.ndarray],
        selected_ids: List[int]
    ) -> np.ndarray:
        """
        聚合客户端更新

        Args:
            client_updates: 客户端更新列表
            selected_ids: 对应的客户端ID

        Returns:
            聚合后的更新
        """
        selected_weights = [self.client_weights[self.clients[i].client_id]
                           for i in range(len(self.clients))
                           if self.clients[i].client_id in selected_ids]

        # 归一化权重
        total = sum(selected_weights)
        normalized_weights = [w / total for w in selected_weights]

        aggregated = np.zeros_like(client_updates[0])
        for update, weight in zip(client_updates, normalized_weights):
            aggregated += weight * update

        return aggregated

    def run_round(
        self,
        selection_ratio: float = 1.0,
        selection_strategy: str = "random"
    ) -> RoundResult:
        """
        执行一轮联邦学习

        Args:
            selection_ratio: 客户端选择比例
            selection_strategy: 选择策略

        Returns:
            本轮结果
        """
        start_time = time.time()

        # 1. 选择客户端
        selected_ids = self.select_clients(selection_ratio, selection_strategy)
        selected_clients = [c for c in self.clients if c.client_id in selected_ids]

        # 2. 广播全局模型
        self.broadcast_to_clients(selected_ids)

        # 3. 本地训练
        client_updates = []
        for client in selected_clients:
            update, loss = client.local_train()
            client_updates.append(update)

        # 4. 聚合
        aggregated_update = self.aggregate_updates(client_updates, selected_ids)
        self.global_params = self.global_params + aggregated_update

        # 5. 更新状态
        for client in selected_clients:
            client.last_train_round = len(self.round_results) + 1

        elapsed = time.time() - start_time

        # 6. 估算通信开销
        # 假设每个参数为float64(8 bytes),上传和下载各一次
        param_bytes = self.model_dim * 8
        communication = len(selected_ids) * 2 * param_bytes
        self.total_communication += communication

        result = RoundResult(
            round_number=len(self.round_results) + 1,
            selected_clients=selected_ids,
            global_loss=np.mean([c.local_loss for c in selected_clients]),
            global_mse=0.0,
            communication_cost=communication,
            elapsed_time=elapsed
        )

        self.round_results.append(result)

        return result

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

    def train(
        self,
        n_rounds: int,
        selection_ratio: float = 1.0,
        selection_strategy: str = "random",
        test_data: np.ndarray = None,
        test_labels: np.ndarray = None,
        verbose: bool = True
    ) -> Dict:
        """
        运行完整训练流程

        Args:
            n_rounds: 训练轮数
            selection_ratio: 每轮选择比例
            selection_strategy: 选择策略
            test_data: 测试数据(可选)
            test_labels: 测试标签(可选)
            verbose: 是否打印进度

        Returns:
            训练历史
        """
        history = {
            "rounds": [],
            "global_loss": [],
            "global_mse": [],
            "communication_per_round": [],
            "elapsed_per_round": []
        }

        for round_idx in range(n_rounds):
            result = self.run_round(selection_ratio, selection_strategy)

            metrics = None
            if test_data is not None:
                metrics = self.evaluate(test_data, test_labels)

            history["rounds"].append(result.round_number)
            history["global_loss"].append(result.global_loss)
            history["global_mse"].append(metrics["mse"] if metrics else 0.0)
            history["communication_per_round"].append(result.communication_cost)
            history["elapsed_per_round"].append(result.elapsed_time)

            if verbose and (round_idx + 1) % 5 == 0:
                msg = f"轮次 {round_idx + 1}/{n_rounds} | 参与: {len(result.selected_clients)}"
                if metrics:
                    msg += f" | MSE: {metrics['mse']:.6f}"
                print(msg)

        history["total_communication"] = self.total_communication
        return history

    def get_communication_summary(self) -> Dict:
        """
        获取通信开销汇总

        Returns:
            通信统计字典
        """
        return {
            "total_bytes": self.total_communication,
            "total_mb": self.total_communication / (1024 ** 2),
            "avg_per_round": self.total_communication / len(self.round_results)
            if self.round_results else 0
        }


def create_fl_simulation(
    n_clients: int,
    model_dim: int,
    data_per_client: int,
    test_size: int,
    seed: int = 42
) -> Tuple[FederatedSimulator, np.ndarray, np.ndarray]:
    """
    创建联邦学习模拟场景

    Args:
        n_clients: 客户端数量
        model_dim: 模型维度
        data_per_client: 每客户端数据量
        test_size: 测试集大小
        seed: 随机种子

    Returns:
        (模拟器, 测试数据, 测试标签)
    """
    np.random.seed(seed)

    w_true = np.random.randn(model_dim) * 0.5

    clients = []
    for i in range(n_clients):
        noise_scale = 0.1 + 0.2 * (i / n_clients)
        X = np.random.randn(data_per_client, model_dim)
        y = X @ w_true + np.random.randn(data_per_client) * noise_scale

        client = FederatedClient(
            client_id=i,
            train_data=X,
            train_labels=y,
            model_dim=model_dim,
            learning_rate=0.1,
            local_epochs=5
        )
        client.initialize_params(seed)
        clients.append(client)

    X_test = np.random.randn(test_size, model_dim)
    y_test = X_test @ w_true + np.random.randn(test_size) * 0.1

    simulator = FederatedSimulator(clients, aggregation_method="fedavg", seed=seed)

    return simulator, X_test, y_test


if __name__ == "__main__":
    print("=" * 60)
    print("联邦学习模拟器演示")
    print("=" * 60)

    # 创建模拟
    simulator, X_test, y_test = create_fl_simulation(
        n_clients=10,
        model_dim=20,
        data_per_client=200,
        test_size=500,
        seed=42
    )

    print(f"创建了 {simulator.n_clients} 个客户端")
    print(f"客户端权重: {[f'{w:.3f}' for w in simulator.client_weights]}")

    # 运行训练
    history = simulator.train(
        n_rounds=20,
        selection_ratio=0.6,
        selection_strategy="random",
        test_data=X_test,
        test_labels=y_test,
        verbose=True
    )

    # 通信开销统计
    comm_summary = simulator.get_communication_summary()
    print("\n" + "=" * 60)
    print("通信开销汇总:")
    print(f"  总通信: {comm_summary['total_mb']:.4f} MB")
    print(f"  平均每轮: {comm_summary['avg_per_round'] / 1024:.2f} KB")
    print("=" * 60)
