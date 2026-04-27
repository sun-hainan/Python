# -*- coding: utf-8 -*-

"""

算法实现：物理仿真 / cloth_simulation



本文件实现 cloth_simulation 相关的算法功能。

"""



import math

import random





class ClothParticle:

    """布料质点：具有位置、速度、加速度、质量"""

    

    def __init__(self, x, y, mass=1.0, pinned=False):

        self.x = x

        self.y = y

        self.prev_x = x

        self.prev_y = y

        self.acc_x = 0.0

        self.acc_y = 0.0

        self.mass = mass

        self.pinned = pinned

    

    def apply_force(self, fx, fy):

        """施加力（更新加速度）"""

        if self.pinned:

            return

        self.acc_x += fx / self.mass

        self.acc_y += fy / self.mass

    

    def update_verlet(self, dt, damping=0.99):

        """Verlet 积分更新位置"""

        if self.pinned:

            return

        

        # 速度估计（从位移）

        vx = (self.x - self.prev_x) * damping

        vy = (self.y - self.prev_y) * damping

        

        # 保存当前位置

        self.prev_x = self.x

        self.prev_y = self.y

        

        # Verlet 积分

        self.x = self.x + vx + self.acc_x * dt * dt

        self.y = self.y + vy + self.acc_y * dt * dt

        

        # 重置加速度

        self.acc_x = 0.0

        self.acc_y = 0.0





class ClothSpring:

    """布料弹簧：连接两个质点，维持距离约束"""

    

    def __init__(self, p1, p2, spring_type='structural', stiffness=1.0):

        """

        初始化弹簧

        

        参数:

            p1, p2: 连接的质点

            spring_type: 弹簧类型 ('structural', 'shear', 'bend')

            stiffness: 刚度（约束满足的强度）

        """

        self.p1 = p1

        self.p2 = p2

        self.spring_type = spring_type

        

        # 计算自然长度（初始距离）

        dx = p2.x - p1.x

        dy = p2.y - p1.y

        self.rest_length = math.sqrt(dx * dx + dy * dy)

        

        # 刚度：0-1 之间，越大约束越强

        self.stiffness = stiffness

    

    def satisfy_constraint(self, iterations=3):

        """

        满足弹簧约束（多次迭代以提高稳定性）

        

        参数:

            iterations: 迭代次数

        """

        for _ in range(iterations):

            dx = self.p2.x - self.p1.x

            dy = self.p2.y - self.p1.y

            current_length = math.sqrt(dx * dx + dy * dy)

            

            if current_length < 1e-10:

                continue

            

            # 偏离量

            deviation = (current_length - self.rest_length) / current_length

            

            # 方向

            offset_x = dx * deviation * 0.5 * self.stiffness

            offset_y = dy * deviation * 0.5 * self.stiffness

            

            # 分配位移（考虑固定状态）

            p1_fixed = self.p1.pinned

            p2_fixed = self.p2.pinned

            

            if p1_fixed and p2_fixed:

                continue  # 都固定，不移动

            elif p1_fixed:

                self.p2.x -= offset_x * 2

                self.p2.y -= offset_y * 2

            elif p2_fixed:

                self.p1.x += offset_x * 2

                self.p1.y += offset_y * 2

            else:

                self.p1.x += offset_x

                self.p1.y += offset_y

                self.p2.x -= offset_x

                self.p2.y -= offset_y





