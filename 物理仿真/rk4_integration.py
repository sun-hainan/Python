# -*- coding: utf-8 -*-
"""
算法实现：物理仿真 / rk4_integration

本文件实现 rk4_integration 相关的算法功能。
"""

import numpy as np
import matplotlib.pyplot as plt


class RK4Integrator:
    """
    四阶Runge-Kutta积分器
    
    适用于任何形如 dy/dt = f(y, t) 的一阶ODE系统
    """
    
    def __init__(self, dt=0.01):
        """
        初始化积分器
        
        参数:
            dt: 时间步长 (float)
        """
        self.dt = dt
    
    def derivative(self, state, t):
        """
        计算系统导数 dy/dt
        
        参数:
            state: 当前状态向量 [position, velocity] (numpy array)
            t: 当前时间 (float)
        
        返回:
            状态导数向量 [velocity, acceleration] (numpy array)
        """
        position = state[0]
        velocity = state[1]
        
        # 简谐振子模型：d²x/dt² = -omega² * x
        omega_squared = 1.0  # omega = 1 rad/s
        acceleration = -omega_squared * position
        
        # 返回状态导数 [dx/dt, d²x/dt²]
        return np.array([velocity, acceleration])
    
    def step(self, state, t):
        """
        执行一次RK4积分步骤
        
        参数:
            state: 当前状态向量 (numpy array)
            t: 当前时刻时间 (float)
        
        返回:
            new_state: 下一时刻状态向量
        """
        # 计算四个斜率
        # k1: 区间起点的斜率
        k1 = self.derivative(state, t)
        
        # k2: 中点斜率（使用 k1 预测）
        # state + k1*dt/2 表示从起点走半步的状态
        state_k2 = state + k1 * (self.dt / 2.0)
        k2 = self.derivative(state_k2, t + self.dt / 2.0)
        
        # k3: 另一个中点斜率（使用 k2 预测）
        # 与k2的区别是使用了更精确的中间状态
        state_k3 = state + k2 * (self.dt / 2.0)
        k3 = self.derivative(state_k3, t + self.dt / 2.0)
        
        # k4: 区间终点的斜率（使用 k3 预测）
        state_k4 = state + k3 * self.dt
        k4 = self.derivative(state_k4, t + self.dt)
        
        # 加权平均四个斜率（辛普森加权）
        # 注意：速度分量用速度的加权平均，加速度分量用加速度的加权平均
        weighted_derivative = (k1 + 2.0*k2 + 2.0*k3 + k4) / 6.0
        
        # 更新状态：y_new = y_old + weighted_slope * dt
        new_state = state + weighted_derivative * self.dt
        
        return new_state
    
    def simulate(self, initial_state, total_time):
        """
        运行完整模拟
        
        参数:
            initial_state: 初始状态向量 (numpy array)
            total_time: 总模拟时长 (float)
        
        返回:
            times: 时间数组
            states: 状态历史（每行是一个状态）
        """
        # 初始化
        state = initial_state.copy()
        t = 0.0
        
        # 计算步数
        num_steps = int(total_time / self.dt)
        
        # 预分配数组（提高效率）
        times = np.zeros(num_steps + 1)
        states = np.zeros((num_steps + 1, len(state)))
        
        # 记录初始状态
        times[0] = t
        states[0] = state
        
        # 主循环
        for i in range(num_steps):
            # RK4一步
            state = self.step(state, t)
            
            # 更新时间
            t += self.dt
            
            # 记录
            times[i + 1] = t
            states[i + 1] = state
        
        return times, states


def analytical_solution(t, initial_position, initial_velocity):
    """
    简谐振子解析解
    
    参数:
        t: 时间（数组）
        initial_position: 初始位移
        initial_velocity: 初始速度
    
    返回:
        位置数组
    """
    omega = 1.0
    A = initial_position
    B = initial_velocity / omega
    return A * np.cos(omega * t) + B * np.sin(omega * t)


