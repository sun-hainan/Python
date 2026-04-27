# -*- coding: utf-8 -*-
"""
算法实现：物理仿真 / midpoint_integration

本文件实现 midpoint_integration 相关的算法功能。
"""

import numpy as np
import matplotlib.pyplot as plt


class MidpointIntegrator:
    """
    Midpoint法积分器类
    
    用于求解形如 dy/dt = f(y, t) 的一阶常微分方程组
    """
    
    def __init__(self, dt=0.01):
        """
        初始化积分器
        
        参数:
            dt: 时间步长 (float)
        """
        self.dt = dt
    
    def acceleration(self, position, velocity, t):
        """
        计算加速度（由系统动力学决定）
        
        参数:
            position: 当前位置 (float)
            velocity: 当前速度 (float)
            t: 当前时间 (float)
        
        返回:
            加速度值 (float)
        """
        # 简谐振子模型：加速度 = -omega^2 * position
        omega_squared = 4.0  # omega = 2 rad/s
        return -omega_squared * position
    
    def step(self, position, velocity, t):
        """
        执行一次Midpoint积分步骤
        
        参数:
            position: 当前时刻位置 (float)
            velocity: 当前时刻速度 (float)
            t: 当前时刻时间 (float)
        
        返回:
            new_position: 下一时刻位置
            new_velocity: 下一时刻速度
        """
        # 第一步：计算区间起点的斜率（Euler预测）
        # k1是位置对时间的导数（即速度）
        k1_position = velocity
        
        # k1_velocity是速度对时间的导数（即加速度）
        k1_velocity = self.acceleration(position, velocity, t)
        
        # 计算中点位置和中点速度
        # mid_position = position + k1_position * (dt/2)
        mid_position = position + k1_position * (self.dt / 2.0)
        
        # mid_velocity = velocity + k1_velocity * (dt/2)
        mid_velocity = velocity + k1_velocity * (self.dt / 2.0)
        
        # 第二步：计算中点处的加速度（利用中点位置和中点速度）
        # 这是"中点法"名称的由来
        k2_velocity = self.acceleration(mid_position, mid_velocity, t + self.dt / 2.0)
        
        # 使用中点处的加速度更新状态
        # position_new = position + k2_position * dt ≈ position + mid_velocity * dt
        new_position = position + mid_velocity * self.dt
        
        # velocity_new = velocity + k2_velocity * dt
        new_velocity = velocity + k2_velocity * self.dt
        
        return new_position, new_velocity
    
    def simulate(self, initial_position, initial_velocity, total_time):
        """
        运行完整模拟
        
        参数:
            initial_position: 初始位置 (float)
            initial_velocity: 初始速度 (float)
            total_time: 总模拟时长 (float)
        
        返回:
            times, positions, velocities: 时间、位置、速度数组
        """
        # 初始化状态
        position = initial_position
        velocity = initial_velocity
        t = 0.0
        
        # 存储轨迹
        times = [t]
        positions = [position]
        velocities = [velocity]
        
        # 迭代模拟
        num_steps = int(total_time / self.dt)
        for _ in range(num_steps):
            # 执行一步积分
            position, velocity = self.step(position, velocity, t)
            
            # 更新时间
            t += self.dt
            
            # 记录数据
            times.append(t)
            positions.append(position)
            velocities.append(velocity)
        
        return np.array(times), np.array(positions), np.array(velocities)


def analytical_solution(t, initial_position, initial_velocity):
    """
    简谐振子的解析解，用于验证数值积分精度
    
    参数:
        t: 时间点（数组）
        initial_position: 初始位置
        initial_velocity: 初始速度
    
    返回:
        解析解位置
    """
    omega = 2.0  # 与数值模拟中的omega一致
    # x(t) = A*cos(omega*t) + B*sin(omega*t)
    # 其中 A = x0, B = v0/omega
    A = initial_position
    B = initial_velocity / omega
    return A * np.cos(omega * t) + B * np.sin(omega * t)


