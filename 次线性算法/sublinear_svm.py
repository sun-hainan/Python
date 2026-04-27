# -*- coding: utf-8 -*-
"""
算法实现：次线性算法 / sublinear_svm

本文件实现 sublinear_svm 相关的算法功能。
"""

import numpy as np
import random


def svm_pegasos(X, y, lambda_param=0.01, max_iter=1000, batch_size=1):
    """
    Pegasos: 次梯度 SVM 求解器
    
    算法:
    for t = 1, 2, ..., T:
        1. 随机选择一个小批次 A_t ⊆ {1,...,n}
        2. 计算 ∇_t = (1/|A_t|) Σ_{(x,y)∈A_t} max(0, 1 - y(w·x))
        3. w = w - η_t (λ w - ∇_t)
        4. w = min(1, 1/√λ ||w||) * w (投影)
    
    时间复杂度: O(d * T) 其中 d 是维度
    
    Parameters
    ----------
    X : np.ndarray
        训练数据,形状 (n_samples, n_features)
    y : np.ndarray
        标签, +1 或 -1
    lambda_param : float
        正则化参数 λ
    max_iter : int
        最大迭代次数
    batch_size : int
        小批次大小
    
    Returns
    -------
    np.ndarray
        学到的权重向量
    """
    n_samples, n_features = X.shape
    
    # 初始化权重
    w = np.zeros(n_features)
    
    for t in range(1, max_iter + 1):
        # 学习率: η_t = 1/(λ * t)
        eta = 1.0 / (lambda_param * t)
        
        # 随机选择批次
        indices = random.sample(range(n_samples), min(batch_size, n_samples))
        
        # 计算损失梯度
        gradient = np.zeros(n_features)
        
        for idx in indices:
            x_i = X[idx]
            y_i = y[idx]
            
            if y_i * np.dot(w, x_i) < 1:
                gradient -= y_i * x_i
        
        gradient /= len(indices)
        
        # 梯度步骤
        w = w - eta * (lambda_param * w - gradient)
        
        # 投影到半径 1/√λ 的球内
        norm_w = np.linalg.norm(w)
        if norm_w > 1.0 / np.sqrt(lambda_param):
            w = w * (1.0 / np.sqrt(lambda_param)) / norm_w
    
    return w


def coordinate_descent_svm(X, y, C=1.0, max_iter=100):
    """
    坐标下降 SVM (libsvm 风格)
    
    对每个坐标 i 求解:
    min_{α_i} W(α)
    其中 α_i 是一维优化变量
    
    时间复杂度: O(n^2 d) 最坏情况,但实践中更快
    
    Parameters
    ----------
    X : np.ndarray
        训练数据
    y : np.ndarray
        标签
    C : float
        惩罚参数
    max_iter : int
        最大迭代轮数
    
    Returns
    -------
    np.ndarray
        对偶变量 α
    """
    n_samples, n_features = X.shape
    
    # 初始化 α
    alpha = np.zeros(n_samples)
    
    # 预计算 X * y (用于快速计算梯度)
    X_y = X * y.reshape(-1, 1)  # n_samples x n_features
    
    # 迭代
    for iteration in range(max_iter):
        alpha_old = alpha.copy()
        
        for i in range(n_samples):
            # 计算当前梯度 (对 α_i 的偏导)
            grad_i = 1 - np.dot(X_y[i], X_y.T @ alpha)
            
            # 更新 α_i
            alpha[i] = np.clip(alpha[i] + grad_i / (X_y[i] @ X_y[i]), 0, C)
        
        # 检查收敛
        diff = np.sum(np.abs(alpha - alpha_old))
        if diff < 1e-6:
            print(f"在第 {iteration} 轮收敛")
            break
    
    return alpha


def svm_predict(X, w, b=0):
    """
    SVM 预测
    
    Parameters
    ----------
    X : np.ndarray
        测试数据
    w : np.ndarray
        权重向量
    b : float
        偏置
    
    Returns
    -------
    np.ndarray
        预测标签 (+1 或 -1)
    """
    scores = X @ w + b
    return np.sign(scores)


def sgd_svm_single(X, y, lr=0.01, lambda_reg=0.01, epochs=10):
    """
    SGD SVM (单次随机梯度下降)
    
    每次只用一个样本更新
    
    Parameters
    ----------
    X : np.ndarray
        训练数据
    y : np.ndarray
        标签
    lr : float
        学习率
    lambda_reg : float
        正则化参数
    epochs : int
        轮数
    
    Returns
    -------
    np.ndarray
        权重向量
    """
    n_samples, n_features = X.shape
    w = np.zeros(n_features)
    
    for epoch in range(epochs):
        # 打乱顺序
        indices = list(range(n_samples))
        random.shuffle(indices)
        
        for i in indices:
            x_i = X[i]
            y_i = y[i]
            
            # 计算 hinge 损失梯度
            if y_i * np.dot(w, x_i) < 1:
                gradient = w - y_i * x_i
            else:
                gradient = w
            
            # 更新
            w = w - lr * gradient
        
        # 衰减学习率
        lr *= 0.95
    
    return w


