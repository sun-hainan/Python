# -*- coding: utf-8 -*-
"""
算法实现：物理仿真 / spring_damper

本文件实现 spring_damper 相关的算法功能。
"""

import numpy as np
import matplotlib.pyplot as plt


class SpringDamperSystem:
    """
    弹簧-阻尼系统
    
    模拟一维质量-弹簧-阻尼系统
    """
    
    def __init__(self, mass=1.0, stiffness=10.0, damping=1.0):
        """
        初始化系统
        
        参数:
            mass: 质量 (kg)
            stiffness: 弹簧刚度 (N/m)
            damping: 阻尼系数 (N·s/m)
        """
        self.mass = mass
        self.stiffness = stiffness
        self.damping = damping
        
        # 状态
        self.position = 0.0  # 相对平衡位置
        self.velocity = 0.0
        
        # 预计算参数
        self.natural_frequency = np.sqrt(stiffness / mass)  # ω₀ = sqrt(k/m)
        self.damping_ratio = damping / (2 * np.sqrt(mass * stiffness))  # ζ = c/(2*sqrt(m*k))
    
    def get_acceleration(self, position, velocity, external_force=0.0):
        """
        计算加速度
        
        公式：a = (F - c*v - k*x) / m
        
        参数:
            position: 当前位置
            velocity: 当前速度
            external_force: 外力
        
        返回:
            加速度
        """
        # 弹簧力：F_spring = -k * x
        spring_force = -self.stiffness * position
        
        # 阻尼力：F_damping = -c * v
        damping_force = -self.damping * velocity
        
        # 合力
        total_force = spring_force + damping_force + external_force
        
        # 加速度：a = F / m
        return total_force / self.mass
    
    def step_euler(self, dt, external_force=0.0):
        """
        使用Euler法一步
        
        参数:
            dt: 时间步长
            external_force: 外力
        """
        acc = self.get_acceleration(self.position, self.velocity, external_force)
        self.velocity += acc * dt
        self.position += self.velocity * dt
    
    def step_rk4(self, dt, external_force=0.0):
        """
        使用RK4一步（高精度）
        
        参数:
            dt: 时间步长
            external_force: 外力
        """
        def derivative(pos, vel):
            return vel, self.get_acceleration(pos, vel, external_force)
        
        k1_pos, k1_vel = derivative(self.position, self.velocity)
        
        k2_pos, k2_vel = derivative(
            self.position + k1_pos * dt/2,
            self.velocity + k1_vel * dt/2
        )
        
        k3_pos, k3_vel = derivative(
            self.position + k2_pos * dt/2,
            self.velocity + k2_vel * dt/2
        )
        
        k4_pos, k4_vel = derivative(
            self.position + k3_pos * dt,
            self.velocity + k3_vel * dt
        )
        
        self.position += (k1_pos + 2*k2_pos + 2*k3_pos + k4_pos) * dt / 6
        self.velocity += (k1_vel + 2*k2_vel + 2*k3_vel + k4_vel) * dt / 6
    
    def step(self, dt, external_force=0.0, method='rk4'):
        """
        执行一步仿真
        
        参数:
            dt: 时间步长
            external_force: 外力
            method: 积分方法 ('euler' 或 'rk4')
        """
        if method == 'euler':
            self.step_euler(dt, external_force)
        else:
            self.step_rk4(dt, external_force)
    
    def simulate(self, dt, total_time, external_force_func=None):
        """
        运行完整仿真
        
        参数:
            dt: 时间步长
            total_time: 总时长
            external_force_func: 外力函数 f(t)，None表示无外力
        
        返回:
            times, positions, velocities
        """
        num_steps = int(total_time / dt)
        times = np.zeros(num_steps + 1)
        positions = np.zeros(num_steps + 1)
        velocities = np.zeros(num_steps + 1)
        
        times[0] = 0
        positions[0] = self.position
        velocities[0] = self.velocity
        
        t = 0.0
        for i in range(num_steps):
            force = external_force_func(t) if external_force_func else 0.0
            self.step(dt, force)
            t += dt
            
            times[i+1] = t
            positions[i+1] = self.position
            velocities[i+1] = self.velocity
        
        return times, positions, velocities
    
    def reset(self, position=0.0, velocity=0.0):
        """
        重置状态
        
        参数:
            position: 初始位置
            velocity: 初始速度
        """
        self.position = position
        self.velocity = 0.0


