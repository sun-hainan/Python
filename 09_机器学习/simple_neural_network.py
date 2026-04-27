# -*- coding: utf-8 -*-
"""
算法实现：09_机器学习 / simple_neural_network

本文件实现 simple_neural_network 相关的算法功能。
"""

import math
import random


def sigmoid_function(value: float, deriv: bool = False) -> float:
    """
    Sigmoid 激活函数

    参数:
        value: 输入值
        deriv: 是否返回导数

    返回:
        sigmoid(value) 或 sigmoid'(value)

    示例:
        >>> sigmoid_function(3.5)
        0.9706877692486436
        >>> sigmoid_function(0.5, deriv=True)
        0.25
    """
    if deriv:
        return value * (1 - value)  # sigmoid 的导数
    return 1 / (1 + math.exp(-value))


# 学习率
LEARNING_RATE = 0.02


def forward_propagation(expected: int, number_propagations: int) -> float:
    """
    简单神经网络训练（单层感知机）

    参数:
        expected: 期望输出（作为百分比，如 32 表示 32%）
        number_propagations: 训练迭代次数

    返回:
        训练后的预测值
    """
    # 初始化随机权重
    weight = float(2 * (random.randint(1, 100)) - 1)

    for _ in range(number_propagations):
        # 前向传播
        layer_1 = sigmoid_function(LEARNING_RATE * weight)

        # 计算误差
        layer_1_error = (expected / 100) - layer_1

        # 反向传播：计算梯度并更新权重
        layer_1_delta = layer_1_error * sigmoid_function(layer_1, deriv=True)
        weight += LEARNING_RATE * layer_1_delta

    return layer_1 * 100


if __name__ == "__main__":
    print("=" * 50)
    print("神经网络前向传播演示")
    print("=" * 50)

    # 测试不同迭代次数的效果
    expected = 32
    print(f"\n期望输出: {expected}%")

    for iters in [1000, 10000, 100000, 500000]:
        result = forward_propagation(expected, iters)
        print(f"迭代 {iters:>7}: 预测 = {result:.2f}%")

    print("\n注意：迭代次数越多，预测越接近期望值")
