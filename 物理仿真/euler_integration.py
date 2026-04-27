# -*- coding: utf-8 -*-
"""
算法实现：物理仿真 / euler_integration

本文件实现 euler_integration 相关的算法功能。
"""

import numpy as np
import matplotlib.pyplot as plt


def euler_step(position, velocity, acceleration, dt):
    """
    执行一次Euler积分步骤
    
    参数:
        position: 当前时刻位置 (float)
        velocity: 当前时刻速度 (float)
        acceleration: 当前时刻加速度，由力/质量计算得出 (float)
        dt: 时间步长 (float)
    
    返回:
        new_position: 下一时刻位置
        new_velocity: 下一时刻速度
    """
    # 根据当前速度更新位置：position_new = position + velocity * dt
    new_position = position + velocity * dt
    
    # 根据当前加速度更新速度：velocity_new = velocity + acceleration * dt
    new_velocity = velocity + acceleration * dt
    
    return new_position, new_velocity


def simulate_hooke_pendulum(initial_angle, dt=0.01, total_time=10.0):
    """
    模拟弹簧摆系统（Hooke pendulum）
    弹簧一端固定，另一端连接质点，在重力场中做二维振动
    
    参数:
        initial_angle: 初始偏角（弧度）
        dt: 时间步长（秒）
        total_time: 模拟总时长（秒）
    
    返回:
        times: 时间数组
        angles: 角度数组
        angular_velocities: 角速度数组
    """
    # 弹簧原长（未伸长时的长度）
    natural_length = 1.0
    
    # 弹簧刚度系数
    spring_constant = 5.0
    
    # 重力加速度
    g = 9.81
    
    # 质点质量
    mass = 1.0
    
    # 初始时刻
    t = 0.0
    
    # 初始角度（弧度）
    angle = initial_angle
    
    # 初始角速度
    angular_velocity = 0.0
    
    # 存储轨迹数据
    times = [t]
    angles = [angle]
    angular_velocities = [angular_velocity]
    
    # 迭代模拟直到总时长
    while t < total_time:
        # 计算弹簧当前长度（使用小角度近似）
        # 弹簧形变量 = 垂直位移，简化计算用
        extension = natural_length * np.sin(angle)
        
        # 弹簧弹力沿弹簧方向：F_spring = -k * extension
        # 分解为切向分量产生恢复力矩
        spring_force_tangential = -spring_constant * extension * np.cos(angle)
        
        # 重力产生的切向力分量：F_gravity = -m*g*sin(angle)（负号表示恢复方向）
        gravity_force_tangential = -mass * g * np.sin(angle)
        
        # 合力切向分量
        total_force = spring_force_tangential + gravity_force_tangential
        
        # 角加速度 = 合外力矩 / 转动惯量（简化：质点距离为1，I = m*L^2 = m）
        angular_acceleration = total_force / mass
        
        # 使用Euler积分更新状态
        angle, angular_velocity = euler_step(
            position=angle,
            velocity=angular_velocity,
            acceleration=angular_acceleration,
            dt=dt
        )
        
        # 更新时间
        t += dt
        
        # 记录轨迹
        times.append(t)
        angles.append(angle)
        angular_velocities.append(angular_velocity)
    
    return np.array(times), np.array(angles), np.array(angular_velocities)


def plot_simulation(times, angles, angular_velocities):
    """
    可视化模拟结果
    
    参数:
        times: 时间数组
        angles: 角度数组
        angular_velocities: 角速度数组
    """
    fig, axes = plt.subplots(2, 1, figsize=(10, 8))
    
    # 绘制角度随时间变化
    axes[0].plot(times, angles, 'b-', linewidth=1.5, label='角度 (rad)')
    axes[0].set_xlabel('时间 (s)')
    axes[0].set_ylabel('角度 (rad)')
    axes[0].set_title('Euler积分 - 弹簧摆角度')
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()
    
    # 绘制相图（角度 vs 角速度）
    axes[1].plot(angles, angular_velocities, 'r-', linewidth=1.0, alpha=0.7)
    axes[1].set_xlabel('角度 (rad)')
    axes[1].set_ylabel('角速度 (rad/s)')
    axes[1].set_title('相图')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('euler_integration_result.png', dpi=150)
    plt.show()
    print("图像已保存至 euler_integration_result.png")


if __name__ == "__main__":
    # 设置随机种子确保可复现
    np.random.seed(42)
    
    # 初始偏角（弧度），约30度
    initial_angle = np.pi / 6
    
    # 打印参数信息
    print("=" * 50)
    print("Euler积分器测试")
    print("=" * 50)
    print(f"初始角度: {np.degrees(initial_angle):.1f}°")
    print(f"时间步长: 0.01 s")
    print(f"总时长: 10 s")
    print("-" * 50)
    
    # 运行模拟
    times, angles, angular_velocities = simulate_hooke_pendulum(
        initial_angle=initial_angle,
        dt=0.01,
        total_time=10.0
    )
    
    # 输出统计信息
    print(f"模拟步数: {len(times)}")
    print(f"最大角度: {np.max(np.abs(angles)):.4f} rad ({np.degrees(np.max(np.abs(angles))):.2f}°)")
    print(f"最终角度: {angles[-1]:.4f} rad ({np.degrees(angles[-1]):.2f}°)")
    print(f"最终角速度: {angular_velocities[-1]:.4f} rad/s")
    
    # 绘制结果
    plot_simulation(times, angles, angular_velocities)
    
    print("\n测试完成！Euler积分虽然简单，但误差会随时间累积。")
