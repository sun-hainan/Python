# -*- coding: utf-8 -*-

"""

算法实现：物理仿真 / rigid_body



本文件实现 rigid_body 相关的算法功能。

"""



import math





class AABB:

    """轴对齐边界框"""



    def __init__(self, min_x: float, max_x: float, min_y: float, max_y: float):

        self.min_x = min_x

        self.max_x = max_x

        self.min_y = min_y

        self.max_y = max_y



    @staticmethod

    def from_center(cx: float, cy: float, width: float, height: float):

        """从中心点和宽高创建"""

        hw = width / 2

        hh = height / 2

        return AABB(cx - hw, cx + hw, cy - hh, cy + hh)



    def intersects(self, other) -> bool:

        """检测两个AABB是否碰撞"""

        return (self.max_x > other.min_x and self.min_x < other.max_x and

                self.max_y > other.min_y and self.min_y < other.max_y)



    def contains(self, x: float, y: float) -> bool:

        """检测点是否在AABB内"""

        return self.min_x <= x <= self.max_x and self.min_y <= y <= self.max_y



    def center(self):

        """获取中心点"""

        return (self.min_x + self.max_x) / 2, (self.min_y + self.max_y) / 2



    def width(self):

        return self.max_x - self.min_x



    def height(self):

        return self.max_y - self.min_y





class RigidBody:

    """刚体"""



    def __init__(self, x: float, y: float, vx: float = 0, vy: float = 0,

                 width: float = 1, height: float = 1, mass: float = 1):

        self.aabb = AABB.from_center(x, y, width, height)

        self.vx = vx

        self.vy = vy

        self.mass = mass

        self.restitution = 0.5  # 弹性系数



    def update(self, dt: float):

        """更新位置（简单欧拉积分）"""

        cx, cy = self.aabb.center()

        cx += self.vx * dt

        cy += self.vy * dt

        hw = self.aabb.width() / 2

        hh = self.aabb.height() / 2

        self.aabb = AABB(cx - hw, cx + hw, cy - hh, cy + hh)



    def apply_gravity(self, g: float, dt: float):

        """应用重力"""

        self.vy += g * dt





class CollisionDetector:

    """碰撞检测器"""



    def __init__(self):

        self.bodies = []

        self.collisions = []



    def add_body(self, body: RigidBody):

        self.bodies.append(body)



    def detect(self) -> list:

        """

        检测所有碰撞



        返回：碰撞对列表 [(body1, body2), ...]

        """

        self.collisions = []

        n = len(self.bodies)



        for i in range(n):

            for j in range(i + 1, n):

                if self.bodies[i].aabb.intersects(self.bodies[j].aabb):

                    self.collisions.append((self.bodies[i], self.bodies[j]))



        return self.collisions



    def resolve(self):

        """

        简单碰撞响应：速度反向 + 弹性

        """

        for b1, b2 in self.collisions:

            # 简单响应：交换速度分量

            b1.vx, b2.vx = b2.vx * b2.restitution, b1.vx * b1.restitution

            b1.vy, b2.vy = b2.vy * b2.restitution, b1.vy * b1.restitution





def simulate(n_bodies: int = 5, n_steps: int = 100, dt: float = 0.1, gravity: float = -9.8):

    """

    模拟刚体碰撞



    参数：

        n_bodies: 物体数量

        n_steps: 模拟步数

        dt: 时间步长

        gravity: 重力加速度

    """

    print("=== 刚体碰撞检测模拟 ===\n")



    detector = CollisionDetector()



    # 初始化物体

    for i in range(n_bodies):

        import random

        x = random.uniform(0, 10)

        y = random.uniform(5, 15)

        vx = random.uniform(-2, 2)

        vy = random.uniform(-1, 1)

        w = random.uniform(1, 2)

        h = random.uniform(1, 2)

        body = RigidBody(x, y, vx, vy, w, h)

        detector.add_body(body)

        print(f"Body {i+1}: pos=({x:.1f},{y:.1f}), vel=({vx:.1f},{vy:.1f}), size={w:.1f}x{h:.1f}")



    print(f"\n模拟 {n_steps} 步...")



    for step in range(n_steps):

        # 应用重力

        for body in detector.bodies:

            body.apply_gravity(gravity, dt)



        # 更新位置

        for body in detector.bodies:

            body.update(dt)



        # 检测碰撞

        collisions = detector.detect()



        if collisions:

            print(f"  Step {step+1}: 检测到 {len(collisions)} 个碰撞")



        # 碰撞响应

        detector.resolve()



    print("\n模拟完成")

    print(f"最终位置:")

    for i, body in enumerate(detector.bodies):

        cx, cy = body.aabb.center()

        print(f"  Body {i+1}: ({cx:.1f}, {cy:.1f}), vel=({body.vx:.1f}, {body.vy:.1f})")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    simulate(n_bodies=5, n_steps=50, dt=0.1, gravity=-9.8)

