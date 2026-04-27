# -*- coding: utf-8 -*-
"""
算法实现：物理仿真 / soft_body_simulation

本文件实现 soft_body_simulation 相关的算法功能。
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


class MassPoint:
    """
    质点类
    
    存储单个质点的状态
    """
    
    def __init__(self, position, mass=1.0, pinned=False):
        """
        初始化质点
        
        参数:
            position: 位置 [x, y]
            mass: 质量
            pinned: 是否固定（固定点不受力影响）
        """
        self.position = np.array(position, dtype=float)
        self.prev_position = np.array(position, dtype=float)  # 上一步位置（用于Verlet）
        self.acceleration = np.array([0.0, 0.0])
        self.mass = mass
        self.pinned = pinned
        self.velocity = np.array([0.0, 0.0])  # 速度（用于显示）


class Spring:
    """
    弹簧类
    
    连接两个质点，提供恢复力
    """
    
    def __init__(self, point1, point2, stiffness=500.0, damping=5.0):
        """
        初始化弹簧
        
        参数:
            point1: 质点1
            point2: 质点2
            stiffness: 刚度系数（越大越硬）
            damping: 阻尼系数（越大振动衰减越快）
        """
        self.point1 = point1
        self.point2 = point2
        self.stiffness = stiffness
        self.damping = damping
        
        # 记录自然长度（初始长度）
        self.rest_length = np.linalg.norm(point2.position - point1.position)
    
    def apply_force(self):
        """
        计算并施加弹簧力到两个质点
        
        力公式：F = -k * (length - rest_length) * direction - c * velocity_diff
        """
        if self.point1.pinned and self.point2.pinned:
            return  # 两个都固定则无需计算
        
        # 当前长度和方向
        delta = self.point2.position - self.point1.position
        current_length = np.linalg.norm(delta)
        
        if current_length < 1e-10:
            return  # 避免除零
        
        # 单位方向向量
        direction = delta / current_length
        
        # 弹性力：F = -k * (length - rest_length)
        stretch = current_length - self.rest_length
        elastic_force = self.stiffness * stretch
        
        # 阻尼力：与相对速度点积方向
        velocity_diff = self.point2.velocity - self.point1.velocity
        damping_force = self.damping * np.dot(velocity_diff, direction)
        
        # 总力（标量乘以方向向量）
        total_force_magnitude = elastic_force + damping_force
        force_vector = total_force_magnitude * direction
        
        # 施加到质点（作用力与反作用力）
        if not self.point1.pinned:
            self.point1.acceleration += force_vector / self.point1.mass
        if not self.point2.pinned:
            self.point2.acceleration -= force_vector / self.point2.mass


class SoftBody:
    """
    软体系统
    
    管理质点和弹簧，执行仿真
    """
    
    def __init__(self, gravity=np.array([0.0, -9.81])):
        """
        初始化软体
        
        参数:
            gravity: 重力加速度
        """
        self.points = []
        self.springs = []
        self.gravity = np.array(gravity)
    
    def add_point(self, position, mass=1.0, pinned=False):
        """
        添加质点
        
        参数:
            position: 位置
            mass: 质量
            pinned: 是否固定
        
        返回:
            添加的质点
        """
        point = MassPoint(position, mass, pinned)
        self.points.append(point)
        return point
    
    def add_spring(self, point1, point2, stiffness=500.0, damping=5.0):
        """
        添加弹簧
        
        参数:
            point1: 质点1
            point2: 质点2
            stiffness: 刚度
            damping: 阻尼
        
        返回:
            添加的弹簧
        """
        spring = Spring(point1, point2, stiffness, damping)
        self.springs.append(spring)
        return spring
    
    def add_structural_springs(self):
        """
        为所有相邻质点添加结构弹簧
        
        假设质点按网格排列
        """
        # 获取网格尺寸（根据质点数量估算）
        n = len(self.points)
        grid_size = int(np.sqrt(n)) + 1
        
        for i, p1 in enumerate(self.points):
            # 水平邻居（右）
            if (i + 1) % grid_size != 0 and i + 1 < n:
                self.add_spring(p1, self.points[i + 1])
            
            # 垂直邻居（上）
            if i + grid_size < n:
                self.add_spring(p1, self.points[i + grid_size])
    
    def apply_gravity(self):
        """对所有非固定质点施加重力"""
        for point in self.points:
            if not point.pinned:
                point.acceleration += self.gravity
    
    def apply_damping(self, damping_factor=0.99):
        """
        应用速度阻尼（全局）
        
        参数:
            damping_factor: 阻尼因子（0-1之间）
        """
        for point in self.points:
            if not point.pinned:
                point.velocity *= damping_factor
    
    def constrain_points(self):
        """
        约束质点位置（如边界约束）
        """
        for point in self.points:
            if point.pinned:
                continue
            
            # 简单边界约束
            if point.position[1] < 0:  # 底部
                point.position[1] = 0
                point.prev_position[1] = 0
    
    def verlet_step(self, dt):
        """
        使用Verlet积分执行一步
        
        参数:
            dt: 时间步长
        """
        # 重置加速度
        for point in self.points:
            point.acceleration[:] = 0.0
        
        # 施加重力
        self.apply_gravity()
        
        # 计算弹簧力
        for spring in self.springs:
            spring.apply_force()
        
        # Verlet积分
        for point in self.points:
            if point.pinned:
                continue
            
            # 计算新位置
            # pos_new = 2*pos - pos_old + acc*dt²
            new_position = 2 * point.position - point.prev_position + point.acceleration * dt**2
            
            # 更新速度（用于阻尼力和可视化）
            point.velocity = (new_position - point.prev_position) / (2 * dt)
            
            # 保存旧位置
            point.prev_position = point.position.copy()
            
            # 更新位置
            point.position = new_position
        
        # 约束
        self.constrain_points()
    
    def get_positions(self):
        """获取所有质点位置"""
        return np.array([p.position for p in self.points])


def create_cloth(width, height, segments, stiffness=500.0):
    """
    创建布料软体
    
    参数:
        width: 布料宽度
        height: 布料高度
        segments: 分段数（布料为segments x segments格点）
        stiffness: 弹簧刚度
    
    返回:
        SoftBody对象
    """
    body = SoftBody()
    
    # 创建网格质点
    spacing_x = width / segments
    spacing_y = height / segments
    
    grid = []  # 存储质点引用，用于连接弹簧
    
    for j in range(segments + 1):
        row = []
        for i in range(segments + 1):
            x = i * spacing_x
            y = height - j * spacing_y  # 从顶部悬挂
            
            # 顶部固定
            pinned = (j == 0)
            
            point = body.add_point([x, y], mass=1.0, pinned=pinned)
            row.append(point)
        grid.append(row)
    
    # 创建结构弹簧（水平和垂直）
    for j in range(segments + 1):
        for i in range(segments + 1):
            # 水平弹簧
            if i < segments:
                body.add_spring(grid[j][i], grid[j][i+1], stiffness=stiffness)
            # 垂直弹簧
            if j < segments:
                body.add_spring(grid[j][i], grid[j+1][i], stiffness=stiffness)
    
    # 创建剪切弹簧（对角线）
    for j in range(segments):
        for i in range(segments):
            body.add_spring(grid[j][i], grid[j+1][i+1], stiffness=stiffness * 0.5)
            body.add_spring(grid[j][i+1], grid[j+1][i], stiffness=stiffness * 0.5)
    
    # 创建弯曲弹簧（隔点连接）
    for j in range(segments + 1):
        for i in range(segments - 1):
            body.add_spring(grid[j][i], grid[j][i+2], stiffness=stiffness * 0.2)
    for i in range(segments + 1):
        for j in range(segments - 1):
            body.add_spring(grid[j][i], grid[j+2][i], stiffness=stiffness * 0.2)
    
    return body


def animate_soft_body(body, num_frames=100, dt=0.001):
    """
    动画演示软体
    
    参数:
        body: SoftBody对象
        num_frames: 帧数
        dt: 时间步长
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    positions = body.get_positions()
    scatter = ax.scatter(positions[:, 0], positions[:, 1], s=30, c='blue')
    
    # 绘制弹簧线
    lines = []
    for spring in body.springs:
        line, = ax.plot([], [], 'b-', linewidth=0.5, alpha=0.5)
        lines.append(line)
    
    ax.set_xlim(-1, 11)
    ax.set_ylim(-2, 6)
    ax.set_aspect('equal')
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Y (m)')
    ax.set_title('软体仿真 - 布料悬挂')
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='k', linewidth=2)  # 地面
    
    def update(frame):
        # 运行多步仿真
        for _ in range(10):
            body.verlet_step(dt)
        
        # 更新质点
        positions = body.get_positions()
        scatter.set_offsets(positions)
        
        # 更新弹簧线
        for i, spring in enumerate(body.springs):
            x = [spring.point1.position[0], spring.point2.position[0]]
            y = [spring.point1.position[1], spring.point2.position[1]]
            lines[i].set_data(x, y)
        
        return scatter, *lines
    
    anim = FuncAnimation(fig, update, frames=num_frames, interval=30, blit=True)
    plt.tight_layout()
    plt.savefig('soft_body_result.png', dpi=150)
    plt.show()
    print("图像已保存至 soft_body_result.png")


