# -*- coding: utf-8 -*-
"""
算法实现：联邦学习 / 18_fl_benchmark

本文件实现 18_fl_benchmark 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Dict, Callable
from abc import ABC, abstractmethod


class FederatedAlgorithm(ABC):
    """联邦学习算法抽象基类"""

    @abstractmethod
    def __init__(self, config: Dict):
        """初始化算法"""
        pass

    @abstractmethod
    def local_train(
        self,
        params: np.ndarray,
        data: np.ndarray,
        labels: np.ndarray,
        **kwargs
    ) -> np.ndarray:
        """本地训练"""
        pass

    @abstractmethod
    def aggregate(
        self,
        client_params_list: List[np.ndarray],
        client_weights: List[float],
        **kwargs
    ) -> np.ndarray:
        """聚合"""
        pass


class FedSGD(FederatedAlgorithm):
    """
    FedSGD - 联邦随机梯度下降

    每轮通信中,每个客户端执行一次本地梯度下降,
    然后服务器立即聚合(无本地多轮迭代)。

    特点:
    - 通信频繁,但每次通信量小
    - 收敛速度快,但通信成本高
    """

    def __init__(self, config: Dict):
        self.lr = config.get("learning_rate", 0.01)

    def local_train(
        self,
        params: np.ndarray,
        data: np.ndarray,
        labels: np.ndarray,
        **kwargs
    ) -> np.ndarray:
        """执行一次本地SGD"""
        n_samples = len(labels)
        predictions = data @ params
        errors = predictions - labels
        gradients = (1.0 / n_samples) * (data.T @ errors)
        new_params = params - self.lr * gradients
        return new_params

    def aggregate(
        self,
        client_params_list: List[np.ndarray],
        client_weights: List[float],
        **kwargs
    ) -> np.ndarray:
        """加权平均聚合"""
        total_weight = sum(client_weights)
        normalized_weights = [w / total_weight for w in client_weights]
        aggregated = np.zeros_like(client_params_list[0])
        for params, weight in zip(client_params_list, normalized_weights):
            aggregated += weight * params
        return aggregated


class FedAvg(FederatedAlgorithm):
    """
    FedAvg - 联邦平均

    McMahan et al., 2017
    每轮通信中,每个客户端执行多轮本地梯度下降,
    然后服务器聚合模型参数。
    """

    def __init__(self, config: Dict):
        self.lr = config.get("learning_rate", 0.01)
        self.local_epochs = config.get("local_epochs", 5)

    def local_train(
        self,
        params: np.ndarray,
        data: np.ndarray,
        labels: np.ndarray,
        **kwargs
    ) -> np.ndarray:
        """执行多轮本地训练"""
        local_params = params.copy()
        n_samples = len(labels)

        for _ in range(self.local_epochs):
            predictions = data @ local_params
            errors = predictions - labels
            gradients = (1.0 / n_samples) * (data.T @ errors)
            local_params = local_params - self.lr * gradients

        return local_params

    def aggregate(
        self,
        client_params_list: List[np.ndarray],
        client_weights: List[float],
        **kwargs
    ) -> np.ndarray:
        """加权平均聚合"""
        total_weight = sum(client_weights)
        normalized_weights = [w / total_weight for w in client_weights]
        aggregated = np.zeros_like(client_params_list[0])
        for params, weight in zip(client_params_list, normalized_weights):
            aggregated += weight * params
        return aggregated


class FedProx(FederatedAlgorithm):
    """
    FedProx - 带近端正则化的联邦平均

    Li et al., 2020
    在FedAvg基础上添加近端项,解决数据异构性问题。
    """

    def __init__(self, config: Dict):
        self.lr = config.get("learning_rate", 0.01)
        self.local_epochs = config.get("local_epochs", 5)
        self.mu = config.get("mu", 0.01)

    def local_train(
        self,
        params: np.ndarray,
        data: np.ndarray,
        labels: np.ndarray,
        global_params: np.ndarray = None,
        **kwargs
    ) -> np.ndarray:
        """执行带近端正则化的本地训练"""
        if global_params is None:
            global_params = params

        local_params = params.copy()
        n_samples = len(labels)

        for _ in range(self.local_epochs):
            predictions = data @ local_params
            errors = predictions - labels
            data_grad = (1.0 / n_samples) * (data.T @ errors)
            prox_grad = self.mu * (local_params - global_params)
            total_grad = data_grad + prox_grad
            local_params = local_params - self.lr * total_grad

        return local_params

    def aggregate(
        self,
        client_params_list: List[np.ndarray],
        client_weights: List[float],
        **kwargs
    ) -> np.ndarray:
        """加权平均聚合"""
        total_weight = sum(client_weights)
        normalized_weights = [w / total_weight for w in client_weights]
        aggregated = np.zeros_like(client_params_list[0])
        for params, weight in zip(client_params_list, normalized_weights):
            aggregated += weight * params
        return aggregated


class BenchmarkRunner:
    """
    联邦学习基准测试运行器

    提供统一的接口来运行和比较不同算法
    """

    def __init__(self, algorithms: Dict[str, FederatedAlgorithm]):
        """
        初始化运行器

        Args:
            algorithms: 算法名称到算法实例的映射
        """
        self.algorithms = algorithms
        self.results = {}

    def run_single_algorithm(
        self,
        name: str,
        algorithm: FederatedAlgorithm,
        client_data_list: List[Tuple[np.ndarray, np.ndarray]],
        client_weights: List[float],
        n_rounds: int,
        test_data: np.ndarray = None,
        test_labels: np.ndarray = None,
        verbose: bool = True
    ) -> Dict:
        """
        运行单个算法

        Args:
            name: 算法名称
            algorithm: 算法实例
            client_data_list: 客户端数据列表
            client_weights: 客户端权重
            n_rounds: 训练轮数
            test_data: 测试数据
            test_labels: 测试标签
            verbose: 是否打印进度

        Returns:
            训练历史
        """
        # 初始化全局参数
        dim = client_data_list[0][0].shape[1]
        global_params = np.random.randn(dim) * np.sqrt(2.0 / dim)

        history = {
            "rounds": [],
            "test_mse": [] if test_data is not None else None,
            "test_accuracy": [] if test_labels is not None else None
        }

        for round_idx in range(n_rounds):
            client_updates = []

            # 本地训练
            for data, labels in client_data_list:
                if name == "FedProx":
                    updated = algorithm.local_train(
                        global_params, data, labels, global_params=global_params
                    )
                else:
                    updated = algorithm.local_train(global_params, data, labels)
                client_updates.append(updated)

            # 聚合
            global_params = algorithm.aggregate(client_updates, client_weights)

            # 评估
            if test_data is not None:
                predictions = test_data @ global_params
                mse = np.mean((predictions - test_labels) ** 2)
                history["test_mse"].append(mse)

            history["rounds"].append(round_idx + 1)

            if verbose and (round_idx + 1) % 5 == 0:
                msg = f"{name} 轮次 {round_idx + 1}/{n_rounds}"
                if test_data is not None:
                    msg += f" | MSE: {mse:.6f}"
                print(f"   {msg}")

        return history

    def run_all(
        self,
        client_data_list: List[Tuple[np.ndarray, np.ndarray]],
        client_weights: List[float],
        n_rounds: int,
        test_data: np.ndarray = None,
        test_labels: np.ndarray = None
    ) -> Dict:
        """
        运行所有算法并比较

        Args:
            client_data_list: 客户端数据
            client_weights: 客户端权重
            n_rounds: 训练轮数
            test_data: 测试数据
            test_labels: 测试标签

        Returns:
            各算法的结果字典
        """
        results = {}

        for name, algorithm in self.algorithms.items():
            print(f"\n运行 {name}...")
            history = self.run_single_algorithm(
                name, algorithm, client_data_list, client_weights,
                n_rounds, test_data, test_labels
            )
            results[name] = history

        return results


def run_benchmark():
    """运行基准测试"""

    print("=" * 60)
    print("联邦学习基准算法测试")
    print("=" * 60)

    np.random.seed(42)

    # 配置
    n_clients = 5
    model_dim = 10
    n_rounds = 20
    data_per_client = 200
    test_size = 500

    # 生成数据
    w_true = np.random.randn(model_dim) * 0.5

    client_data_list = []
    client_weights = []

    for i in range(n_clients):
        noise_scale = 0.1 + 0.2 * (i / n_clients)
        X = np.random.randn(data_per_client, model_dim)
        y = X @ w_true + np.random.randn(data_per_client) * noise_scale
        client_data_list.append((X, y))
        client_weights.append(float(data_per_client))

    X_test = np.random.randn(test_size, model_dim)
    y_test = X_test @ w_true + np.random.randn(test_size) * 0.1

    # 创建算法
    algorithms = {
        "FedSGD": FedSGD({"learning_rate": 0.1}),
        "FedAvg": FedAvg({"learning_rate": 0.1, "local_epochs": 5}),
        "FedProx": FedProx({"learning_rate": 0.1, "local_epochs": 5, "mu": 0.1}),
    }

    # 运行基准测试
    runner = BenchmarkRunner(algorithms)
    results = runner.run_all(
        client_data_list, client_weights, n_rounds,
        X_test, y_test
    )

    # 汇总结果
    print("\n" + "=" * 60)
    print("基准测试结果汇总")
    print("=" * 60)
    print(f"{'算法':<12} {'初始MSE':<15} {'最终MSE':<15} {'提升':<10}")
    print("-" * 60)

    for name, history in results.items():
        initial_mse = history["test_mse"][0]
        final_mse = history["test_mse"][-1]
        improvement = (initial_mse - final_mse) / initial_mse * 100
        print(f"{name:<12} {initial_mse:<15.6f} {final_mse:<15.6f} {improvement:>7.2f}%")


if __name__ == "__main__":
    run_benchmark()
