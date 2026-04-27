# -*- coding: utf-8 -*-

"""

算法实现：联邦学习 / 02_fedprox



本文件实现 02_fedprox 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict





def local_train_prox(

    global_params: np.ndarray,

    train_data: np.ndarray,

    train_labels: np.ndarray,

    local_epochs: int,

    learning_rate: float,

    mu: float = 0.01

) -> np.ndarray:

    """

    FedProx本地训练 - 带近端正则化的梯度下降



    目标函数: L_local(w) = L_data(w) + (mu/2) * ||w - w_global||^2



    梯度: grad = grad_data + mu * (w - w_global)



    Args:

        global_params: 当前全局模型参数(近端项的参考点)

        train_data: 本地训练数据特征

        train_labels: 本地训练数据标签

        local_epochs: 本地训练轮数

        learning_rate: 学习率

        mu: 正则化系数,控制近端项权重



    Returns:

        更新后的本地模型参数

    """

    local_params = global_params.copy()

    n_samples = len(train_labels)



    for _ in range(local_epochs):

        # 计算数据损失项的梯度: (1/n) * X.T @ (X @ w - y)

        predictions = train_data @ local_params

        data_errors = predictions - train_labels

        data_gradients = (1.0 / n_samples) * (train_data.T @ data_errors)



        # 计算近端项的梯度: mu * (w - w_global)

        prox_gradients = mu * (local_params - global_params)



        # 合并梯度

        total_gradients = data_gradients + prox_gradients



        # 梯度下降更新

        local_params = local_params - learning_rate * total_gradients



    return local_params





def federated_prox(

    client_params_list: List[np.ndarray],

    client_weights: List[float] = None

) -> np.ndarray:

    """

    FedProx聚合函数 - 与FedAvg相同的加权平均



    Args:

        client_params_list: 各客户端上传的模型参数列表

        client_weights: 各客户端权重



    Returns:

        聚合后的全局模型参数

    """

    n_clients = len(client_params_list)



    if client_weights is None:

        client_weights = [1.0 / n_clients] * n_clients



    total_weight = sum(client_weights)

    normalized_weights = [w / total_weight for w in client_weights]



    global_params = np.zeros_like(client_params_list[0])

    for params, weight in zip(client_params_list, normalized_weights):

        global_params += weight * params



    return global_params





def compute_drift(

    local_params: np.ndarray,

    global_params: np.ndarray

) -> float:

    """

    计算本地参数与全局参数的漂移量(drift)



    漂移量是衡量FedProx近端项作用效果的指标,

    漂移越小说明本地更新越保守。



    Args:

        local_params: 本地模型参数

        global_params: 全局模型参数



    Returns:

        漂移量的L2范数

    """

    return np.linalg.norm(local_params - global_params)





def evaluate_model(

    params: np.ndarray,

    test_data: np.ndarray,

    test_labels: np.ndarray

) -> Dict[str, float]:

    """

    评估全局模型性能



    Args:

        params: 待评估的模型参数

        test_data: 测试数据特征

        test_labels: 测试数据标签



    Returns:

        包含MSE和RMSE的字典

    """

    predictions = test_data @ params

    mse = np.mean((predictions - test_labels) ** 2)

    return {"mse": mse, "rmse": np.sqrt(mse)}





def run_federated_prox(

    n_clients: int,

    model_dim: int,

    n_rounds: int,

    local_epochs: int,

    learning_rate: float,

    mu: float = 0.1,

    data_per_client: int = 100,

    test_size: int = 500,

    seed: int = 42

) -> Dict:

    """

    运行完整的FedProx训练流程



    Args:

        n_clients: 客户端数量

        model_dim: 模型参数维度

        n_rounds: 联邦通信轮数

        local_epochs: 每轮本地训练epoch数

        learning_rate: 学习率

        mu: 正则化系数

        data_per_client: 每个客户端的数据量

        test_size: 测试集大小

        seed: 随机种子



    Returns:

        包含训练过程历史和最终结果的字典

    """

    np.random.seed(seed)



    # 生成模拟数据

    w_true = np.random.randn(model_dim) * 0.5



    client_data_list = []

    client_weights = []



    for i in range(n_clients):

        # 模拟non-IID数据分布

        noise_scale = 0.1 + 0.3 * (i / n_clients)

        X = np.random.randn(data_per_client, model_dim)

        y = X @ w_true + np.random.randn(data_per_client) * noise_scale

        client_data_list.append((X, y))

        client_weights.append(float(data_per_client))



    # 测试集

    X_test = np.random.randn(test_size, model_dim)

    y_test = X_test @ w_true + np.random.randn(test_size) * 0.1



    # 初始化全局模型

    global_params = np.random.randn(model_dim) * np.sqrt(2.0 / model_dim)



    history = {

        "rounds": [],

        "global_mse": [],

        "avg_drift": []

    }



    print(f"FedProx训练配置: mu={mu}, local_epochs={local_epochs}, "

          f"lr={learning_rate}")



    for round_idx in range(n_rounds):

        updated_params_list = []

        drifts = []



        # 本地训练

        for data, labels in client_data_list:

            updated_params = local_train_prox(

                global_params, data, labels,

                local_epochs, learning_rate, mu

            )

            updated_params_list.append(updated_params)

            drifts.append(compute_drift(updated_params, global_params))



        # 聚合

        global_params = federated_prox(updated_params_list, client_weights)



        # 评估

        metrics = evaluate_model(global_params, X_test, y_test)



        history["rounds"].append(round_idx + 1)

        history["global_mse"].append(metrics["mse"])

        history["avg_drift"].append(np.mean(drifts))



        if (round_idx + 1) % 5 == 0 or round_idx == 0:

            print(f"轮次 {round_idx + 1}/{n_rounds} | "

                  f"MSE: {metrics['mse']:.6f} | "

                  f"平均漂移: {np.mean(drifts):.6f}")



    return {"final_params": global_params, "history": history}





if __name__ == "__main__":

    print("=" * 60)

    print("联邦学习 - FedProx 正则化算法演示")

    print("=" * 60)



    result = run_federated_prox(

        n_clients=5,

        model_dim=10,

        n_rounds=20,

        local_epochs=5,

        learning_rate=0.1,

        mu=0.1,           # 近端正则化系数

        data_per_client=200,

        test_size=500,

        seed=42

    )



    print("\n" + "=" * 60)

    print("训练完成!")

    print(f"最终MSE: {result['history']['global_mse'][-1]:.6f}")

    print("=" * 60)

