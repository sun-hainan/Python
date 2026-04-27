# -*- coding: utf-8 -*-

"""

算法实现：物理仿真 / fluid_simple



本文件实现 fluid_simple 相关的算法功能。

"""



import numpy as np

from collections import deque





class FluidGrid:

    """

    流体仿真网格

    

    属性:

        nx, ny: 网格尺寸

        dt: 时间步长

        viscosity: 粘性系数

        diffusion: 扩散系数

    """

    

    def __init__(self, nx, ny, dt=0.1, viscosity=0.0, diffusion=0.0):

        self.nx = nx

        self.ny = ny

        self.dt = dt

        self.viscosity = viscosity

        self.diffusion = diffusion

        

        # 速度场分量

        self.velocity_x = np.zeros((nx, ny))

        self.velocity_y = np.zeros((nx, ny))

        

        # 前一帧速度（用于计算）

        self.prev_velocity_x = np.zeros((nx, ny))

        self.prev_velocity_y = np.zeros((nx, ny))

        

        # 压力场

        self.pressure = np.zeros((nx, ny))

        self.prev_pressure = np.zeros((nx, ny))

        

        # 密度场（用于可视化示踪）

        self.density = np.zeros((nx, ny))

        self.prev_density = np.zeros((nx, ny))

        

        # 速度发散

        self.divergence = np.zeros((nx, ny))

    

    def add_velocity(self, x, y, amount_x, amount_y, radius=3):

        """

        在指定位置添加速度

        

        参数:

            x, y: 添加速度的位置

            amount_x, amount_y: 速度增量

            radius: 影响半径

        """

        x = int(np.clip(x, 0, self.nx - 1))

        y = int(np.clip(y, 0, self.ny - 1))

        r = int(radius)

        

        for i in range(max(0, x - r), min(self.nx, x + r + 1)):

            for j in range(max(0, y - r), min(self.ny, y + r + 1)):

                self.velocity_x[i, j] += amount_x

                self.velocity_y[i, j] += amount_y

    

    def add_density(self, x, y, amount, radius=3):

        """

        在指定位置添加密度（示踪剂）

        

        参数:

            x, y: 添加密度的位置

            amount: 密度增量

            radius: 影响半径

        """

        x = int(np.clip(x, 0, self.nx - 1))

        y = int(np.clip(y, 0, self.ny - 1))

        r = int(radius)

        

        for i in range(max(0, x - r), min(self.nx, x + r + 1)):

            for j in range(max(0, y - r), min(self.ny, y + r + 1)):

                self.density[i, j] += amount

    

    def advect_velocity(self):

        """

        平流步骤：沿速度场传输速度

        

        使用半拉格朗日法：追踪质点回溯到上一位置

        """

        # 保存当前速度

        self.prev_velocity_x = self.velocity_x.copy()

        self.prev_velocity_y = self.velocity_y.copy()

        

        # 网格步长

        dx = 1.0

        dy = 1.0

        

        for i in range(self.nx):

            for j in range(self.ny):

                # 当前速度

                vx = self.prev_velocity_x[i, j]

                vy = self.prev_velocity_y[i, j]

                

                # 回溯到上一位置

                prev_i = i - vx * self.dt / dx

                prev_j = j - vy * self.dt / dy

                

                # 双线性插值获取速度

                self.velocity_x[i, j] = self._bilinear_interpolate(

                    self.prev_velocity_x, prev_i, prev_j

                )

                self.velocity_y[i, j] = self._bilinear_interpolate(

                    self.prev_velocity_y, prev_i, prev_j

                )

        

        # 应用边界条件

        self._apply_velocity_boundary()

    

    def advect_density(self):

        """

        平流密度场

        """

        self.prev_density = self.density.copy()

        

        for i in range(self.nx):

            for j in range(self.ny):

                vx = self.velocity_x[i, j]

                vy = self.velocity_y[i, j]

                

                prev_i = i - vx * self.dt

                prev_j = j - vy * self.dt

                

                self.density[i, j] = self._bilinear_interpolate(

                    self.prev_density, prev_i, prev_j

                )

        

        self._apply_density_boundary()

    

    def diffuse_velocity(self):

        """

        扩散步骤：模拟粘性

        

        使用 Jacobi 迭代求解扩散方程

        """

        if self.viscosity < 1e-6:

            return

        

        # 扩散系数

        a = self.dt * self.viscosity

        

        for _ in range(20):  # 迭代次数

            # 临时存储

            temp_x = self.velocity_x.copy()

            temp_y = self.velocity_y.copy()

            

            for i in range(1, self.nx - 1):

                for j in range(1, self.ny - 1):

                    # 五点差分格式

                    laplacian_x = (

                        temp_x[i+1, j] + temp_x[i-1, j] +

                        temp_x[i, j+1] + temp_x[i, j-1] - 4 * temp_x[i, j]

                    )

                    laplacian_y = (

                        temp_y[i+1, j] + temp_y[i-1, j] +

                        temp_y[i, j+1] + temp_y[i, j-1] - 4 * temp_y[i, j]

                    )

                    

                    self.velocity_x[i, j] = (temp_x[i, j] + a * laplacian_x) / (1 + 4 * a)

                    self.velocity_y[i, j] = (temp_y[i, j] + a * laplacian_y) / (1 + 4 * a)

    

    def project_velocity(self):

        """

        投影步骤：去除速度场的散度

        

        通过求解泊松方程获得压力场，然后减去梯度

        使速度场满足不可压缩条件（div(v) = 0）

        """

        # 计算速度散度

        for i in range(1, self.nx - 1):

            for j in range(1, self.ny - 1):

                self.divergence[i, j] = (

                    (self.velocity_x[i+1, j] - self.velocity_x[i-1, j]) / 2 +

                    (self.velocity_y[i, j+1] - self.velocity_y[i, j-1]) / 2

                )

        

        # 求解压力泊松方程（Jacobi 迭代）

        self.pressure.fill(0)

        

        for _ in range(40):

            prev_pressure = self.pressure.copy()

            

            for i in range(1, self.nx - 1):

                for j in range(1, self.ny - 1):

                    self.pressure[i, j] = (

                        prev_pressure[i+1, j] + prev_pressure[i-1, j] +

                        prev_pressure[i, j+1] + prev_pressure[i, j-1] -

                        self.divergence[i, j]

                    ) / 4

        

        # 从速度场减去压力梯度

        for i in range(1, self.nx - 1):

            for j in range(1, self.ny - 1):

                self.velocity_x[i, j] -= (

                    self.pressure[i+1, j] - self.pressure[i-1, j]

                ) / 2

                self.velocity_y[i, j] -= (

                    self.pressure[i, j+1] - self.pressure[i, j-1]

                ) / 2

        

        self._apply_velocity_boundary()

    

    def step(self):

        """

        执行一步仿真

        

        完整步骤：

        1. 添加外力/源

        2. 扩散

        3. 平流速度

        4. 投影（不可压缩化）

        5. 平流密度

        """

        # 扩散速度

        self.diffuse_velocity()

        

        # 平流速度

        self.advect_velocity()

        

        # 投影去除散度

        self.project_velocity()

        

        # 平流密度

        self.advect_density()

    

    def _bilinear_interpolate(self, field, x, y):

        """

        双线性插值

        

        参数:

            field: 2D 场

            x, y: 插值位置（浮点数）

        

        返回:

            插值结果

        """

        # 边界处理

        x = np.clip(x, 0, self.nx - 1.001)

        y = np.clip(y, 0, self.ny - 1.001)

        

        i0 = int(x)

        j0 = int(y)

        i1 = i0 + 1

        j1 = j0 + 1

        

        if i1 >= self.nx:

            i1 = self.nx - 1

            i0 = i1 - 1

        if j1 >= self.ny:

            j1 = self.ny - 1

            j0 = j1 - 1

        

        sx = x - i0

        sy = y - j0

        

        # 双线性插值

        return (

            field[i0, j0] * (1 - sx) * (1 - sy) +

            field[i1, j0] * sx * (1 - sy) +

            field[i0, j1] * (1 - sx) * sy +

            field[i1, j1] * sx * sy

        )

    

    def _apply_velocity_boundary(self):

        """应用速度边界条件"""

        # 左右边界

        for j in range(self.ny):

            self.velocity_x[0, j] = 0

            self.velocity_x[-1, j] = 0

            self.velocity_y[0, j] = -self.velocity_y[1, j]

            self.velocity_y[-1, j] = -self.velocity_y[-2, j]

        

        # 上下边界

        for i in range(self.nx):

            self.velocity_x[i, 0] = -self.velocity_x[i, 1]

            self.velocity_x[i, -1] = -self.velocity_x[i, -2]

            self.velocity_y[i, 0] = 0

            self.velocity_y[i, -1] = 0

    

    def _apply_density_boundary(self):

        """应用密度边界条件"""

        for j in range(self.ny):

            self.density[0, j] = 0

            self.density[-1, j] = 0

        for i in range(self.nx):

            self.density[i, 0] = 0

            self.density[i, -1] = 0





