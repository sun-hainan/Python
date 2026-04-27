# -*- coding: utf-8 -*-

"""

算法实现：多智能体系统 / robust_multiagent



本文件实现 robust_multiagent 相关的算法功能。

"""



import numpy as np

import matplotlib.pyplot as plt





class GraphLaplacian:

    """图拉普拉斯矩阵与谱分析"""

    

    def __init__(self, adjacency_matrix):

        # adjacency_matrix: 邻接矩阵

        self.adjacency = np.array(adjacency_matrix)

        self.n_agents = len(adjacency_matrix)

        self.laplacian = self._compute_laplacian()

        self.eigenvalues = self._compute_spectrum()

    

    def _compute_laplacian(self):

        """计算拉普拉斯矩阵 L = D - A"""

        degree = np.sum(self.adjacency, axis=1)

        laplacian = np.diag(degree) - self.adjacency

        return laplacian

    

    def _compute_spectrum(self):

        """计算拉普拉斯矩阵的特征值"""

        eigenvalues = np.linalg.eigvals(self.laplacian)

        eigenvalues = np.sort(eigenvalues.real)

        return eigenvalues

    

    def get_algebraic_connectivity(self):

        """获取代数连通性（第二小特征值）"""

        return self.eigenvalues[1]

    

    def is_connected(self):

        """检查图是否连通"""

        return self.eigenvalues[0] < 1e-10





class RobustConsensusProtocol:

    """鲁棒一致性协议"""

    

    def __init__(self, laplacian, gamma=1.0, rho=0.5):

        # laplacian: 图拉普拉斯矩阵

        # gamma: 协议增益

        # rho: 扰动衰减系数

        self.L = laplacian

        self.gamma = gamma

        self.rho = rho

        self.n_agents = len(laplacian)

        

        # 状态

        self.state = np.zeros(self.n_agents)

        self.disturbance = np.zeros(self.n_agents)

    

    def set_initial_state(self, x0):

        """设置初始状态"""

        self.state = np.array(x0, dtype=float)

    

    def set_disturbance(self, d):

        """设置外部扰动"""

        self.disturbance = np.array(d, dtype=float)

    

    def protocol(self):

        """

        鲁棒一致性协议

        u = -γ L x - ρ d

        其中d是估计的扰动

        """

        # 主协议项

        consensus_term = -self.gamma * np.dot(self.L, self.state)

        # 扰动抑制项

        disturbance_term = -self.rho * self.disturbance

        return consensus_term + disturbance_term

    

    def step(self, dt=0.01):

        """单步状态更新"""

        control = self.protocol()

        # 状态更新

        self.state += dt * control

        return self.state.copy()





class DisturbanceObserver:

    """干扰观测器：估计系统扰动"""

    

    def __init__(self, n_agents, observer_gain=5.0):

        # n_agents: 智能体数量

        # observer_gain: 观测器增益

        self.n_agents = n_agents

        self.gamma_o = observer_gain

        

        # 估计状态

        self.estimated_disturbance = np.zeros(n_agents)

        self.estimated_state = np.zeros(n_agents)

        

        # 中间变量

        self.z = np.zeros(n_agents)

    

    def update(self, measured_state, control_input, dt=0.01):

        """

        更新扰动估计

        使用扩张状态观测器(ESO)结构

        """

        # 观测器更新

        self.z += dt * (

            -self.gamma_o * self.z 

            + self.gamma_o * (measured_state - self.estimated_state)

            + control_input

        )

        

        # 更新估计

        self.estimated_state += dt * (control_input + self.z)

        self.estimated_disturbance = self.z

        

        return self.estimated_disturbance.copy()





class HInfinityController:

    """H∞ 控制器设计（简化版）"""

    

    def __init__(self, A, B, gamma=1.0):

        # A: 系统矩阵

        # B: 输入矩阵

        # gamma: H∞ 性能指标

        self.A = A

        self.B = B

        self.gamma = gamma

        self.n_states = len(A)

        

        # Riccati方程求解（简化版）

        self.K = self._solve_riccati()

    

    def _solve_riccati(self):

        """求解代数Riccati方程（简化迭代法）"""

        n = self.n_states

        P = np.eye(n) * 0.1  # 初始P

        

        # 迭代求解

        for _ in range(50):

            # P = A^T P A - A^T P B (B^T P B + I)^{-1} B^T P A + I

            BT_P = np.dot(self.B.T, P)

            BT_P_B = np.dot(BT_P, self.B) + np.eye(n)

            inv_term = np.linalg.inv(BT_P_B)

            K_term = np.dot(np.dot(self.A.T, P), self.B)

            

            P_new = np.dot(np.dot(self.A.T, P), self.A) - \

                    np.dot(K_term, np.dot(inv_term, K_term.T)) + \

                    np.eye(n) * (1.0 / self.gamma)

            

            # 检查收敛

            if np.max(np.abs(P_new - P)) < 1e-6:

                P = P_new

                break

            P = 0.9 * P + 0.1 * P_new

        

        # 计算K

        K = np.dot(np.dot(np.linalg.inv(np.dot(self.B.T, np.dot(P, self.B)) + np.eye(n)), 

                          self.B.T), np.dot(P, self.A))

        

        return K

    

    def compute_control(self, x):

        """计算控制输入"""

        return -np.dot(self.K, x)





