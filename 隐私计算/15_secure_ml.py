# -*- coding: utf-8 -*-
"""
算法实现：隐私计算 / 15_secure_ml

本文件实现 15_secure_ml 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple, Dict
import hashlib


class SecureInference:
    """
    安全推理

    使用同态加密在密文上执行推理
    """

    def __init__(self, model_params: np.ndarray):
        """
        初始化安全推理器

        Args:
            model_params: 模型参数
        """
        self.model_params = model_params
        self.modulus = 2**31 - 1

    def encrypt_input(self, x: float, key: int = 42) -> int:
        """
        加密输入

        Args:
            x: 输入值
            key: 加密密钥

        Returns:
            密文
        """
        # 简化的加密
        return int(x * 1000 + key) % self.modulus

    def decrypt_output(self, ciphertext: int, key: int = 42) -> float:
        """
        解密输出

        Args:
            ciphertext: 密文
            key: 解密密钥

        Returns:
            明文
        """
        return (ciphertext - key) / 1000.0

    def predict_single(self, x: float, key: int = 42) -> float:
        """
        安全预测单个输入

        Args:
            x: 输入
            key: 密钥

        Returns:
            预测结果
        """
        # 加密输入
        encrypted_x = self.encrypt_input(x, key)

        # 在密文上计算 (简化的线性模型)
        # 密文推理: E(y) = E(x) * w
        encrypted_y = (encrypted_x * int(self.model_params[0])) % self.modulus
        for w in self.model_params[1:]:
            encrypted_y = (encrypted_y + encrypted_x * int(w)) % self.modulus

        # 解密输出
        return self.decrypt_output(encrypted_y, key)


class PrivacyPreservingML:
    """
    隐私保护机器学习

    结合差分隐私和联邦学习
    """

    def __init__(self, epsilon: float = 1.0):
        """
        初始化

        Args:
            epsilon: 隐私预算
        """
        self.epsilon = epsilon
        self.model_params = None

    def add_noise_to_gradient(self, gradient: np.ndarray, sensitivity: float = 1.0) -> np.ndarray:
        """
        添加噪声到梯度

        Args:
            gradient: 原始梯度
            sensitivity: 敏感度

        Returns:
            加噪梯度
        """
        scale = sensitivity / self.epsilon
        noise = np.random.laplace(0, scale, gradient.shape)
        return gradient + noise

    def train_with_dp(
        self,
        train_data: np.ndarray,
        train_labels: np.ndarray,
        n_epochs: int = 10,
        lr: float = 0.1
    ) -> np.ndarray:
        """
        差分隐私训练

        Args:
            train_data: 训练数据
            train_labels: 训练标签
            n_epochs: 训练轮数
            lr: 学习率

        Returns:
            训练后的模型参数
        """
        n_samples, n_features = train_data.shape
        self.model_params = np.random.randn(n_features) * 0.01

        for epoch in range(n_epochs):
            # 计算梯度
            predictions = train_data @ self.model_params
            errors = predictions - train_labels
            gradients = (1.0 / n_samples) * (train_data.T @ errors)

            # 添加噪声
            noisy_gradients = self.add_noise_to_gradient(gradients)

            # 更新
            self.model_params = self.model_params - lr * noisy_gradients

        return self.model_params


class SecureAggregation:
    """
    安全聚合

    在联邦学习中安全地聚合模型更新
    """

    def __init__(self, n_parties: int):
        """
        初始化安全聚合

        Args:
            n_parties: 参与方数量
        """
        self.n_parties = n_parties
        self.secret_shares = []

    def share_secret(self, secret: np.ndarray) -> List[np.ndarray]:
        """
        将秘密分享给各方

        Args:
            secret: 要分享的秘密

        Returns:
            分享列表
        """
        np.random.seed(42)
        shares = []

        # 生成n-1个随机份额
        for _ in range(self.n_parties - 1):
            share = np.random.randn(*secret.shape) * 0.1
            shares.append(share)

        # 最后一个份额使得总和等于原秘密
        sum_shares = np.sum(shares, axis=0)
        last_share = secret - sum_shares
        shares.append(last_share)

        self.secret_shares = shares
        return shares

    def aggregate(self, shares: List[np.ndarray]) -> np.ndarray:
        """
        聚合秘密份额

        Args:
            shares: 各方分享的份额

        Returns:
            聚合结果
        """
        return np.sum(shares, axis=0)

    def secure_aggregate_updates(
        self,
        updates: List[np.ndarray],
        mask_func=None
    ) -> np.ndarray:
        """
        安全聚合模型更新

        Args:
            updates: 各方的模型更新
            mask_func: 可选的掩码函数

        Returns:
            聚合后的更新
        """
        # 简化的安全聚合
        # 实际使用秘密共享和验证
        return np.mean(updates, axis=0)


class ModelIntegrityVerification:
    """
    模型完整性验证

    验证模型更新没有被篡改
    """

    def __init__(self):
        """初始化验证器"""
        self.model_hashes = {}

    def compute_model_hash(self, model_params: np.ndarray) -> str:
        """
        计算模型哈希

        Args:
            model_params: 模型参数

        Returns:
            哈希字符串
        """
        params_bytes = model_params.tobytes()
        return hashlib.sha256(params_bytes).hexdigest()

    def register_model(self, model_id: str, model_params: np.ndarray):
        """
        注册模型哈希

        Args:
            model_id: 模型ID
            model_params: 模型参数
        """
        model_hash = self.compute_model_hash(model_params)
        self.model_hashes[model_id] = model_hash

    def verify_model(self, model_id: str, model_params: np.ndarray) -> bool:
        """
        验证模型完整性

        Args:
            model_id: 模型ID
            model_params: 模型参数

        Returns:
            是否通过验证
        """
        if model_id not in self.model_hashes:
            return False

        current_hash = self.compute_model_hash(model_params)
        return current_hash == self.model_hashes[model_id]


class SecureMLPipeline:
    """
    完整的安全ML流程

    整合多种安全技术
    """

    def __init__(self, model_dim: int, epsilon: float = 1.0):
        """
        初始化安全ML流程

        Args:
            model_dim: 模型维度
            epsilon: 隐私预算
        """
        self.model_dim = model_dim
        self.privacy_ml = PrivacyPreservingML(epsilon)
        self.model_verification = ModelIntegrityVerification()
        self.global_params = np.random.randn(model_dim) * 0.01

    def secure_train_round(
        self,
        client_data_list: List[Tuple[np.ndarray, np.ndarray]],
        client_weights: List[float]
    ) -> np.ndarray:
        """
        执行一轮安全训练

        Args:
            client_data_list: 客户端数据
            client_weights: 客户端权重

        Returns:
            更新后的全局参数
        """
        n_clients = len(client_data_list)
        total_weight = sum(client_weights)

        aggregated_update = np.zeros_like(self.global_params)

        for i, (data, labels) in enumerate(client_data_list):
            # 本地训练
            local_params = self.privacy_ml.train_with_dp(
                data, labels, n_epochs=1, lr=0.1
            )

            # 计算更新
            update = local_params - self.global_params

            # 加权
            weight = client_weights[i] / total_weight
            aggregated_update += weight * update

        return self.global_params + aggregated_update


def secure_ml_demo():
    """
    安全机器学习演示
    """

    print("安全机器学习演示")
    print("=" * 60)

    np.random.seed(42)

    # 1. 安全推理
    print("\n1. 安全推理 (同态加密)")
    model = np.array([0.5, -0.3, 0.8])
    inferrer = SecureInference(model)

    test_input = 2.5
    result = inferrer.predict_single(test_input)
    print(f"   模型: {model}")
    print(f"   输入: {test_input}")
    print(f"   预测: {result:.4f}")

    # 2. 差分隐私训练
    print("\n2. 差分隐私机器学习")
    dp_ml = PrivacyPreservingML(epsilon=1.0)

    X = np.random.randn(100, 5)
    y = X @ np.random.randn(5) + np.random.randn(100) * 0.1

    trained_params = dp_ml.train_with_dp(X, y, n_epochs=10, lr=0.1)
    print(f"   训练后参数: {trained_params[:3]}...")

    # 3. 安全聚合
    print("\n3. 安全聚合 (秘密共享)")
    aggregator = SecureAggregation(n_parties=3)

    secret = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    shares = aggregator.share_secret(secret)

    print(f"   原始秘密: {secret}")
    for i, share in enumerate(shares):
        print(f"   份额{i+1}: {share}")

    reconstructed = aggregator.aggregate(shares)
    print(f"   重构: {reconstructed}")

    # 4. 模型完整性验证
    print("\n4. 模型完整性验证")
    verifier = ModelIntegrityVerification()

    model_params = np.random.randn(10)
    verifier.register_model("round_0", model_params)

    print(f"   注册模型哈希: {verifier.model_hashes['round_0'][:16]}...")

    # 验证原始模型
    is_valid = verifier.verify_model("round_0", model_params)
    print(f"   原始模型验证: {'通过 ✓' if is_valid else '失败 ✗'}")

    # 验证被篡改的模型
    tampered_params = model_params + 0.1
    is_valid = verifier.verify_model("round_0", tampered_params)
    print(f"   篡改模型验证: {'通过 ✓' if is_valid else '失败 ✗ (检测到篡改)'}")

    # 5. 完整安全ML流程
    print("\n5. 完整安全ML流程")
    pipeline = SecureMLPipeline(model_dim=5, epsilon=1.0)

    # 创建客户端数据
    client_data = []
    for i in range(3):
        X = np.random.randn(50, 5)
        y = X @ np.random.randn(5) + np.random.randn(50) * 0.1
        client_data.append((X, y))

    client_weights = [50, 50, 50]

    print(f"   执行3方安全联邦学习...")

    for round_idx in range(3):
        new_params = pipeline.secure_train_round(client_data, client_weights)
        print(f"   轮次{round_idx + 1}完成")


if __name__ == "__main__":
    secure_ml_demo()

    print("\n" + "=" * 60)
    print("安全机器学习演示完成!")
    print("=" * 60)
