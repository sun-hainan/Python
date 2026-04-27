# -*- coding: utf-8 -*-

"""

算法实现：强化学习 / mpc_control



本文件实现 mpc_control 相关的算法功能。

"""



import numpy as np

import random





class LinearDynamicalSystem:

    """

    线性动态系统



    状态方程：x_{k+1} = A @ x_k + B @ u_k

    输出方程：y_k = C @ x_k

    """



    def __init__(self, A, B, C=None):

        """

        初始化线性系统



        参数:

            A: 状态转移矩阵 (n_x, n_x)

            B: 输入矩阵 (n_x, n_u)

            C: 输出矩阵 (n_y, n_x)，默认为单位阵

        """

        self.A = A

        self.B = B

        self.n_x = A.shape[0]

        self.n_u = B.shape[1]

        self.C = C if C is not None else np.eye(self.n_x)



    def predict(self, x, u):

        """

        预测下一个状态



        参数:

            x: 当前状态

            u: 当前输入

        返回:

            x_next: 下一个状态

        """

        x_next = self.A @ x + self.B @ u

        return x_next



    def simulate(self, x0, u_seq):

        """

        模拟多步轨迹



        参数:

            x0: 初始状态

            u_seq: 输入序列 (N, n_u)

        返回:

            x_seq: 状态序列 (N+1, n_x)

        """

        N = u_seq.shape[0]

        x_seq = [x0]

        x = x0



        for k in range(N):

            x = self.predict(x, u_seq[k])

            x_seq.append(x)



        return np.array(x_seq)





class MPCController:

    """

    模型预测控制器



    求解如下优化问题：

    min_{u_0,...,u_{N-1}} Σ_{k=0}^{N} (x_k^T Q x_k + u_k^T R u_k)

    s.t. x_{k+1} = A x_k + B u_k

         x_min ≤ x_k ≤ x_max

         u_min ≤ u_k ≤ u_max

    """



    def __init__(self, A, B, Q, R, N=10, x_min=None, x_max=None,

                 u_min=None, u_max=None, verbose=False):

        """

        初始化 MPC 控制器



        参数:

            A: 状态转移矩阵

            B: 输入矩阵

            Q: 状态权重矩阵

            R: 输入权重矩阵

            N: 预测时域

            x_min: 状态下界

            x_max: 状态上界

            u_min: 输入下界

            u_max: 输入上界

            verbose: 是否打印调试信息

        """

        self.system = LinearDynamicalSystem(A, B)

        self.Q = Q

        self.R = R

        self.N = N

        self.x_min = x_min if x_min is not None else -np.inf * np.ones(A.shape[0])

        self.x_max = x_max if x_max is not None else np.inf * np.ones(A.shape[0])

        self.u_min = u_min if u_min is not None else -np.inf * np.ones(B.shape[1])

        self.u_max = u_max if u_max is not None else np.inf * np.ones(B.shape[1])

        self.verbose = verbose



        # 预计算矩阵（用于快速计算）

        self._precompute()



    def _precompute(self):

        """预计算矩阵（用于代价函数和梯度）"""

        n_x = self.system.n_x

        n_u = self.system.n_u



        # 构造增广代价函数中的矩阵

        # 代价 = Σ (x_k^T Q x_k + u_k^T R u_k)

        # 使用 vectorization 加速

        self._Q_block = np.kron(np.eye(self.N + 1), self.Q)

        self._R_block = np.kron(np.eye(self.N), self.R)



    def solve(self, x0, u_init=None, max_iter=100, lr=0.1):

        """

        求解 MPC 优化问题（梯度下降法）



        参数:

            x0: 当前状态

            u_init: 初始输入序列

            max_iter: 最大迭代次数

            lr: 学习率

        返回:

            u_opt: 最优控制序列

            cost: 最优代价

        """

        n_x = self.system.n_x

        n_u = self.system.n_u



        # 初始化

        if u_init is None:

            u_seq = np.zeros((self.N, n_u))

        else:

            u_seq = u_init.copy()



        # 梯度下降

        for iteration in range(max_iter):

            u_old = u_seq.copy()



            # 模拟轨迹

            x_seq = self.system.simulate(x0, u_seq)



            # 计算梯度（反向传播）

            grad = self._compute_gradient(x_seq, u_seq)



            # 线搜索步长

            u_seq = u_seq - lr * grad



            # 投影到输入约束

            u_seq = np.clip(u_seq, self.u_min, self.u_max)



            # 检查收敛

            if np.max(np.abs(u_seq - u_old)) < 1e-4:

                if self.verbose:

                    print(f"Converged at iteration {iteration}")

                break



        # 计算最终代价

        cost = self._compute_cost(x_seq, u_seq)



        if self.verbose:

            print(f"MPC solved: cost={cost:.4f}, final_u={u_seq[0]}")



        return u_seq, cost



    def _compute_gradient(self, x_seq, u_seq):

        """计算控制序列的梯度"""

        n_x = self.system.n_x

        n_u = self.system.n_u

        A, B = self.system.A, self.system.B



        grad = np.zeros((self.N, n_u))



        for k in range(self.N):

            # 代价对 u_k 的梯度

            # ∂J/∂u_k = ∂J/∂x_{k+1} * ∂x_{k+1}/∂u_k + 2R u_k

            x_k = x_seq[k]

            x_k1 = x_seq[k + 1]



            # 简化：直接用数值梯度

            epsilon = 1e-5

            u_plus = u_seq.copy()

            u_plus[k] += epsilon

            x_plus = self.system.simulate(x0=x_seq[0], u_seq=u_plus)

            cost_plus = self._compute_cost(x_plus, u_plus)



            u_minus = u_seq.copy()

            u_minus[k] -= epsilon

            x_minus = self.system.simulate(x0=x_seq[0], u_seq=u_minus)

            cost_minus = self._compute_cost(x_minus, u_minus)



            grad[k] = (cost_plus - cost_minus) / (2 * epsilon)



        return grad



    def _compute_cost(self, x_seq, u_seq):

        """计算总代价"""

        cost = 0.0

        for k in range(len(x_seq) - 1):

            cost += x_seq[k] @ self.Q @ x_seq[k]

        for k in range(len(u_seq)):

            cost += u_seq[k] @ self.R @ u_seq[k]

        return cost



    def step(self, x0, u_mpc=None):

        """

        执行一步 MPC 控制



        参数:

            x0: 当前状态

            u_mpc: 上一步的 MPC 解（用于热启动）

        返回:

            u: 第一个最优控制

        """

        u_seq, cost = self.solve(x0, u_init=u_mpc[:-1] if u_mpc is not None else None)

        return u_seq[0], u_seq