def random_feature_map(x, gamma, D=100):
    """
    随机傅里叶特征映射
    
    将 d 维 x 映射到 D 维特征
    使得 k(x, z) ≈ φ(x) · φ(z)
    
    其中 k(x,z) = exp(-γ||x-z||^2) 是 RBF 核
    
    Parameters
    ----------
    x : np.ndarray
        输入向量,形状 (d,)
    gamma : float
        RBF 核参数
    D : int
        特征维度
    
    Returns
    -------
    np.ndarray
        映射后的特征,形状 (D,)
    """
    d = len(x)
    
    # 采样频率
    w = np.random.normal(0, np.sqrt(2 * gamma), size=(D, d))
    
    # 采样偏移
    b = np.random.uniform(0, 2 * np.pi, size=D)
    
    # 计算映射
    z = x @ w.T + b
    phi = np.sqrt(2 / D) * np.cos(z)
    
    return phi


def kernel_approximation_svm(X, y, gamma=0.1, D=100, C=1.0, max_iter=100):
    """
    核 SVM 的线性近似
    
    使用随机特征映射将 RBF 核 SVM 转化为线性 SVM
    
    步骤:
    1. 将数据映射到随机特征空间
    2. 在新空间训练线性 SVM
    
    时间复杂度: O(n * D * max_iter)
    
    Parameters
    ----------
    X : np.ndarray
        训练数据
    y : np.ndarray
        标签
    gamma : float
        RBF 核参数
    D : int
        随机特征维度
    C : float
        SVM 惩罚参数
    max_iter : int
        最大迭代次数
    
    Returns
    -------
    tuple
        (映射后的权重, 映射函数)
    """
    n_samples, n_features = X.shape
    
    # 构建随机特征映射
    w_random = np.random.normal(0, np.sqrt(2 * gamma), size=(D, n_features))
    b_random = np.random.uniform(0, 2 * np.pi, size=D)
    
    def phi(x):
        z = x @ w_random.T + b_random
        return np.sqrt(2 / D) * np.cos(z)
    
    # 映射训练数据
    X_phi = np.array([phi(x) for x in X])
    
    # 训练线性 SVM (使用 SGD)
    w = sgd_svm_single(X_phi, y, lr=0.01, lambda_reg=1.0/(n_samples * C), epochs=max_iter)
    
    return w, phi


def coreset_svm(X, y, k, C=1.0):
    """
    核心集方法求解大规模 SVM
    
    从 n 个样本中选择 k 个代表性样本
    在核心集上训练 SVM
    
    时间复杂度: O(n log n) 用于选择核心集
    
    Parameters
    ----------
    X : np.ndarray
        训练数据
    y : np.ndarray
        标签
    k : int
        核心集大小
    C : float
        SVM 惩罚参数
    
    Returns
    -------
    np.ndarray
        核心集权重
    """
    n_samples, n_features = X.shape
    
    if k >= n_samples:
        # 返回所有样本,等权重
        return np.ones(n_samples)
    
    # 简化的核心集选择: 基于几何间隔
    # 计算每个样本的"重要性"分数
    
    # 近似计算 (简化版本)
    scores = np.sum(X ** 2, axis=1)  # 简化: 基于范数
    
    # 选择分数最高的 k 个样本
    indices = np.argsort(scores)[-k:]
    
    # 构建权重
    weights = np.zeros(n_samples)
    weights[indices] = 1.0
    
    return weights


