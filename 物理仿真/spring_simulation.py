# -*- coding: utf-8 -*-
"""
算法实现：物理仿真 / spring_simulation

本文件实现 spring_simulation 相关的算法功能。
"""

import math


class Point:
    """质点"""

    def __init__(self, x: float, y: float, mass: float = 1.0, pinned: bool = False):
        self.x = x
        self.y = y
        self.mass = mass
        self.pinned = pinned  # 是否固定（如墙壁上的点）
        self.old_x = x
        self.old_y = y

    def update(self, ax: float, ay: float, dt: float):
        """Verlet 积分更新位置"""
        if self.pinned:
            return
        # Verlet: x_new = 2x - x_old + a*dt²
        new_x = 2 * self.x - self.old_x + ax * dt * dt
        new_y = 2 * self.y - self.old_y + ay * dt * dt
        self.old_x, self.old_y = self.x, self.y
        self.x, self.y = new_x, new_y


class Spring:
    """弹簧连接"""

    def __init__(self, p1: Point, p2: Point, stiffness: float, rest_length: float):
        self.p1 = p1
        self.p2 = p2
        self.stiffness = stiffness  # 劲度系数 k
        self.rest_length = rest_length

    def apply_force(self):
        """计算并施加弹簧力"""
        dx = self.p2.x - self.p1.x
        dy = self.p2.y - self.p1.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < 1e-6:
            return

        # 弹簧力 F = k * (length - rest_length)
        stretch = dist - self.rest_length
        force_mag = self.stiffness * stretch

        # 单位方向
        fx = force_mag * dx / dist
        fy = force_mag * dy / dist

        # 施加力（无质量弹簧，作用力在质点上）
        if not self.p1.pinned:
            self.p1.x += fx / self.p1.mass
            self.p1.y += fy / self.p1.mass
        if not self.p2.pinned:
            self.p2.x -= fx / self.p2.mass
            self.p2.y -= fy / self.p2.mass


class SpringSystem:
    """弹簧质点系统"""

    def __init__(self, gravity: float = 9.8, damping: float = 0.99):
        self.points = []
        self.springs = []
        self.gravity = gravity
        self.damping = damping
        self.time = 0.0

    def add_point(self, x: float, y: float, mass: float = 1.0, pinned: bool = False):
        p = Point(x, y, mass, pinned)
        self.points.append(p)
        return p

    def add_spring(self, p1: Point, p2: Point, stiffness: float, rest_length: float = None):
        if rest_length is None:
            dx = p2.x - p1.x
            dy = p2.y - p1.y
            rest_length = math.sqrt(dx * dx + dy * dy)
        spring = Spring(p1, p2, stiffness, rest_length)
        self.springs.append(spring)
        return spring

    def step(self, dt: float, iterations: int = 5):
        """
        仿真一步

        参数：
            dt: 时间步长
            iterations: 约束迭代次数（越多越稳定但越慢）
        """
        # 应用重力
        for p in self.points:
            if not p.pinned:
                ay = self.gravity

        # 约束迭代
        for _ in range(iterations):
            # 应用弹簧约束
            for s in self.springs:
                s.apply_force()

            # 阻尼
            for p in self.points:
                if not p.pinned:
                    p.x *= self.damping
                    p.y *= self.damping

        # Verlet 积分
        for p in self.points:
            ay = self.gravity
            p.update(0, ay, dt)

        self.time += dt

    def get_state(self) -> list:
        """获取所有质点位置"""
        return [(p.x, p.y) for p in self.points]


def create_demo_chain(n: int = 10, spacing: float = 30) -> SpringSystem:
    """创建链条演示"""
    system = SpringSystem(gravity=0.5, damping=0.995)
    stiffness = 0.5

    # 创建点
    points = []
    for i in range(n):
        x = i * spacing
        y = 100
        pinned = (i == 0)  # 第一个固定
        p = system.add_point(x, y, mass=1.0, pinned=pinned)
        points.append(p)

    # 创建弹簧
    for i in range(n - 1):
        system.add_spring(points[i], points[i + 1], stiffness)

    return system


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 弹簧质点系统测试 ===\n")

    # 创建简单链条
    system = create_demo_chain(8)

    print(f"初始状态：{system.points.Count} 个点，{len(system.springs)} 个弹簧")
    print(f"初始位置：{system.get_state()}\n")

    # 运行几步仿真
    print("运行 10 步仿真...")
    for i in range(10):
        system.step(dt=0.5, iterations=3)
        print(f"  步 {i+1}: time={system.time:.1f}, 位置={system.get_state()}")

    print("\n模拟完成")

    # 创建网格演示
    print("\n--- 创建网格结构 ---")
    system2 = SpringSystem(gravity=0.3, damping=0.99)
    rows, cols = 5, 5

    # 创建点网格
    grid = []
    for r in range(rows):
        row = []
        for c in range(cols):
            x = c * 30 + 50
            y = r * 30 + 50
            pinned = (r == 0)
            p = system2.add_point(x, y, mass=1.0, pinned=pinned)
            row.append(p)
        grid.append(row)

    # 水平弹簧
    for r in range(rows):
        for c in range(cols - 1):
            system2.add_spring(grid[r][c], grid[r][c+1], 0.5)

    # 垂直弹簧
    for r in range(rows - 1):
        for c in range(cols):
            system2.add_spring(grid[r][c], grid[r+1][c], 0.5)

    print(f"网格：{len(system2.points)} 个点，{len(system2.springs)} 个弹簧")
    print(f"运行 20 步...")
    for i in range(20):
        system2.step(dt=0.3, iterations=2)

    print("网格仿真完成")