# ==================== 测试代码 ====================



if __name__ == "__main__":

    import time

    

    print("=" * 60)

    print("简化流体仿真 (Navier-Stokes) 测试")

    print("=" * 60)

    

    # 创建网格

    grid = FluidGrid(64, 64, dt=0.1, viscosity=0.0001)

    

    # 测试用例1：添加速度并仿真

    print("\n[测试1] 基础流体仿真")

    

    # 在左侧添加速度（模拟风从左吹入）

    for j in range(20, 40):

        grid.add_velocity(2, j, 5.0, 0.0, radius=5)

        grid.add_density(2, j, 1.0, radius=3)

    

    print(f"  初始速度 (5,5): ({grid.velocity_x[5, 5]:.4f}, {grid.velocity_y[5, 5]:.4f})")

    print(f"  初始密度 (5,25): {grid.density[5, 25]:.4f}")

    

    # 执行几步仿真

    for step in range(10):

        grid.step()

    

    print(f"  10步后速度 (5,5): ({grid.velocity_x[5, 5]:.4f}, {grid.velocity_y[5, 5]:.4f})")

    print(f"  10步后密度 (30,25): {grid.density[30, 25]:.4f}")

    

    # 密度应该从左边传播开

    assert grid.density[30, 25] > 0, "密度场应该传播"

    print("✅ 通过\n")

    

    # 测试用例2：漩涡生成

    print("[测试2] 漩涡生成测试")

    

    grid2 = FluidGrid(50, 50, dt=0.1, viscosity=0.0)

    

    # 在中心添加旋转速度

    cx, cy = 25, 25

    for i in range(50):

        for j in range(50):

            dx = i - cx

            dy = j - cy

            dist = np.sqrt(dx * dx + dy * dy)

            if dist < 10 and dist > 1:

                # 切向速度（形成漩涡）

                vx = -dy / dist * 3.0

                vy = dx / dist * 3.0

                grid2.velocity_x[i, j] = vx

                grid2.velocity_y[i, j] = vy

    

    print(f"  中心速度: ({grid2.velocity_x[cx, cy]:.4f}, {grid2.velocity_y[cx, cy]:.4f})")

    

    # 仿真若干步

    for _ in range(20):

        grid2.step()

    

    # 检查速度是否有变化（漩涡应该衰减）

    total_velocity = np.sum(np.abs(grid2.velocity_x)) + np.sum(np.abs(grid2.velocity_y))

    print(f"  20步后总速度: {total_velocity:.4f}")

    assert total_velocity > 0, "速度场应该存在"

    print("✅ 通过\n")

    

    # 测试用例3：性能测试

    print("[测试3] 性能测试")

    

    grid3 = FluidGrid(100, 100, dt=0.1)

    

    # 添加一些速度和密度

    grid3.add_velocity(10, 10, 5.0, 2.0)

    grid3.add_density(10, 10, 1.0)

    

    start = time.time()

    for _ in range(100):

        grid3.step()

    elapsed = time.time() - start

    

    print(f"  100×100网格，100步仿真耗时: {elapsed:.4f}秒")

    assert elapsed < 30.0, "性能测试失败"

    print("✅ 通过\n")

    

    # 测试用例4：边界行为

    print("[测试4] 边界条件测试")

    

    grid4 = FluidGrid(30, 30, dt=0.1)

    

    # 在边界附近添加速度

    grid4.add_velocity(1, 15, 10.0, 0.0, radius=3)

    

    # 保存边界值

    left_vel_before = grid4.velocity_x[0, 15]

    

    for _ in range(5):

        grid4.step()

    

    left_vel_after = grid4.velocity_x[0, 15]

    

    print(f"  左边界速度（处理前）: {left_vel_before:.4f}")

    print(f"  左边界速度（处理后）: {left_vel_after:.4f}")

    

    # 边界速度应该接近零

    assert abs(left_vel_after) < 1.0, "边界速度应该受限"

    print("✅ 通过")

    

    print("\n" + "=" * 60)

    print("所有测试通过！简化流体仿真验证完成。")

    print("=" * 60)

