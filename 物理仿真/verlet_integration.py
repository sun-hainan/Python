# -*- coding: utf-8 -*-
"""
算法实现：物理仿真 / verlet_integration

本文件实现 verlet_integration 相关的算法功能。
"""

import numpy as np
import matplotlib.pyplot as plt


class VerletPoint:
    """
    Verlet粒子
    
    存储当前位置、上一步位置和加速度
    """
    
    def __init__(self, position, mass=1.0, pinned=False):
        """
        初始化粒子
        
        参数:
            position: 当前位置 [x, y]
            mass: 质量
            pinned: 是否固定（固定点不移动）
        """
        self.position = np.array(position, dtype=float)
        self.prev_position = np.array(position, dtype=float)  # 上一步位置
        self.acceleration = np.array([0.0, 0.0])
        self.mass = mass
        self.pinned = pinned
    
    def apply_force(self, force):
        """
        施加力
        
        参数:
            force: 力向量 [Fx, Fy]
        """
        if not self.pinned:
            self.acceleration += np.array(force) / self.mass
    
    def integrate(self, dt):
        """
        执行Verlet积分一步
        
        参数:
            dt: 时间步长
        """
        if self.pinned:
            return
        
        # Verlet公式: x_new = 2*x - x_old + a*dt²
        new_position = 2 * self.position - self.prev_position + self.acceleration * dt**2
        
        # 保存当前位置为"旧位置"
        self.prev_position = self.position.copy()
        
        # 更新位置
        self.position = new_position
        
        # 清零加速度（每帧重新计算）
        self.acceleration[:] = 0.0
    
    def get_velocity(self, dt):
        """
        获取当前速度（隐式计算）
        
        参数:
            dt: 时间步长
        
        返回:
            速度向量
        """
        return (self.position - self.prev_position) / (2 * dt)
    
    def constrain_to_bounds(self, min_pos, max_pos):
        """
        简单边界约束
        
        参数:
            min_pos: 最小坐标 [xmin, ymin]
            max_pos: 最大坐标 [xmax, ymax]
        """
        for i in range(2):
            if self.position[i] < min_pos[i]:
                self.position[i] = min_pos[i]
                self.prev_position[i] = min_pos[i]  # 反弹后速度清零
            elif self.position[i] > max_pos[i]:
                self.position[i] = max_pos[i]
                self.prev_position[i] = max_pos[i]


class VerletDistanceConstraint:
    """
    距离约束（维持两点间固定距离）
    
    公式：|p1 - p2| = rest_length
    """
    
    def __init__(self, point1, point2, rest_length=None, stiffness=1.0):
        """
        初始化距离约束
        
        参数:
            point1: 粒子1
            point2: 粒子2
            rest_length: 自然长度，None表示当前距离
            stiffness: 刚度 [0, 1]，1表示完全约束
        """
        self.point1 = point1
        self.point2 = point2
        self.stiffness = stiffness
        
        # 自然长度
        if rest_length is None:
            self.rest_length = np.linalg.norm(point2.position - point1.position)
        else:
            self.rest_length = rest_length
    
    def solve(self):
        """
        求解约束（位置修正）
        
        将两个粒子移动到满足距离约束的位置
        """
        # 当前差向量
        delta = self.point2.position - self.point1.position
        current_length = np.linalg.norm(delta)
        
        if current_length < 1e-10:
            return  # 避免除零
        
        # 差值（用于修正）
        difference = current_length - self.rest_length
        
        # 单位方向
        direction = delta / current_length
        
        # 修正量（考虑刚度）
        correction = difference * self.stiffness
        
        # 计算每个粒子的质量因子（用于按质量比例分配修正）
        total_mass = self.point1.mass + self.point2.mass
        ratio1 = self.point2.mass / total_mass  # p1移动比例
        ratio2 = self.point1.mass / total_mass   # p2移动比例
        
        # 如果粒子固定，只移动另一个
        if self.point1.pinned:
            ratio1 = 0
            ratio2 = 1
        elif self.point2.pinned:
            ratio1 = 1
            ratio2 = 0
        
        # 应用修正
        if not self.point1.pinned:
            self.point1.position += direction * correction * ratio1
        if not self.point2.pinned:
            self.point2.position -= direction * correction * ratio2


