# -*- coding: utf-8 -*-
"""
算法实现：时间序列分析 / kalman_filter_extended

本文件实现 kalman_filter_extended 相关的算法功能。
"""

import numpy as np
from typing import Tuple, Callable, Optional


class ExtendedKalmanFilter:
    """
    扩展卡尔曼滤波器
    
    参数:
        state_transition: 状态转移函数 f(x, u) -> x_next
        observation: 观测函数 h(x) -> y
        state_transition_jacobian: 状态转移雅可比矩阵
        observation_jacobian: 观测雅可比矩阵
        Q: 过程噪声协方差
        R: 观测噪声协方差
    """
    
    def __init__(self, 
                 state_transition: Callable,
                 observation: Callable,
                 state_transition_jacobian: Callable,
                 observation_jacobian: Callable,
                 Q: np.ndarray,
                 R: np.ndarray,
                 x_init: Optional[np.ndarray] = None,
                 P_init: Optional[np.ndarray] = None):
        self.f = state_transition      # 状态转移函数
        self.h = observation            # 观测函数
        self.F_jac = state_transition_jacobian  # 状态雅可比
        self.H_jac = observation_jacobian        # 观测雅可比
        
        self.Q = Q   # 过程噪声协方差
        self.R = R   # 观测噪声协方差
        
        self.dim_state = Q.shape[0]
        self.dim_obs = R.shape[0]
        
        # 初始化状态
        if x_init is None:
            self.x = np.zeros(self.dim_state)
        else:
            self.x = x_init.copy()
        
        if P_init is None:
            self.P = np.eye(self.dim_state)
        else:
            self.P = P_init.copy()
        
        self.history = []
    
    def predict(self, u: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        预测步骤
        
        参数:
            u: 可选的控制输入
        
        返回:
            (预测状态, 预测协方差)
        """
        # 计算状态转移的雅可比矩阵
        F = self.F_jac(self.x, u)
        
        # 预测状态
        self.x_pred = self.f(self.x, u)
        
        # 预测协方差
        self.P_pred = F @ self.P @ F.T + self.Q
        
        return self.x_pred, self.P_pred
    
    def update(self, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        更新步骤
        
        参数:
            y: 观测值
        
        返回:
            (更新后状态, 更新后协方差)
        """
        # 计算观测雅可比
        H = self.H_jac(self.x_pred)
        
        # 新息（观测预测误差）
        innovation = y - self.h(self.x_pred)
        
        # 新息协方差
        S = H @ self.P_pred @ H.T + self.R
        
        # 卡尔曼增益
        K = self.P_pred @ H.T @ np.linalg.inv(S + 1e-10)
        
        # 状态更新
        self.x = self.x_pred + K @ innovation
        
        # 协方差更新（Joseph形式）
        I_KH = np.eye(self.dim_state) - K @ H
        self.P = I_KH @ self.P_pred @ I_KH.T + K @ self.R @ K.T
        
        return self.x, self.P
    
    def filter(self, observations: np.ndarray, 
               controls: Optional[np.ndarray] = None) -> dict:
        """
        对序列进行滤波
        
        参数:
            observations: 观测序列 (T, dim_obs)
            controls: 控制输入序列 (T, dim_control)，可选
        
        返回:
            滤波结果
        """
        T = len(observations)
        
        x_filtered = np.zeros((T, self.dim_state))
        P_filtered = np.zeros((T, self.dim_state, self.dim_state))
        x_predicted = np.zeros((T, self.dim_state))
        P_predicted = np.zeros((T, self.dim_state, self.dim_state))
        
        for t in range(T):
            if t == 0:
                # 初始预测
                u_t = controls[t] if controls is not None else None
                x_predicted[t], P_predicted[t] = self.predict(u_t)
            else:
                # 使用上一步结果预测
                self.x, self.P = x_filtered[t - 1], P_filtered[t - 1]
                u_t = controls[t] if controls is not None else None
                x_predicted[t], P_predicted[t] = self.predict(u_t)
            
            # 更新
            x_filtered[t], P_filtered[t] = self.update(observations[t])
        
        return {
            'x_filtered': x_filtered,
            'P_filtered': P_filtered,
            'x_predicted': x_predicted,
            'P_predicted': P_predicted
        }


class EKFSimpleModels:
    """EKF应用示例：简单非线性系统"""
    
    @staticmethod
    def simple_ekf_tracking():
        """
        简单的2D跟踪问题
        状态: [x, y, vx, vy]
        观测: [x, y]（只有位置观测）
        """
        # 状态维度4，观测维度2
        dim_x = 4
        dim_z = 2
        
        # 过程噪声
        Q = np.eye(dim_x) * 0.01
        Q[0, 0] = 0.1  # x噪声
        Q[1, 1] = 0.1  # y噪声
        
        # 观测噪声
        R = np.eye(dim_z) * 0.5
        
        # 状态转移函数（匀速模型）
        def f(x, u=None):
            dt = 0.1
            F = np.array([
                [1, 0, dt, 0],
                [0, 1, 0, dt],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ])
            return F @ x
        
        # 状态转移雅可比
        def F_jac(x, u=None):
            dt = 0.1
            return np.array([
                [1, 0, dt, 0],
                [0, 1, 0, dt],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ])
        
        # 观测函数（只观测位置）
        def h(x):
            return np.array([x[0], x[1]])
        
        # 观测雅可比
        def H_jac(x):
            return np.array([
                [1, 0, 0, 0],
                [0, 1, 0, 0]
            ])
        
        # 初始状态
        x0 = np.array([0, 0, 5, 2])  # 初始位置和速度
        P0 = np.eye(dim_x)
        
        # 创建EKF
        ekf = ExtendedKalmanFilter(f, h, F_jac, H_jac, Q, R, x0, P0)
        
        # 生成跟踪数据
        np.random.seed(42)
        n_steps = 100
        
        true_states = np.zeros((n_steps, dim_x))
        observations = np.zeros((n_steps, dim_z))
        
        x = x0.copy()
        for t in range(n_steps):
            # 真实状态
            x = f(x) + np.random.randn(dim_x) * 0.1
            true_states[t] = x
            
            # 观测
            z = h(x) + np.random.randn(dim_z) * 0.5
            observations[t] = z
        
        # 滤波
        results = ekf.filter(observations)
        
        return true_states, observations, results


class EKFBearingsOnly:
    """
    纯角度跟踪（ Bearings-only Tracking）
    
    状态: [x, y, vx, vy]
    观测: 角度 θ = atan2(y - y_sensor, x - x_sensor)
    
    这是一个严重的非线性问题
    """
    
    def __init__(self, sensor_position: np.ndarray, Q: np.ndarray, R: float):
        self.sensor_pos = sensor_position.copy()
        self.Q = Q.copy()
        self.R = R.copy()
        
        dim_x = 4
        dim_z = 1
        
        # 创建EKF
        def f(x, u=None):
            dt = 0.1
            F = np.array([
                [1, 0, dt, 0],
                [0, 1, 0, dt],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ])
            return F @ x
        
        def F_jac(x, u=None):
            dt = 0.1
            return np.array([
                [1, 0, dt, 0],
                [0, 1, 0, dt],
                [0, 0, 1, 0],
                [0, 0, 0, 1]
            ])
        
        def h(x):
            dx = x[0] - self.sensor_pos[0]
            dy = x[1] - self.sensor_pos[1]
            return np.array([np.arctan2(dy, dx)])
        
        def H_jac(x):
            dx = x[0] - self.sensor_pos[0]
            dy = x[1] - self.sensor_pos[1]
            r2 = dx**2 + dy**2
            r = np.sqrt(r2)
            
            if r < 1e-10:
                return np.zeros((1, 4))
            
            return np.array([
                [-dy / r2, dx / r2, 0, 0]
            ])
        
        x0 = np.array([10, 10, -1, 0])
        P0 = np.eye(4) * 1
        
        self.ekf = ExtendedKalmanFilter(f, h, F_jac, H_jac, Q, np.array([[R]]), x0, P0)
    
    def filter(self, observations: np.ndarray) -> dict:
        """滤波"""
        return self.ekf.filter(observations)


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("扩展卡尔曼滤波（EKF）测试")
    print("=" * 50)
    
    np.random.seed(42)
    
    # 1. 简单2D跟踪
    print("\n--- 2D目标跟踪 ---")
    true_states, observations, results = EKFSimpleModels.simple_ekf_tracking()
    
    print(f"跟踪数据: {len(observations)} 步")
    print(f"初始位置: 真实={true_states[0, :2]}, 估计={results['x_filtered'][0, :2]}")
    
    # 计算位置误差
    position_error = np.sqrt(
        (results['x_filtered'][:, 0] - true_states[:, 0])**2 +
        (results['x_filtered'][:, 1] - true_states[:, 1])**2
    )
    print(f"平均位置误差: {np.mean(position_error):.3f}")
    print(f"最大位置误差: {np.max(position_error):.3f}")
    
    # 2. 纯角度跟踪
    print("\n--- 纯角度跟踪 ---")
    
    sensor_pos = np.array([0, 0])  # 传感器在原点
    Q = np.eye(4) * 0.01
    R = 0.05  # 角度噪声（弧度）
    
    bearings_ekf = EKFBearingsOnly(sensor_pos, Q, R)
    
    # 生成纯角度数据
    n_steps = 100
    true_states_bo = np.zeros((n_steps, 4))
    observations_bo = np.zeros((n_steps, 1))
    
    x = np.array([50, 20, -1, -0.5])
    for t in range(n_steps):
        # 匀速运动
        dt = 0.1
        F = np.array([
            [1, 0, dt, 0],
            [0, 1, 0, dt],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        
        x = F @ x + np.random.randn(4) * 0.05
        true_states_bo[t] = x
        
        # 角度观测
        dx = x[0] - sensor_pos[0]
        dy = x[1] - sensor_pos[1]
        angle = np.arctan2(dy, dx) + np.random.randn() * 0.05
        observations_bo[t] = angle
    
    # 滤波
    results_bo = bearings_ekf.filter(observations_bo)
    
    # 计算误差
    pos_error_bo = np.sqrt(
        (results_bo['x_filtered'][:, 0] - true_states_bo[:, 0])**2 +
        (results_bo['x_filtered'][:, 1] - true_states_bo[:, 1])**2
    )
    print(f"纯角度跟踪平均误差: {np.mean(pos_error_bo):.2f}")
    print(f"纯角度跟踪最终误差: {pos_error_bo[-1]:.2f}")
    
    # 3. 非线性振荡器示例
    print("\n--- 非线性振荡器 ---")
    
    # 状态: [theta, omega]
    # 动力学: theta_dot = omega, omega_dot = -sin(theta)
    # 这是非线性系统，无法用线性KF处理
    
    def pendulum_f(x, u=None):
        dt = 0.01
        theta, omega = x[0], x[1]
        
        # 使用Euler方法
        dtheta = omega * dt
        domega = (-np.sin(theta) + 0.1 * np.random.randn()) * dt
        
        return np.array([theta + dtheta, omega + domega])
    
    def pendulum_F(x, u=None):
        dt = 0.01
        return np.array([
            [1, dt],
            [-dt * np.cos(x[0]), 1]
        ])
    
    def pendulum_h(x):
        return np.array([x[0]])  # 观测角度
    
    def pendulum_H(x):
        return np.array([[1, 0]])
    
    Q_pend = np.array([[0.001, 0], [0, 0.01]])
    R_pend = np.array([[0.1]])
    
    x0_pend = np.array([0.5, 0])
    P0_pend = np.eye(2)
    
    ekf_pend = ExtendedKalmanFilter(pendulum_f, pendulum_h, pendulum_F, pendulum_H, 
                                   Q_pend, R_pend, x0_pend, P0_pend)
    
    # 生成数据
    n_pend = 500
    true_theta = np.zeros(n_pend)
    obs_theta = np.zeros(n_pend)
    
    x = x0_pend.copy()
    for t in range(n_pend):
        x = pendulum_f(x) + np.array([0, 0.1 * np.random.randn()])
        true_theta[t] = x[0]
        obs_theta[t] = x[0] + np.random.randn() * 0.3
    
    # 滤波
    results_pend = ekf_pend.filter(obs_theta.reshape(-1, 1))
    
    print(f"角度跟踪误差（RMSE）: {np.sqrt(np.mean((results_pend['x_filtered'][:, 0] - true_theta)**2)):.4f}")
    
    print("\n" + "=" * 50)
    print("测试完成")
