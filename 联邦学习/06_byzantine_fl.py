# -*- coding: utf-8 -*-

"""

算法实现：联邦学习 / 06_byzantine_fl



本文件实现 06_byzantine_fl 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict





def compute_pairwise_distances(

    client_updates: List[np.ndarray]

) -> np.ndarray:

    """

    计算客户端更新之间的成对欧氏距离



    用于检测异常更新:拜占庭节点发送的更新通常与其他节点距离较远。



    Args:

        client_updates: 各客户端更新的参数列表



    Returns:

        距离矩阵, shape为(n_clients, n_clients)

    """

    n = len(client_updates)

    distances = np.zeros((n, n))



    for i in range(n):

        for j in range(i + 1, n):

            dist = np.linalg.norm(client_updates[i] - client_updates[j])

            distances[i, j] = dist

            distances[j, i] = dist



    return distances





def krum_aggregate(

    client_updates: List[np.ndarray],

    client_weights: List[float],

    n_byzantine: int = 1

) -> np.ndarray:

    """

    Krum聚合算法 - 拜占庭容错联邦平均



    核心思想:选择与其他更新"最相似"的更新作为代表



    步骤:

    1. 对每个客户端更新,计算其到其他更新的距离

    2. 对于每个更新i,找出距离最小的n-f-2个更新的平均距离

    3. 选择距离最小的更新作为输出



    Args:

        client_updates: 各客户端的更新列表

        client_weights: 各客户端的权重

        n_byzantine: 预期的拜占庭节点数量



    Returns:

        聚合后的全局更新

    """

    n_clients = len(client_updates)

    dim = len(client_updates[0])



    # 计算成对距离

    distances = compute_pairwise_distances(client_updates)



    # 对每个客户端,计算其到最近n-f-2个客户端的平均距离

    # n-f-2确保即使去掉f个拜占庭节点,也能找到诚实节点

    n_neighbors = max(1, n_clients - n_byzantine - 2)



    scores = []

    for i in range(n_clients):

        # 找出距离最小的n_neighbors个客户端(排除自己)

        sorted_indices = np.argsort(distances[i])

        # 排除自己和距离最远的(可能是拜占庭)

        nearest_indices = sorted_indices[1:n_neighbors + 1]

        # 计算平均距离

        avg_dist = np.mean(distances[i, nearest_indices])

        scores.append(avg_dist)



    # 选择距离最小的客户端更新

    selected_idx = np.argmin(scores)



    # 加权返回(简化版,直接返回选中的更新)

    return client_updates[selected_idx]





def multi_krum_aggregate(

    client_updates: List[np.ndarray],

    client_weights: List[float],

    n_byzantine: int = 1,

    multi_k: int = None

) -> np.ndarray:

    """

    Multi-Krum聚合算法 - Krum的多版本



    与Krum不同,Multi-Krum选择多个"好"的更新进行平均



    Args:

        client_updates: 各客户端的更新列表

        client_weights: 各客户端的权重

        n_byzantine: 预期的拜占庭节点数量

        multi_k: 选择多少个更新进行平均,默认为n-f



    Returns:

        聚合后的全局更新

    """

    n_clients = len(client_updates)



    if multi_k is None:

        multi_k = n_clients - n_byzantine



    # 计算成对距离

    distances = compute_pairwise_distances(client_updates)



    # 计算每个更新的分数(平均到其他更新的距离)

    n_neighbors = max(1, n_clients - n_byzantine - 2)



    scores = []

    for i in range(n_clients):

        sorted_indices = np.argsort(distances[i])

        nearest_indices = sorted_indices[1:n_neighbors + 1]

        avg_dist = np.mean(distances[i, nearest_indices])

        scores.append(avg_dist)



    # 选择分数最小的multi_k个更新

    sorted_by_score = np.argsort(scores)

    selected_indices = sorted_by_score[:multi_k]



    # 加权平均选中的更新

    selected_updates = [client_updates[i] for i in selected_indices]

    selected_weights = [client_weights[i] for i in selected_indices]



    total_weight = sum(selected_weights)

    normalized_weights = [w / total_weight for w in selected_weights]



    aggregated = np.zeros_like(client_updates[0])

    for update, weight in zip(selected_updates, normalized_weights):

        aggregated += weight * update



    return aggregated





def trimmed_mean_aggregate(

    client_updates: List[np.ndarray],

    client_weights: List[float],

    n_byzantine: int = 1

) -> np.ndarray:

    """

    Trimmed Mean聚合 - 去掉极值后取平均



    步骤:

    1. 对每个参数维度,将所有客户端的值排序

    2. 去掉最大和最小的beta个值

    3. 对剩余值取平均



    Args:

        client_updates: 各客户端的更新列表

        client_weights: 各客户端的权重

        n_byzantine: 预期的拜占庭节点数量



    Returns:

        聚合后的全局更新

    """

    n_clients = len(client_updates)

    dim = len(client_updates[0])



    # 每端去掉多少个值(两边各去掉n_byzantine个)

    trim_count = n_byzantine



    aggregated = np.zeros(dim)



    for d in range(dim):

        # 提取第d个参数维度的所有值

        values = np.array([update[d] for update in client_updates])

        weights = np.array(client_weights)



        # 排序(按值排序,保持权重对应)

        sorted_indices = np.argsort(values)

        sorted_values = values[sorted_indices]



        # 去掉最大和最小的trim_count个

        trimmed_values = sorted_values[trim_count:-trim_count] if trim_count > 0 else sorted_values

        trimmed_indices = sorted_indices[trim_count:-trim_count] if trim_count > 0 else sorted_indices

        trimmed_weights = weights[trim_indices]



        # 归一化权重

        total_weight = sum(trimmed_weights)

        normalized_weights = [w / total_weight for w in trimmed_weights]



        # 加权平均

        aggregated[d] = sum(v * w for v, w in zip(trimmed_values, normalized_weights))



    return aggregated





def coordinate_wise_median_aggregate(

    client_updates: List[np.ndarray],

    client_weights: List[float] = None

) -> np.ndarray:

    """

    坐标-wise中位数聚合



    对每个参数维度,取所有客户端更新的中位数



    Args:

        client_updates: 各客户端的更新列表

        client_weights: 权重(中位数忽略权重)



    Returns:

        聚合后的全局更新

    """

    n_clients = len(client_updates)

    dim = len(client_updates[0])



    aggregated = np.zeros(dim)



    for d in range(dim):

        values = np.array([update[d] for update in client_updates])

        aggregated[d] = np.median(values)



    return aggregated





def detect_anomalies(

    client_updates: List[np.ndarray],

    threshold: float = 2.0

) -> List[bool]:

    """

    异常检测 - 基于统计方法检测恶意更新



    使用马氏距离(Mahalanobis Distance)的简化版本:

    计算每个更新与均值的距离,超过阈值的标记为异常



    Args:

        client_updates: 各客户端的更新列表

        threshold: 异常阈值(标准差倍数)



    Returns:

        布尔列表,True表示正常,False表示异常

    """

    updates_matrix = np.array(client_updates)

    mean = np.mean(updates_matrix, axis=0)

    std = np.std(updates_matrix, axis=0)



    # 避免除零

    std = np.where(std < 1e-10, 1e-10, std)



    # 计算Z-score

    z_scores = np.abs((updates_matrix - mean) / std)

    avg_z_score = np.mean(z_scores, axis=1)



    # 超过阈值的标记为异常

    anomalies = avg_z_score < threshold * np.mean(avg_z_score)



    return list(anomalies)





def byzantine_resilient_federated_round(

    global_params: np.ndarray,

    client_data_list: List[Tuple[np.ndarray, np.ndarray]],

    client_weights: List[float],

    local_epochs: int,

    learning_rate: float,

    defense_method: str = "krum",

    n_byzantine: int = 1

) -> np.ndarray:

    """

    拜占庭容错联邦学习一轮



    Args:

        global_params: 当前全局模型参数

        client_data_list: 各客户端的(data, labels)

        client_weights: 各客户端权重

        local_epochs: 本地训练轮数

        learning_rate: 学习率

        defense_method: 防御方法,"krum","multi_krum","trimmed_mean","median"

        n_byzantine: 预期的拜占庭节点数量



    Returns:

        聚合后的全局模型参数

    """

    n_clients = len(client_data_list)



    # 本地训练得到更新

    client_updates = []

    for data, labels in client_data_list:

        local_params = global_params.copy()

        n_samples = len(labels)



        for _ in range(local_epochs):

            predictions = data @ local_params

            errors = predictions - labels

            gradients = (1.0 / n_samples) * (data.T @ errors)

            local_params = local_params - learning_rate * gradients



        # 计算参数更新量

        update = local_params - global_params

        client_updates.append(update)



    # 选择防御方法进行聚合

    if defense_method == "krum":

        aggregated_update = krum_aggregate(client_updates, client_weights, n_byzantine)

    elif defense_method == "multi_krum":

        aggregated_update = multi_krum_aggregate(client_updates, client_weights, n_byzantine)

    elif defense_method == "trimmed_mean":

        aggregated_update = trimmed_mean_aggregate(client_updates, client_weights, n_byzantine)

    elif defense_method == "median":

        aggregated_update = coordinate_wise_median_aggregate(client_updates, client_weights)

    else:

        # 默认使用简单平均(无防御)

        aggregated_update = np.mean(client_updates, axis=0)



    return global_params + aggregated_update





def run_byzantine_federated_learning(

    n_clients: int,

    model_dim: int,

    n_rounds: int,

    local_epochs: int,

    learning_rate: float,

    n_byzantine: int = 1,

    defense_method: str = "krum",

    data_per_client: int = 100,

    test_size: int = 500,

    seed: int = 42

) -> Dict:

    """

    运行拜占庭容错联邦学习



    Args:

        n_clients: 客户端数量

        model_dim: 模型参数维度

        n_rounds: 联邦通信轮数

        local_epochs: 每轮本地训练epoch数

        learning_rate: 学习率

        n_byzantine: 恶意客户端数量

        defense_method: 防御方法

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



    history = {"rounds": [], "test_mse": []}



    print(f"拜占庭容错FL: {n_byzantine}个恶意客户端, 方法={defense_method}")



    for round_idx in range(n_rounds):

        global_params = byzantine_resilient_federated_round(

            global_params, client_data_list, client_weights,

            local_epochs, learning_rate, defense_method, n_byzantine

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

    print("联邦学习 - 拜占庭容错聚合演示")

    print("=" * 60)



    result = run_byzantine_federated_learning(

        n_clients=5,

        model_dim=10,

        n_rounds=20,

        local_epochs=5,

        learning_rate=0.1,

        n_byzantine=1,

        defense_method="krum",

        data_per_client=200,

        test_size=500,

        seed=42

    )



    print("\n" + "=" * 60)

    print("训练完成!")

    print(f"最终MSE: {result['history']['test_mse'][-1]:.6f}")

    print("=" * 60)

