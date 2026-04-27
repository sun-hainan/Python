# -*- coding: utf-8 -*-
"""
算法实现：物理仿真 / particle_system_simple

本文件实现 particle_system_simple 相关的算法功能。
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


class Particle:
    """
    粒子类
    
    存储单个粒子的状态
    """
    
    def __init__(self, position, velocity, lifetime, size=5.0, color=None):
        """
        初始化粒子
        
        参数:
            position: 位置 [x, y]
            velocity: 速度 [vx, vy]
            lifetime: 生命周期（秒）
            size: 大小
            color: 颜色 [r, g, b]
        """
        self.position = np.array(position, dtype=float)
        self.velocity = np.array(velocity, dtype=float)
        self.lifetime = lifetime  # 剩余寿命
        self.max_lifetime = lifetime
        self.size = size
        self.initial_size = size
        self.color = color if color else np.array([1.0, 1.0, 1.0])  # 默认白色
        self.initial_color = self.color.copy()
        
        # 加速度（用于力场）
        self.acceleration = np.array([0.0, 0.0])
        
        # 是否存活
        self.alive = True
    
    def apply_force(self, force):
        """
        施加力
        
        参数:
            force: 力向量 [Fx, Fy]
        """
        self.acceleration += np.array(force)
    
    def update(self, dt):
        """
        更新粒子状态
        
        参数:
            dt: 时间步长
        """
        if not self.alive:
            return
        
        # 速度积分
        self.velocity += self.acceleration * dt
        
        # 位置积分
        self.position += self.velocity * dt
        
        # 减少寿命
        self.lifetime -= dt
        
        # 死亡判断
        if self.lifetime <= 0:
            self.alive = False
            return
        
        # 计算生命周期进度 [0, 1]
        progress = 1.0 - (self.lifetime / self.max_lifetime)
        
        # 尺寸随生命周期变化（渐隐）
        self.size = self.initial_size * (1.0 - progress * 0.5)
        
        # 颜色渐变（可自定义）
        self.color = self.initial_color * (1.0 - progress * 0.3)
        
        # 清零加速度
        self.acceleration[:] = 0.0
    
    def is_alive(self):
        """检查粒子是否存活"""
        return self.alive


class ForceField:
    """
    力场
    
    定义作用在粒子上的外力
    """
    
    def __init__(self, gravity=None, wind=None):
        """
        初始化力场
        
        参数:
            gravity: 重力加速度 [gx, gy]
            wind: 风力（可以是常量或函数）
        """
        self.gravity = np.array(gravity if gravity else [0.0, -9.81])
        self.wind = wind  # 可以是函数 wind(particle, t)
        self.time = 0.0
    
    def apply_to(self, particle):
        """
        对粒子施力
        
        参数:
            particle: Particle对象
        """
        # 重力
        particle.apply_force(self.gravity)
        
        # 风力（如果定义了的话）
        if callable(self.wind):
            wind_force = self.wind(particle, self.time)
            particle.apply_force(wind_force)
        elif self.wind is not None:
            particle.apply_force(self.wind)
    
    def advance_time(self, dt):
        """推进力场时间"""
        self.time += dt


class Emitter:
    """
    发射器
    
    控制粒子的生成
    """
    
    def __init__(self, position, emission_rate=10.0, particle_lifetime=2.0):
        """
        初始化发射器
        
        参数:
            position: 发射位置 [x, y]
            emission_rate: 发射率（个/秒）
            particle_lifetime: 粒子生命周期
        """
        self.position = np.array(position, dtype=float)
        self.emission_rate = emission_rate
        self.particle_lifetime = particle_lifetime
        
        # 发射参数
        self.emission_angle_range = (-np.pi/2, np.pi/2)  # 发射方向范围
        self.emission_speed_range = (2.0, 5.0)  # 发射速度范围
        self.particle_size_range = (3.0, 8.0)  # 粒子大小范围
    
    def emit(self):
        """
        发射一个粒子
        
        返回:
            Particle对象
        """
        # 随机发射方向（默认向上）
        angle = np.random.uniform(*self.emission_angle_range)
        
        # 随机速度
        speed = np.random.uniform(*self.emission_speed_range)
        velocity = np.array([np.cos(angle) * speed, np.sin(angle) * speed])
        
        # 随机大小
        size = np.random.uniform(*self.particle_size_range)
        
        # 创建粒子
        particle = Particle(
            position=self.position.copy(),
            velocity=velocity,
            lifetime=self.particle_lifetime,
            size=size,
            color=self.get_color()
        )
        
        return particle
    
    def get_color(self):
        """
        获取粒子颜色（可被子类重写）
        
        返回:
            RGB颜色数组
        """
        return np.array([1.0, 0.8, 0.2])  # 默认橙黄色
    
    def set_angle_range(self, min_angle, max_angle):
        """
        设置发射角度范围
        
        参数:
            min_angle: 最小角度（弧度）
            max_angle: 最大角度（弧度）
        """
        self.emission_angle_range = (min_angle, max_angle)


class ParticleSystem:
    """
    粒子系统
    
    管理所有粒子，执行仿真循环
    """
    
    def __init__(self, force_field=None):
        """
        初始化粒子系统
        
        参数:
            force_field: ForceField对象
        """
        self.particles = []
        self.emitters = []
        self.force_field = force_field if force_field else ForceField()
    
    def add_emitter(self, emitter):
        """
        添加发射器
        
        参数:
            emitter: Emitter对象
        """
        self.emitters.append(emitter)
    
    def update(self, dt):
        """
        更新所有粒子
        
        参数:
            dt: 时间步长
        """
        # 更新力场时间
        self.force_field.advance_time(dt)
        
        # 从发射器生成粒子
        for emitter in self.emitters:
            # 计算这个dt应该发射的粒子数
            num_to_emit = emitter.emission_rate * dt
            self.particles_remaining = getattr(self, 'particles_remaining', 0.0) + num_to_emit
            
            # 发射整数个粒子
            while self.particles_remaining >= 1.0:
                self.particles.append(emitter.emit())
                self.particles_remaining -= 1.0
        
        # 更新所有粒子
        for particle in self.particles:
            # 施加力场
            self.force_field.apply_to(particle)
            
            # 更新状态
            particle.update(dt)
        
        # 移除死亡粒子
        self.particles = [p for p in self.particles if p.is_alive()]
    
    def get_alive_count(self):
        """获取存活粒子数"""
        return len(self.particles)
    
    def get_positions(self):
        """获取所有存活粒子的位置"""
        return np.array([p.position for p in self.particles if p.is_alive()])


class FireEmitter(Emitter):
    """
    火焰发射器
    
    产生向上的火焰粒子
    """
    
    def __init__(self, position, emission_rate=50.0):
        super().__init__(position, emission_rate, particle_lifetime=1.5)
        self.set_angle_range(-np.pi/6, np.pi/6)  # 向上发射
        self.emission_speed_range = (3.0, 7.0)
    
    def get_color(self):
        """火焰颜色：底部黄，顶部红"""
        progress = np.random.random()
        if progress < 0.3:
            return np.array([1.0, 1.0, 0.3])  # 亮黄
        elif progress < 0.7:
            return np.array([1.0, 0.5, 0.1])  # 橙
        else:
            return np.array([1.0, 0.2, 0.0])  # 红


class SmokeEmitter(Emitter):
    """
    烟雾发射器
    
    产生缓慢上升的烟雾
    """
    
    def __init__(self, position, emission_rate=20.0):
        super().__init__(position, emission_rate, particle_lifetime=3.0)
        self.set_angle_range(-np.pi/4, np.pi/4)
        self.emission_speed_range = (1.0, 3.0)
    
    def get_color(self):
        """烟雾颜色：灰白色"""
        gray = 0.4 + np.random.random() * 0.3
        return np.array([gray, gray, gray])


class ExplosionEmitter(Emitter):
    """
    爆炸发射器（单次发射大量粒子）
    """
    
    def __init__(self, position):
        super().__init__(position, emission_rate=0, particle_lifetime=2.0)
        self.to_emit = 100  # 爆炸粒子数
        self.emission_speed_range = (5.0, 15.0)
    
    def emit_all(self):
        """发射所有爆炸粒子"""
        particles = []
        for _ in range(self.to_emit):
            angle = np.random.uniform(0, 2*np.pi)
            speed = np.random.uniform(*self.emission_speed_range)
            velocity = np.array([np.cos(angle) * speed, np.sin(angle) * speed])
            
            particle = Particle(
                position=self.position.copy(),
                velocity=velocity,
                lifetime=self.particle_lifetime * np.random.uniform(0.5, 1.5),
                size=np.random.uniform(3, 8),
                color=np.array([1.0, 0.8, 0.2])
            )
            particles.append(particle)
        
        self.to_emit = 0
        return particles
    
    def should_emit(self):
        """检查是否还有粒子要发射"""
        return self.to_emit > 0


def animate_firework(ps, num_frames=100):
    """
    动画演示烟花
    """
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # 创建爆炸发射器
    explosion_emitters = []
    
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_aspect('equal')
    ax.set_facecolor('black')
    fig.patch.set_facecolor('black')
    ax.set_xticks([])
    ax.set_yticks([])
    
    def update(frame):
        ax.clear()
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        ax.set_aspect('equal')
        ax.set_facecolor('black')
        ax.set_xticks([])
        ax.set_yticks([])
        
        # 定期创建新的爆炸
        if frame % 60 == 0:
            emitter = ExplosionEmitter([np.random.uniform(2, 8), np.random.uniform(3, 7)])
            explosion_emitters.append(emitter)
        
        # 处理所有爆炸发射器
        for emitter in explosion_emitters[:]:
            if emitter.should_emit():
                new_particles = emitter.emit_all()
                ps.particles.extend(new_particles)
        
        # 更新粒子
        ps.update(1/30)
        
        # 绘制粒子
        positions = ps.get_positions()
        colors = np.array([p.color for p in ps.particles])
        
        if len(positions) > 0:
            ax.scatter(positions[:, 0], positions[:, 1], c=colors, 
                      s=np.array([p.size for p in ps.particles]) * 10,
                      alpha=0.8)
        
        ax.set_title(f'粒子数: {ps.get_alive_count()}', color='white')
        
        return []
    
    anim = FuncAnimation(fig, update, frames=num_frames, interval=30, blit=False)
    plt.tight_layout()
    plt.savefig('particle_system_result.png', dpi=150)
    plt.show()
    print("图像已保存至 particle_system_result.png")


def demo_particle_system():
    """
    演示各种粒子效果
    """
    print("=" * 55)
    print("粒子系统演示")
    print("=" * 55)
    
    # 创建力场
    gravity = ForceField(gravity=[0, -5.0])  # 较弱重力
    ps = ParticleSystem(force_field=gravity)
    
    # 创建火焰发射器
    fire_emitter = FireEmitter([5, 1], emission_rate=100)
    ps.add_emitter(fire_emitter)
    
    print("\n火焰粒子系统:")
    print(f"  发射率: 100个/秒")
    print(f"  重力: [0, -5.0]")
    
    # 运行几帧
    print("\n运行仿真（10帧）...")
    for frame in range(10):
        ps.update(0.1)
        print(f"  Frame {frame}: 粒子数={ps.get_alive_count()}")
    
    return ps


if __name__ == "__main__":
    # 基本粒子系统演示
    ps = demo_particle_system()
    
    # 烟花动画
    print("\n生成烟花动画...")
    gravity = ForceField(gravity=[0, -2.0])  # 缓慢下落
    ps = ParticleSystem(force_field=gravity)
    animate_firework(ps, num_frames=200)
    
    print("\n测试完成！粒子系统是游戏和特效的基础。")
