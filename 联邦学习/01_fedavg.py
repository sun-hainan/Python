# -*- coding: utf-8 -*-
"""
算法实现：联邦学习 / 01_fedavg

本文件实现 01_fedavg 相关的算法功能。
"""

import numpy as np
from typing import List, Dict, Callable, Tuple


def initialize_model_params(model_dim: int, seed: int = 42) -> np.ndarray:
    """
    初始化模型参数(权重向量)

    Args:
        model_dim: 模型参数维度
        seed: 随机种子,保证实验可复现性

    Returns:
        初始化后的模型参数向量
    """
    np.random.seed(seed)
    # 使用Xavier初始化,适合sigmoid/tanh激活函数
    params = np.random.randn(model_dim) * np.sqrt(2.0 / model_dim)
    return params


def local_train(
    params: np.ndarray,
    train_data: np.ndarray,
    train_labels: np.ndarray,
    local_epochs: int,
    learning_rate: float = 0.01
) -> np.ndarray:
    """
    客户端本地训练函数 - 使用梯度下降法

    使用随机梯度下降(SGD)进行本地模型更新,
    模拟客户端使用私有数据训练的过程。

    Args:
        params: 当前全局模型参数
        train_data: 本地训练数据特征,shape为(n_samples, n_features)
        train_labels: 本地训练数据标签,shape为(n_samples,)
        local_epochs: 本地训练轮数
        learning_rate: 学习率,控制每步更新幅度

    Returns:
        更新后的本地模型参数
    """
    local_params = params.copy()
    n_samples = len(train_labels)

    for _ in range(local_epochs):
        # 前向传播:计算预测值
        # 使用线性模型: y = X @ w + b (简化为无偏置项)
        predictions = train_data @ local_params

        # 计算均方误差损失函数的梯度
        # Loss = (1/2n) * sum((y_pred - y_true)^2)
        # dLoss/dw = (1/n) * X.T @ (predictions - labels)
        errors = predictions - train_labels
        gradients = (1.0 / n_samples) * (train_data.T @ errors)

        # 梯度下降更新参数
        local_params = local_params - learning_rate * gradients

    return local_params


def federated_averaging(
    client_params_list: List[np.ndarray],
    client_weights: List[float] = None
) -> np.ndarray:
    """
    联邦平均聚合函数 - 对客户端模型参数进行加权平均

    FedAvg的核心步骤:根据各客户端的数据量权重,
    对本地训练后的模型参数进行聚合,得到新的全局模型。

    Args:
        client_params_list: 各客户端上传的模型参数列表
        client_weights: 各客户端的权重,默认为数据量权重(样本数量)

    Returns:
        聚合后的全局模型参数
    """
    n_clients = len(client_params_list)

    # 默认权重为等权重
    if client_weights is None:
        client_weights = [1.0 / n_clients] * n_clients

    # 归一化权重,确保和为1
    total_weight = sum(client_weights)
    normalized_weights = [w / total_weight for w in client_weights]

    # 加权求和聚合参数
    global_params = np.zeros_like(client_params_list[0])
    for params, weight in zip(client_params_list, normalized_weights):
        global_params += weight * params

    return global_params


def evaluate_model(
    params: np.ndarray,
    test_data: np.ndarray,
    test_labels: np.ndarray
) -> Dict[str, float]:
    """
    评估全局模型性能

    使用均方误差(MSE)和均方根误差(RMSE)评估模型预测效果。

    Args:
        params: 待评估的模型参数
        test_data: 测试数据特征
        test_labels: 测试数据标签

    Returns:
        包含MSE和RMSE的字典
    """
    predictions = test_data @ params
    mse = np.mean((predictions - test_labels) ** 2)
    rmse = np.sqrt(mse)
    return {"mse": mse, "rmse": rmse}


