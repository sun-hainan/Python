"""
线性回归 (Linear Regression) - 中文注释版
==========================================

问题定义：
    线性回归是最基础的回归算法，用于预测连续值输出。
    目标是找到一条直线（或超平面），使得预测值与真实值的误差最小。

模型公式：
    y = θ^T * x = θ0 + θ1*x1 + θ2*x2 + ...

    其中：
    - y: 预测值
    - x: 特征向量
    - θ: 参数向量（权重）

损失函数（均方误差 MSE）：
    J(θ) = (1/m) * Σ(预测值 - 真实值)²

优化方法：
    梯度下降法（Gradient Descent）

评价指标：
    - MSE（均方误差）
    - MAE（平均绝对误差）
    - R²（决定系数）
"""

import numpy as np


def run_steep_gradient_descent(data_x, data_y, len_data, alpha, theta):
    """
    梯度下降更新参数

    公式：θ = θ - (α/m) * X^T * (X*θ - y)

    参数:
        data_x: 特征矩阵
        data_y: 目标值向量
        len_data: 样本数量
        alpha: 学习率
        theta: 当前参数

    返回:
        更新后的参数
    """
    n = len_data
    # 计算预测误差
    prod = np.dot(theta, data_x.transpose())
    prod -= data_y.transpose()
    # 计算梯度并更新
    sum_grad = np.dot(prod, data_x)
    theta = theta - (alpha / n) * sum_grad
    return theta


def sum_of_square_error(data_x, data_y, len_data, theta):
    """
    计算均方误差（MSE）

    MSE = (1/2m) * Σ(预测值 - 真实值)²
    """
    prod = np.dot(theta, data_x.transpose())
    prod -= data_y.transpose()
    sum_elem = np.sum(np.square(prod))
    return sum_elem / (2 * len_data)


def run_linear_regression(data_x, data_y):
    """
    线性回归主函数

    参数:
        data_x: 特征矩阵（第一列为偏置1）
        data_y: 目标值向量

    返回:
        训练好的参数向量
    """
    iterations = 100000
    alpha = 0.0001550  # 学习率

    no_features = data_x.shape[1]
    len_data = data_x.shape[0] - 1

    theta = np.zeros((1, no_features))

    for i in range(iterations):
        theta = run_steep_gradient_descent(data_x, data_y, len_data, alpha, theta)
        error = sum_of_square_error(data_x, data_y, len_data, theta)

    return theta


def mean_absolute_error(predicted_y, original_y):
    """
    计算平均绝对误差（MAE）

    MAE = (1/m) * Σ|预测值 - 真实值|
    """
    total = sum(abs(y - predicted_y[i]) for i, y in enumerate(original_y))
    return total / len(original_y)


if __name__ == "__main__":
    # 示例：假设有房价数据
    # features: [面积, 卧室数, 房龄]
    # target: 价格
    X = np.array([
        [1, 1400, 3, 10],  # 偏置 + 特征
        [1, 1600, 3, 8],
        [1, 1700, 2, 5],
        [1, 1875, 4, 3],
    ])
    y = np.array([245000, 312000, 279000, 308000])

    theta = run_linear_regression(X, y)
    print(f"训练好的参数: {theta}")

    # 预测
    new_house = np.array([[1, 1500, 3, 7]])
    prediction = np.dot(new_house, theta.T)
    print(f"预测房价: {prediction[0]:.2f}")