class RobustFormationControl:

    """鲁棒编队控制器"""

    

    def __init__(self, n_agents, formation_graph, kp=1.0, kv=1.0):

        # n_agents: 智能体数量

        # formation_graph: 编队拓扑

        # kp: 位置误差增益

        # kv: 速度误差增益

        self.n_agents = n_agents

        self.L = formation_graph.laplacian

        self.kp = kp

        self.kv = kv

        

        # 扰动观测器

        self.observers = [DisturbanceObserver(n_agents) for _ in range(n_agents)]

        

        # 状态

        self.position = np.zeros(n_agents)

        self.velocity = np.zeros(n_agents)

    

    def set_initial_state(self, x0, v0):

        """设置初始状态"""

        self.position = np.array(x0, dtype=float)

        self.velocity = np.array(v0, dtype=float)

    

    def control_law(self, leader_position, leader_velocity=None):

        """

        鲁棒编队控制律

        u_i = -kp * sum(a_ij(x_i - x_j - d_ij)) - kv * (v_i - v_j) + disturbance_estimate

        """

        # 编队误差

        formation_error = np.zeros(self.n_agents)

        

        for i in range(self.n_agents):

            for j in range(self.n_agents):

                if self.L[i, j] != 0:

                    # 计算期望距离d_ij（简化处理）

                    d_ij = 1.0

                    formation_error[i] += self.L[i, j] * (

                        (self.position[i] - self.position[j]) - d_ij

                    )

        

        # 速度误差

        velocity_error = np.zeros(self.n_agents)

        if leader_velocity is not None:

            velocity_error = self.velocity - leader_velocity

        

        # 控制输入

        u = -self.kp * formation_error - self.kv * velocity_error

        

        # 扰动补偿

        for i in range(self.n_agents):

            est_dist = self.observers[i].estimated_disturbance[i]

            u[i] -= 0.1 * est_dist

        

        return u

    

    def step(self, dt, leader_position, leader_velocity=None):

        """单步仿真"""

        # 计算控制输入

        u = self.control_law(leader_position, leader_velocity)

        

        # 更新扰动估计

        for i in range(self.n_agents):

            self.observers[i].update(self.position, u, dt)

        

        # 状态更新

        self.velocity += dt * u

        self.position += dt * self.velocity

        

        return self.position.copy(), self.velocity.copy()





class FaultTolerantController:

    """容错控制器"""

    

    def __init__(self, n_agents, nominal_gain=1.0):

        # n_agents: 智能体数量

        # nominal_gain: 标称增益

        self.n_agents = n_agents

        self.K0 = nominal_gain

        

        # 故障指示

        self.fault_indicator = np.ones(n_agents)

        self.fault_detection_threshold = 0.5

    

    def detect_fault(self, actual_output, expected_output):

        """检测故障"""

        error = np.abs(actual_output - expected_output)

        

        for i in range(self.n_agents):

            if error[i] > self.fault_detection_threshold:

                # 故障检测

                if self.fault_indicator[i] > 0.5:

                    self.fault_indicator[i] = 0.5

                    print(f"  故障检测: Agent {i}")

    

    def adjust_gain(self, agent_id):

        """调整增益以补偿故障"""

        return self.K0 * self.fault_indicator[agent_id]

    

    def reconfigure_control(self, agent_id, nominal_control):

        """重新配置控制（故障后）"""

        adjusted_gain = self.adjust_gain(agent_id)

        return nominal_control * adjusted_gain





if __name__ == "__main__":

    # 测试鲁棒多智能体控制

    print("=" * 50)

    print("鲁棒多智能体控制测试")

    print("=" * 50)

    

    # 创建通信拓扑（环形，5个智能体）

    n = 5

    adj = np.zeros((n, n))

    for i in range(n):

        adj[i, (i+1) % n] = 1

        adj[i, (i-1) % n] = 1

    

    laplacian = GraphLaplacian(adj)

    

    print(f"\n通信拓扑: {n}个智能体环形连接")

    print(f"  代数连通性: {laplacian.get_algebraic_connectivity():.4f}")

    print(f"  连通性: {'是' if laplacian.is_connected() else '否'}")

    

    # 鲁棒一致性协议测试

    print("\n--- 鲁棒一致性协议测试 ---")

    protocol = RobustConsensusProtocol(laplacian.laplacian, gamma=2.0, rho=0.5)

    protocol.set_initial_state([1.0, 2.0, 3.0, 4.0, 5.0])

    

    print(f"  初始状态: {protocol.state}")

    

    # 添加扰动

    disturbance = [0.1, 0.2, -0.1, 0.15, -0.05]

    protocol.set_disturbance(disturbance)

    

    # 运行仿真

    for step in range(100):

        protocol.step(dt=0.01)

    

    print(f"  最终状态: {protocol.state.round(4)}")

    print(f"  收敛均值: {np.mean(protocol.state):.4f}")

    

    # H∞ 控制器测试

    print("\n--- H∞ 控制器测试 ---")

    A = np.array([[0, 1], [-2, -1]])  # 稳定系统矩阵

    B = np.array([[0], [1]])

    

    h_inf = HInfinityController(A, B, gamma=1.5)

    print(f"  控制器增益矩阵K:\n{h_inf.K}")

    

    # 测试状态

    x_test = np.array([1.0, 0.5])

    u_test = h_inf.compute_control(x_test)

    print(f"  测试状态x={x_test}, 控制u={u_test[0]:.4f}")

    

    # 容错控制器测试

    print("\n--- 容错控制器测试 ---")

    ftc = FaultTolerantController(n_agents=3, nominal_gain=2.0)

    print(f"  初始故障指示: {ftc.fault_indicator}")

    

    # 模拟故障检测

    actual = np.array([1.0, 2.5, 3.0])

    expected = np.array([1.0, 2.0, 3.0])

    ftc.detect_fault(actual, expected)

    print(f"  检测后故障指示: {ftc.fault_indicator}")

    

    print("\n✓ 鲁棒多智能体控制测试完成")