def plot_comparison(times, positions, analytical_positions, euler_positions=None):
    """
    可视化比较数值解与解析解
    
    参数:
        times: 时间数组
        positions: Midpoint数值解
        analytical_positions: 解析解
        euler_positions: Euler解（可选，用于对比）
    """
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    
    # 上图：位移对比
    axes[0].plot(times, positions, 'b-', linewidth=2, label='Midpoint数值解', alpha=0.8)
    axes[0].plot(times, analytical_positions, 'r--', linewidth=2, label='解析解', alpha=0.8)
    
    if euler_positions is not None:
        axes[0].plot(times, euler_positions, 'g:', linewidth=1.5, label='Euler数值解', alpha=0.7)
    
    axes[0].set_xlabel('时间 (s)')
    axes[0].set_ylabel('位移 (m)')
    axes[0].set_title('简谐振子 - Midpoint法 vs 解析解')
    axes[0].legend(loc='upper right')
    axes[0].grid(True, alpha=0.3)
    
    # 下图：误差分析
    midpoint_error = np.abs(positions - analytical_positions)
    axes[1].plot(times, midpoint_error, 'b-', linewidth=1.5, label='Midpoint误差')
    
    if euler_positions is not None:
        euler_error = np.abs(euler_positions - analytical_positions)
        axes[1].plot(times, euler_error, 'g-', linewidth=1.5, label='Euler误差', alpha=0.7)
    
    axes[1].set_xlabel('时间 (s)')
    axes[1].set_ylabel('绝对误差 (m)')
    axes[1].set_title('数值积分误差对比')
    axes[1].set_yscale('log')  # 对数坐标更清晰
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('midpoint_integration_result.png', dpi=150)
    plt.show()
    print("图像已保存至 midpoint_integration_result.png")


def run_euler_for_comparison(dt, initial_position, initial_velocity, total_time):
    """
    运行Euler积分用于对比（与Midpoint相同的参数）
    """
    times = np.arange(0, total_time + dt, dt)
    positions = np.zeros_like(times)
    velocities = np.zeros_like(times)
    
    positions[0] = initial_position
    velocities[0] = initial_velocity
    
    omega_squared = 4.0
    
    for i in range(len(times) - 1):
        acceleration = -omega_squared * positions[i]
        positions[i + 1] = positions[i] + velocities[i] * dt
        velocities[i + 1] = velocities[i] + acceleration * dt
    
    return times, positions


if __name__ == "__main__":
    # 设置参数
    dt = 0.02  # 时间步长
    total_time = 20.0  # 总时长
    initial_position = 1.0  # 初始位移
    initial_velocity = 0.0  # 初始速度
    
    print("=" * 55)
    print("Midpoint（中点法）积分器测试")
    print("=" * 55)
    print(f"时间步长: {dt} s")
    print(f"总时长: {total_time} s")
    print(f"初始位移: {initial_position} m")
    print(f"初始速度: {initial_velocity} m/s")
    print("-" * 55)
    
    # 创建积分器并运行模拟
    integrator = MidpointIntegrator(dt=dt)
    times, positions, velocities = integrator.simulate(
        initial_position=initial_position,
        initial_velocity=initial_velocity,
        total_time=total_time
    )
    
    # 计算解析解
    analytical_positions = analytical_solution(times, initial_position, initial_velocity)
    
    # 运行Euler积分用于对比
    times_euler, euler_positions = run_euler_for_comparison(
        dt, initial_position, initial_velocity, total_time
    )
    
    # 统计输出
    print(f"模拟步数: {len(times)}")
    print(f"\n最终状态对比:")
    print(f"  Midpoint: 位置={positions[-1]:.6f}, 速度={velocities[-1]:.6f}")
    print(f"  解析解:   位置={analytical_positions[-1]:.6f}, 速度=-{analytical_positions[-1]*4:.6f}")
    print(f"  Euler:    位置={euler_positions[-1]:.6f}")
    
    # 计算误差
    midpoint_final_error = np.abs(positions[-1] - analytical_positions[-1])
    euler_final_error = np.abs(euler_positions[-1] - analytical_solution(np.array([total_time]), initial_position, initial_velocity)[0])
    
    print(f"\n最终时刻绝对误差:")
    print(f"  Midpoint误差: {midpoint_final_error:.2e}")
    print(f"  Euler误差:    {euler_final_error:.2e}")
    print(f"  精度提升:     {euler_final_error/midpoint_final_error:.1f}x")
    
    # 绘图
    plot_comparison(times, positions, analytical_positions, euler_positions)
    
    print("\n测试完成！Midpoint法比Euler法精度高很多，但计算量仅增加一倍。")
