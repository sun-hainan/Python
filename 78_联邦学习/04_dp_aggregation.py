# -*- coding: utf-8 -*-

"""

算法实现：联邦学习 / 04_dp_aggregation



本文件实现 04_dp_aggregation 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict





def compute_sensitivity(l2_norm: float, clipping_threshold: float) -> float:

    """

    计算梯度的L2敏感度



    敏感度定义为: 当一个客户端的数据改变时,聚合结果变化的最大值。

    通过梯度裁剪限制敏感度。



    Args:

        l2_norm: 梯度的L2范数

        clipping_threshold: 裁剪阈值C



    Returns:

        裁剪后的敏感度值

    """

    # 如果梯度L2范数超过阈值,则裁剪到阈值

    if l2_norm > clipping_threshold:

        return clipping_threshold

    return l2_norm





def clip_gradient(gradient: np.ndarray, clipping_threshold: float) -> np.ndarray:

    """

    梯度裁剪 - 限制梯度的L2范数



    裁剪公式: gradient_clipped = gradient * (C / ||gradient||)

    其中C为裁剪阈值



    Args:

        gradient: 原始梯度向量

        clipping_threshold: 裁剪阈值C



    Returns:

        裁剪后的梯度

    """

    l2_norm = np.linalg.norm(gradient)

    if l2_norm > clipping_threshold:

        # 按比例缩放梯度到阈值

        scale_factor = clipping_threshold / l2_norm

        return gradient * scale_factor

    return gradient





def add_laplace_noise(

    gradient: np.ndarray,

    sensitivity: float,

    epsilon: float

) -> np.ndarray:

    """

    添加拉普拉斯噪声实现差分隐私



    拉普拉斯机制: 输出 = 真实值 + Lap(sensitivity / epsilon)



    拉普拉斯分布的概率密度函数:

    f(x) = (1/(2b)) * exp(-|x|/b), 其中b = sensitivity / epsilon



    Args:

        gradient: 原始梯度/参数

        sensitivity: 敏感度(噪声尺度参数)

        epsilon: 隐私预算(越小隐私保护越强)



    Returns:

        添加了拉普拉斯噪声的梯度

    """

    # 拉普拉斯噪声的尺度参数 b = sensitivity / epsilon

    scale = sensitivity / epsilon



    # 为梯度向量的每个元素生成拉普拉斯噪声

    noise = np.random.laplace(0, scale, gradient.shape)



    return gradient + noise





def add_gaussian_noise(

    gradient: np.ndarray,

    sensitivity: float,

    epsilon: float,

    delta: float = 1e-5

) -> np.ndarray:

    """

    添加高斯噪声实现差分隐私(近似差分隐私)



    高斯机制满足(epsilon, delta)-差分隐私:

    输出 = 真实值 + N(0, sigma^2), 其中 sigma >= C * sqrt(2*ln(1.25/delta)) / epsilon



    Args:

        gradient: 原始梯度/参数

        sensitivity: 敏感度(裁剪阈值C)

        epsilon: 隐私预算

        delta: 失败概率上界(通常设为小值如1e-5)



    Returns:

        添加了高斯噪声的梯度

    """

    # 计算高斯噪声的标准差

    # sigma = sensitivity * sqrt(2 * ln(1.25/delta)) / epsilon

    sigma = sensitivity * np.sqrt(2 * np.log(1.25 / delta)) / epsilon



    noise = np.random.normal(0, sigma, gradient.shape)



    return gradient + noise





def private_federated_aggregate(

    client_gradients: List[np.ndarray],

    client_weights: List[float],

    clipping_threshold: float,

    epsilon: float,

    noise_type: str = "laplace",

    delta: float = 1e-5

) -> np.ndarray:

    """

    差分隐私联邦聚合 - 完整流程



    步骤:

    1. 对每个客户端梯度进行裁剪(限制敏感度)

    2. 对裁剪后的梯度添加噪声(拉普拉斯或高斯)

    3. 加权平均聚合



    Args:

        client_gradients: 各客户端的梯度列表

        client_weights: 各客户端的权重

        clipping_threshold: 梯度裁剪阈值C

        epsilon: 隐私预算

        noise_type: 噪声类型, "laplace"或"gaussian"

        delta: 高斯机制参数delta



    Returns:

        聚合后的隐私保护梯度

    """

    n_clients = len(client_gradients)



    # 归一化权重

    total_weight = sum(client_weights)

    normalized_weights = [w / total_weight for w in client_weights]



    # 聚合噪声(用于追踪隐私消耗)

    aggregated_gradient = np.zeros_like(client_gradients[0])



    for gradient, weight in zip(client_gradients, normalized_weights):

        # 步骤1: 梯度裁剪

        clipped_gradient = clip_gradient(gradient, clipping_threshold)



        # 步骤2: 添加噪声

        if noise_type == "laplace":

            # 拉普拉斯机制的敏感度即为裁剪阈值

            noisy_gradient = add_laplace_noise(

                clipped_gradient, clipping_threshold, epsilon

            )

        else:  # gaussian

            noisy_gradient = add_gaussian_noise(

                clipped_gradient, clipping_threshold, epsilon, delta

            )



        # 步骤3: 加权累加

        aggregated_gradient += weight * noisy_gradient



    return aggregated_gradient





def compute_privacy_budget(

    epsilon: float,

    n_clients_per_round: int,

    n_rounds: int,

    noise_type: str = "laplace"

) -> Dict[str, float]:

    """

    计算总体隐私预算消耗



    使用顺序组合定理:

    - 拉普拉斯机制: 总epsilon = 每轮epsilon * 轮数

    - 高斯机制: 使用更复杂的隐私会计(简化版)



    Args:

        epsilon: 每轮隐私预算

        n_clients_per_round: 每轮参与的客户端数

        n_rounds: 总通信轮数

        noise_type: 噪声类型



    Returns:

        总隐私预算信息字典

    """

    if noise_type == "laplace":

        # 拉普拉斯机制: 线性组合

        total_epsilon = epsilon * n_rounds

        # 实际上每个客户端独立添加噪声,聚合后噪声会减小

        # 简化: sqrt(n)因子

        effective_epsilon = epsilon * np.sqrt(n_rounds)

    else:

        # 高斯机制: 平方和组合

        total_epsilon = epsilon * np.sqrt(n_rounds)

        effective_epsilon = total_epsilon



    return {

        "per_round_epsilon": epsilon,

        "total_epsilon": total_epsilon,

        "effective_epsilon": effective_epsilon,

        "n_rounds": n_rounds

    }





def local_train_with_dp(

    global_params: np.ndarray,

    train_data: np.ndarray,

    train_labels: np.ndarray,

    local_epochs: int,

    learning_rate: float

) -> np.ndarray:

    """

    本地训练产生梯度(无差分隐私)



    Args:

        global_params: 当前全局模型参数

        train_data: 本地训练数据

        train_labels: 本地训练标签

        local_epochs: 本地训练轮数

        learning_rate: 学习率



    Returns:

        梯度向量

    """

    local_params = global_params.copy()

    n_samples = len(train_labels)



    for _ in range(local_epochs):

        predictions = train_data @ local_params

        errors = predictions - train_labels

        gradients = (1.0 / n_samples) * (train_data.T @ errors)

        local_params = local_params - learning_rate * gradients



    # 返回的是参数更新量(即梯度 * 学习率)

    return local_params - global_params





def run_dp_federated_learning(

    n_clients: int,

    model_dim: int,

    n_rounds: int,

    local_epochs: int,

    learning_rate: float,

    clipping_threshold: float = 1.0,

    epsilon: float = 1.0,

    noise_type: str = "laplace",

    data_per_client: int = 100,

    test_size: int = 500,

    seed: int = 42

) -> Dict:

    """

    运行差分隐私联邦学习



    Args:

        n_clients: 客户端数量

        model_dim: 模型参数维度

        n_rounds: 联邦通信轮数

        local_epochs: 每轮本地训练epoch数

        learning_rate: 学习率

        clipping_threshold: 梯度裁剪阈值

        epsilon: 隐私预算

        noise_type: 噪声类型

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

        noise_scale = 0.1 + 0.2 * (i / n_clients)

        X = np.random.randn(data_per_client, model_dim)

        y = X @ w_true + np.random.randn(data_per_client) * noise_scale

        client_data_list.append((X, y))

        client_weights.append(float(data_per_client))



    X_test = np.random.randn(test_size, model_dim)

    y_test = X_test @ w_true + np.random.randn(test_size) * 0.1



    global_params = np.random.randn(model_dim) * np.sqrt(2.0 / model_dim)



    history = {"rounds": [], "test_mse": [], "privacy_budget": []}



    print(f"差分隐私FL: epsilon={epsilon}, "

          f"clipping={clipping_threshold}, noise={noise_type}")



    for round_idx in range(n_rounds):

        client_gradients = []



        for data, labels in client_data_list:

            gradient = local_train_with_dp(

                global_params, data, labels, local_epochs, learning_rate

            )

            client_gradients.append(gradient)



        # 差分隐私聚合

        aggregated_gradient = private_federated_aggregate(

            client_gradients, client_weights,

            clipping_threshold, epsilon, noise_type

        )



        # 更新全局模型

        global_params = global_params - aggregated_gradient



        # 评估

        predictions = X_test @ global_params

        mse = np.mean((predictions - y_test) ** 2)



        history["rounds"].append(round_idx + 1)

        history["test_mse"].append(mse)



        if (round_idx + 1) % 5 == 0 or round_idx == 0:

            print(f"轮次 {round_idx + 1}/{n_rounds} | MSE: {mse:.6f}")



    # 计算总隐私预算

    privacy_info = compute_privacy_budget(

        epsilon, n_clients, n_rounds, noise_type

    )

    history["privacy_budget"] = privacy_info



    return {"final_params": global_params, "history": history}





if __name__ == "__main__":

    print("=" * 60)

    print("联邦学习 - 差分隐私聚合演示")

    print("=" * 60)



    result = run_dp_federated_learning(

        n_clients=5,

        model_dim=10,

        n_rounds=20,

        local_epochs=5,

        learning_rate=0.1,

        clipping_threshold=1.0,

        epsilon=1.0,

        noise_type="laplace",

        data_per_client=200,

        test_size=500,

        seed=42

    )



    print("\n" + "=" * 60)

    print("训练完成!")

    print(f"最终MSE: {result['history']['test_mse'][-1]:.6f}")

    print(f"总隐私预算(有效): {result['history']['privacy_budget']['effective_epsilon']:.4f}")

    print("=" * 60)

