# -*- coding: utf-8 -*-
"""
算法实现：物理仿真 / rigid_body_dynamics

本文件实现 rigid_body_dynamics 相关的算法功能。
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch


class RigidBody:
    """
    刚体类
    
    表示一个二维刚体，具有质量、位置、速度、角度、角速度等属性
    """
    
    def __init__(self, mass=1.0, position=[0, 0], angle=0.0):
        """
        初始化刚体
        
        参数:
            mass: 质量 (kg)
            position: 质心位置 [x, y]
            angle: 朝向角度（弧度）
        """
        self.mass = mass
        
        # 位置和速度（线性运动）
        self.position = np.array(position, dtype=float)
        self.velocity = np.array([0.0, 0.0])
        self.force = np.array([0.0, 0.0])
        
        # 角度和角速度（旋转运动）
        self.angle = angle
        self.angular_velocity = 0.0
        self.torque = 0.0
        
        # 转动惯量（默认为实心圆盘）
        # I = (1/2) * m * r²
        self.moment_of_inertia = 0.5 * mass  # 假设半径=1
        
        # 尺寸（用于可视化）
        self.width = 2.0
        self.height = 1.0
        self.radius = 1.0  # 外接圆半径
    
    def apply_force(self, force, application_point=None):
        """
        施加力到刚体
        
        参数:
            force: 力向量 [Fx, Fy]
            application_point: 施加点（世界坐标），None表示作用在质心
        """
        self.force += np.array(force)
        
        if application_point is not None:
            # 计算力矩：τ = r × F
            # r = 从质心到施加点的向量
            r = np.array(application_point) - self.position
            torque = r[0] * force[1] - r[1] * force[0]  # 2D叉积
            self.torque += torque
    
    def apply_torque(self, torque):
        """
        直接施加力矩
        
        参数:
            torque: 力矩（标量）
        """
        self.torque += torque
    
    def update_linear(self, dt):
        """
        更新线性运动
        
        使用Euler积分
        速度 = 速度 + 加速度 * dt
        位置 = 位置 + 速度 * dt
        """
        # 加速度 = 力 / 质量
        acceleration = self.force / self.mass
        
        # 更新速度
        self.velocity += acceleration * dt
        
        # 更新位置
        self.position += self.velocity * dt
    
    def update_rotation(self, dt):
        """
        更新旋转运动
        
        使用Euler积分
        角加速度 = 力矩 / 转动惯量
        角速度 = 角速度 + 角加速度 * dt
        角度 = 角度 + 角速度 * dt
        """
        # 角加速度 = τ / I
        angular_acceleration = self.torque / self.moment_of_inertia
        
        # 更新角速度
        self.angular_velocity += angular_acceleration * dt
        
        # 更新角度
        self.angle += self.angular_velocity * dt
        
        # 角度归一化到 [-π, π]
        while self.angle > np.pi:
            self.angle -= 2 * np.pi
        while self.angle < -np.pi:
            self.angle += 2 * np.pi
    
    def update(self, dt):
        """
        更新刚体状态（线性+旋转）
        
        参数:
            dt: 时间步长
        """
        self.update_linear(dt)
        self.update_rotation(dt)
        
        # 清零力（每帧重新计算）
        self.force[:] = 0.0
        self.torque = 0.0
    
    def get_corners(self):
        """
        获取刚体的四个角点（世界坐标）
        
        用于碰撞检测和可视化
        
        返回:
            numpy array [4, 2]，四个角点坐标
        """
        # 本地坐标系的角点（中心为原点）
        hw, hh = self.width / 2, self.height / 2
        local_corners = np.array([
            [-hw, -hh],
            [hw, -hh],
            [hw, hh],
            [-hw, hh]
        ])
        
        # 旋转矩阵
        c, s = np.cos(self.angle), np.sin(self.angle)
        rotation = np.array([[c, -s], [s, c]])
        
        # 旋转并平移到世界坐标
        rotated = local_corners @ rotation.T
        world_corners = rotated + self.position
        
        return world_corners
    
    def draw(self, ax, color='blue', alpha=0.6):
        """
        绘制刚体
        
        参数:
            ax: matplotlib Axes对象
            color: 颜色
            alpha: 透明度
        """
        corners = self.get_corners()
        
        # 绘制填充矩形
        polygon = plt.Polygon(corners, closed=True, facecolor=color, 
                             edgecolor='black', linewidth=2, alpha=alpha)
        ax.add_patch(polygon)
        
        # 绘制朝向箭头
        arrow_length = self.width / 2 + 0.3
        dx = arrow_length * np.cos(self.angle)
        dy = arrow_length * np.sin(self.angle)
        ax.arrow(self.position[0], self.position[1], dx, dy, 
                head_width=0.2, head_length=0.1, fc='red', ec='red')


def compute_moment_of_inertia_rectangle(mass, width, height):
    """
    计算矩形薄板的转动惯量（绕质心轴）
    
    公式：I = (1/12) * m * (w² + h²)
    
    参数:
        mass: 质量
        width: 宽度
        height: 高度
    
    返回:
        转动惯量
    """
    return (1.0 / 12.0) * mass * (width**2 + height**2)


def compute_moment_of_inertia_disk(mass, radius):
    """
    计算实心圆盘的转动惯量（绕中心轴）
    
    公式：I = (1/2) * m * r²
    
    参数:
        mass: 质量
        radius: 半径
    
    返回:
        转动惯量
    """
    return 0.5 * mass * radius**2


def compute_parallel_axis_term(mass, distance):
    """
    计算平行轴定理的附加项
    
    定理：I = I_cm + m * d²
    其中I_cm是绕质心的转动惯量，d是两平行轴的距离
    
    参数:
        mass: 质量
        distance: 两轴距离
    
    返回:
        m * d²
    """
    return mass * distance**2


def simulate_falling_rotation():
    """
    模拟刚体下落和旋转
    """
    print("=" * 55)
    print("刚体动力学 - 自由落体与旋转")
    print("=" * 55)
    
    # 创建刚体
    body = RigidBody(mass=2.0, position=[5.0, 8.0], angle=np.pi/6)
    
    # 设置为实心矩形
    body.width = 2.0
    body.height = 1.0
    body.moment_of_inertia = compute_moment_of_inertia_rectangle(
        body.mass, body.width, body.height
    )
    
    print(f"\n刚体属性:")
    print(f"  质量: {body.mass} kg")
    print(f"  初始位置: {body.position}")
    print(f"  初始角度: {np.degrees(body.angle):.1f}°")
    print(f"  转动惯量: {body.moment_of_inertia:.4f} kg·m²")
    
    # 模拟
    dt = 0.01
    time = 0.0
    
    # 存储轨迹
    positions = [body.position.copy()]
    angles = [body.angle]
    times = [time]
    
    print(f"\n模拟中（每0.5秒采样）...")
    while time < 3.0:
        # 施加重力
        body.apply_force([0, -body.mass * 9.81])
        
        # 更新状态
        body.update(dt)
        time += dt
        
        # 记录轨迹
        if len(times) == 0 or time - times[-1] >= 0.5:
            positions.append(body.position.copy())
            angles.append(body.angle)
            times.append(time)
    
    print(f"\n轨迹采样:")
    for t, pos, ang in zip(times, positions, angles):
        print(f"  t={t:.1f}s: 位置=({pos[0]:.2f}, {pos[1]:.2f}), 角度={np.degrees(ang):.1f}°")
    
    return times, positions, angles


def simulate_torque_rotation():
    """
    模拟力矩使刚体旋转
    """
    print("\n" + "=" * 55)
    print("刚体动力学 - 力矩驱动旋转")
    print("=" * 55)
    
    # 创建刚体
    body = RigidBody(mass=1.0, position=[5.0, 5.0], angle=0.0)
    body.width = 2.0
    body.height = 1.0
    body.moment_of_inertia = compute_moment_of_inertia_rectangle(
        body.mass, body.width, body.height
    )
    
    print(f"\n刚体属性:")
    print(f"  质量: {body.mass} kg")
    print(f"  转动惯量: {body.moment_of_inertia:.4f} kg·m²")
    
    # 施加恒定力矩（通过在边缘施加力）
    # 力臂 = 1m, 力 = 10N
    lever_arm = 1.0
    force_magnitude = 10.0
    
    print(f"\n施加力矩:")
    print(f"  力臂: {lever_arm} m")
    print(f"  力: {force_magnitude} N")
    print(f"  力矩: {lever_arm * force_magnitude:.1f} N·m")
    
    # 模拟
    dt = 0.001
    time = 0.0
    
    # 存储轨迹
    angular_velocities = [body.angular_velocity]
    angles = [body.angle]
    times = [time]
    
    while time < 2.0:
        # 在刚体右边缘施加向上的力，产生逆时针力矩
        application_point = body.position + np.array([
            body.width/2 * np.cos(body.angle),
            body.width/2 * np.sin(body.angle)
        ])
        body.apply_force([0, force_magnitude], application_point)
        
        body.update(dt)
        time += dt
        
        if len(times) == 0 or time - times[-1] >= 0.2:
            angular_velocities.append(body.angular_velocity)
            angles.append(body.angle)
            times.append(time)
    
    print(f"\n旋转采样:")
    for t, ang, omega in zip(times, angles, angular_velocities):
        print(f"  t={t:.1f}s: 角度={np.degrees(ang):.1f}°, 角速度={omega:.2f} rad/s")
    
    # 理论验证：α = τ/I = 10/(1/6) = 60 rad/s²
    # ω = α*t = 60 * 2 = 120 rad/s ≈ 19 rev/s
    theoretical_omega = (lever_arm * force_magnitude) / body.moment_of_inertia * 2.0
    print(f"\n理论角速度（t=2s）: {theoretical_omega:.2f} rad/s")
    print(f"模拟角速度: {angular_velocities[-1]:.2f} rad/s")


def plot_rigid_body_motion(times, positions, angles):
    """
    可视化刚体运动
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # 位置轨迹
    positions = np.array(positions)
    axes[0, 0].plot(times, positions[:, 0], 'b-', label='X')
    axes[0, 0].plot(times, positions[:, 1], 'r-', label='Y')
    axes[0, 0].set_xlabel('时间 (s)')
    axes[0, 0].set_ylabel('位置 (m)')
    axes[0, 0].set_title('位置随时间变化')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 角度轨迹
    axes[0, 1].plot(times, np.degrees(angles), 'g-')
    axes[0, 1].set_xlabel('时间 (s)')
    axes[0, 1].set_ylabel('角度 (°)')
    axes[0, 1].set_title('角度随时间变化')
    axes[0, 1].grid(True, alpha=0.3)
    
    # 轨迹图
    axes[1, 0].plot(positions[:, 0], positions[:, 1], 'b-o', markersize=3)
    axes[1, 0].set_xlabel('X (m)')
    axes[1, 0].set_ylabel('Y (m)')
    axes[1, 0].set_title('位置轨迹')
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].set_aspect('equal')
    
    # 刚体示意图
    ax = axes[1, 1]
    
    # 创建简单刚体用于示意
    body = RigidBody(mass=1.0, position=[0, 0], angle=angles[-1])
    body.width = 0.5
    body.height = 0.3
    body.draw(ax, 'blue')
    
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.set_aspect('equal')
    ax.set_title('刚体最终朝向')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('rigid_body_dynamics_result.png', dpi=150)
    plt.show()
    print("图像已保存至 rigid_body_dynamics_result.png")


if __name__ == "__main__":
    # 自由落体与旋转
    times, positions, angles = simulate_falling_rotation()
    
    # 力矩驱动旋转
    simulate_torque_rotation()
    
    # 可视化
    plot_rigid_body_motion(times, positions, angles)
    
    print("\n测试完成！刚体动力学是机器人、汽车仿真的基础。")
