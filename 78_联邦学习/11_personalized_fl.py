# -*- coding: utf-8 -*-

"""

算法实现：联邦学习 / 11_personalized_fl



本文件实现 11_personalized_fl 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict





def per_fedavg_local_adaptation(

    global_params: np.ndarray,

    train_data: np.ndarray,

    train_labels: np.ndarray,

    adaptation_epochs: int = 5,

    adaptation_lr: float = 0.01

) -> np.ndarray:

    """

    Per-FedAvg本地适配 - 在全局模型基础上进行微调



    步骤:

    1. 以全局模型w_g初始化本地模型w

    2. 在本地数据上进行几步梯度下降

    3. 返回适配后的个性化模型



    Args:

        global_params: 全局模型参数

        train_data: 本地训练数据

        train_labels: 本地训练标签

        adaptation_epochs: 适配epoch数(通常较少,1-10)

        adaptation_lr: 适配学习率



    Returns:

        个性化模型参数

    """

    local_params = global_params.copy()

    n_samples = len(train_labels)



    for _ in range(adaptation_epochs):

        # 前向传播

        predictions = train_data @ local_params

        # 计算梯度

        errors = predictions - train_labels

        gradients = (1.0 / n_samples) * (train_data.T @ errors)

        # 梯度下降更新

        local_params = local_params - adaptation_lr * gradients



    return local_params





def per_fedavg_loss_on_global(

    personalized_params: np.ndarray,

    global_params: np.ndarray,

    train_data: np.ndarray,

    train_labels: np.ndarray,

    alpha: float = 0.1

) -> float:

    """

    计算Per-FedAvg的元损失



    损失 = 本地适配后模型在本地数据的损失 + 正则化项



    正则化项: (alpha/2) * ||w_personalized - w_global||^2



    Args:

        personalized_params: 个性化模型参数

        global_params: 全局模型参数

        train_data: 本地训练数据

        train_labels: 本地训练标签

        alpha: 正则化系数



    Returns:

        元损失值

    """

    # 数据损失

    predictions = train_data @ personalized_params

    data_loss = np.mean((predictions - train_labels) ** 2)



    # 正则化损失

    reg_loss = (alpha / 2) * np.sum((personalized_params - global_params) ** 2)



    return data_loss + reg_loss





def per_fedavg_gradient_on_global(

    personalized_params: np.ndarray,

    global_params: np.ndarray,

    train_data: np.ndarray,

    train_labels: np.ndarray,

    adaptation_epochs: int,

    adaptation_lr: float,

    alpha: float = 0.1

) -> np.ndarray:

    """

    计算对全局模型参数的梯度(通过链式法则)



    Per-FedAvg的关键: 使用一阶近似计算元梯度



    dL/dw_global = dL/dw_personalized * dw_personalized/dw_global



    其中 dw_personalized/dw_global 可以通过Hessian近似估计



    Args:

        personalized_params: 个性化模型参数

        global_params: 全局模型参数

        train_data: 本地训练数据

        train_labels: 本地训练标签

        adaptation_epochs: 适配epoch数

        adaptation_lr: 适配学习率

        alpha: 正则化系数



    Returns:

        对全局模型的梯度

    """

    n_samples = len(train_labels)



    # 计算个性化模型处的梯度

    predictions = train_data @ personalized_params

    errors = predictions - train_labels

    data_grad = (1.0 / n_samples) * (train_data.T @ errors)



    # 近似: dL/dw_global ≈ dL/dw_personalized * F

    # 其中F是近端项的梯度贡献

    proximal_grad = alpha * (global_params - personalized_params)



    # 链式法则近似: 乘以适配过程的衰减因子

    # 简化: 使用 (1 - adaptation_lr * alpha)^adaptation_epochs 作为衰减

    decay = (1 - adaptation_lr * alpha) ** adaptation_epochs



    # 元梯度 = 数据损失在个性化模型处的梯度 * 衰减 + 近端项梯度

    meta_grad = data_grad * decay + proximal_grad



    return meta_grad





def per_fedavg_round(

    global_params: np.ndarray,

    client_data_list: List[Tuple[np.ndarray, np.ndarray]],

    client_weights: List[float],

    adaptation_epochs: int = 5,

    adaptation_lr: float = 0.01,

    meta_lr: float = 0.01,

    alpha: float = 0.1

) -> Tuple[np.ndarray, List[np.ndarray]]:

    """

    Per-FedAvg一轮



    Args:

        global_params: 当前全局模型参数

        client_data_list: 各客户端(data, labels)元组列表

        client_weights: 各客户端权重

        adaptation_epochs: 本地适配epoch数

        adaptation_lr: 适配学习率

        meta_lr: 元学习率(全局更新步长)

        alpha: 正则化系数



    Returns:

        (新全局参数, 个性化参数列表)

    """

    n_clients = len(client_data_list)



    # 归一化权重

    total_weight = sum(client_weights)

    normalized_weights = [w / total_weight for w in client_weights]



    personalized_params_list = []

    global_grad_accumulator = np.zeros_like(global_params)



    for i, ((data, labels), weight) in enumerate(zip(client_data_list, normalized_weights)):

        # 步骤1: 本地适配

        personalized = per_fedavg_local_adaptation(

            global_params, data, labels,

            adaptation_epochs, adaptation_lr

        )

        personalized_params_list.append(personalized)



        # 步骤2: 计算对全局模型的元梯度

        meta_grad = per_fedavg_gradient_on_global(

            personalized, global_params, data, labels,

            adaptation_epochs, adaptation_lr, alpha

        )



        # 加权累加

        global_grad_accumulator += weight * meta_grad



    # 更新全局模型

    new_global_params = global_params - meta_lr * global_grad_accumulator



    return new_global_params, personalized_params_list





def pfedme_loss(

    personalized_params: np.ndarray,

    global_params: np.ndarray,

    train_data: np.ndarray,

    train_labels: np.ndarray,

    beta: float

) -> float:

    """

    pFedMe的损失函数 - Moreau envelope正则化



    L_personalized(w_p, w_g) = L_data(w_p) + (beta/2) * ||w_p - w_g||^2



    其中w_p是个性化模型,w_g是全局模型



    Args:

        personalized_params: 个性化模型参数

        global_params: 全局模型参数

        train_data: 本地训练数据

        train_labels: 本地训练标签

        beta: 近端正则化系数



    Returns:

        损失值

    """

    predictions = train_data @ personalized_params

    data_loss = np.mean((predictions - train_labels) ** 2)

    proximal_loss = (beta / 2) * np.sum((personalized_params - global_params) ** 2)

    return data_loss + proximal_loss





def pfedme_personalized_update(

    global_params: np.ndarray,

    train_data: np.ndarray,

    train_labels: np.ndarray,

    local_epochs: int,

    lr: float,

    beta: float

) -> np.ndarray:

    """

    pFedMe个性化模型更新 - 使用Moreau envelope的近端梯度下降



    步骤:

    1. 固定全局模型,更新个性化模型(多步)

    2. 个性化模型被近端项拉向全局模型



    Args:

        global_params: 全局模型参数

        train_data: 本地训练数据

        train_labels: 本地训练标签

        local_epochs: 本地训练轮数

        lr: 学习率

        beta: 近端系数



    Returns:

        更新后的个性化模型参数

    """

    personalized_params = global_params.copy()

    n_samples = len(train_labels)



    for _ in range(local_epochs):

        # 数据损失梯度

        predictions = train_data @ personalized_params

        errors = predictions - train_labels

        data_grad = (1.0 / n_samples) * (train_data.T @ errors)



        # 近端梯度: beta * (w_p - w_g)

        proximal_grad = beta * (personalized_params - global_params)



        # 总梯度

        total_grad = data_grad + proximal_grad



        # 更新

        personalized_params = personalized_params - lr * total_grad



    return personalized_params





def pfedme_global_update(

    personalized_params_list: List[np.ndarray],

    global_params: np.ndarray,

    global_lr: float,

    beta: float,

    client_weights: List[float]

) -> np.ndarray:

    """

    pFedMe全局模型更新 - 聚合个性化模型



    全局模型向所有个性化模型的均值移动:

    w_g_new = w_g + eta * sum(w_p_i - w_g) / K



    Args:

        personalized_params_list: 各客户端个性化参数列表

        global_params: 当前全局参数

        global_lr: 全局学习率

        beta: 近端系数

        client_weights: 客户端权重



    Returns:

        更新后的全局模型

    """

    total_weight = sum(client_weights)

    normalized_weights = [w / total_weight for w in client_weights]



    # 计算加权平均的个性化与全局的差异

    diff_accumulator = np.zeros_like(global_params)

    for params, weight in zip(personalized_params_list, normalized_weights):

        diff_accumulator += weight * (params - global_params)



    # 全局更新: w_g_new = w_g + global_lr * diff

    new_global = global_params + global_lr * diff_accumulator



    return new_global





def run_personalized_fl(

    n_clients: int,

    model_dim: int,

    n_rounds: int,

    local_epochs: int,

    learning_rate: float,

    method: str = "per_fedavg",

    data_per_client: int = 100,

    test_size: int = 500,

    seed: int = 42

) -> Dict:

    """

    运行个性化联邦学习



    Args:

        n_clients: 客户端数量

        model_dim: 模型维度

        n_rounds: 训练轮数

        local_epochs: 本地训练轮数

        learning_rate: 学习率

        method: 方法,"per_fedavg"或"pfedme"

        data_per_client: 每客户端数据量

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

        noise_scale = 0.1 + 0.4 * (i / n_clients)  # 高异构性

        X = np.random.randn(data_per_client, model_dim)

        y = X @ w_true + np.random.randn(data_per_client) * noise_scale

        client_data_list.append((X, y))

        client_weights.append(float(data_per_client))



    X_test = np.random.randn(test_size, model_dim)

    y_test = X_test @ w_true + np.random.randn(test_size) * 0.1



    global_params = np.random.randn(model_dim) * np.sqrt(2.0 / model_dim)



    history = {"rounds": [], "global_mse": [], "avg_personalized_mse": []}



    print(f"个性化FL: {method}")



    for round_idx in range(n_rounds):

        if method == "per_fedavg":

            global_params, personalized_list = per_fedavg_round(

                global_params, client_data_list, client_weights,

                adaptation_epochs=5, adaptation_lr=0.01,

                meta_lr=0.1, alpha=0.1

            )

        else:  # pfedme

            personalized_list = []

            for data, labels in client_data_list:

                personalized = pfedme_personalized_update(

                    global_params, data, labels,

                    local_epochs, learning_rate, beta=0.1

                )

                personalized_list.append(personalized)



            global_params = pfedme_global_update(

                personalized_list, global_params,

                global_lr=0.1, beta=0.1,

                client_weights=client_weights

            )



        # 评估全局模型

        global_pred = X_test @ global_params

        global_mse = np.mean((global_pred - y_test) ** 2)



        # 评估个性化模型(平均)

        personalized_mses = []

        for personalized, (data, labels) in zip(personalized_list, client_data_list):

            # 在测试集上评估

            pred = X_test @ personalized

            mse = np.mean((pred - y_test) ** 2)

            personalized_mses.append(mse)



        avg_personalized_mse = np.mean(personalized_mses)



        history["rounds"].append(round_idx + 1)

        history["global_mse"].append(global_mse)

        history["avg_personalized_mse"].append(avg_personalized_mse)



        if (round_idx + 1) % 5 == 0 or round_idx == 0:

            print(f"轮次 {round_idx + 1}/{n_rounds} | "

                  f"全局MSE: {global_mse:.6f} | "

                  f"个性化平均MSE: {avg_personalized_mse:.6f}")



    return {"final_global": global_params, "final_personalized": personalized_list,

            "history": history}





if __name__ == "__main__":

    print("=" * 60)

    print("个性化联邦学习演示: Per-FedAvg vs pFedMe")

    print("=" * 60)



    print("\n--- Per-FedAvg ---")

    result = run_personalized_fl(

        n_clients=5,

        model_dim=10,

        n_rounds=20,

        local_epochs=5,

        learning_rate=0.1,

        method="per_fedavg",

        data_per_client=200,

        test_size=500,

        seed=42

    )

    print(f"最终全局MSE: {result['history']['global_mse'][-1]:.6f}")

    print(f"最终个性化平均MSE: {result['history']['avg_personalized_mse'][-1]:.6f}")



    print("\n--- pFedMe ---")

    result = run_personalized_fl(

        n_clients=5,

        model_dim=10,

        n_rounds=20,

        local_epochs=5,

        learning_rate=0.1,

        method="pfedme",

        data_per_client=200,

        test_size=500,

        seed=42

    )

    print(f"最终全局MSE: {result['history']['global_mse'][-1]:.6f}")

    print(f"最终个性化平均MSE: {result['history']['avg_personalized_mse'][-1]:.6f}")



    print("\n" + "=" * 60)

    print("训练完成!")

    print("=" * 60)

