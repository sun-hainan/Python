# -*- coding: utf-8 -*-

"""

算法实现：联邦学习 / 03_fednova



本文件实现 03_fednova 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict





def compute_effective_stepsize(

    learning_rate: float,

    local_epochs: int,

    batch_size: int,

    data_size: int

) -> float:

    """

    计算有效步长(effective stepsize)



    有效步长考虑了本地训练中实际执行的梯度步数,

    用于归一化梯度贡献。



    effective_stepsize = lr * batch_size / data_size * local_epochs



    Args:

        learning_rate: 原始学习率

        local_epochs: 本地训练轮数

        batch_size: 批大小(简化使用全批次)

        data_size: 客户端数据量



    Returns:

        有效步长

    """

    # 简化为: effective_lr = lr * local_epochs / data_size

    # 考虑实际SGD步骤数的影响

    return learning_rate * local_epochs / data_size





def local_train_nova(

    global_params: np.ndarray,

    train_data: np.ndarray,

    train_labels: np.ndarray,

    local_epochs: int,

    learning_rate: float

) -> Tuple[np.ndarray, float, int]:

    """

    FedNova本地训练 - 返回归一化所需的统计量



    与标准本地训练相同,但额外返回:

    - accumulated_noise: 累积的随机噪声(用于归一化)

    - steps: 本地步数



    Args:

        global_params: 当前全局模型参数

        train_data: 本地训练数据特征

        train_labels: 本地训练数据标签

        local_epochs: 本地训练轮数

        learning_rate: 学习率



    Returns:

        (更新后参数, 累积噪声标准差估计, 本地步数)

    """

    local_params = global_params.copy()

    n_samples = len(train_labels)



    # 累积梯度噪声估计(通过跟踪参数更新的方差)

    accumulated_update = np.zeros_like(global_params)

    steps = 0



    for _ in range(local_epochs):

        predictions = train_data @ local_params

        errors = predictions - train_labels

        gradients = (1.0 / n_samples) * (train_data.T @ errors)



        # 记录更新量

        update = learning_rate * gradients

        accumulated_update += np.abs(update)

        steps += 1



        local_params = local_params - update



    # 计算有效步长(用于后续归一化)

    effective_lr = compute_effective_stepsize(

        learning_rate, local_epochs, n_samples, n_samples

    )



    return local_params, np.mean(accumulated_update), steps





def nova_aggregate(

    global_params: np.ndarray,

    client_params_list: List[np.ndarray],

    client_steps_list: List[int],

    client_weights: List[float] = None

) -> np.ndarray:

    """

    FedNova聚合函数 - 归一化后加权平均



    关键步骤:

    1. 计算每轮通信的总有效步长

    2. 对每个客户端的更新进行归一化

    3. 加权平均归一化后的更新



    Args:

        global_params: 当前全局模型参数

        client_params_list: 各客户端更新后的参数

        client_steps_list: 各客户端本地步数

        client_weights: 各客户端权重(默认等权重)



    Returns:

        聚合后的全局模型参数

    """

    n_clients = len(client_params_list)



    if client_weights is None:

        client_weights = [1.0 / n_clients] * n_clients



    total_weight = sum(client_weights)

    normalized_weights = [w / total_weight for w in client_weights]



    # 计算每客户端的累积有效步长

    client_effective_steps = []

    for steps in client_steps_list:

        # 假设每步的有效步长为1(相对单位)

        client_effective_steps.append(float(steps))



    # 计算总有效步长

    total_steps = sum(client_effective_steps)



    # 归一化因子(防止某客户端主导)

    new_global_params = global_params.copy()



    for params, weight, eff_step in zip(

        client_params_list, normalized_weights, client_effective_steps

    ):

        # 归一化权重: 考虑有效步长的比例

        normalized_weight = weight * (eff_step / total_steps) if total_steps > 0 else 0

        # 应用更新

        new_global_params = new_global_params + normalized_weight * (params - global_params)



    return new_global_params





def evaluate_model(

    params: np.ndarray,

    test_data: np.ndarray,

    test_labels: np.ndarray

) -> Dict[str, float]:

    """评估全局模型性能"""

    predictions = test_data @ params

    mse = np.mean((predictions - test_labels) ** 2)

    return {"mse": mse, "rmse": np.sqrt(mse)}





def run_federated_nova(

    n_clients: int,

    model_dim: int,

    n_rounds: int,

    local_epochs_list: List[int],

    learning_rate: float,

    data_per_client: int = 100,

    test_size: int = 500,

    seed: int = 42

) -> Dict:

    """

    运行FedNova训练流程



    Args:

        n_clients: 客户端数量

        model_dim: 模型参数维度

        n_rounds: 联邦通信轮数

        local_epochs_list: 每个客户端的本地训练轮数列表(可不同)

        learning_rate: 学习率

        data_per_client: 每个客户端的数据量

        test_size: 测试集大小

        seed: 随机种子



    Returns:

        训练结果字典

    """

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



    history = {"rounds": [], "global_mse": []}



    print(f"FedNova训练: 客户端本地轮数={local_epochs_list}")



    for round_idx in range(n_rounds):

        updated_params_list = []

        client_steps_list = []



        for i, (data, labels) in enumerate(client_data_list):

            local_epochs = local_epochs_list[i % len(local_epochs_list)]

            updated_params, _, steps = local_train_nova(

                global_params, data, labels, local_epochs, learning_rate

            )

            updated_params_list.append(updated_params)

            client_steps_list.append(steps)



        global_params = nova_aggregate(

            global_params, updated_params_list, client_steps_list, client_weights

        )



        metrics = evaluate_model(global_params, X_test, y_test)

        history["rounds"].append(round_idx + 1)

        history["global_mse"].append(metrics["mse"])



        if (round_idx + 1) % 5 == 0 or round_idx == 0:

            print(f"轮次 {round_idx + 1}/{n_rounds} | MSE: {metrics['mse']:.6f}")



    return {"final_params": global_params, "history": history}





if __name__ == "__main__":

    print("=" * 60)

    print("联邦学习 - FedNova 归一化联邦优化演示")

    print("=" * 60)



    # 模拟不同客户端有不同本地训练轮数

    result = run_federated_nova(

        n_clients=5,

        model_dim=10,

        n_rounds=20,

        local_epochs_list=[3, 5, 7, 4, 6],  # 不同客户端不同轮数

        learning_rate=0.1,

        data_per_client=200,

        test_size=500,

        seed=42

    )



    print("\n" + "=" * 60)

    print("训练完成!")

    print(f"最终MSE: {result['history']['global_mse'][-1]:.6f}")

    print("=" * 60)