class VerletSimulation:
    """
    Verlet粒子仿真器
    
    支持力、约束、边界
    """
    
    def __init__(self, dt=0.01, gravity=None):
        """
        初始化仿真器
        
        参数:
            dt: 时间步长
            gravity: 重力加速度，默认 [0, -9.81]
        """
        self.dt = dt
        self.gravity = np.array(gravity if gravity else [0.0, -9.81])
        self.points = []
        self.constraints = []
    
    def add_point(self, position, mass=1.0, pinned=False):
        """
        添加粒子
        
        参数:
            position: 位置
            mass: 质量
            pinned: 是否固定
        """
        point = VerletPoint(position, mass, pinned)
        self.points.append(point)
        return point
    
    def add_constraint(self, point1, point2, rest_length=None, stiffness=1.0):
        """
        添加距离约束
        
        参数:
            point1: 粒子1
            point2: 粒子2
            rest_length: 自然长度
            stiffness: 刚度
        """
        constraint = VerletDistanceConstraint(point1, point2, rest_length, stiffness)
        self.constraints.append(constraint)
        return constraint
    
    def apply_gravity(self):
        """对所有非固定粒子施加重力"""
        for point in self.points:
            if not point.pinned:
                point.apply_force(self.gravity * point.mass)
    
    def step(self, constraint_iterations=3):
        """
        执行一步仿真
        
        参数:
            constraint_iterations: 约束求解迭代次数
        """
        # 1. 施加重力
        self.apply_gravity()
        
        # 2. 积分所有粒子
        for point in self.points:
            point.integrate(self.dt)
        
        # 3. 迭代求解约束
        for _ in range(constraint_iterations):
            for constraint in self.constraints:
                constraint.solve()
        
        # 4. 应用边界约束
        for point in self.points:
            point.constrain_to_bounds([0, 0], [10, 10])
    
    def get_positions(self):
        """获取所有粒子位置"""
        return np.array([p.position for p in self.points])


def create_rope(num_points=10, start_pos=[1, 8], end_pos=[5, 8]):
    """
    创建绳索
    
    参数:
        num_points: 粒子数量
        start_pos: 起始位置（固定）
        end_pos: 结束位置
    
    返回:
        VerletSimulation对象
    """
    sim = VerletSimulation(dt=0.01)
    
    # 创建粒子
    points = []
    for i in range(num_points):
        t = i / (num_points - 1)
        pos = np.array(start_pos) + t * (np.array(end_pos) - np.array(start_pos))
        pinned = (i == 0)  # 只固定第一个
        point = sim.add_point(pos, mass=1.0, pinned=pinned)
        points.append(point)
    
    # 创建约束（相邻粒子）
    for i in range(num_points - 1):
        sim.add_constraint(points[i], points[i+1], stiffness=1.0)
    
    return sim, points


def create_chain_grid(rows, cols, spacing=0.5):
    """
    创建网格链（2D网格）
    
    参数:
        rows: 行数
        cols: 列数
        spacing: 粒子间距
    
    返回:
        VerletSimulation对象
    """
    sim = VerletSimulation(dt=0.01)
    
    grid = []
    for j in range(rows):
        row = []
        for i in range(cols):
            pos = [2 + i * spacing, 8 - j * spacing]
            pinned = (j == 0)  # 顶部固定
            point = sim.add_point(pos, mass=1.0, pinned=pinned)
            row.append(point)
        grid.append(row)
    
    # 水平约束
    for j in range(rows):
        for i in range(cols - 1):
            sim.add_constraint(grid[j][i], grid[j][i+1])
    
    # 垂直约束
    for j in range(rows - 1):
        for i in range(cols):
            sim.add_constraint(grid[j][i], grid[j+1][i])
    
    return sim, grid


