# -*- coding: utf-8 -*-
"""
算法实现：联邦学习 / 12_federated_transfer_learning

本文件实现 12_federated_transfer_learning 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Dict, Optional


class TransferLearningClient:
    """
    支持迁移学习的客户端

    可以作为源客户端(有知识可迁移)或目标客户端(需要学习)
    """

    def __init__(
        self,
        client_id: int,
        train_data: np.ndarray,
        train_labels: np.ndarray,
        model_dim: int,
        domain_id: int = 0
    ):
        """
        初始化迁移学习客户端

        Args:
            client_id: 客户端ID
            train_data: 本地训练数据
            train_labels: 本地训练标签
            model_dim: 模型维度
            domain_id: 域ID,用于标识数据来源分布
        """
        self.client_id = client_id
        self.train_data = train_data
        self.train_labels = train_labels
        self.model_dim = model_dim
        self.domain_id = domain_id
        self.model_params = None

    def initialize_params(self, seed: int = 42):
        """初始化模型参数"""
        np.random.seed(seed + self.client_id)
        self.model_params = np.random.randn(self.model_dim) * np.sqrt(2.0 / self.model_dim)

    def receive_model(self, model_params: np.ndarray):
        """接收服务器下发的模型"""
        self.model_params = model_params.copy()

    def local_train(
        self,
        epochs: int,
        lr: float,
        freeze_layers: int = 0
    ) -> float:
        """
        本地训练

        Args:
            epochs: 训练轮数
            lr: 学习率
            freeze_layers: 冻结的前几层数量(用于迁移学习)

        Returns:
            训练损失
        """
        params = self.model_params.copy()
        n_samples = len(self.train_labels)

        # 可训练参数索引(排除冻结层)
        trainable_start = freeze_layers * (self.model_dim // 10) if freeze_layers > 0 else 0

        for _ in range(epochs):
            predictions = self.train_data @ params
            errors = predictions - self.train_labels
            gradients = (1.0 / n_samples) * (self.train_data.T @ errors)

            # 只更新可训练部分
            if freeze_layers > 0:
                full_gradients = np.zeros_like(params)
                full_gradients[trainable_start:] = gradients[trainable_start:]
                params = params - lr * full_gradients
            else:
                params = params - lr * gradients

        self.model_params = params

        predictions = self.train_data @ params
        loss = np.mean((predictions - self.train_labels) ** 2)
        return loss


def compute_model_similarity(
    params1: np.ndarray,
    params2: np.ndarray
) -> float:
    """
    计算两个模型的相似度

    使用余弦相似度和参数距离两种度量

    Args:
        params1: 模型1参数
        params2: 模型2参数

    Returns:
        相似度分数(0-1)
    """
    # 余弦相似度
    dot_product = np.dot(params1, params2)
    norm1 = np.linalg.norm(params1)
    norm2 = np.linalg.norm(params2)

    if norm1 < 1e-10 or norm2 < 1e-10:
        return 0.0

    cosine_sim = dot_product / (norm1 * norm2)

    # 转换为距离
    distance = np.linalg.norm(params1 - params2)
    max_distance = norm1 + norm2
    distance_sim = 1.0 - min(distance / max_distance, 1.0)

    # 综合相似度
    similarity = 0.5 * (cosine_sim + 1.0) + 0.5 * distance_sim
    return similarity / 2.0


def knowledge_distillation(
    teacher_models: List[np.ndarray],
    student_params: np.ndarray,
    temperature: float = 2.0,
    alpha: float = 0.5
) -> np.ndarray:
    """
    知识蒸馏 - 从多个教师模型提取知识到学生模型

    软目标损失: KL_divergence(soft_predictions, student_predictions)
    硬目标损失: Cross_entropy(hard_labels, student_predictions)
    总损失: alpha * soft_loss + (1-alpha) * hard_loss

    Args:
        teacher_models: 教师模型参数列表
        student_params: 学生模型当前参数
        temperature: 温度参数,控制软化的程度
        alpha: 软目标权重

    Returns:
        蒸馏后的学生模型参数
    """
    # 简化: 计算教师模型的加权平均作为软目标
    teacher_avg = np.mean(teacher_models, axis=0)

    # 软化教师预测
    soft_teacher = teacher_avg / temperature

    # 学生与教师的差距
    delta = soft_teacher - student_params

    # 使用差距更新学生(模拟蒸馏过程)
    # 温差越大,学生越需要模仿教师
    student_update = delta * temperature ** 2

    distilled_params = student_params + alpha * student_update

    return distilled_params


def federated_transfer_learning_round(
    global_params: np.ndarray,
    client_data_list: List[Tuple[np.ndarray, np.ndarray]],
    client_weights: List[float],
    client_domains: List[int],
    local_epochs: int,
    lr: float,
    source_domain: int = 0
) -> np.ndarray:
    """
    联邦迁移学习一轮

    核心思想: 利用源域(有丰富数据的客户端)的知识,
    帮助目标域(数据稀缺的客户端)更快学习

    Args:
        global_params: 当前全局模型参数
        client_data_list: 客户端数据列表
        client_weights: 客户端权重
        client_domains: 各客户端所属域
        local_epochs: 本地训练轮数
        lr: 学习率
        source_domain: 源域ID

    Returns:
        聚合后的全局模型参数
    """
    n_clients = len(client_data_list)

    # 分离源域和目标域客户端
    source_clients = []
    target_clients = []

    for i in range(n_clients):
        if client_domains[i] == source_domain:
            source_clients.append(i)
        else:
            target_clients.append(i)

    # 1. 源域客户端训练
    source_updates = []
    for idx in source_clients:
        data, labels = client_data_list[idx]
        local_params = global_params.copy()
        n_samples = len(labels)

        for _ in range(local_epochs):
            predictions = data @ local_params
            errors = predictions - labels
            gradients = (1.0 / n_samples) * (data.T @ errors)
            local_params = local_params - lr * gradients

        source_updates.append(local_params - global_params)

    # 2. 目标域客户端训练(带迁移)
    target_updates = []
    for idx in target_clients:
        data, labels = client_data_list[idx]
        local_params = global_params.copy()
        n_samples = len(labels)

        # 计算与源域的相似度(作为迁移权重)
        domain_similarity = 1.0 - abs(client_domains[idx] - source_domain) / 10.0

        for _ in range(local_epochs):
            predictions = data @ local_params
            errors = predictions - labels
            gradients = (1.0 / n_samples) * (data.T @ errors)

            # 梯度被相似度加权
            local_params = local_params - lr * gradients * domain_similarity

        target_updates.append(local_params - global_params)

    # 3. 聚合(源域权重更高)
    total_weight = sum(client_weights)
    normalized_weights = [w / total_weight for w in client_weights]

    aggregated_update = np.zeros_like(global_params)

    for i, weight in enumerate(normalized_weights):
        if i in source_clients:
            # 源域客户端给予更高权重
            update = source_updates[source_clients.index(i)]
            aggregated_update += weight * 1.5 * update
        elif i in target_clients:
            update = target_updates[target_clients.index(i)]
            aggregated_update += weight * update

    return global_params + aggregated_update


def transfer_based_initialization(
    source_models: List[np.ndarray],
    target_dim: int
) -> np.ndarray:
    """
    基于迁移的模型初始化

    使用源域模型的通用特征初始化目标域模型

    Args:
        source_models: 源域模型参数列表
        target_dim: 目标模型维度

    Returns:
        初始化后的目标模型参数
    """
    # 对源域模型参数进行平均
    source_avg = np.mean(source_models, axis=0)

    # 如果维度不同,需要进行映射
    if len(source_avg) != target_dim:
        # 简化的线性映射
        # 实际上可以使用PCA或学习到的映射函数
        if target_dim > len(source_avg):
            # 填充
            init_params = np.zeros(target_dim)
            init_params[:len(source_avg)] = source_avg
            init_params[len(source_avg):] = np.mean(source_avg)
        else:
            # 截断+填充
            init_params = source_avg[:target_dim]
    else:
        init_params = source_avg.copy()

    return init_params


def run_federated_transfer_learning(
    n_clients: int,
    model_dim: int,
    n_rounds: int,
    local_epochs: int,
    lr: float,
    source_domain: int = 0,
    n_source_clients: int = 2,
    data_per_client: int = 100,
    test_size: int = 500,
    seed: int = 42
) -> Dict:
    """
    运行联邦迁移学习

    Args:
        n_clients: 总客户端数
        model_dim: 模型维度
        n_rounds: 训练轮数
        local_epochs: 本地训练轮数
        lr: 学习率
        source_domain: 源域ID
        n_source_clients: 源域客户端数量
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
    client_domains = []

    for i in range(n_clients):
        # 根据ID确定域
        if i < n_source_clients:
            domain = source_domain
            noise_scale = 0.1  # 源域数据质量高
        else:
            domain = i % 3 + 1  # 目标域有多个子域
            noise_scale = 0.3 + 0.2 * (i / n_clients)  # 目标域数据质量低

        X = np.random.randn(data_per_client, model_dim)
        y = X @ w_true + np.random.randn(data_per_client) * noise_scale

        client_data_list.append((X, y))
        client_weights.append(float(data_per_client))
        client_domains.append(domain)

    X_test = np.random.randn(test_size, model_dim)
    y_test = X_test @ w_true + np.random.randn(test_size) * 0.1

    global_params = np.random.randn(model_dim) * np.sqrt(2.0 / model_dim)

    history = {"rounds": [], "test_mse": []}

    print(f"联邦迁移学习: {n_source_clients}个源域客户端, "
          f"{n_clients - n_source_clients}个目标域客户端")

    for round_idx in range(n_rounds):
        global_params = federated_transfer_learning_round(
            global_params, client_data_list, client_weights, client_domains,
            local_epochs, lr, source_domain
        )

        predictions = X_test @ global_params
        mse = np.mean((predictions - y_test) ** 2)

        history["rounds"].append(round_idx + 1)
        history["test_mse"].append(mse)

        if (round_idx + 1) % 5 == 0 or round_idx == 0:
            print(f"轮次 {round_idx + 1}/{n_rounds} | MSE: {mse:.6f}")

    return {"final_params": global_params, "history": history}