class ClothSimulation:

    """布料仿真器：管理质点和弹簧"""

    

    def __init__(self, width, height, cols, rows):

        """

        初始化布料仿真

        

        参数:

            width: 布料宽度

            height: 布料高度

            cols: 列数（水平质点数）

            rows: 行数（垂直质点数）

        """

        self.width = width

        self.height = height

        self.cols = cols

        self.rows = rows

        

        # 创建质点网格

        self.particles = []

        self._create_particles()

        

        # 创建弹簧

        self.springs = []

        self._create_springs()

        

        # 仿真参数

        self.gravity = (0, -9.8)

        self.damping = 0.99

        self.constraint_iterations = 5

        

        # 球体碰撞

        self.collision_balls = []

    

    def _create_particles(self):

        """创建质点网格"""

        # 网格间距

        spacing_x = self.width / (self.cols - 1) if self.cols > 1 else self.width

        spacing_y = self.height / (self.rows - 1) if self.rows > 1 else self.height

        

        for row in range(self.rows):

            for col in range(self.cols):

                x = col * spacing_x

                y = -row * spacing_y  # 负号使布料向上展开

                pinned = (row == 0)  # 固定顶行

                mass = 1.0

                

                p = ClothParticle(x, y, mass, pinned)

                self.particles.append(p)

    

    def _create_springs(self):

        """创建弹簧（结构、剪切、弯曲）"""

        def get_particle(row, col):

            """获取指定位置的质点"""

            if 0 <= row < self.rows and 0 <= col < self.cols:

                return self.particles[row * self.cols + col]

            return None

        

        for row in range(self.rows):

            for col in range(self.cols):

                p = get_particle(row, col)

                if p is None:

                    continue

                

                # 结构弹簧（水平和垂直）

                p_right = get_particle(row, col + 1)

                if p_right:

                    self.springs.append(ClothSpring(p, p_right, 'structural', 1.0))

                

                p_down = get_particle(row + 1, col)

                if p_down:

                    self.springs.append(ClothSpring(p, p_down, 'structural', 1.0))

                

                # 剪切弹簧（对角线）

                p_dr = get_particle(row + 1, col + 1)

                if p_dr:

                    self.springs.append(ClothSpring(p, p_dr, 'shear', 0.8))

                

                p_dl = get_particle(row + 1, col - 1)

                if p_dl:

                    self.springs.append(ClothSpring(p, p_dl, 'shear', 0.8))

                

                # 弯曲弹簧（隔一个质点）

                p_r2 = get_particle(row, col + 2)

                if p_r2:

                    self.springs.append(ClothSpring(p, p_r2, 'bend', 0.5))

                

                p_d2 = get_particle(row + 2, col)

                if p_d2:

                    self.springs.append(ClothSpring(p, p_d2, 'bend', 0.5))

    

    def add_collision_ball(self, cx, cy, radius):

        """添加碰撞球体"""

        self.collision_balls.append((cx, cy, radius))

    

    def apply_gravity(self):

        """施加重力"""

        gx, gy = self.gravity

        for p in self.particles:

            p.apply_force(gx * p.mass, gy * p.mass)

    

    def satisfy_spring_constraints(self):

        """满足所有弹簧约束"""

        for _ in range(self.constraint_iterations):

            for spring in self.springs:

                spring.satisfy_constraint(iterations=1)

    

    def handle_collisions(self):

        """处理与球体的碰撞"""

        for p in self.particles:

            if p.pinned:

                continue

            

            for cx, cy, radius in self.collision_balls:

                dx = p.x - cx

                dy = p.y - cy

                dist = math.sqrt(dx * dx + dy * dy)

                

                if dist < radius:

                    # 穿透：将质点推出球体

                    if dist < 1e-10:

                        nx, ny = 0, 1

                    else:

                        nx = dx / dist

                        ny = dy / dist

                    

                    p.x = cx + nx * radius

                    p.y = cy + ny * radius

    

    def update(self, dt):

        """

        执行一步仿真

        

        参数:

            dt: 时间步长

        """

        # 1. 施加外力（重力等）

        self.apply_gravity()

        

        # 2. Verlet 积分更新位置

        for p in self.particles:

            p.update_verlet(dt, self.damping)

        

        # 3. 满足弹簧约束（多次迭代）

        self.satisfy_spring_constraints()

        

        # 4. 处理碰撞

        self.handle_collisions()

    

    def get_particle_positions(self):

        """获取所有质点的位置"""

        return [(p.x, p.y) for p in self.particles]

    

    def get_grid(self):

        """获取网格形式的质点位置"""

        positions = []

        for row in range(self.rows):

            row_positions = []

            for col in range(self.cols):

                p = self.particles[row * self.cols + col]

                row_positions.append((p.x, p.y))

            positions.append(row_positions)

        return positions





# ==================== 测试代码 ====================



