# -*- coding: utf-8 -*-
"""
算法实现：时间序列分析 / unscented_kalman_filter

本文件实现 unscented_kalman_filter 相关的算法功能。
"""

import numpy as np
from typing import Callable, Tuple, Optional


class UnscentedKalmanFilter:
    """
    无迹卡尔曼滤波器
    
    参数:
        state_transition: 状态转移函数 f(x, u) -> x_next
        observation: 观测函数 h(x) -> y
        dim_state: 状态维度
        dim_obs: 观测维度
        Q: 过程噪声协方差
        R: 观测噪声协方差
        alpha: UKF参数（控制Sigma点分布）
        beta: UKF参数（通常设为2）
        kappa: UKF参数（通常设为0）
    """
    
    def __init__(self,
                 state_transition: Callable,
                 observation: Callable,
                 dim_state: int,
                 dim_obs: int,
                 Q: np.ndarray,
                 R: np.ndarray,
                 x_init: Optional[np.ndarray] = None,
                 P_init: Optional[np.ndarray] = None,
                 alpha: float = 1e-3,
                 beta: float = 2.0,
                 kappa: float = 0.0):
        self.f = state_transition
        self.h = observation
        
        self.dim_state = dim_state
        self.dim_obs = dim_obs
        
        self.Q = Q
        self.R = R
        
        # 初始化状态
        if x_init is None:
            self.x = np.zeros(dim_state)
        else:
            self.x = x_init.copy()
        
        if P_init is None:
            self.P = np.eye(dim_state)
        else:
            self.P = P_init.copy()
        
        # UKF参数
        self.alpha = alpha
        self.beta = beta
        self.kappa = kappa
        
        # 计算UKF权重
        self._compute_weights()
    
    def _compute_weights(self):
        """计算Sigma点权重"""
        n = self.dim_state
        lambda_ = self.alpha ** 2 * (n + self.kappa) - n
        
        self.lambda_ = lambda_
        
        # 权重
        self.Wm = np.zeros(2 * n + 1)  # 均值权重
        self.Wc = np.zeros(2 * n + 1)  # 协方差权重
        
        self.Wm[0] = lambda_ / (n + lambda_)
        self.Wc[0] = lambda_ / (n + lambda_) + (1 - self.alpha ** 2 + self.beta)
        
        for i in range(1, 2 * n + 1):
            self.Wm[i] = 1 / (2 * (n + lambda_))
            self.Wc[i] = 1 / (2 * (n + lambda_))
    
    def _generate_sigma_points(self) -> np.ndarray:
        """生成Sigma点"""
        n = self.dim_state
        
        # 确保P是正定的
        try:
            L = np.linalg.cholesky(self.P)
        except np.LinAlgError:
            # 如果不正定，做调整
            eigvals, eigvecs = np.linalg.eigh(self.P)
            eigvals = np.maximum(eigvals, 1e-6)
            self.P = eigvecs @ np.diag(eigvals) @ eigvecs.T
            L = np.linalg.cholesky(self.P)
        
        # 扩展参数
        lambda_ = self.lambda_
        
        # Sigma点矩阵 (n, 2n+1)
        sigma_points = np.zeros((n, 2 * n + 1))
        sigma_points[:, 0] = self.x
        
        sqrt_factor = np.sqrt(n + lambda_)
        
        for i in range(n):
            sigma_points[:, i + 1] = self.x + sqrt_factor * L[:, i]
            sigma_points[:, n + i + 1] = self.x - sqrt_factor * L[:, i]
        
        return sigma_points
    
    def predict(self, u: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        预测步骤
        
        参数:
            u: 可选的控制输入
        
        返回:
            (预测状态, 预测协方差)
        """
        # 生成Sigma点
        sigma_points = self._generate_sigma_points()
        
        # 变换Sigma点
        n = self.dim_state
        sigma_transformed = np.zeros((n, 2 * n + 1))
        
        for i in range(2 * n + 1):
            sigma_transformed[:, i] = self.f(sigma_points[:, i], u)
        
        # 预测均值
        x_pred = np.zeros(n)
        for i in range(2 * n + 1):
            x_pred += self.Wm[i] * sigma_transformed[:, i]
        
        # 预测协方差
        P_pred = self.Q.copy()
        for i in range(2 * n + 1):
            diff = sigma_transformed[:, i] - x_pred
            P_pred += self.Wc[i] * np.outer(diff, diff)
        
        self.x_pred = x_pred
        self.P_pred = P_pred
        self.sigma_predicted = sigma_transformed
        
        return x_pred, P_pred
    
    def update(self, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        更新步骤
        
        参数:
            y: 观测值
        
        返回:
            (更新后状态, 更新后协方差)
        """
        n = self.dim_state
        m = self.dim_obs
        
        # 使用预测时的Sigma点
        sigma_points = self._generate_sigma_points()
        
        # 变换到观测空间
        sigma_obs = np.zeros((m, 2 * n + 1))
        for i in range(2 * n + 1):
            sigma_obs[:, i] = self.h(sigma_points[:, i])
        
        # 预测观测均值
        y_pred = np.zeros(m)
        for i in range(2 * n + 1):
            y_pred += self.Wm[i] * sigma_obs[:, i]
        
        # 新息协方差
        S = self.R.copy()
        for i in range(2 * n + 1):
            diff = sigma_obs[:, i] - y_pred
            S += self.Wc[i] * np.outer(diff, diff)
        
        # 互协方差
        Pxy = np.zeros((n, m))
        for i in range(2 * n + 1):
            diff_x = sigma_points[:, i] - self.x_pred
            diff_y = sigma_obs[:, i] - y_pred
            Pxy += self.Wc[i] * np.outer(diff_x, diff_y)
        
        # 卡尔曼增益
        K = Pxy @ np.linalg.inv(S + 1e-10)
        
        # 状态更新
        innovation = y - y_pred
        self.x = self.x_pred + K @ innovation
        
        # 协方差更新
        self.P = self.P_pred - K @ S @ K.T
        
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
                # 使用上一步结果
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


class UKFExamples:
    """UKF应用示例"""
    
    @staticmethod
    def robot_localization():
        """
        机器人定位示例
        
        状态: [x, y, theta] (位置和朝向)
        观测: 距离和角度传感器
        
        运动模型是非线性的
        """
        dim_x = 3
        dim_z = 2
        
        # 过程噪声
        Q = np.diag([0.1, 0.1, 0.05])
        # 观测噪声
        R = np.diag([0.5, 0.05])
        
        def f(x, u=None):
            """运动模型"""
            if u is None:
                v, omega = 1.0, 0.1  # 默认控制
            else:
                v, omega = u[0], u[1]
            
            x_new = x.copy()
            dt = 0.1
            
            if abs(omega) < 1e-6:
                # 直线运动
                x_new[0] += v * dt * np.cos(x[2])
                x_new[1] += v * dt * np.sin(x[2])
            else:
                # 曲线运动
                R_turn = v / omega
                x_new[0] += R_turn * (np.sin(x[2] + omega * dt) - np.sin(x[2]))
                x_new[1] += R_turn * (-np.cos(x[2] + omega * dt) + np.cos(x[2]))
            
            x_new[2] = x[2] + omega * dt
            
            # 归一化角度
            x_new[2] = np.arctan2(np.sin(x_new[2]), np.cos(x_new[2]))
            
            return x_new
        
        def h(x):
            """观测模型：到原点的距离和角度"""
            dist = np.sqrt(x[0]**2 + x[1]**2)
            angle = np.arctan2(x[1], x[0])
            return np.array([dist, angle])
        
        # 创建UKF
        x0 = np.array([5, 5, np.pi / 4])
        P0 = np.eye(dim_x)
        
        ukf = UnscentedKalmanFilter(f, h, dim_x, dim_z, Q, R, x0, P0)
        
        # 生成模拟数据
        np.random.seed(42)
        n_steps = 100
        
        true_states = np.zeros((n_steps, dim_x))
        observations = np.zeros((n_steps, dim_z))
        controls = np.zeros((n_steps, 2))
        
        x = x0.copy()
        for t in range(n_steps):
            # 控制输入
            v = 0.5 + 0.3 * np.sin(t * 0.1)
            omega = 0.1 + 0.05 * np.cos(t * 0.1)
            u = np.array([v, omega])
            
            # 真实状态
            x = f(x, u) + np.random.randn(dim_x) * 0.1
            true_states[t] = x
            
            # 观测
            z = h(x) + np.random.randn(dim_z) * np.array([0.3, 0.05])
            observations[t] = z
            controls[t] = u
        
        # 滤波
        results = ukf.filter(observations, controls)
        
        # 计算误差
        pos_error = np.sqrt(
            (results['x_filtered'][:, 0] - true_states[:, 0])**2 +
            (results['x_filtered'][:, 1] - true_states[:, 1])**2
        )
        
        return true_states, observations, results, pos_error
    
    @staticmethod
    def nonlinear_oscillator():
        """
        非线性振荡器
        
        状态: [theta, omega]
        动力学: theta_dot = omega
                 omega_dot = -sin(theta) - 0.5*omega + noise
        
        比EKF更适用于这种强非线性系统
        """
        dim_x = 2
        dim_z = 1
        
        Q = np.diag([0.001, 0.01])
        R = np.array([[0.1]])
        
        def f(x, u=None):
            dt = 0.05
            theta, omega = x[0], x[1]
            
            # 非线性动力学
            dtheta = omega * dt
            domega = (-np.sin(theta) - 0.5 * omega) * dt
            
            return np.array([theta + dtheta, omega + domega])
        
        def h(x):
            return np.array([x[0]])
        
        # 初始状态
        x0 = np.array([np.pi / 4, 0])
        P0 = np.eye(dim_x)
        
        ukf = UnscentedKalmanFilter(f, h, dim_x, dim_z, Q, R, x0, P0,
                                     alpha=1e-3, beta=2.0, kappa=0)
        
        # 生成数据
        np.random.seed(42)
        n_steps = 300
        
        true_theta = np.zeros(n_steps)
        true_omega = np.zeros(n_steps)
        observations = np.zeros(n_steps)
        
        x = x0.copy()
        for t in range(n_steps):
            # 添加噪声驱动
            x = f(x) + np.array([0, 0.1 * np.random.randn()])
            true_theta[t] = x[0]
            true_omega[t] = x[1]
            observations[t] = x[0] + np.random.randn() * 0.3
        
        # 滤波
        results = ukf.filter(observations.reshape(-1, 1))
        
        # 计算RMSE
        theta_error = results['x_filtered'][:, 0] - true_theta
        rmse_theta = np.sqrt(np.mean(theta_error**2))
        
        return true_theta, observations, results, rmse_theta


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("无迹卡尔曼滤波（UKF）测试")
    print("=" * 50)
    
    np.random.seed(42)
    
    # 1. 机器人定位
    print("\n--- 机器人定位 ---")
    true_states, observations, results, pos_error = UKFExamples.robot_localization()
    
    print(f"定位数据: {len(observations)} 步")
    print(f"初始位置误差: {pos_error[0]:.3f}")
    print(f"平均位置误差: {np.mean(pos_error):.3f}")
    print(f"最终位置误差: {pos_error[-1]:.3f}")
    
    # 2. 非线性振荡器
    print("\n--- 非线性振荡器 ---")
    true_theta, obs_theta, results_osc, rmse = UKFExamples.nonlinear_oscillator()
    
    print(f"振荡器数据: {len(obs_theta)} 步")
    print(f"角度RMSE: {rmse:.4f}")
    
    # 对比EKF（简化版本）
    print("\n--- 对比EKF ---")
    
    # EKF需要雅可比，这里用数值近似
    from kalman_filter_extended import ExtendedKalmanFilter
    
    def f_ekf(x, u=None):
        dt = 0.05
        return np.array([x[0] + x[1] * dt, x[1] + (-np.sin(x[0]) - 0.5 * x[1]) * dt])
    
    def F_jac(x, u=None):
        dt = 0.05
        return np.array([
            [1, dt],
            [-dt * np.cos(x[0]), 1 - 0.5 * dt]
        ])
    
    def h_ekf(x):
        return np.array([x[0]])
    
    def H_jac(x):
        return np.array([[1, 0]])
    
    Q_ekf = np.diag([0.001, 0.01])
    R_ekf = np.array([[0.1]])
    
    x0_ekf = np.array([np.pi / 4, 0])
    P0_ekf = np.eye(2)
    
    ekf = ExtendedKalmanFilter(f_ekf, h_ekf, F_jac, H_jac, Q_ekf, R_ekf, x0_ekf, P0_ekf)
    
    results_ekf = ekf.filter(obs_theta.reshape(-1, 1))
    
    theta_error_ekf = results_ekf['x_filtered'][:, 0] - true_theta
    rmse_ekf = np.sqrt(np.mean(theta_error_ekf**2))
    
    print(f"EKF角度RMSE: {rmse_ekf:.4f}")
    print(f"UKF角度RMSE: {rmse:.4f}")
    print(f"UKF vs EKF: {'UKF更优' if rmse < rmse_ekf else 'EKF更优'} ({abs(rmse_ekf - rmse):.4f})")
    
    print("\n" + "=" * 50)
    print("测试完成")