def plot_results(times, states, analytical_positions):
    """
    可视化结果
    """
    positions = states[:, 0]
    velocities = states[:, 1]
    
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    
    # 位移对比
    axes[0].plot(times, positions, 'b-', linewidth=2, label='RK4数值解')
    axes[0].plot(times, analytical_positions, 'r--', linewidth=2, label='解析解')
    axes[0].set_ylabel('位移 (m)')
    axes[0].set_title('RK4积分 - 简谐振子位移')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # 速度
    axes[1].plot(times, velocities, 'g-', linewidth=2)
    axes[1].set_xlabel('时间 (s)')
    axes[1].set_ylabel('速度 (m/s)')
    axes[1].set_title('速度时程')
    axes[1].grid(True, alpha=0.3)
    
    # 误差（对数坐标）
    error = np.abs(positions - analytical_positions)
    axes[2].plot(times, error, 'm-', linewidth=1.5)
    axes[2].set_xlabel('时间 (s)')
    axes[2].set_ylabel('绝对误差 (m)')
    axes[2].set_title('数值误差（对数坐标）')
    axes[2].set_yscale('log')
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('rk4_integration_result.png', dpi=150)
    plt.show()
    print("图像已保存至 rk4_integration_result.png")


def compare_methods(dt, total_time, initial_state):
    """
    对比Euler、Midpoint、RK4三种方法的精度
    """
    results = {}
    
    # Euler
    euler_states = [initial_state.copy()]
    state = initial_state.copy()
    t = 0.0
    omega_sq = 1.0
    while t < total_time:
        acc = -omega_sq * state[0]
        new_state = np.array([
            state[0] + state[1] * dt,
            state[1] + acc * dt
        ])
        state = new_state
        t += dt
        euler_states.append(state.copy())
    results['Euler'] = np.array(euler_states)
    
    # Midpoint
    midpoint_states = [initial_state.copy()]
    state = initial_state.copy()
    t = 0.0
    while t < total_time:
        k1_v = state[1]
        k1_a = -omega_sq * state[0]
        mid = state + np.array([k1_v, k1_a]) * dt / 2
        k2_a = -omega_sq * mid[0]
        new_state = np.array([
            state[0] + mid[0] * dt,
            state[1] + k2_a * dt
        ])
        state = new_state
        t += dt
        midpoint_states.append(state.copy())
    results['Midpoint'] = np.array(midpoint_states)
    
    # RK4
    rk4 = RK4Integrator(dt=dt)
    _, rk4_states = rk4.simulate(initial_state, total_time)
    results['RK4'] = rk4_states
    
    return results


if __name__ == "__main__":
    # 参数设置
    dt = 0.1  # 较大的步长，用于体现方法差异
    total_time = 50.0
    initial_state = np.array([1.0, 0.0])  # [位置, 速度]
    
    print("=" * 55)
    print("RK4（4阶Runge-Kutta）积分器测试")
    print("=" * 55)
    print(f"时间步长: {dt} s (故意取较大值以展示精度差异)")
    print(f"总时长: {total_time} s")
    print(f"初始状态: 位置={initial_state[0]}, 速度={initial_state[1]}")
    print("-" * 55)
    
    # 解析解
    times = np.arange(0, total_time + dt, dt)
    analytical = analytical_solution(times, initial_state[0], initial_state[1])
    
    # RK4模拟
    rk4 = RK4Integrator(dt=dt)
    sim_times, sim_states = rk4.simulate(initial_state, total_time)
    
    # 统计
    print(f"模拟步数: {len(sim_times)}")
    print(f"\n最终时刻误差对比:")
    
    # 计算各方法最终误差
    analytical_final = analytical_solution(np.array([total_time]), initial_state[0], initial_state[1])[0]
    
    print(f"  RK4最终位移: {sim_states[-1, 0]:.8f}")
    print(f"  解析解:      {analytical_final:.8f}")
    print(f"  RK4误差:     {np.abs(sim_states[-1, 0] - analytical_final):.2e}")
    
    # 对比三种方法
    results = compare_methods(dt, total_time, initial_state)
    
    print(f"\n三种方法最终误差对比 (dt={dt}):")
    for name, states in results.items():
        final_pos = states[-1, 0]
        error = np.abs(final_pos - analytical_final)
        print(f"  {name:10s}: {error:.2e}")
    
    # 绘图
    plot_results(sim_times, sim_states, analytical)
    
    print("\n测试完成！RK4即使使用较大步长也能保持高精度。")
