# -*- coding: utf-8 -*-

"""

算法实现：物理仿真 / heat_equation



本文件实现 heat_equation 相关的算法功能。

"""



import numpy as np





class HeatEquation:

    """1D热传导方程求解器"""



    def __init__(self, n: int, alpha: float = 0.1, length: float = 1.0):

        """

        参数：

            n: 空间点数

            alpha: 热扩散系数

            length: 棒的长度

        """

        self.n = n

        self.alpha = alpha

        self.length = length

        self.dx = length / (n - 1)  # 空间步长

        self.T = np.zeros(n)           # 温度分布

        self.dx2 = self.dx * self.dx



    def set_initial_condition(self, func):

        """设置初始温度分布 T(x, 0) = func(x)"""

        for i in range(self.n):

            x = i * self.dx

            self.T[i] = func(x)



    def step(self, dt: float) -> float:

        """

        前进一个时间步（显式FTCS格式）



        T[i]_new = T[i] + α*dt/dx² * (T[i+1] - 2*T[i] + T[i-1])



        稳定性条件：α*dt/dx² ≤ 0.5

        """

        # 稳定性检查

        r = self.alpha * dt / self.dx2

        if r > 0.5:

            print(f"警告：r={r:.2f} > 0.5，可能不稳定！")



        T_new = self.T.copy()

        for i in range(1, self.n - 1):

            T_new[i] = self.T[i] + r * (self.T[i+1] - 2 * self.T[i] + self.T[i-1])



        self.T = T_new

        return dt



    def run(self, dt: float, n_steps: int):

        """运行多步"""

        for _ in range(n_steps):

            self.step(dt)





def gauss_seidel(A, b, x=None, tol=1e-10, max_iter=100):

    """求解线性方程组 Ax = b（Gauss-Seidel迭代）"""

    n = len(b)

    if x is None:

        x = np.zeros(n)

    for iteration in range(max_iter):

        x_old = x.copy()

        for i in range(n):

            sigma = sum(A[i][j] * x[j] for j in range(n) if j != i)

            x[i] = (b[i] - sigma) / A[i][i]

        if np.max(np.abs(x - x_old)) < tol:

            return x, iteration

    return x, max_iter





def create_2d_heat_solver(nx: int, ny: int, alpha: float = 0.1):

    """

    创建2D热传导方程求解器（隐式格式）



    ∂T/∂t = α*(∂²T/∂x² + ∂²T/∂y²)



    使用隐式格式，稳定性更好但需要解线性方程

    """

    # 空间网格

    dx = 1.0 / (nx - 1)

    dy = 1.0 / (ny - 1)



    # 系数矩阵（5点 stencil）

    N = nx * ny

    A = np.zeros((N, N))



    # 构建矩阵（这里简化处理，实际更复杂）

    for i in range(ny):

        for j in range(nx):

            idx = i * nx + j

            A[idx, idx] = 1.0 + 4 * alpha

            if i > 0: A[idx, idx - nx] = -alpha

            if i < ny - 1: A[idx, idx + nx] = -alpha

            if j > 0: A[idx, idx - 1] = -alpha

            if j < nx - 1: A[idx, idx + 1] = -alpha



    return A, dx, dy





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 热传导方程测试 ===\n")



    # 创建求解器

    solver = HeatEquation(n=50, alpha=0.1, length=1.0)



    # 初始条件：T(x,0) = sin(πx)

    def initial(x):

        return np.sin(np.pi * x)



    solver.set_initial_condition(initial)



    print("初始温度分布：两端为0，中间最高")



    # 运行仿真

    dt = 0.001  # 时间步长

    n_steps = 500



    print(f"\n运行 {n_steps} 步 (dt={dt})...")

    solver.run(dt, n_steps)



    print("最终温度分布（采样点）：")

    for i in range(0, solver.n, 10):

        x = i * solver.dx

        print(f"  x={x:.2f}: T={solver.T[i]:.4f}")



    # 稳定性分析

    r = solver.alpha * dt / (solver.dx ** 2)

    print(f"\n稳定性参数 r = α*dt/dx² = {r:.4f}")

    print(f"稳定性条件 r ≤ 0.5: {'✅ 通过' if r <= 0.5 else '❌ 警告'}")



    print("\n热传导模拟完成")