def demo_rope():
    """
    演示绳索仿真
    """
    print("=" * 55)
    print("Verlet积分器 - 绳索仿真演示")
    print("=" * 55)
    
    # 创建绳索
    sim, points = create_rope(num_points=15, start_pos=[2, 8], end_pos=[6, 6])
    
    print(f"\n绳索设置:")
    print(f"  粒子数量: {len(points)}")
    print(f"  约束数量: {len(sim.constraints)}")
    print(f"  初始长度: {np.linalg.norm(points[-1].position - points[0].position):.2f} m")
    
    # 运行仿真
    print(f"\n运行100帧仿真...")
    for frame in range(100):
        sim.step(constraint_iterations=5)
        if frame % 25 == 0:
            print(f"  Frame {frame}: 末端位置={points[-1].position}")
    
    final_length = np.linalg.norm(points[-1].position - points[0].position)
    print(f"\n最终长度: {final_length:.4f} m")
    print("（重力下坠导致水平投影缩短，这是正常的）")


def demo_bouncing():
    """
    演示弹跳球
    """
    print("\n" + "=" * 55)
    print("Verlet积分器 - 弹跳球演示")
    print("=" * 55)
    
    sim = VerletSimulation(dt=0.01, gravity=[0, -9.81])
    
    # 创建球
    ball = sim.add_point([5, 8], mass=1.0, pinned=False)
    
    print(f"\n初始位置: {ball.position}")
    
    # 运行仿真
    positions = []
    times = []
    
    for frame in range(200):
        sim.step()
        
        if frame % 20 == 0:
            print(f"  Frame {frame}: 位置={ball.position}, 速度={ball.get_velocity(sim.dt)}")
            positions.append(ball.position.copy())
            times.append(frame * sim.dt)
    
    print(f"\n最终位置: {ball.position}")
    
    return times, positions


def demo_cloth():
    """
    演示简单的布片
    """
    print("\n" + "=" * 55)
    print("Verlet积分器 - 简单布片演示")
    print("=" * 55)
    
    sim, grid = create_chain_grid(rows=5, cols=8, spacing=0.5)
    
    print(f"\n布片设置:")
    print(f"  粒子数量: {len(sim.points)}")
    print(f"  约束数量: {len(sim.constraints)}")
    
    # 运行仿真
    print(f"\n运行500帧预热...")
    for _ in range(500):
        sim.step(constraint_iterations=3)
    
    # 检查结果
    bottom_row = grid[-1]
    y_coords = [p.position[1] for p in bottom_row]
    print(f"底部行Y坐标: {np.mean(y_coords):.2f} (初始应该约8，重力下坠后降低)")
    
    return sim


def plot_verlet_results():
    """
    可视化结果
    """
    # 弹跳球轨迹
    times, positions = demo_bouncing()
    positions = np.array(positions)
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # 位置时程
    axes[0].plot(times, positions[:, 1], 'b-', linewidth=2)
    axes[0].set_xlabel('时间 (s)')
    axes[0].set_ylabel('高度 (m)')
    axes[0].set_title('弹跳球高度随时间变化')
    axes[0].grid(True, alpha=0.3)
    
    # 相图
    velocities = []
    for pos in positions:
        # 手动计算速度（从轨迹）
        pass
    axes[1].plot(positions[:, 0], positions[:, 1], 'r-o', markersize=3)
    axes[1].set_xlabel('X (m)')
    axes[1].set_ylabel('Y (m)')
    axes[1].set_title('弹跳球轨迹')
    axes[1].grid(True, alpha=0.3)
    axes[1].set_aspect('equal')
    
    plt.tight_layout()
    plt.savefig('verlet_integration_result.png', dpi=150)
    plt.show()
    print("图像已保存至 verlet_integration_result.png")


if __name__ == "__main__":
    # 绳索演示
    demo_rope()
    
    # 弹跳球演示
    demo_bouncing()
    
    # 布片演示
    demo_cloth()
    
    # 可视化
    plot_verlet_results()
    
    print("\n测试完成！Verlet积分是约束系统仿真的标准方法。")