def simulate_federated_round(
    global_params: np.ndarray,
    client_data_list: List[Tuple[np.ndarray, np.ndarray]],
    client_weights: List[float],
    local_epochs: int,
    learning_rate: float
) -> Tuple[np.ndarray, List[float]]:
    """
    模拟一轮联邦学习通信

    完整的一轮通信包括:
    1. 服务器将全局参数分发给各客户端
    2. 各客户端使用本地数据训练并更新参数
    3. 各客户端上传更新后的参数
    4. 服务器进行FedAvg聚合得到新全局参数

    Args:
        global_params: 当前全局模型参数
        client_data_list: 各客户端的(data, labels)元组列表
        client_weights: 各客户端权重(基于数据量)
        local_epochs: 每轮本地训练epoch数
        learning_rate: 学习率

    Returns:
        (新全局参数, 各客户端本轮损失值列表)
    """
    updated_params_list = []
    losses = []

    # 步骤1&2: 各客户端本地训练
    for data, labels in client_data_list:
        # 本地训练得到更新后的参数
        updated_params = local_train(
            global_params, data, labels, local_epochs, learning_rate
        )
        updated_params_list.append(updated_params)

        # 计算本地训练后的损失(用于监控)
        predictions = data @ updated_params
        loss = np.mean((predictions - labels) ** 2)
        losses.append(loss)

    # 步骤3&4: 联邦平均聚合
    new_global_params = federated_averaging(updated_params_list, client_weights)

    return new_global_params, losses


def run_federated_learning(
    n_clients: int,
    model_dim: int,
    n_rounds: int,
    local_epochs: int,
    learning_rate: float,
    data_per_client: int = 100,
    test_size: int = 500,
    seed: int = 42
) -> Dict:
    """
    运行完整的联邦学习训练流程

    端到端模拟联邦学习系统,包括:
    - 生成模拟数据(模拟各客户端的非IID数据分布)
    - 初始化全局模型
    - 多轮联邦通信训练
    - 最终评估

    Args:
        n_clients: 客户端数量
        model_dim: 模型参数维度
        n_rounds: 联邦通信轮数
        local_epochs: 每轮本地训练epoch数
        learning_rate: 学习率
        data_per_client: 每个客户端的数据量
        test_size: 测试集大小
        seed: 随机种子

    Returns:
        包含训练过程历史和最终结果的字典
    """
    np.random.seed(seed)

    # 生成模拟数据: y = X @ w_true + noise
    # 模拟各客户端数据分布偏移(non-IID)的场景
    w_true = np.random.randn(model_dim) * 0.5

    client_data_list = []
    client_weights = []

    for i in range(n_clients):
        # 每个客户端有不同的数据分布(通过不同的noise scale体现)
        noise_scale = 0.1 + 0.2 * (i / n_clients)
        X = np.random.randn(data_per_client, model_dim)
        y = X @ w_true + np.random.randn(data_per_client) * noise_scale
        client_data_list.append((X, y))
        client_weights.append(float(data_per_client))

    # 测试集
    X_test = np.random.randn(test_size, model_dim)
    y_test = X_test @ w_true + np.random.randn(test_size) * 0.1

    # 初始化全局模型
    global_params = initialize_model_params(model_dim, seed)

    # 训练历史记录
    history = {
        "rounds": [],
        "global_mse": [],
        "avg_local_loss": []
    }

    # 联邦学习主循环
    for round_idx in range(n_rounds):
        # 执行一轮联邦学习
        global_params, local_losses = simulate_federated_round(
            global_params,
            client_data_list,
            client_weights,
            local_epochs,
            learning_rate
        )

        # 评估全局模型
        metrics = evaluate_model(global_params, X_test, y_test)

        # 记录历史
        history["rounds"].append(round_idx + 1)
        history["global_mse"].append(metrics["mse"])
        history["avg_local_loss"].append(np.mean(local_losses))

        # 每5轮输出一次进度
        if (round_idx + 1) % 5 == 0 or round_idx == 0:
            print(f"轮次 {round_idx + 1}/{n_rounds} | "
                  f"全局MSE: {metrics['mse']:.6f} | "
                  f"平均本地损失: {np.mean(local_losses):.6f}")

    return {
        "final_params": global_params,
        "history": history,
        "true_params": w_true
    }


if __name__ == "__main__":
    # 运行联邦学习模拟
    print("=" * 60)
    print("联邦学习 - FedAvg 算法演示")
    print("=" * 60)

    # 模拟配置
    result = run_federated_learning(
        n_clients=5,          # 5个客户端
        model_dim=10,         # 模型参数维度10
        n_rounds=20,          # 20轮通信
        local_epochs=5,       # 每轮本地训练5个epoch
        learning_rate=0.1,    # 学习率0.1
        data_per_client=200,  # 每客户端200条数据
        test_size=500,        # 测试集500条
        seed=42
    )

    print("\n" + "=" * 60)
    print("训练完成!")
    print(f"最终测试MSE: {result['history']['global_mse'][-1]:.6f}")
    print(f"最终测试RMSE: {np.sqrt(result['history']['global_mse'][-1]):.6f}")
    print("=" * 60)
