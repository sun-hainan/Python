# -*- coding: utf-8 -*-

"""

算法实现：联邦学习 / 15_moon



本文件实现 15_moon 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict





def compute_cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:

    """计算余弦相似度"""

    norm_a = np.linalg.norm(a)

    norm_b = np.linalg.norm(b)

    if norm_a < 1e-10 or norm_b < 1e-10:

        return 0.0

    return np.dot(a, b) / (norm_a * norm_b)





def compute_representation(z: np.ndarray, dim: int) -> np.ndarray:

    """将参数映射到表示空间"""

    # 简化:直接使用参数作为表示

    return z / (np.linalg.norm(z) + 1e-10)





def moon_local_train(

    global_params: np.ndarray,

    prev_local_params: np.ndarray,  # 上一轮的本地模型

    train_data: np.ndarray,

    train_labels: np.ndarray,

    local_epochs: int,

    learning_rate: float,

    tau: float = 0.5,

    lambda_coef: float = 1.0

) -> np.ndarray:

    """

    MOON本地训练



    损失函数: L_local = L_task + lambda * L_contrast

    其中L_contrast = -log(exp(sim(z, z+)/tau)) / sum(exp(sim(z, z-)/tau))



    Args:

        global_params: 全局模型参数

        prev_local_params: 上一轮本地模型参数

        train_data: 本地训练数据

        train_labels: 本地训练标签

        local_epochs: 本地训练轮数

        learning_rate: 学习率

        tau: 温度参数

        lambda_coef: 对比损失权重



    Returns:

        更新后的本地模型参数

    """

    local_params = global_params.copy()

    n_samples = len(train_labels)



    # 获取全局和上一轮的表示

    z_global = compute_representation(global_params, len(global_params))

    z_prev = compute_representation(prev_local_params, len(prev_local_params))



    for _ in range(local_epochs):

        # 任务损失梯度

        predictions = train_data @ local_params

        errors = predictions - train_labels

        task_gradients = (1.0 / n_samples) * (train_data.T @ errors)



        # 对比损失梯度(简化)

        z_local = compute_representation(local_params, len(local_params))

        sim_pos = compute_cosine_similarity(z_local, z_global)

        sim_neg = compute_cosine_similarity(z_local, z_prev)



        # InfoNCE-like gradient approximation

        contrast_grad = lambda_coef * (sim_neg - sim_pos) * z_local / (tau + 1e-10)



        # 总梯度

        total_gradients = task_gradients + contrast_grad



        # 更新

        local_params = local_params - learning_rate * total_gradients



    return local_params





def moon_aggregate(

    client_params_list: List[np.ndarray],

    client_weights: List[float]

) -> np.ndarray:

    """MOON聚合(加权平均)"""

    total_weight = sum(client_weights)

    normalized_weights = [w / total_weight for w in client_weights]



    global_params = np.zeros_like(client_params_list[0])

    for params, weight in zip(client_params_list, normalized_weights):

        global_params += weight * params



    return global_params





def run_moon_fl(

    n_clients: int,

    model_dim: int,

    n_rounds: int,

    local_epochs: int,

    learning_rate: float,

    tau: float = 0.5,

    lambda_coef: float = 1.0,

    data_per_client: int = 100,

    test_size: int = 500,

    seed: int = 42

) -> Dict:

    """运行MOON"""

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



    # 跟踪每轮的本地参数(用于对比)

    prev_local_params_list = [global_params.copy() for _ in range(n_clients)]



    history = {"rounds": [], "test_mse": []}



    print(f"MOON联邦学习: tau={tau}, lambda={lambda_coef}")



    for round_idx in range(n_rounds):

        client_updates = []



        for i, (data, labels) in enumerate(client_data_list):

            updated = moon_local_train(

                global_params,

                prev_local_params_list[i],

                data, labels,

                local_epochs, learning_rate,

                tau, lambda_coef

            )

            client_updates.append(updated)

            prev_local_params_list[i] = updated.copy()



        # 聚合

        global_params = moon_aggregate(client_updates, client_weights)



        # 评估

        mse = np.mean((X_test @ global_params - y_test) ** 2)



        history["rounds"].append(round_idx + 1)

        history["test_mse"].append(mse)



        if (round_idx + 1) % 5 == 0 or round_idx == 0:

            print(f"轮次 {round_idx + 1}/{n_rounds} | MSE: {mse:.6f}")



    return {"final_params": global_params, "history": history}





if __name__ == "__main__":

    print("=" * 60)

    print("联邦学习 - MOON (Model-Contrastive FL) 演示")

    print("=" * 60)



    result = run_moon_fl(

        n_clients=5,

        model_dim=10,

        n_rounds=20,

        local_epochs=5,

        learning_rate=0.1,

        tau=0.5,

        lambda_coef=1.0,

        data_per_client=200,

        test_size=500,

        seed=42

    )



    print("\n" + "=" * 60)

    print(f"最终MSE: {result['history']['test_mse'][-1]:.6f}")

    print("=" * 60)