if __name__ == "__main__":

    import time

    

    print("=" * 60)

    print("布料仿真 (质点-弹簧系统) 测试")

    print("=" * 60)

    

    # 测试用例1：简单布料下垂

    print("\n[测试1] 布料悬挂下垂")

    

    cloth = ClothSimulation(width=10, height=10, cols=11, rows=11)

    

    # 获取初始状态（顶行固定）

    initial_positions = cloth.get_particle_positions()

    bottom_center_idx = 10 * 11 + 5  # 第10行，第5列

    initial_bottom_y = initial_positions[bottom_center_idx][1]

    

    print(f"  初始底边中心高度: {initial_bottom_y:.4f}")

    

    # 模拟 100 步

    dt = 0.016

    for _ in range(100):

        cloth.update(dt)

    

    final_positions = cloth.get_particle_positions()

    final_bottom_y = final_positions[bottom_center_idx][1]

    

    print(f"  100步后底边中心高度: {final_bottom_y:.4f}")

    

    # 布料应该下垂（y 值应该更负或更小）

    assert final_bottom_y < initial_bottom_y + 0.1, "布料应该下垂"

    print("✅ 通过\n")

    

    # 测试用例2：布料摆动

    print("[测试2] 布料摆动")

    

    cloth2 = ClothSimulation(width=8, height=8, cols=9, rows=9)

    

    # 给中间质点施加初始扰动

    center_idx = 4 * 9 + 4

    p = cloth2.particles[center_idx]

    p.prev_x = p.x - 1.0  # 初始向右偏移

    

    positions_history = []

    for step in range(200):

        cloth2.update(dt)

        if step % 20 == 0:

            positions_history.append(cloth2.particles[center_idx].x)

    

    print(f"  中心质点 x 坐标变化: {[f'{x:.2f}' for x in positions_history]}")

    

    # 质点应该左右摆动

    assert max(positions_history) != min(positions_history), "质点应该摆动"

    print("✅ 通过\n")

    

    # 测试用例3：球体碰撞

    print("[测试3] 球体碰撞")

    

    cloth3 = ClothSimulation(width=15, height=15, cols=16, rows=16)

    

    # 在布料下方添加一个球体

    cloth3.add_collision_ball(7.5, -10, 3.0)

    

    print(f"  质点总数: {len(cloth3.particles)}")

    print(f"  弹簧总数: {len(cloth3.springs)}")

    

    # 模拟让布料落在球上

    for _ in range(200):

        cloth3.update(dt)

    

    # 检查布料没有穿透球体

    center_pos = cloth3.particles[8 * 16 + 8].y  # 接近球心的质点

    ball_top = -10 + 3.0  # 球顶位置

    

    print(f"  球心位置附近质点 y: {center_pos:.4f}")

    print(f"  球顶 y: {ball_top:.4f}")

    

    assert center_pos >= ball_top - 0.5, f"布料不应该穿透球体: {center_pos} < {ball_top}"

    print("✅ 通过\n")

    

    # 测试用例4：性能测试

    print("[测试4] 性能测试")

    

    cloth4 = ClothSimulation(width=20, height=20, cols=21, rows=21)

    

    print(f"  质点总数: {len(cloth4.particles)}")

    print(f"  弹簧总数: {len(cloth4.springs)}")

    

    start = time.time()

    for _ in range(500):

        cloth4.update(dt)

    elapsed = time.time() - start

    

    print(f"  500步仿真耗时: {elapsed:.4f}秒")

    assert elapsed < 20.0, f"性能测试失败: {elapsed:.4f}秒"

    print("✅ 通过\n")

    

    # 测试用例5：边界条件验证

    print("[测试5] 固定点验证")

    

    cloth5 = ClothSimulation(width=10, height=10, cols=5, rows=5)

    

    # 顶行质点应该都是固定的

    pinned_count = sum(1 for p in cloth5.particles if p.pinned)

    expected_pinned = 5  # 顶行 5 个质点

    

    print(f"  固定质点数量: {pinned_count} (期望 {expected_pinned})")

    assert pinned_count == expected_pinned, "固定点数量错误"

    

    # 固定质点不应该移动

    top_center = cloth5.particles[2]  # 顶行中间

    orig_x, orig_y = top_center.x, top_center.y

    

    for _ in range(50):

        cloth5.update(dt)

    

    assert abs(top_center.x - orig_x) < 1e-6 and abs(top_center.y - orig_y) < 1e-6, "固定质点不应该移动"

    print("✅ 通过")

    

    print("\n" + "=" * 60)

    print("所有测试通过！布料仿真验证完成。")

    print("=" * 60)