class NonlinearMPC:

    """

    非线性 MPC（使用数值优化）



    适用于非线性系统：

    x_{k+1} = f(x_k, u_k)

    min Σ l(x_k, u_k)

    """



    def __init__(self, f, l, n_x, n_u, N=10,

                 u_min=None, u_max=None, dt=0.1):

        """

        初始化非线性 MPC



        参数:

            f: 非线性动态函数 f(x, u)

            l: 阶段代价函数 l(x, u)

            n_x: 状态维度

            n_u: 控制维度

            N: 预测时域

            u_min: 控制下界

            u_max: 控制上界

            dt: 时间步长

        """

        self.f = f

        self.l = l

        self.n_x = n_x

        self.n_u = n_u

        self.N = N

        self.dt = dt

        self.u_min = u_min if u_min is not None else -np.inf * np.ones(n_u)

        self.u_max = u_max if u_max is not None else np.inf * np.ones(n_u)



    def solve(self, x0, max_iter=50, lr=0.1):

        """

        求解非线性 MPC（梯度下降）



        参数:

            x0: 初始状态

            max_iter: 最大迭代次数

            lr: 学习率

        返回:

            u_opt: 最优控制序列

        """

        u_seq = np.zeros((self.N, self.n_u))



        for iteration in range(max_iter):

            # 模拟轨迹

            x_seq, u_seq_shaped = self._simulate(x0, u_seq)



            # 计算梯度

            grad = self._gradient(x_seq, u_seq_shaped)



            # 更新

            u_seq = u_seq - lr * grad

            u_seq = np.clip(u_seq, self.u_min, self.u_max)



        return u_seq



    def _simulate(self, x0, u_seq):

        """模拟轨迹"""

        x_seq = [x0]

        x = x0



        for k in range(self.N):

            u = u_seq[k] if k < len(u_seq) else np.zeros(self.n_u)

            x = x + self.f(x, u) * self.dt

            x_seq.append(x)



        return np.array(x_seq), u_seq



    def _gradient(self, x_seq, u_seq):

        """计算梯度（数值法）"""

        grad = np.zeros_like(u_seq)

        eps = 1e-5



        for k in range(self.N):

            for j in range(self.n_u):

                u_plus = u_seq.copy()

                u_plus[k, j] += eps

                x_plus = self._simulate(x_seq[0], u_plus)[0]

                cost_plus = sum(self.l(x_plus[t], u_plus[t])

                               for t in range(min(self.N, len(x_plus) - 1)))



                grad[k, j] = cost_plus / eps



        return grad



    def step(self, x0):

        """执行一步控制"""

        u_seq = self.solve(x0)

        return u_seq[0], u_seq





if __name__ == "__main__":

    # 测试线性 MPC

    print("=== 线性 MPC 测试 ===")

    n_x = 2

    n_u = 1



    # 状态转移矩阵（A = I + dt*A_cont）

    dt = 0.1

    A = np.array([[1.0, dt], [0.0, 1.0]])

    B = np.array([[0.0], [dt]])



    # 权重矩阵

    Q = np.eye(n_x) * 1.0

    R = np.eye(n_u) * 0.1



    # 创建 MPC 控制器

    mpc = MPCController(A, B, Q, R, N=10,

                        u_min=np.array([-1.0]),

                        u_max=np.array([1.0]),

                        verbose=False)



    # 闭环仿真

    x = np.array([1.0, 0.0])  # 初始状态

    u_mpc = None



    print(f"初始状态: {x}")

    for step in range(20):

        u_first, u_mpc = mpc.step(x, u_mpc)

        x = mpc.system.predict(x, u_first)

        print(f"Step {step+1}: x={x}, u={u_first}")



    # 测试非线性 MPC

    print("\n=== 非线性 MPC 测试 ===")



    def f(x, u):

        """非线性动态：倒立摆"""

        theta = x[1]

        return np.array([x[1], np.sin(theta) - u[0]])



    def l(x, u):

        """代价函数"""

        return x[0]**2 + 0.1 * u[0]**2



    nl_mpc = NonlinearMPC(f, l, n_x=2, n_u=1, N=10, u_min=[-1], u_max=[1])



    x_nl = np.array([0.5, 0.0])

    for step in range(10):

        u, _ = nl_mpc.step(x_nl)

        x_nl = x_nl + f(x_nl, u) * 0.1

        print(f"Step {step+1}: x={x_nl}, u={u}")



    print("\nMPC 控制测试完成!")

