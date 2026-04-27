# -*- coding: utf-8 -*-
"""
算法实现：强化学习 / unscented_kalman

本文件实现 unscented_kalman 相关的算法功能。
"""

import numpy as np


class UnscentedTransform:
    """
    无迹变换

    计算 sigma 点和权重。
    """

    def __init__(self, alpha=0.001, beta=2.0, kappa=0.0):
        self.alpha = alpha
        self.beta = beta
        self.kappa = kappa

    def compute_sigma_points(self, x, P):
        """
        计算 sigma 点

        参数:
            x: 均值向量
            P: 协方差矩阵
        返回:
            sigma_points: sigma 点矩阵
            weights_mean: 均值权重
            weights_cov: 协方差权重
        """
        n = len(x)
        lam = self.alpha**2 * (n + self.kappa) - n

        # Cholesky 分解
        try:
            P_sqrt = np.linalg.cholesky((n + lam) * P)
        except:
            P_sqrt = np.eye(n) * np.sqrt(np.trace(P) / n)

        sigma_points = np.zeros((2 * n + 1, n))
        sigma_points[0] = x

        for i in range(n):
            sigma_points[i + 1] = x + P_sqrt[:, i]
            sigma_points[i + n + 1] = x - P_sqrt[:, i]

        # 权重
        wm = np.zeros(2 * n + 1)
        wc = np.zeros(2 * n + 1)
        wm[0] = lam / (n + lam)
        wc[0] = wm[0] + (1 - self.alpha**2 + self.beta)
        for i in range(1, 2 * n + 1):
            wm[i] = 1 / (2 * (n + lam))
            wc[i] = wm[i]

        return sigma_points, wm, wc


def unscented_kalman_filter(z, x, P, f, h, Q, R, alpha=0.001, beta=2.0, kappa=0.0):
    """
    UKF 单步更新

    参数:
        z: 观测
        x: 状态估计
        P: 协方差估计
        f: 非线性状态转移函数
        h: 非线性观测函数
        Q: 过程噪声协方差
        R: 观测噪声协方差
    返回:
        x_new: 更新后状态
        P_new: 更新后协方差
    """
    n = len(x)
    lam = alpha**2 * (n + kappa) - n

    # Sigma 点
    try:
        P_sqrt = np.linalg.cholesky((n + lam) * P)
    except:
        P_sqrt = np.eye(n) * np.sqrt(np.trace(P) / n)

    sigma = np.zeros((2 * n + 1, n))
    sigma[0] = x
    for i in range(n):
        sigma[i + 1] = x + P_sqrt[:, i]
        sigma[i + n + 1] = x - P_sqrt[:, i]

    # 权重
    wm = np.zeros(2 * n + 1)
    wc = np.zeros(2 * n + 1)
    wm[0] = lam / (n + lam)
    wc[0] = wm[0] + 1 - alpha**2 + beta
    for i in range(1, 2 * n + 1):
        wm[i] = 1 / (2 * (n + lam))
        wc[i] = wm[i]

    # 预测步骤
    sigma_pred = np.array([f(sp) for sp in sigma])
    x_pred = np.sum(wm[:, None] * sigma_pred, axis=0)
    P_pred = Q.copy()
    for i in range(len(sigma)):
        diff = sigma_pred[i] - x_pred
        P_pred += wc[i] * np.outer(diff, diff)

    # 更新步骤
    sigma_upd = np.array([h(sp) for sp in sigma_pred])
    z_pred = np.sum(wm[:, None] * sigma_upd, axis=0)

    Pzz = R.copy()
    for i in range(len(sigma)):
        diff = sigma_upd[i] - z_pred
        Pzz += wc[i] * np.outer(diff, diff)

    Pxz = np.zeros((n, len(z_pred)))
    for i in range(len(sigma)):
        Pxz += wc[i] * np.outer(sigma_pred[i] - x_pred, sigma_upd[i] - z_pred)

    K = Pxz @ np.linalg.inv(Pzz)
    x_new = x_pred + K @ (z - z_pred)
    P_new = P_pred - K @ Pzz @ K.T

    return x_new, P_new


if __name__ == "__main__":
    print("=== 无迹 Kalman 滤波器测试 ===")

    np.random.seed(42)

    # 非线性状态转移和观测
    def f(x):
        return np.array([x[0] + 0.1 * x[1], x[1] + 0.05 * np.sin(x[0])])

    def h(x):
        return np.array([np.sqrt(x[0]**2 + x[1]**2)])

    Q = np.diag([0.01, 0.01])
    R = np.array([[1.0]])

    x = np.array([0.0, 1.0])
    P = np.eye(2) * 0.1

    print("\n1. 非线性系统状态估计")
    print(f"初始状态: {x}")

    true_states = [x.copy()]
    measurements = []
    estimates = []

    for i in range(20):
        # 真实动态
        x_true = f(true_states[-1]) + np.random.randn(2) * 0.1

        # 观测
        z = h(x_true) + np.random.randn(1) * 0.5

        true_states.append(x_true)
        measurements.append(z)

        # UKF 更新
        x, P = unscented_kalman_filter(z.flatten(), x, P, f, h, Q, R)
        estimates.append(x.copy())

        print(f"Step {i+1}: 真值={x_true.round(2)}, 估计={x.round(2)}")

    print("\nUKF 测试完成!")
