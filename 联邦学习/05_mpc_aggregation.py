# -*- coding: utf-8 -*-
"""
算法实现：联邦学习 / 05_mpc_aggregation

本文件实现 05_mpc_aggregation 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Dict
import hashlib


class SecretShare:
    """
    秘密共享类 - 实现加法秘密共享

    加法秘密共享: 将秘密s拆分为n个份额s1, s2, ..., sn
    使得 s = s1 + s2 + ... + sn
    任意少于n个份额无法推断出任何关于s的信息
    """

    def __init__(self, n_parties: int = 3, prime: int = None):
        """
        初始化秘密共享

        Args:
            n_parties: 份额数量(参与方数量)
            prime: 大素数模数,默认为2^61-1(Mersenne素数)
        """
        self.n_parties = n_parties
        # 使用大素数保证运算安全性
        self.prime = prime if prime else (1 << 61) - 1

    def share(self, secret: np.ndarray) -> List[np.ndarray]:
        """
        将秘密拆分为n个份额

        步骤:
        1. 生成n-1个随机数作为前n-1个份额
        2. 最后一个份额 = 秘密 - sum(前n-1个份额) mod prime

        Args:
            secret: 要分享的秘密(数值或向量)

        Returns:
            n个份额的列表
        """
        shares = []
        # 生成n-1个随机份额
        for _ in range(self.n_parties - 1):
            share = np.random.randint(0, self.prime, secret.shape, dtype=np.int64)
            shares.append(share)

        # 计算最后一个份额使得总和等于秘密
        sum_shares = np.sum(shares, axis=0)
        last_share = (secret.astype(np.int64) - sum_shares) % self.prime
        shares.append(last_share)

        return shares

    def reconstruct(self, shares: List[np.ndarray]) -> np.ndarray:
        """
        重构秘密 - 将所有份额相加

        Args:
            shares: n个份额的列表

        Returns:
            重构的秘密值
        """
        total = np.sum(shares, axis=0) % self.prime
        return total.astype(np.float64)


class AdditiveHomomorphicEncryption:
    """
    加法同态加密模拟类

    简化版的Paillier加密系统:
    - 加密: E(m) = g^m * r^n mod n^2
    - 加法: E(m1) * E(m2) = E(m1 + m2)
    - 标量乘法: E(m)^k = E(k*m)

    这里使用简化的模拟版本便于演示原理
    """

    def __init__(self, key_size: int = 256):
        """
        初始化加密系统

        Args:
            key_size: 密钥位长(模拟用小值)
        """
        self.key_size = key_size
        # 生成密钥对(简化版)
        np.random.seed(42)
        self.public_key = 999979  # n (两个大素数的乘积)
        self.private_key = None   # lambda (简化不实现解密演示)

    def encrypt(self, plaintext: np.ndarray) -> np.ndarray:
        """
        模拟加密 - 将明文转换为密文

        实际使用Paillier: E(m) = (1 + n*m) * r^n mod n^2
        简化版: 直接添加随机掩码模拟密文

        Args:
            plaintext: 明文数组

        Returns:
            密文数组
        """
        # 添加随机掩码模拟加密效果
        mask = np.random.randint(1, 1000, plaintext.shape)
        ciphertext = plaintext + mask * self.public_key
        return ciphertext

    def decrypt(self, ciphertext: np.ndarray) -> np.ndarray:
        """
        模拟解密 - 恢复明文(实际需要私钥)

        这里简化: 假设知道掩码能解密
        实际Paillier需要使用欧拉函数和中国剩余定理

        Args:
            ciphertext: 密文数组

        Returns:
            解密后的明文
        """
        # 简化: 假设能恢复明文
        return ciphertext % self.public_key

    def add(self, ciphertext1: np.ndarray, ciphertext2: np.ndarray) -> np.ndarray:
        """
        密文加法 - E(m1) + E(m2) = E(m1 + m2)

        在密文上直接相加即可得到密文形式的和

        Args:
            ciphertext1: 第一个密文
            ciphertext2: 第二个密文

        Returns:
            密文形式的和
        """
        return ciphertext1 + ciphertext2

    def scalar_multiply(self, ciphertext: np.ndarray, scalar: float) -> np.ndarray:
        """
        密文标量乘法 - k * E(m) = E(k*m)

        将密文重复相加(模拟乘法效果)

        Args:
            ciphertext: 密文
            scalar: 标量系数

        Returns:
            密文形式的标量乘积
        """
        return ciphertext * scalar


def mpc_federated_aggregate(
    client_params_list: List[np.ndarray],
    client_weights: List[float],
    use_encryption: bool = True
) -> np.ndarray:
    """
    基于MPC的联邦聚合

    完整流程:
    1. 客户端将参数秘密分享给多个计算方
    2. 各计算方对收到的份额进行聚合
    3. 汇总所有份额重构得到最终结果

    Args:
        client_params_list: 各客户端的模型参数列表
        client_weights: 各客户端的权重
        use_encryption: 是否使用加法同态加密

    Returns:
        聚合后的全局模型参数
    """
    n_clients = len(client_params_list)

    if client_weights is None:
        client_weights = [1.0 / n_clients] * n_clients

    total_weight = sum(client_weights)
    normalized_weights = [w / total_weight for w in client_weights]

    # 加法同态加密聚合
    if use_encryption:
        encryption = AdditiveHomomorphicEncryption()
        aggregated = np.zeros_like(client_params_list[0])

        for params, weight in zip(client_params_list, normalized_weights):
            # 加密参数
            encrypted_params = encryption.encrypt(params)
            # 密文加权
            weighted = encryption.scalar_multiply(encrypted_params, weight)
            # 密文累加
            aggregated = encryption.add(aggregated, weighted)

        # 解密得到结果
        result = encryption.decrypt(aggregated)
        return result

    # 秘密共享方式聚合
    else:
        secret_sharing = SecretShare(n_parties=3)
        n_shares = secret_sharing.n_parties

        # 每个计算方维护一个累加器
        accumulators = [np.zeros_like(client_params_list[0]) for _ in range(n_shares)]

        for params, weight in zip(client_params_list, normalized_weights):
            # 分享参数
            shares = secret_sharing.share(params.astype(np.int64))
            # 权重化并分发给各计算方
            for i, share in enumerate(shares):
                accumulators[i] += weight * share

        # 各计算方将自己累加结果发给可信第三方(模拟)
        # TTP将所有累加结果相加
        total = np.sum(accumulators, axis=0)
        return secret_sharing.reconstruct([total, total, total]) / n_shares


def local_train_secure(
    global_params: np.ndarray,
    train_data: np.ndarray,
    train_labels: np.ndarray,
    local_epochs: int,
    learning_rate: float
) -> np.ndarray:
    """
    本地训练 - 与标准FedAvg相同

    Args:
        global_params: 当前全局模型参数
        train_data: 本地训练数据
        train_labels: 本地训练标签
        local_epochs: 本地训练轮数
        learning_rate: 学习率

    Returns:
        更新后的本地模型参数
    """
    local_params = global_params.copy()
    n_samples = len(train_labels)

    for _ in range(local_epochs):
        predictions = train_data @ local_params
        errors = predictions - train_labels
        gradients = (1.0 / n_samples) * (train_data.T @ errors)
        local_params = local_params - learning_rate * gradients

    return local_params


def run_mpc_federated_learning(
    n_clients: int,
    model_dim: int,
    n_rounds: int,
    local_epochs: int,
    learning_rate: float,
    use_encryption: bool = True,
    data_per_client: int = 100,
    test_size: int = 500,
    seed: int = 42
) -> Dict:
    """
    运行基于MPC的联邦学习

    Args:
        n_clients: 客户端数量
        model_dim: 模型参数维度
        n_rounds: 联邦通信轮数
        local_epochs: 每轮本地训练epoch数
        learning_rate: 学习率
        use_encryption: 是否使用加密方式
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
    client_weights = [1.0 / n_clients] * n_clients

    history = {"rounds": [], "test_mse": []}

    mode_name = "加法同态加密" if use_encryption else "秘密共享"
    print(f"MPC联邦学习: 使用{mode_name}")

    for round_idx in range(n_rounds):
        client_params = []

        for data, labels in client_data_list:
            params = local_train_secure(
                global_params, data, labels, local_epochs, learning_rate
            )
            client_params.append(params)

        # MPC聚合
        global_params = mpc_federated_aggregate(
            client_params, client_weights, use_encryption
        )

        # 评估
        predictions = X_test @ global_params
        mse = np.mean((predictions - y_test) ** 2)

        history["rounds"].append(round_idx + 1)
        history["test_mse"].append(mse)

        if (round_idx + 1) % 5 == 0 or round_idx == 0:
            print(f"轮次 {round_idx + 1}/{n_rounds} | MSE: {mse:.6f}")

    return {"final_params": global_params, "history": history}


if __name__ == "__main__":
    print("=" * 60)
    print("联邦学习 - 安全多方计算(MPC)聚合演示")
    print("=" * 60)

    result = run_mpc_federated_learning(
        n_clients=5,
        model_dim=10,
        n_rounds=20,
        local_epochs=5,
        learning_rate=0.1,
        use_encryption=True,
        data_per_client=200,
        test_size=500,
        seed=42
    )

    print("\n" + "=" * 60)
    print("训练完成!")
    print(f"最终MSE: {result['history']['test_mse'][-1]:.6f}")
    print("=" * 60)
