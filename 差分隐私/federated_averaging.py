# -*- coding: utf-8 -*-
"""
算法实现：差分隐私 / federated_averaging

本文件实现 federated_averaging 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple


class FederatedAveraging:
    """联邦平均算法"""

    def __init__(self, n_clients: int, model_size: int):
        """
        参数：
            n_clients: 客户端数量
            model_size: 模型参数量
        """
        self.n_clients = n_clients
        self.model_size = model_size
        self.global_model = np.random.randn(model_size)

    def distribute_model(self) -> np.ndarray:
        """
        分发全局模型

        返回：模型参数
        """
        return self.global_model.copy()

    def local_update(self, client_id: int,
                   local_data: np.ndarray,
                   n_epochs: int = 5) -> np.ndarray:
        """
        本地更新（简化）

        参数：
            client_id: 客户端ID
            local_data: 本地数据
            n_epochs: 本地训练轮数

        返回：更新后的模型
        """
        # 简化：用随机梯度代替真实训练
        local_model = self.global_model.copy()

        # 模拟训练
        for _ in range(n_epochs):
            # 随机梯度更新
            gradient = np.random.randn(self.model_size) * 0.01
            local_model -= gradient

        return local_model

    def aggregate(self, client_updates: List[np.ndarray],
                 client_weights: List[float] = None) -> np.ndarray:
        """
        聚合客户端更新

        参数：
            client_updates: 客户端更新列表
            client_weights: 客户端权重（默认相等）

        返回：新的全局模型
        """
        n_updates = len(client_updates)

        if client_weights is None:
            client_weights = [1.0 / n_updates] * n_updates

        # 加权平均
        new_model = np.zeros_like(self.global_model)

        for update, weight in zip(client_updates, client_weights):
            new_model += weight * update

        self.global_model = new_model

        return self.global_model

    def run_round(self, client_data: List[np.ndarray],
                 client_weights: List[float] = None,
                 n_epochs: int = 5) -> Tuple[np.ndarray, List[float]]:
        """
        运行一轮联邦学习

        参数：
            client_data: 各客户端数据
            client_weights: 权重

        返回：(新模型, 客户端损失列表)
        """
        # 分发模型
        global_model = self.distribute_model()

        # 本地更新
        client_updates = []

        for client_id, data in enumerate(client_data):
            local_model = self.local_update(client_id, data, n_epochs)
            client_updates.append(local_model)

        # 聚合
        self.aggregate(client_updates, client_weights)

        # 计算损失（简化）
        losses = [np.random.rand() for _ in range(self.n_clients)]

        return self.global_model, losses


def fedavg_analysis():
    """FedAvg分析"""
    print("=== FedAvg分析 ===")
    print()
    print("优点：")
    print("  - 保护数据隐私")
    print("  - 减少通信开销")
    print("  - 允许异构数据")
    print()
    print("挑战：")
    print("  - Non-IID数据分布")
    print("  - 通信效率")
    print("  - 模型收敛性")
    print()
    print("改进：")
    print("  - FedProx: 处理异构性")
    print("  - SCAFFOLD: 方差减少")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 联邦平均算法测试 ===\n")

    np.random.seed(42)

    # 设置
    n_clients = 5
    model_size = 10
    n_rounds = 3

    fedavg = FederatedAveraging(n_clients, model_size)

    print(f"客户端数: {n_clients}")
    print(f"模型大小: {model_size}")
    print(f"训练轮数: {n_rounds}")
    print()

    # 模拟数据
    client_data = [np.random.randn(100, model_size) for _ in range(n_clients)]

    # 运行联邦学习
    for round in range(n_rounds):
        global_model, losses = fedavg.run_round(client_data, n_epochs=2)

        avg_loss = np.mean(losses)
        print(f"轮 {round+1}: 全局模型范数={np.linalg.norm(global_model):.2f}, 平均损失={avg_loss:.4f}")

    print()
    fedavg_analysis()

    print()
    print("说明：")
    print("  - FedAvg是联邦学习的核心算法")
    print("  - Google将其用于Gboard")
    print("  - 与差分隐私结合可以保护隐私")
