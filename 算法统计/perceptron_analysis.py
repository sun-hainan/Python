# -*- coding: utf-8 -*-
"""
算法实现：算法统计 / perceptron_analysis

本文件实现 perceptron_analysis 相关的算法功能。
"""

import random
import numpy as np
from typing import List, Tuple


class Perceptron:
    """感知器"""

    def __init__(self, n_features: int):
        """
        参数：
            n_features: 特征数
        """
        self.n_features = n_features
        self.weights = np.zeros(n_features)
        self.bias = 0.0
        self.learning_rate = 1.0

    def predict(self, x: List[float]) -> int:
        """
        预测

        返回：类别 (0或1)
        """
        activation = np.dot(self.weights, x) + self.bias
        return 1 if activation >= 0 else 0

    def fit(self, X: List[List[float]], y: List[int],
           max_iter: int = 1000) -> dict:
        """
        训练感知器

        参数：
            X: 特征矩阵
            y: 标签
            max_iter: 最大迭代

        返回：训练结果
        """
        n_samples = len(X)
        updates = 0

        for iteration in range(max_iter):
            errors = 0

            for i in range(n_samples):
                prediction = self.predict(X[i])

                if prediction != y[i]:
                    # 更新权重
                    error = y[i] - prediction
                    self.weights += self.learning_rate * error * np.array(X[i])
                    self.bias += self.learning_rate * error
                    errors += 1
                    updates += 1

            if errors == 0:
                break

        return {
            'iterations': iteration + 1,
            'updates': updates,
            'converged': errors == 0
        }

    def margin(self, X: List[List[float]], y: List[int]) -> float:
        """
        计算几何间隔

        返回：最小间隔
        """
        min_margin = float('inf')

        for i, x in enumerate(X):
            activation = y[i] * (np.dot(self.weights, x) + self.bias)
            margin = activation / np.linalg.norm(self.weights)

            if margin < min_margin:
                min_margin = margin

        return min_margin if min_margin > 0 else 0


def perceptron_convergence():
    """感知器收敛"""
    print("=== 感知器收敛性 ===")
    print()
    print("Novikoff定理：")
    print("  - 如果数据线性可分")
    print("  - 存在间隔 γ > 0")
    print("  - 感知器在 O(R²/γ²) 步收敛")
    print()
    print("其中：")
    print("  - R = max(||x||)")
    print("  - γ = 几何间隔")
    print()
    print("如果数据不可分：")
    print("  - 感知器可能不收敛")
    print("  - 会震荡或持续错误")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 感知器分析测试 ===\n")

    np.random.seed(42)

    # 创建线性可分数据
    n_samples = 100
    n_features = 2

    X = []
    y = []

    # 类0：中心在(-1, -1)
    for _ in range(n_samples // 2):
        x = np.random.randn(n_features) + np.array([-1, -1])
        X.append(x.tolist())
        y.append(0)

    # 类1：中心在(1, 1)
    for _ in range(n_samples // 2):
        x = np.random.randn(n_features) + np.array([1, 1])
        X.append(x.tolist())
        y.append(1)

    # 训练感知器
    perceptron = Perceptron(n_features)

    print(f"样本数: {len(X)}")
    print(f"特征数: {n_features}")
    print()

    result = perceptron.fit(X, y, max_iter=1000)

    print(f"训练结果:")
    print(f"  迭代次数: {result['iterations']}")
    print(f"  权重更新: {result['updates']}")
    print(f"  收敛: {'是' if result['converged'] else '否'}")
    print()

    # 计算间隔
    margin = perceptron.margin(X, y)
    print(f"几何间隔: {margin:.4f}")

    # 测试预测
    test_x = [[0.5, 0.5], [-0.5, -0.5]]
    print(f"\n测试预测:")
    for x in test_x:
        pred = perceptron.predict(x)
        print(f"  {x} -> {pred}")

    print()
    perceptron_convergence()

    print()
    print("说明：")
    print("  - 感知器是神经网络基础")
    print("  - 线性可分时保证收敛")
    print("  - 不可分时可能不收敛")