def demo_single_spring():
    """
    演示单弹簧-质点系统
    """
    print("=" * 55)
    print("软体仿真 - 单弹簧系统演示")
    print("=" * 55)
    
    # 创建简单系统
    body = SoftBody()
    
    # 质点1固定在天花板
    p1 = body.add_point([5.0, 5.0], mass=1.0, pinned=True)
    
    # 质点2自由悬挂
    p2 = body.add_point([5.0, 4.0], mass=1.0, pinned=False)
    
    # 弹簧连接
    body.add_spring(p1, p2, stiffness=1000.0, damping=2.0)
    
    print(f"\n初始状态:")
    print(f"  质点1 (固定): {p1.position}")
    print(f"  质点2 (自由): {p2.position}")
    print(f"  弹簧自然长度: {body.springs[0].rest_length:.4f}")
    
    # 运行仿真
    print(f"\n运行100帧仿真...")
    dt = 0.01
    for step in range(100):
        body.verlet_step(dt)
        if step % 20 == 0:
            print(f"  Step {step}: p2位置=[{p2.position[0]:.4f}, {p2.position[1]:.4f}]")
    
    print(f"\n最终状态:")
    print(f"  质点2: [{p2.position[0]:.4f}, {p2.position[1]:.4f}]")
    print(f"  速度: [{p2.velocity[0]:.4f}, {p2.velocity[1]:.4f}]")


if __name__ == "__main__":
    # 单弹簧演示
    demo_single_spring()
    
    # 布料仿真
    print("\n" + "=" * 55)
    print("创建布料仿真...")
    print("=" * 55)
    
    cloth = create_cloth(width=6.0, height=4.0, segments=10, stiffness=800.0)
    print(f"质点数量: {len(cloth.points)}")
    print(f"弹簧数量: {len(cloth.springs)}")
    
    # 运行一些步骤让布料自然悬挂
    print("\n预运行仿真让布料达到平衡...")
    dt = 0.002
    for _ in range(500):
        cloth.verlet_step(dt)
    
    # 动画
    print("\n生成动画...")
    animate_soft_body(cloth, num_frames=100, dt=dt)
    
    print("\n测试完成！软体仿真是游戏和动画中的重要技术。")
