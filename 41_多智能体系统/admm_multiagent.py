# -*- coding: utf-8 -*-

"""

算法实现：多智能体系统 / admm_multiagent



本文件实现 admm_multiagent 相关的算法功能。

"""



import numpy as np





class ADMMOptimizer:

    """ADMM优化器基础类"""

    

    def __init__(self, rho=1.0, max_iterations=100, tolerance=1e-6):

        # rho: 惩罚参数

        # max_iterations: 最大迭代次数

        # tolerance: 收敛容差

        self.rho = rho

        self.max_iterations = max_iterations

        self.tolerance = tolerance

        self.history = []

    

    def check_convergence(self, r_norm, s_norm, eps_pri, eps_dual):

        """检查收敛条件"""

        return r_norm <= eps_pri and s_norm <= eps_dual

    

    def compute_dual_residual(self, x_new, x_old, u, z):

        """计算对偶残差"""

        return np.linalg.norm(self.rho * (z - x_new) - (x_new - x_old))

    

    def compute_primal_residual(self, x, z):

        """计算原始残差"""

        return np.linalg.norm(x - z)





class DistributedConsensusADMM(ADMMOptimizer):

    """分布式一致性ADMM

    

    目标: min sum_i f_i(x_i)  s.t. x_i = z (一致性约束)

    其中f_i是智能体i的本地成本函数

    """

    

    def __init__(self, n_agents, dimension, rho=1.0):

        # n_agents: 智能体数量

        # dimension: 优化变量维度

        # rho: 惩罚参数

        super().__init__(rho=rho)

        self.n_agents = n_agents

        self.dim = dimension

        

        # 初始化变量

        self.x = [np.zeros(dimension) for _ in range(n_agents)]  # 本地变量

        self.z = np.zeros(dimension)  # 全局一致变量

        self.u = [np.zeros(dimension) for _ in range(n_agents)]  # 拉格朗日乘子

        self.w = [np.zeros(dimension) for _ in range(n_agents)]  # 缩放乘子

    

    def set_local_cost_gradient(self, agent_id, x):

        """计算本地成本函数梯度（需子类实现）"""

        return np.zeros(self.dim)

    

    def set_local_cost(self, agent_id, x):

        """计算本地成本函数值（需子类实现）"""

        return 0.0

    

    def x_update(self, agent_id, neighbor_z, neighbor_u):

        """

        x_i 更新: x_i = argmin(f_i(x_i) + (rho/2)||x_i - z + u_i||^2)

        """

        # 简化的梯度下降更新

        grad = self.set_local_cost_gradient(agent_id, self.x[agent_id])

        rhs = neighbor_z - self.u[agent_id]

        

        # 闭式解（对于二次函数）

        self.x[agent_id] = (self.rho * rhs - grad) / self.rho

    

    def z_update(self):

        """

        z 更新: z = (1/n) * sum(x_i + u_i)

        """

        sum_x_u = sum(self.x[i] + self.u[i] for i in range(self.n_agents))

        self.z = sum_x_u / self.n_agents

    

    def u_update(self, agent_id):

        """

        u_i 更新: u_i = u_i + x_i - z

        """

        self.u[agent_id] += self.x[agent_id] - self.z

    

    def step(self):

        """单步ADMM迭代"""

        # 备份旧值

        x_old = [x.copy() for x in self.x]

        

        # x更新

        for i in range(self.n_agents):

            self.x_update(i, self.z, self.u[i])

        

        # z更新

        self.z_update()

        

        # u更新

        for i in range(self.n_agents):

            self.u_update(i)

        

        # 计算残差

        r_norm = self.compute_primal_residual(

            np.mean(self.x, axis=0), self.z)

        s_norm = self.compute_dual_residual(

            np.mean(self.x, axis=0), np.mean(x_old, axis=0), self.u, self.z)

        

        return r_norm, s_norm

    

    def solve(self, verbose=True):

        """运行ADMM求解"""

        if verbose:

            print("\n===== 分布式一致性ADMM求解 =====")

        

        for iteration in range(self.max_iterations):

            r_norm, s_norm = self.step()

            

            if verbose and iteration % 10 == 0:

                print(f"  迭代 {iteration}: 原始残差={r_norm:.6f}, "

                      f"对偶残差={s_norm:.6f}, z={self.z.round(3)}")

            

            # 检查收敛

            if r_norm < self.tolerance and s_norm < self.tolerance:

                if verbose:

                    print(f"  在第 {iteration} 轮收敛")

                break

        

        return self.z





