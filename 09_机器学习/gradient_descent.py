# -*- coding: utf-8 -*-
"""
算法实现：09_机器学习 / gradient_descent

本文件实现 gradient_descent 相关的算法功能。
"""

import numpy as np

# 训练数据：输入(x1, x2, x3) -> 输出y
train_data = (
    ((5, 2, 3), 15),
    ((6, 5, 9), 25),
    ((11, 12, 13), 41),
    ((1, 1, 1), 8),
    ((11, 12, 13), 41),
)
test_data = (((515, 22, 13), 555), ((61, 35, 49), 150))

# 初始参数向量 [偏置, w1, w2, w3]
parameter_vector = [2, 4, 1, 5]
m = len(train_data)
LEARNING_RATE = 0.009


def _hypothesis_value(data_input_tuple):
    """
    假设函数（预测值）
    h(x) = θ0 + θ1*x1 + θ2*x2 + θ3*x3

    参数:
        data_input_tuple: 输入特征元组 (x1, x2, x3)

    返回:
        预测的输出值
    """
    hyp_val = 0
    for i in range(len(parameter_vector) - 1):
        hyp_val += data_input_tuple[i] * parameter_vector[i + 1]
    hyp_val += parameter_vector[0]  # 加上偏置项
    return hyp_val


def _error(example_no, data_set="train"):
    """
    计算单个样本的误差

    误差 = 预测值 - 真实值
    """
    return calculate_hypothesis_value(example_no, data_set) - output(example_no, data_set)


def output(example_no, data_set):
    """获取真实输出值"""
    if data_set == "train":
        return train_data[example_no][1]
    elif data_set == "test":
        return test_data[example_no][1]
    return None


def calculate_hypothesis_value(example_no, data_set):
    """计算假设函数值"""
    if data_set == "train":
        return _hypothesis_value(train_data[example_no][0])
    elif data_set == "test":
        return _hypothesis_value(test_data[example_no][0])
    return None


def summation_of_cost_derivative(index, end=m):
    """
    计算损失函数偏导数的累加和

    对于参数 θi：
    Σ(预测误差 * x_i) / m
    """
    summation_value = 0
    for i in range(end):
        if index == -1:
            # 偏置项的梯度
            summation_value += _error(i)
        else:
            # 其他参数的梯度
            summation_value += _error(i) * train_data[i][0][index]
    return summation_value


def get_cost_derivative(index):
    """
    获取代价函数相对于参数 index 的偏导数

    导数 = 累加和 / 样本数
    """
    return summation_of_cost_derivative(index, m) / m


def run_gradient_descent():
    """
    运行梯度下降算法

    迭代更新参数，直到收敛：
    θ_new = θ_old - α * 梯度
    """
    global parameter_vector

    absolute_error_limit = 0.000002

    iteration = 0
    while True:
        iteration += 1
        temp_parameter_vector = [0, 0, 0, 0]

        # 更新所有参数
        for i in range(len(parameter_vector)):
            cost_derivative = get_cost_derivative(i - 1)
            temp_parameter_vector[i] = parameter_vector[i] - LEARNING_RATE * cost_derivative

        # 检查是否收敛（参数变化小于阈值）
        if np.allclose(parameter_vector, temp_parameter_vector, atol=absolute_error_limit):
            break

        parameter_vector = temp_parameter_vector

    print(f"迭代次数: {iteration}")


def test_gradient_descent():
    """测试梯度下降结果"""
    for i in range(len(test_data)):
        print(f"真实输出: {output(i, 'test')}")
        print(f"预测输出: {calculate_hypothesis_value(i, 'test')}")


if __name__ == "__main__":
    run_gradient_descent()
    print("\n测试结果:")
    test_gradient_descent()