def approximate_svm_training(X, y, method='pegasos', **kwargs):
    """
    次线性 SVM 训练的通用接口
    
    Parameters
    ----------
    X : np.ndarray
        训练数据
    y : np.ndarray
        标签
    method : str
        方法: 'pegasos', 'coordinate', 'kernel_approx'
    **kwargs : dict
        其他参数
    
    Returns
    -------
    tuple
        (权重向量, 方法特定的信息)
    """
    n_samples, n_features = X.shape
    
    if method == 'pegasos':
        lambda_param = kwargs.get('lambda_param', 0.01)
        max_iter = kwargs.get('max_iter', 1000)
        batch_size = kwargs.get('batch_size', 10)
        
        w = svm_pegasos(X, y, lambda_param, max_iter, batch_size)
        return w, {'method': 'pegasos', 'iterations': max_iter}
    
    elif method == 'coordinate':
        C = kwargs.get('C', 1.0)
        max_iter = kwargs.get('max_iter', 100)
        
        alpha = coordinate_descent_svm(X, y, C, max_iter)
        # 转换回原始权重
        w = (y * alpha) @ X
        return w, {'method': 'coordinate', 'alpha': alpha}
    
    elif method == 'kernel_approx':
        gamma = kwargs.get('gamma', 0.1)
        D = kwargs.get('D', 100)
        C = kwargs.get('C', 1.0)
        
        w, phi = kernel_approximation_svm(X, y, gamma, D, C)
        return w, {'method': 'kernel_approx', 'phi': phi}
    
    else:
        raise ValueError(f"未知方法: {method}")


def compute_accuracy(y_true, y_pred):
    """
    计算分类准确率
    
    Parameters
    ----------
    y_true : np.ndarray
        真实标签
    y_pred : np.ndarray
        预测标签
    
    Returns
    -------
    float
        准确率
    """
    return np.mean(y_true == y_pred)


if __name__ == "__main__":
    # 测试: 次线性 SVM
    
    print("=" * 60)
    print("次线性 SVM 算法测试")
    print("=" * 60)
    
    np.random.seed(42)
    random.seed(42)
    
    # 生成测试数据
    n_train = 500
    n_test = 100
    n_features = 20
    
    # 生成线性可分数据
    X_train = np.random.randn(n_train, n_features)
    w_true = np.random.randn(n_features)
    
    # 添加一些噪声
    y_train = np.sign(X_train @ w_true + np.random.randn(n_train) * 0.1)
    y_train[y_train == 0] = 1  # 确保标签为 ±1
    
    X_test = np.random.randn(n_test, n_features)
    y_test = np.sign(X_test @ w_true + np.random.randn(n_test) * 0.1)
    y_test[y_test == 0] = 1
    
    print(f"\n训练数据: {n_train} 样本, {n_features} 特征")
    print(f"测试数据: {n_test} 样本")
    print(f"正类比例: {np.mean(y_train == 1):.2f}")
    
    # 测试 Pegasos
    print("\n--- Pegasos SVM ---")
    
    w_pegasos = svm_pegasos(X_train, y_train, lambda_param=0.01, max_iter=500, batch_size=10)
    y_pred_pegasos = svm_predict(X_test, w_pegasos)
    acc_pegasos = compute_accuracy(y_test, y_pred_pegasos)
    
    print(f"权重范数: {np.linalg.norm(w_pegasos):.4f}")
    print(f"准确率: {acc_pegasos:.4f}")
    
    # 测试坐标下降
    print("\n--- 坐标下降 SVM ---")
    
    alpha = coordinate_descent_svm(X_train, y_train, C=1.0, max_iter=50)
    w_cd = (y_train * alpha) @ X_train
    y_pred_cd = svm_predict(X_test, w_cd)
    acc_cd = compute_accuracy(y_test, y_pred_cd)
    
    print(f"非零 α 数量 (支持向量数): {np.sum(alpha > 1e-6)}")
    print(f"准确率: {acc_cd:.4f}")
    
    # 测试 SGD SVM
    print("\n--- SGD SVM ---")
    
    w_sgd = sgd_svm_single(X_train, y_train, lr=0.01, lambda_reg=0.01, epochs=20)
    y_pred_sgd = svm_predict(X_test, w_sgd)
    acc_sgd = compute_accuracy(y_test, y_pred_sgd)
    
    print(f"权重范数: {np.linalg.norm(w_sgd):.4f}")
    print(f"准确率: {acc_sgd:.4f}")
    
    # 测试核近似
    print("\n--- 核近似 SVM (RBF) ---")
    
    w_kernel, phi = kernel_approximation_svm(X_train, y_train, gamma=0.1, D=50, C=1.0, max_iter=20)
    
    # 在测试数据上评估
    X_test_phi = np.array([phi(x) for x in X_test])
    y_pred_kernel = svm_predict(X_test_phi, w_kernel)
    acc_kernel = compute_accuracy(y_test, y_pred_kernel)
    
    print(f"随机特征维度: {D=}")
    print(f"准确率: {acc_kernel:.4f}")
    
    # 比较
    print("\n--- 方法比较 ---")
    print(f"Pegasos:      {acc_pegasos:.4f}")
    print(f"坐标下降:     {acc_cd:.4f}")
    print(f"SGD:          {acc_sgd:.4f}")
    print(f"核近似 RBF:   {acc_kernel:.4f}")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