class QuadraticConsensusADMM(DistributedConsensusADMM):

    """二次成本函数的分布式一致性ADMM"""

    

    def __init__(self, n_agents, dimension, A_i_list, b_i_list, rho=1.0):

        # A_i_list: 各智能体的二次成本系数矩阵列表

        # b_i_list: 各智能体的线性项系数向量列表

        super().__init__(n_agents, dimension, rho)

        self.A = A_i_list

        self.b = b_i_list

    

    def set_local_cost_gradient(self, agent_id, x):

        """二次函数梯度: ∇f_i(x) = A_i x - b_i"""

        return np.dot(self.A[agent_id], x) - self.b[agent_id]

    

    def x_update(self, agent_id, neighbor_z, neighbor_u):

        """x_i 闭式解: x_i = (A_i + rho*I)^{-1}(b_i + rho(z - u_i))"""

        # A_i + rho*I

        A_aug = self.A[agent_id] + self.rho * np.eye(self.dim)

        # b_i + rho(z - u_i)

        rhs = self.b[agent_id] + self.rho * (neighbor_z - neighbor_u)

        self.x[agent_id] = np.linalg.solve(A_aug, rhs)





class ResourceAllocationADMM(ADMMOptimizer):

    """多智能体资源分配的ADMM

    

    目标: min sum_i f_i(x_i)  s.t. sum(x_i) = d, x_i >= 0

    """

    

    def __init__(self, n_agents, rho=1.0):

        super().__init__(rho=rho)

        self.n_agents = n_agents

        

        # 变量

        self.x = [np.array([0.0]) for _ in range(n_agents)]  # 资源分配

        self.lambda_ = 0.0  # 拉格朗日乘子（单一约束）

        self.v = np.array([0.0])  # 辅助变量

        

        # 约束值

        self.total_demand = 10.0

    

    def cost_function(self, agent_id, x):

        """成本函数（凸函数）"""

        # 简化的二次成本: f_i(x) = c_i * x^2

        c_i = 0.5 + 0.1 * agent_id

        return c_i * (x ** 2)

    

    def x_update(self, agent_id):

        """x_i 更新（闭式解）"""

        c_i = 0.5 + 0.1 * agent_id

        # x_i = (d/2 - lambda/2 - v) / (c_i + rho)

        rhs = self.total_demand / 2 - self.lambda_ / 2 - self.v[0]

        self.x[agent_id] = np.array([max(0, rhs / (c_i + self.rho))])

    

    def v_update(self):

        """v 更新"""

        sum_x = sum(self.x[i] for i in range(self.n_agents))

        self.v += self.rho * (sum_x - self.total_demand)

    

    def lambda_update(self):

        """lambda 更新"""

        sum_x = sum(self.x[i] for i in range(self.n_agents))

        self.lambda_ += self.rho * (sum_x - self.total_demand)

    

    def step(self):

        """单步迭代"""

        for i in range(self.n_agents):

            self.x_update(i)

        

        self.v_update()

        self.lambda_update()

        

        # 计算残差

        sum_x = sum(self.x[i] for i in range(self.n_agents))

        r_norm = abs(sum_x - self.total_demand)

        

        return r_norm, 0.0

    

    def solve(self, verbose=True):

        """求解"""

        if verbose:

            print("\n===== 资源分配ADMM求解 =====")

            print(f"  约束: sum(x_i) = {self.total_demand}")

        

        for iteration in range(self.max_iterations):

            r_norm, _ = self.step()

            

            if verbose and iteration % 20 == 0:

                sum_x = sum(self.x[i][0] for i in range(self.n_agents))

                print(f"  迭代 {iteration}: sum(x)={sum_x:.4f}, "

                      f"残差={r_norm:.6f}, lambda={self.lambda_:.4f}")

            

            if r_norm < self.tolerance:

                print(f"  在第 {iteration} 轮收敛")

                break

        

        return [x[0] for x in self.x]





