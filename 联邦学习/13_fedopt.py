# -*- coding: utf-8 -*-

"""

算法实现：联邦学习 / 13_fedopt



本文件实现 13_fedopt 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict

from abc import ABC, abstractmethod





class ServerOptimizer(ABC):

    """服务器端优化器抽象基类"""



    @abstractmethod

    def update(self, global_params: np.ndarray, update_direction: np.ndarray) -> np.ndarray:

        """更新全局参数"""

        pass





class FedAvgOptimizer(ServerOptimizer):

    """标准FedAvg优化器(作为基线)"""



    def update(self, global_params: np.ndarray, update_direction: np.ndarray) -> np.ndarray:

        """简单的参数更新"""

        return global_params + update_direction





class FedAdamOptimizer(ServerOptimizer):

    """

    FedAdam优化器



    使用动量和自适应学习率:

    m_t = beta1 * m_{t-1} + (1-beta1) * g_t

    v_t = beta2 * v_{t-1} + (1-beta2) * g_t^2

    theta_t = theta_{t-1} - lr * m_t / (sqrt(v_t) + eps)

    """



    def __init__(

        self,

        lr: float = 0.01,

        beta1: float = 0.9,

        beta2: float = 0.99,

        eps: float = 1e-8

    ):

        """初始化FedAdam"""

        self.lr = lr

        self.beta1 = beta1

        self.beta2 = beta2

        self.eps = eps

        self.m = None  # 一阶矩估计

        self.v = None  # 二阶矩估计

        self.t = 0     # 时间步



    def update(self, global_params: np.ndarray, update_direction: np.ndarray) -> np.ndarray:

        """FedAdam更新"""

        self.t += 1



        # 初始化动量

        if self.m is None:

            self.m = np.zeros_like(update_direction)

        if self.v is None:

            self.v = np.zeros_like(update_direction)



        # 更新一阶矩和二阶矩

        self.m = self.beta1 * self.m + (1 - self.beta1) * update_direction

        self.v = self.beta2 * self.v + (1 - self.beta2) * (update_direction ** 2)



        # 偏差校正

        m_hat = self.m / (1 - self.beta1 ** self.t)

        v_hat = self.v / (1 - self.beta2 ** self.t)



        # 参数更新

        new_params = global_params - self.lr * m_hat / (np.sqrt(v_hat) + self.eps)



        return new_params





class FedAdagradOptimizer(ServerOptimizer):

    """

    FedAdagrad优化器



    自适应学习率,累积历史梯度平方:

    v_t = v_{t-1} + g_t^2

    theta_t = theta_{t-1} - lr * g_t / (sqrt(v_t) + eps)

    """



    def __init__(self, lr: float = 0.01, eps: float = 1e-8):

        """初始化FedAdagrad"""

        self.lr = lr

        self.eps = eps

        self.v = None  # 累积梯度平方



    def update(self, global_params: np.ndarray, update_direction: np.ndarray) -> np.ndarray:

        """FedAdagrad更新"""

        if self.v is None:

            self.v = np.zeros_like(update_direction)



        # 累积梯度平方

        self.v += update_direction ** 2



        # 参数更新

        new_params = global_params - self.lr * update_direction / (np.sqrt(self.v) + self.eps)



        return new_params





class FedYogiOptimizer(ServerOptimizer):

    """

    FedYogi优化器



    改进的二阶矩估计:

    v_t = v_{t-1} - (1-beta2) * v_{t-1} * g_t^2 * sign(v_{t-1} - g_t^2) / (v_{t-1} + g_t^2)

    """



    def __init__(

        self,

        lr: float = 0.01,

        beta1: float = 0.9,

        beta2: float = 0.99,

        eps: float = 1e-8

    ):

        """初始化FedYogi"""

        self.lr = lr

        self.beta1 = beta1

        self.beta2 = beta2

        self.eps = eps

        self.m = None

        self.v = None

        self.t = 0



    def update(self, global_params: np.ndarray, update_direction: np.ndarray) -> np.ndarray:

        """FedYogi更新"""

        self.t += 1



        if self.m is None:

            self.m = np.zeros_like(update_direction)

        if self.v is None:

            self.v = np.zeros_like(update_direction)



        # 一阶矩更新

        self.m = self.beta1 * self.m + (1 - self.beta1) * update_direction



        # Yogi二阶矩更新

        g_squared = update_direction ** 2

        sign = np.sign(self.v - g_squared)

        self.v = self.v - (1 - self.beta2) * self.v * g_squared * sign / (self.v + g_squared + self.eps)



        # 偏差校正

        m_hat = self.m / (1 - self.beta1 ** self.t)

        v_hat = np.abs(self.v) / (1 - self.beta2 ** self.t)



        # 参数更新

        new_params = global_params - self.lr * m_hat / (np.sqrt(v_hat) + self.eps)



        return new_params





def local_train(

    params: np.ndarray,

    train_data: np.ndarray,

    train_labels: np.ndarray,

    local_epochs: int,

    learning_rate: float = 0.01

) -> np.ndarray:

    """本地训练"""

    local_params = params.copy()

    n_samples = len(train_labels)



    for _ in range(local_epochs):

        predictions = train_data @ local_params

        errors = predictions - train_labels

        gradients = (1.0 / n_samples) * (train_data.T @ errors)

        local_params = local_params - learning_rate * gradients



    return local_params





def federated_opt_round(

    global_params: np.ndarray,

    client_data_list: List[Tuple[np.ndarray, np.ndarray]],

    client_weights: List[float],

    local_epochs: int,

    learning_rate: float,

    optimizer: ServerOptimizer

) -> np.ndarray:

    """

    联邦优化一轮



    Args:

        global_params: 当前全局参数

        client_data_list: 客户端数据

        client_weights: 客户端权重

        local_epochs: 本地训练轮数

        learning_rate: 学习率

        optimizer: 服务器优化器



    Returns:

        新全局参数

    """

    n_clients = len(client_data_list)

    total_weight = sum(client_weights)

    normalized_weights = [w / total_weight for w in client_weights]



    # 本地训练

    client_updates = []

    for data, labels in client_data_list:

        local_params = local_train(global_params, data, labels, local_epochs, learning_rate)

        update = local_params - global_params

        client_updates.append(update)



    # 计算加权平均更新方向

    update_direction = np.zeros_like(global_params)

    for update, weight in zip(client_updates, normalized_weights):

        update_direction += weight * update



    # 使用优化器更新

    new_params = optimizer.update(global_params, update_direction)



    return new_params





def run_federated_opt(

    n_clients: int,

    model_dim: int,

    n_rounds: int,

    local_epochs: int,

    learning_rate: float,

    optimizer_type: str = "adam",

    data_per_client: int = 100,

    test_size: int = 500,

    seed: int = 42

) -> Dict:

    """运行联邦优化"""

    np.random.seed(seed)



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



    global_params = np.random.randn(model_dim) * np.sqrt(2.0 / model_dim)



    # 选择优化器

    if optimizer_type == "adam":

        optimizer = FedAdamOptimizer(lr=learning_rate)

    elif optimizer_type == "adagrad":

        optimizer = FedAdagradOptimizer(lr=learning_rate)

    elif optimizer_type == "yogi":

        optimizer = FedYogiOptimizer(lr=learning_rate)

    else:

        optimizer = FedAvgOptimizer()



    history = {"rounds": [], "test_mse": []}



    print(f"联邦优化: {optimizer_type.upper()}")



    for round_idx in range(n_rounds):

        global_params = federated_opt_round(

            global_params, client_data_list, client_weights,

            local_epochs, learning_rate, optimizer

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

    print("联邦学习 - FedOpt自适应优化器演示")

    print("=" * 60)



    optimizers = ["adam", "adagrad", "yogi", "avg"]



    for opt in optimizers:

        print(f"\n--- {opt.upper()} ---")

        result = run_federated_opt(

            n_clients=5,

            model_dim=10,

            n_rounds=20,

            local_epochs=5,

            learning_rate=0.1,

            optimizer_type=opt,

            data_per_client=200,

            test_size=500,

            seed=42

        )

        print(f"最终MSE: {result['history']['test_mse'][-1]:.6f}")



    print("\n" + "=" * 60)

