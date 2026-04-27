# -*- coding: utf-8 -*-
"""
算法实现：物理仿真 / sph_fluid

本文件实现 sph_fluid 相关的算法功能。
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


class SPHParticle:
    """
    SPH粒子类
    
    存储单个粒子的物理状态
    """
    
    def __init__(self, position, velocity=None, mass=1.0):
        """
        初始化粒子
        
        参数:
            position: 位置 [x, y]
            velocity: 速度 [vx, vy]，默认[0, 0]
            mass: 质量
        """
        self.position = np.array(position, dtype=float)
        self.velocity = np.array(velocity if velocity else [0.0, 0.0], dtype=float)
        self.acceleration = np.array([0.0, 0.0])
        self.density = 0.0  # 密度
        self.pressure = 0.0  # 压力
        self.mass = mass
        
        # 用于可视化
        self.density_history = []


class SPHFluid:
    """
    SPH流体仿真器
    """
    
    def __init__(self, smoothing_radius=0.1, rest_density=1000.0, gas_constant=1.0, viscosity=0.1):
        """
        初始化SPH仿真器
        
        参数:
            smoothing_radius: 平滑半径h，决定邻域范围
            rest_density: 静止密度（水约为1000 kg/m³）
            gas_constant: 气体常数（控制压缩性）
            viscosity: 动力粘度系数
        """
        self.smoothing_radius = smoothing_radius
        self.h = smoothing_radius
        self.rest_density = rest_density
        self.gas_constant = gas_constant
        self.viscosity = viscosity
        
        # 预计算核函数常数
        # Poly6核的归一化系数：315/(64*π*h^9)
        self.poly6_constant = 315.0 / (64.0 * np.pi * self.h**9)
        
        # Spiky核梯度系数（用于压力）：-45/(π*h^6)
        self.spiky_gradient_constant = -45.0 / (np.pi * self.h**6)
        
        # 粘度核系数：45/(π*h^6)
        self.viscosity_laplacian_constant = 45.0 / (np.pi * self.h**6)
        
        # 粒子列表
        self.particles = []
    
    def add_particle(self, position, velocity=None, mass=1.0):
        """
        添加粒子
        
        参数:
            position: 初始位置
            velocity: 初始速度
            mass: 质量
        """
        particle = SPHParticle(position, velocity, mass)
        self.particles.append(particle)
    
    def kernel_poly6(self, r):
        """
        Poly6核函数 W(r, h)
        
        用于计算密度
        当 r < h 时有值，否则为0
        
        参数:
            r: 距离（标量）
        
        返回:
            核函数值
        """
        if r >= self.h or r < 0:
            return 0.0
        
        # W = 315/(64*π*h^9) * (h² - r²)³
        q = self.h**2 - r**2
        return self.poly6_constant * q**3
    
    def kernel_spiky_gradient(self, r):
        """
        Spiky核函数梯度 ∇W(r, h)
        
        用于计算压力力
        返回标量形式（沿r方向）
        
        参数:
            r: 距离（标量）
        
        返回:
            梯度值（标量）
        """
        if r >= self.h or r <= 0:
            return 0.0
        
        # ∇W = -45/(π*h^6) * (h - r)² / r * r_hat
        # 这里返回标量形式（方向由两粒子相对位置决定）
        q = self.h - r
        return self.spiky_gradient_constant * q**2
    
    def kernel_viscosity_laplacian(self, r):
        """
        粘度核函数的拉普拉斯 ∇²W(r, h)
        
        用于计算粘性力
        
        参数:
            r: 距离（标量）
        
        返回:
            拉普拉斯值
        """
        if r >= self.h or r < 0:
            return 0.0
        
        # ∇²W = 45/(π*h^6) * (h - r)
        return self.viscosity_laplacian_constant * (self.h - r)
    
    def find_neighbors(self, particle):
        """
        找到给定粒子的邻居（在平滑半径内）
        
        参数:
            particle: SPHParticle对象
        
        返回:
            邻居粒子列表
        """
        neighbors = []
        for other in self.particles:
            if other is particle:
                continue
            distance = np.linalg.norm(particle.position - other.position)
            if distance < self.h:
                neighbors.append((other, distance))
        return neighbors
    
    def compute_density_pressure(self):
        """
        计算所有粒子的密度和压力
        
        密度公式：ρ_i = Σ m_j * W(r_ij, h)
        压力公式：P = k * (ρ - ρ_0)
        """
        for particle in self.particles:
            density = 0.0
            neighbors = self.find_neighbors(particle)
            
            for neighbor, distance in neighbors:
                # 密度 = Σ 质量 * 核函数
                density += neighbor.mass * self.kernel_poly6(distance)
            
            # 自身贡献（当distance=0时，核函数取最大值 h^6）
            # 为简化，这里假设粒子自身贡献为 mass * W(0)
            density += particle.mass * self.kernel_poly6(0)
            
            particle.density = density
            
            # 状态方程计算压力
            # 正压模型：P = k * (ρ - ρ_0)
            particle.pressure = self.gas_constant * (particle.density - self.rest_density)
    
    def compute_forces(self):
        """
        计算作用在每个粒子上的力
        
        力包括：
        1. 压力力（来自邻居粒子的压力梯度）
        2. 粘性力（来自邻居粒子的速度差）
        3. 外力（如重力）
        """
        for particle in self.particles:
            pressure_force = np.array([0.0, 0.0])
            viscosity_force = np.array([0.0, 0.0])
            
            neighbors = self.find_neighbors(particle)
            
            for neighbor, distance in neighbors:
                if distance == 0:
                    continue
                
                # 单位方向向量（从neighbor指向particle）
                direction = (particle.position - neighbor.position) / distance
                
                # 压力力（Spiky核梯度）
                # F_pressure = -Σ m_j * (P_i + P_j)/(2*ρ_j) * ∇W
                pressure_gradient = self.kernel_spiky_gradient(distance)
                pressure_term = (neighbor.pressure + particle.pressure) / (2.0 * neighbor.density)
                pressure_force -= neighbor.mass * pressure_term * pressure_gradient * direction
                
                # 粘性力（粘度核拉普拉斯）
                # F_viscosity = μ * Σ m_j * (v_j - v_i) / ρ_j * ∇²W
                velocity_diff = neighbor.velocity - particle.velocity
                viscosity_lap = self.kernel_viscosity_laplacian(distance)
                viscosity_force += self.viscosity * neighbor.mass * velocity_diff / neighbor.density * viscosity_lap
            
            # 重力（沿-y方向）
            gravity = np.array([0.0, -9.81 * particle.density])
            
            # 总加速度 = 总力 / 密度
            total_force = pressure_force + viscosity_force + gravity
            particle.acceleration = total_force / particle.density
    
    def integrate(self, dt):
        """
        积分更新粒子位置和速度
        
        使用半隐式Euler法
        
        参数:
            dt: 时间步长
        """
        for particle in self.particles:
            # 更新速度
            particle.velocity += particle.acceleration * dt
            
            # 更新位置
            particle.position += particle.velocity * dt
            
            # 边界条件（简单反弹）
            x, y = particle.position
            if y < 0:  # 底部边界
                particle.position[1] = 0
                particle.velocity[1] *= -0.5  # 能量损失
            if x < 0:  # 左边界
                particle.position[0] = 0
                particle.velocity[0] *= -0.5
            if x > 10:  # 右边界
                particle.position[0] = 10
                particle.velocity[0] *= -0.5
    
    def step(self, dt):
        """
        执行一步仿真
        
        参数:
            dt: 时间步长
        """
        # 1. 计算密度和压力
        self.compute_density_pressure()
        
        # 2. 计算力
        self.compute_forces()
        
        # 3. 积分
        self.integrate(dt)
    
    def initialize_particles(self, num_particles=50, width=8.0, height=5.0):
        """
        初始化粒子（创建液滴）
        
        参数:
            num_particles: 粒子数量
            width: 容器宽度
            height: 液滴初始高度
        """
        self.particles = []
        
        # 在中心区域创建液滴
        spacing = self.h * 0.5  # 粒子间距
        count_per_row = int(np.sqrt(num_particles))
        
        start_x = (width - count_per_row * spacing) / 2
        start_y = height - 1.0  # 从上方落下
        
        for i in range(count_per_row):
            for j in range(count_per_row):
                if len(self.particles) >= num_particles:
                    break
                x = start_x + i * spacing
                y = start_y + j * spacing
                # 添加一点随机扰动
                x += np.random.uniform(-0.01, 0.01)
                y += np.random.uniform(-0.01, 0.01)
                self.add_particle([x, y], mass=1.0)
            if len(self.particles) >= num_particles:
                break


def animate_fluid(fluid, num_frames=100, dt=0.001):
    """
    动画演示SPH流体
    
    参数:
        fluid: SPHFluid对象
        num_frames: 帧数
        dt: 时间步长
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 初始化
    positions = np.array([p.position for p in fluid.particles])
    scatter = ax.scatter(positions[:, 0], positions[:, 1], s=50, c='blue', alpha=0.7)
    
    ax.set_xlim(-0.5, 10.5)
    ax.set_ylim(-0.5, 6)
    ax.set_aspect('equal')
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_title('SPH流体仿真')
    ax.grid(True, alpha=0.3)
    
    # 绘制边界
    ax.axhline(y=0, color='k', linewidth=2)
    ax.axvline(x=0, color='k', linewidth=2)
    ax.axvline(x=10, color='k', linewidth=2)
    
    def update(frame):
        # 运行多步仿真
        for _ in range(5):
            fluid.step(dt)
        
        # 更新绘图数据
        positions = np.array([p.position for p in fluid.particles])
        scatter.set_offsets(positions)
        
        # 根据密度着色
        densities = np.array([p.density for p in fluid.particles])
        scatter.set_array(densities)
        scatter.set_clim(vmin=800, vmax=1200)
        
        return scatter,
    
    anim = FuncAnimation(fig, update, frames=num_frames, interval=30, blit=True)
    plt.colorbar(scatter, label='密度 (kg/m³)')
    plt.tight_layout()
    plt.savefig('sph_fluid_result.png', dpi=150)
    plt.show()
    print("图像已保存至 sph_fluid_result.png")


if __name__ == "__main__":
    print("=" * 55)
    print("SPH（光滑粒子流体动力学）仿真测试")
    print("=" * 55)
    
    # 创建SPH仿真器
    fluid = SPHFluid(
        smoothing_radius=0.3,  # 平滑半径
        rest_density=1000.0,  # 水的静止密度
        gas_constant=2000.0,  # 气体常数（控制刚性）
        viscosity=0.5  # 粘度
    )
    
    # 初始化粒子
    print("\n初始化粒子...")
    fluid.initialize_particles(num_particles=64)
    print(f"粒子数量: {len(fluid.particles)}")
    
    # 运行几帧仿真
    print("\n运行仿真...")
    dt = 0.002
    for step in range(20):
        fluid.step(dt)
        if step % 5 == 0:
            # 统计信息
            densities = [p.density for p in fluid.particles]
            velocities = [np.linalg.norm(p.velocity) for p in fluid.particles]
            print(f"  Step {step}: 平均密度={np.mean(densities):.1f}, 最大速度={max(velocities):.2f}")
    
    # 动画演示
    print("\n生成动画...")
    animate_fluid(fluid, num_frames=150, dt=dt)
    
    print("\n测试完成！SPH是电影和游戏中最常用的流体方法。")