def analytical_underdamped(t, x0, v0, omega0, zeta):
    """
    欠阻尼系统的解析解
    
    参数:
        t: 时间
        x0: 初始位移
        v0: 初始速度
        omega0: 固有频率
        zeta: 阻尼比
    
    返回:
        位移
    """
    omega_d = omega0 * np.sqrt(1 - zeta**2)  # 阻尼固有频率
    
    # 初始条件系数
    A = x0
    B = (v0 + zeta * omega0 * x0) / omega_d
    
    # 衰减振荡
    decay = np.exp(-zeta * omega0 * t)
    oscillation = A * np.cos(omega_d * t) + B * np.sin(omega_d * t)
    
    return decay * oscillation


def analyze_system_params():
    """
    分析不同参数对系统响应的影响
    """
    print("=" * 55)
    print("弹簧-阻尼系统参数分析")
    print("=" * 55)
    
    m = 1.0  # 质量
    
    # 不同阻尼比
    cases = [
        ("欠阻尼 ζ=0.1", 1.0, 0.1),    # 质量1kg, 刚度1N/m, 阻尼0.1
        ("临界阻尼 ζ=1.0", 1.0, 2.0),   # 阻尼2.0
        ("过阻尼 ζ=2.0", 1.0, 4.0),     # 阻尼4.0
    ]
    
    print("\n三种阻尼情况对比:")
    print(f"{'情况':<20} {'ζ':<8} {'ω₀':<10} {'ω_d':<10}")
    print("-" * 50)
    
    for name, k, c in cases:
        omega0 = np.sqrt(k / m)
        zeta = c / (2 * np.sqrt(m * k))
        if zeta < 1:
            omega_d = omega0 * np.sqrt(1 - zeta**2)
        else:
            omega_d = 0
        print(f"{name:<20} {zeta:<8.2f} {omega0:<10.4f} {omega_d:<10.4f}")


def simulate_step_response():
    """
    模拟阶跃响应
    """
    print("\n" + "=" * 55)
    print("阶跃响应仿真")
    print("=" * 55)
    
    # 创建欠阻尼系统
    sys = SpringDamperSystem(mass=1.0, stiffness=25.0, damping=2.0)
    
    print(f"\n系统参数:")
    print(f"  质量 m = {sys.mass} kg")
    print(f"  刚度 k = {sys.stiffness} N/m")
    print(f"  阻尼 c = {sys.damping} N·s/m")
    print(f"  固有频率 ω₀ = {sys.natural_frequency:.4f} rad/s")
    print(f"  阻尼比 ζ = {sys.damping_ratio:.4f}")
    
    # 初始位移
    initial_position = 1.0
    sys.reset(position=initial_position)
    
    print(f"\n初始条件: x(0) = {initial_position} m, x'(0) = 0")
    
    # 仿真
    dt = 0.01
    total_time = 5.0
    times, positions, velocities = sys.simulate(dt, total_time)
    
    # 解析解
    analytical = analytical_underdamped(
        times, initial_position, 0.0,
        sys.natural_frequency, sys.damping_ratio
    )
    
    print(f"\n最终状态:")
    print(f"  数值解: x = {positions[-1]:.6f} m")
    print(f"  解析解: x = {analytical[-1]:.6f} m")
    print(f"  误差: {abs(positions[-1] - analytical[-1]):.2e}")
    
    return times, positions, analytical