def run_knowledge_distillation_fl(
    n_clients: int,
    model_dim: int,
    n_rounds: int,
    local_epochs: int,
    lr: float,
    temperature: float = 2.0,
    data_per_client: int = 100,
    test_size: int = 500,
    seed: int = 42
) -> Dict:
    """
    运行基于知识蒸馏的联邦学习

    Args:
        n_clients: 客户端数量
        model_dim: 模型维度
        n_rounds: 训练轮数
        local_epochs: 本地训练轮数
        lr: 学习率
        temperature: 蒸馏温度
        data_per_client: 每客户端数据量
        test_size: 测试集大小
        seed: 随机种子

    Returns:
        训练结果字典
    """
    np.random.seed(seed)

    w_true = np.random.randn(model_dim) * 0.5

    client_data_list = []
    for i in range(n_clients):
        noise_scale = 0.1 + 0.2 * (i / n_clients)
        X = np.random.randn(data_per_client, model_dim)
        y = X @ w_true + np.random.randn(data_per_client) * noise_scale
        client_data_list.append((X, y))

    X_test = np.random.randn(test_size, model_dim)
    y_test = X_test @ w_true + np.random.randn(test_size) * 0.1

    global_params = np.random.randn(model_dim) * np.sqrt(2.0 / model_dim)

    history = {"rounds": [], "test_mse": []}

    print(f"知识蒸馏FL: temperature={temperature}")

    for round_idx in range(n_rounds):
        client_params = []

        # 本地训练
        for data, labels in client_data_list:
            local_params = global_params.copy()
            n_samples = len(labels)

            for _ in range(local_epochs):
                predictions = data @ local_params
                errors = predictions - labels
                gradients = (1.0 / n_samples) * (data.T @ errors)
                local_params = local_params - lr * gradients

            client_params.append(local_params)

        # 知识蒸馏
        global_params = knowledge_distillation(
            client_params, global_params,
            temperature=temperature, alpha=0.5
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
    print("联邦迁移学习演示")
    print("=" * 60)

    print("\n--- 联邦迁移学习 ---")
    result = run_federated_transfer_learning(
        n_clients=5,
        model_dim=10,
        n_rounds=20,
        local_epochs=5,
        lr=0.1,
        source_domain=0,
        n_source_clients=2,
        data_per_client=200,
        test_size=500,
        seed=42
    )
    print(f"最终MSE: {result['history']['test_mse'][-1]:.6f}")

    print("\n--- 知识蒸馏FL ---")
    result = run_knowledge_distillation_fl(
        n_clients=5,
        model_dim=10,
        n_rounds=20,
        local_epochs=5,
        lr=0.1,
        temperature=2.0,
        data_per_client=200,
        test_size=500,
        seed=42
    )
    print(f"最终MSE: {result['history']['test_mse'][-1]:.6f}")

    print("\n" + "=" * 60)
    print("训练完成!")
    print("=" * 60)
