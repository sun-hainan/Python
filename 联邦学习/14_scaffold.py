# -*- coding: utf-8 -*-
"""
算法实现：联邦学习 / 14_scaffold

本文件实现 14_scaffold 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Dict


class SCAFFOLDClient:
    """SCAFFOLD客户端"""

    def __init__(self, client_id: int, train_data: np.ndarray, train_labels: np.ndarray):
        """初始化客户端"""
        self.client_id = client_id
        self.train_data = train_data
        self.train_labels = train_labels
        self.control_variable = None  # 控制变量c_i
        self.model_params = None

    def initialize(self, dim: int, seed: int = 42):
        """初始化参数"""
        np.random.seed(seed + self.client_id)
        self.model_params = np.random.randn(dim) * np.sqrt(2.0 / dim)
        self.control_variable = np.zeros(dim)

    def local_train(
        self,
        global_params: np.ndarray,
        global_control: np.ndarray,
        local_epochs: int,
        learning_rate: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        本地训练(带控制变量校正)

        目标: 最小化 L(w) - <c_i, w>

        Args:
            global_params: 全局模型参数
            global_control: 全局控制变量
            local_epochs: 本地训练轮数
            learning_rate: 学习率

        Returns:
            (更新后的模型参数, 更新后的控制变量)
        """
        local_params = global_params.copy()
        local_control = self.control_variable.copy()

        # 计算控制变量增量
        delta_c = np.zeros_like(global_params)

        n_samples = len(self.train_labels)

        for _ in range(local_epochs):
            # 前向传播
            predictions = self.train_data @ local_params
            errors = predictions - self.train_labels
            gradients = (1.0 / n_samples) * (self.train_data.T @ errors)

            # 校正梯度
            corrected_gradients = gradients - global_control + local_control

            # 更新
            local_params = local_params - learning_rate * corrected_gradients

            # 累积控制变量变化
            delta_c = delta_c + gradients

        # 更新控制变量
        delta_c = delta_c / (local_epochs * learning_rate)
        new_control = local_control - global_control + delta_c

        return local_params, new_control


class SCAFFOLDServer:
    """SCAFFOLD服务器"""

    def __init__(self, dim: int):
        """初始化服务器"""
        self.global_params = np.random.randn(dim) * np.sqrt(2.0 / dim)
        self.global_control = np.zeros(dim)

    def aggregate(
        self,
        client_params: List[np.ndarray],
        client_controls: List[np.ndarray],
        client_weights: List[float],
        client_data_sizes: List[int]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        聚合客户端更新

        Args:
            client_params: 客户端模型参数列表
            client_controls: 客户端控制变量列表
            client_weights: 客户端权重
            client_data_sizes: 客户端数据大小

        Returns:
            (新全局参数, 新全局控制变量)
        """
        total_weight = sum(client_weights)
        normalized_weights = [w / total_weight for w in client_weights]

        # 更新全局参数
        # w_g_new = sum(w_i * n_i) / sum(n_i)
        new_params = np.zeros_like(self.global_params)
        for params, weight in zip(client_params, normalized_weights):
            new_params += weight * params

        # 更新全局控制变量
        # c_g_new = c_g + sum(n_i / sum(n)) * (c_i - c_g) - sum(n_i / sum(n)) * (w_i - w_g) / (K * lr)
        # 简化版本
        new_control = np.zeros_like(self.global_control)
        for ctrl, weight in zip(client_controls, normalized_weights):
            new_control += weight * ctrl

        return new_params, new_control


def scaffold_federated_round(
    global_params: np.ndarray,
    global_control: np.ndarray,
    client_data_list: List[Tuple[np.ndarray, np.ndarray]],
    client_weights: List[float],
    local_epochs: int,
    learning_rate: float
) -> Tuple[np.ndarray, np.ndarray, List[Tuple[np.ndarray, np.ndarray]]]:
    """
    SCAFFOLD一轮

    Args:
        global_params: 当前全局参数
        global_control: 当前全局控制变量
        client_data_list: 客户端数据
        client_weights: 客户端权重
        local_epochs: 本地训练轮数
        learning_rate: 学习率

    Returns:
        (新全局参数, 新全局控制变量, 客户端结果列表)
    """
    dim = len(global_params)
    server = SCAFFOLDServer(dim)

    client_results = []

    for i, (data, labels) in enumerate(client_data_list):
        client = SCAFFOLDClient(i, data, labels)
        client.initialize(dim)

        # 如果已有控制变量,使用它
        if global_control is not None:
            client.control_variable = np.zeros(dim)  # 简化:每次重置

        # 本地训练
        new_params, new_control = client.local_train(
            global_params, global_control, local_epochs, learning_rate
        )

        client_results.append((new_params, new_control))

    # 分离参数和控制变量
    client_params = [r[0] for r in client_results]
    client_controls = [r[1] for r in client_results]

    # 聚合
    new_params, new_control = server.aggregate(
        client_params, client_controls,
        client_weights, [len(d[1]) for d in client_data_list]
    )

    return new_params, new_control, client_results


def run_scaffold_fl(
    n_clients: int,
    model_dim: int,
    n_rounds: int,
    local_epochs: int,
    learning_rate: float,
    data_per_client: int = 100,
    test_size: int = 500,
    seed: int = 42
) -> Dict:
    """运行SCAFFOLD"""
    np.random.seed(seed)

    w_true = np.random.randn(model_dim) * 0.5

    client_data_list = []
    client_weights = []

    for i in range(n_clients):
        noise_scale = 0.1 + 0.3 * (i / n_clients)
        X = np.random.randn(data_per_client, model_dim)
        y = X @ w_true + np.random.randn(data_per_client) * noise_scale
        client_data_list.append((X, y))
        client_weights.append(float(data_per_client))

    X_test = np.random.randn(test_size, model_dim)
    y_test = X_test @ w_true + np.random.randn(test_size) * 0.1

    global_params = np.random.randn(model_dim) * np.sqrt(2.0 / model_dim)
    global_control = np.zeros(model_dim)

    history = {"rounds": [], "test_mse": []}

    print("SCAFFOLD联邦学习")

    for round_idx in range(n_rounds):
        global_params, global_control, _ = scaffold_federated_round(
            global_params, global_control, client_data_list,
            client_weights, local_epochs, learning_rate
        )

        predictions = X_test @ global_params
        mse = np.mean((predictions - y_test) ** 2)

        history["rounds"].append(round_idx + 1)
        history["test_mse"].append(mse)

        if (round_idx + 1) % 5 == 0 or round_idx == 0:
            print(f"轮次 {round_idx + 1}/{n_rounds} | MSE: {mse:.6f}")

    return {"final_params": global_params, "history": history}


if __name__ == "__main__":
    print("=" * 60)
    print("联邦学习 - SCAFFOLD算法演示")
    print("=" * 60)

    result = run_scaffold_fl(
        n_clients=5,
        model_dim=10,
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
