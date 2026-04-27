# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / kalman_filter

本文件实现 kalman_filter 相关的算法功能。
"""

import numpy as np


# ExtendedKalmanFilter 类
class ExtendedKalmanFilter:
    """EKF for nonlinear systems"""

# __init__ 算法
    def __init__(self, state_dim, obs_dim):
        self.n = state_dim
        self.m = obs_dim
        self.x = np.zeros(state_dim)
        self.P = np.eye(state_dim)

# predict 算法
    def predict(self, f, F_jac, Q, u=None):
        self.x = f(self.x, u)
        F = F_jac(self.x, u)
        self.P = F @ self.P @ F.T + Q
        return self.x

# update 算法
    def update(self, z, h, H_jac, R):
        z = np.array(z)
        H = H_jac(self.x)
        y = z - h(self.x)
        S = H @ self.P @ H.T + R
        K = self.P @ H.T @ np.linalg.inv(S)
        self.x = self.x + K @ y
        I_KH = np.eye(self.n) - K @ H
        self.P = I_KH @ self.P @ I_KH.T + K @ R @ K.T
        return self.x


if __name__ == "__main__":
    np.random.seed(42)
    ekf = ExtendedKalmanFilter(3, 2)
# f 算法
    def f(x, u): return np.array([x[0]+x[1], x[1], 0])
# h 算法
    def h(x): return np.array([x[0], x[1]])
# Fj 算法
    def Fj(x, u): return np.array([[1,1,0],[0,1,0],[0,0,1]])
# Hj 算法
    def Hj(x): return np.array([[1,0,0],[0,1,0]])
    Q = np.eye(3)*0.1
    R = np.eye(2)*0.5
    for i in range(5):
        ekf.predict(f, Fj, Q)
        z = np.array([i*0.5, 0.5]) + np.random.randn(2)*0.3
        ekf.update(z, h, Hj, R)
        print(f"Step {i+1}: x={ekf.x.round(2)}")
    print("\nEKF 测试完成!")