def simulate_forced_vibration():
    """
    模拟受迫振动
    """
    print("\n" + "=" * 55)
    print("受迫振动仿真")
    print("=" * 55)
    
    # 创建系统
    sys = SpringDamperSystem(mass=1.0, stiffness=10.0, damping=0.5)
    sys.reset(position=0.0, velocity=0.0)
    
    print(f"\n系统参数:")
    print(f"  ω₀ = {sys.natural_frequency:.4f} rad/s")
    print(f"  ζ = {sys.damping_ratio:.4f}")
    
    # 外力函数：F(t) = sin(ω*t)，ω接近固有频率时发生共振
    forcing_freq = sys.natural_frequency * 0.9  # 接近共振频率
    print(f"\n激励频率: ω = {forcing_freq:.4f} rad/s (接近共振)")
    
    def external_force(t):
        return 5.0 * np.sin(forcing_freq * t)
    
    # 仿真
    dt = 0.01
    total_time = 10.0
    times, positions, velocities = sys.simulate(dt, total_time, external_force_func=external_force)
    
    # 振幅分析
    # 稳态振幅公式：A = F₀ / sqrt((k-m*ω²)² + (c*ω)²)
    F0 = 5.0
    omega = forcing_freq
    amplitude = F0 / np.sqrt((sys.stiffness - sys.mass*omega**2)**2 + (sys.damping*omega)**2)
    
    print(f"\n稳态振幅理论值: {amplitude:.4f} m")
    print(f"最大位移观测值: {np.max(np.abs(positions)):.4f} m")
    
    return times, positions


def simulate_impulse_response():
    """
    模拟脉冲响应
    """
    print("\n" + "=" * 55)
    print("脉冲响应仿真")
    print("=" * 55)
    
    sys = SpringDamperSystem(mass=1.0, stiffness=10.0, damping=1.0)
    sys.reset(position=0.0, velocity=5.0)  # 初始速度表示脉冲
    
    print(f"\n初始条件: x(0)=0, x'(0)=5 m/s")
    print(f"阻尼比 ζ = {sys.damping_ratio:.4f}")
    
    dt = 0.01
    total_time = 5.0
    times, positions, velocities = sys.simulate(dt, total_time)
    
    print(f"\n响应:")
    print(f"  最大位移: {np.max(positions):.4f} m")
    print(f"  达到最大位移时间: {times[np.argmax(positions)]:.4f} s")
    print(f"  最终位移: {positions[-1]:.6f} m")
    
    return times, positions


def plot_responses(times, positions, analytical=None, title="响应"):
    """
    绘制响应曲线
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(times, positions, 'b-', linewidth=2, label='数值解')
    
    if analytical is not None:
        ax.plot(times, analytical, 'r--', linewidth=1.5, label='解析解', alpha=0.8)
    
    ax.set_xlabel('时间 (s)', fontsize=12)
    ax.set_ylabel('位移 (m)', fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('spring_damper_result.png', dpi=150)
    plt.show()
    print("图像已保存至 spring_damper_result.png")


def plot_comparison(times_list, positions_list, labels):
    """
    绘制多曲线对比
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for times, positions, label in zip(times_list, positions_list, labels):
        ax.plot(times, positions, linewidth=2, label=label)
    
    ax.set_xlabel('时间 (s)', fontsize=12)
    ax.set_ylabel('位移 (m)', fontsize=12)
    ax.set_title('不同阻尼比的阶跃响应', fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('spring_damper_comparison.png', dpi=150)
    plt.show()
    print("图像已保存至 spring_damper_comparison.png")


if __name__ == "__main__":
    # 参数分析
    analyze_system_params()
    
    # 阶跃响应
    times, positions, analytical = simulate_step_response()
    plot_responses(times, positions, analytical, "欠阻尼系统阶跃响应")
    
    # 受迫振动
    times, positions = simulate_forced_vibration()
    plot_responses(times, positions, title="受迫振动响应")
    
    # 脉冲响应
    times, positions = simulate_impulse_response()
    plot_responses(times, positions, title="脉冲响应")
    
    # 对比不同阻尼
    print("\n" + "=" * 55)
    print("对比不同阻尼比")
    print("=" * 55)
    
    times_list = []
    positions_list = []
    labels = []
    
    for zeta in [0.1, 0.5, 1.0, 2.0]:
        m = 1.0
        k = 25.0
        c = 2 * zeta * np.sqrt(m * k)
        sys = SpringDamperSystem(mass=m, stiffness=k, damping=c)
        sys.reset(position=1.0)
        
        times, positions, _ = sys.simulate(0.01, 5.0)
        times_list.append(times)
        positions_list.append(positions)
        labels.append(f'ζ = {zeta}')
    
    plot_comparison(times_list, positions_list, labels)
    
    print("\n测试完成！弹簧-阻尼系统是振动学的基础模型。")