class GraphADMMDistributed(ADMMOptimizer):

    """图结构上的ADMM（邻居通信）

    

    目标: min sum_i f_i(x_i)  s.t. A_ij x_i = A_ji x_j (边约束)

    """

    

    def __init__(self, adjacency_list, dimension, rho=1.0):

        # adjacency_list: 邻接表 {i: [j1, j2, ...]}

        # dimension: 变量维度

        super().__init__(rho=rho)

        self.adjacency = adjacency_list

        self.n_agents = len(adjacency_list)

        self.dim = dimension

        

        # 边列表

        self.edges = []

        for i, neighbors in adjacency_list.items():

            for j in neighbors:

                if i < j:  # 只添加一次

                    self.edges.append((i, j))

        

        # 变量

        self.x = {i: np.zeros(dimension) for i in adjacency_list}

        self.z = {(i, j): np.zeros(dimension) for i, j in self.edges}  # 边变量

        self.lambda_ = {(i, j): np.zeros(dimension) for i, j in self.edges}

    

    def step(self):

        """图ADMM单步迭代"""

        # x_i 更新

        for i in self.adjacency:

            neighbors = self.adjacency[i]

            # 聚合邻居信息

            neighbor_contrib = np.zeros(self.dim)

            for j in neighbors:

                if (i, j) in self.z:

                    lambda_ij = self.lambda_[(i, j)]

                    z_ij = self.z[(i, j)]

                    neighbor_contrib += (z_ij - lambda_ij)

            

            # 简化的梯度更新

            self.x[i] = neighbor_contrib / max(1, len(neighbors))

        

        # z 更新

        for (i, j) in self.edges:

            z_new = (self.x[i] + self.x[j] + self.lambda_[(i, j)]) / 2

            self.z[(i, j)] = z_new

        

        # lambda 更新

        for (i, j) in self.edges:

            self.lambda_[(i, j)] += self.x[i] - self.z[(i, j)]

    

    def solve(self, verbose=True):

        """求解"""

        if verbose:

            print(f"\n===== 图结构ADMM求解（{self.n_agents}个智能体） =====")

        

        for iteration in range(self.max_iterations):

            self.step()

            

            if verbose and iteration % 20 == 0:

                # 计算一致误差

                total_error = 0.0

                for (i, j) in self.edges:

                    total_error += np.linalg.norm(self.x[i] - self.x[j])

                print(f"  迭代 {iteration}: 一致误差={total_error:.6f}")

        

        return self.x





if __name__ == "__main__":

    # 测试ADMM分布式优化

    print("=" * 50)

    print("ADMM分布式优化测试")

    print("=" * 50)

    

    # 测试1: 二次一致性ADMM

    print("\n--- 二次一致性ADMM测试 ---")

    n_agents = 4

    dim = 3

    

    # 生成随机二次成本函数系数

    np.random.seed(42)

    A_list = [np.eye(dim) * (i + 1) for i in range(n_agents)]

    b_list = [np.random.randn(dim) for _ in range(n_agents)]

    

    admm_quad = QuadraticConsensusADMM(n_agents, dim, A_list, b_list, rho=1.0)

    result = admm_quad.solve(verbose=True)

    

    print(f"  全局一致变量z: {result.round(4)}")

    print(f"  各智能体本地变量:")

    for i in range(n_agents):

        print(f"    Agent {i}: x={admm_quad.x[i].round(4)}")

    

    # 测试2: 资源分配ADMM

    print("\n--- 资源分配ADMM测试 ---")

    n_agents = 5

    admm_resource = ResourceAllocationADMM(n_agents, rho=2.0)

    allocations = admm_resource.solve(verbose=True)

    

    print(f"  最终分配: {[f'{a:.3f}' for a in allocations]}")

    print(f"  总和: {sum(allocations):.4f} (目标: {admm_resource.total_demand})")

    

    # 计算总成本

    total_cost = sum(

        admm_resource.cost_function(i, allocations[i])

        for i in range(n_agents)

    )

    print(f"  总成本: {total_cost:.4f}")

    

    # 测试3: 图结构ADMM

    print("\n--- 图结构ADMM测试 ---")

    adjacency = {

        0: [1, 3],

        1: [0, 2],

        2: [1, 3],

        3: [0, 2]

    }

    

    graph_admm = GraphADMMDistributed(adjacency, dimension=2, rho=1.0)

    graph_admm.solve(verbose=True)

    

    print("  最终状态:")

    for i in adjacency:

        print(f"    Agent {i}: x={graph_admm.x[i].round(4)}")

    

    print("\n✓ ADMM分布式优化测试完成")

