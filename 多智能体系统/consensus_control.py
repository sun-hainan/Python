# -*- coding: utf-8 -*-
"""
算法实现：多智能体系统 / consensus_control

本文件实现 consensus_control 相关的算法功能。
"""

import numpy as np
import matplotlib.pyplot as plt


class GraphTopology:
    """图拓扑结构：描述智能体间的通信关系"""
    
    def __init__(self, n_agents):
        # n_agents: 智能体数量
        self.n_agents = n_agents
        self.adjacency = np.zeros((n_agents, n_agents))  # 邻接矩阵
        self.degree = np.zeros(n_agents)  # 度矩阵
        self.laplacian = np.zeros((n_agents, n_agents))  # 拉普拉斯矩阵
    
    def add_edge(self, i, j, weight=1.0):
        """添加无向边连接智能体i和j"""
        self.adjacency[i, j] = weight
        self.adjacency[j, i] = weight
    
    def build_laplacian(self):
        """构建拉普拉斯矩阵 L = D - A"""
        self.degree = np.sum(self.adjacency, axis=1)
        self.laplacian = np.diag(self.degree) - self.adjacency
        return self.laplacian
    
    def get_neighbors(self, i):
        """获取智能体i的邻居集合"""
        neighbors = []
        for j in range(self.n_agents):
            if self.adjacency[i, j] > 0 and i != j:
                neighbors.append(j)
        return neighbors


class FirstOrderConsensus:
    """一阶积分器一致性协议
    
    系统模型: dx_i/dt = u_i
    目标: 所有智能体状态收敛到相同值
    
    协议: u_i = -sum_{j in N_i} (x_i - x_j)
    即: u_i = -sum_{j in N_i} a_ij(x_i - x_j)
    """
    
    def __init__(self, graph):
        # graph: 图拓扑对象
        self.graph = graph
        self.graph.build_laplacian()
        self.n_agents = graph.n_agents
        
        # 状态初始化
        self.state = np.zeros(self.n_agents)
    
    def set_initial_state(self, x0):
        """设置初始状态"""
        self.state = np.array(x0, dtype=float)
    
    def protocol(self, agent_i):
        """
        计算智能体i的控制输入
        u_i = -sum_{j in N_i} (x_i - x_j)
        """
        neighbors = self.graph.get_neighbors(agent_i)
        u_i = 0.0
        for j in neighbors:
            u_i -= (self.state[agent_i] - self.state[j])
        return u_i
    
    def step(self, dt=0.01):
        """单步状态更新（欧拉法）"""
        control_inputs = np.array([
            self.protocol(i) for i in range(self.n_agents)
        ])
        # 状态更新: dx/dt = u
        self.state += dt * control_inputs
        return self.state
    
    def run(self, duration, dt=0.01):
        """运行一致性协议直到收敛"""
        n_steps = int(duration / dt)
        trajectory = [self.state.copy()]
        
        for step in range(n_steps):
            self.step(dt)
            trajectory.append(self.state.copy())
            
            # 检测收敛
            if np.std(self.state) < 1e-6:
                print(f"  在第{step+1}步收敛")
                break
        
        return np.array(trajectory)


class SecondOrderConsensus:
    """二阶积分器一致性协议
    
    系统模型: dx_i/dt = v_i, dv_i/dt = u_i
    目标: 所有智能体位置和速度都收敛到相同值
    
    协议: u_i = -sum_{j in N_i} a_ij[(x_i-x_j) + gamma*(v_i-v_j)]
    其中gamma > 0为耦合增益参数
    """
    
    def __init__(self, graph, gamma=1.0):
        # graph: 图拓扑对象
        # gamma: 速度耦合增益
        self.graph = graph
        self.graph.build_laplacian()
        self.n_agents = graph.n_agents
        self.gamma = gamma
        
        # 位置和速度状态
        self.position = np.zeros(self.n_agents)
        self.velocity = np.zeros(self.n_agents)
    
    def set_initial_state(self, x0, v0):
        """设置初始位置和速度"""
        self.position = np.array(x0, dtype=float)
        self.velocity = np.array(v0, dtype=float)
    
    def protocol(self, agent_i):
        """
        计算智能体i的控制输入
        u_i = -sum_{j in N_i} a_ij[(x_i-x_j) + gamma*(v_i-v_j)]
        """
        neighbors = self.graph.get_neighbors(agent_i)
        u_i = 0.0
        for j in neighbors:
            # 位置差项
            pos_diff = self.position[agent_i] - self.position[j]
            # 速度差项
            vel_diff = self.velocity[agent_i] - self.velocity[j]
            u_i -= (pos_diff + self.gamma * vel_diff)
        return u_i
    
    def step(self, dt=0.01):
        """单步状态更新"""
        # 计算控制输入
        control_inputs = np.array([
            self.protocol(i) for i in range(self.n_agents)
        ])
        
        # 状态更新: dx/dt = v, dv/dt = u
        self.position += dt * self.velocity
        self.velocity += dt * control_inputs
        
        return self.position, self.velocity
    
    def run(self, duration, dt=0.01):
        """运行二阶一致性协议"""
        n_steps = int(duration / dt)
        positions = [self.position.copy()]
        velocities = [self.velocity.copy()]
        
        for step in range(n_steps):
            self.step(dt)
            positions.append(self.position.copy())
            velocities.append(self.velocity.copy())
            
            # 检测收敛：位置和速度方差都足够小
            if np.std(self.position) < 1e-6 and np.std(self.velocity) < 1e-6:
                print(f"  在第{step+1}步收敛")
                break
        
        return np.array(positions), np.array(velocities)


if __name__ == "__main__":
    # 测试一致性控制协议
    print("=" * 50)
    print("一致性控制协议测试")
    print("=" * 50)
    
    # 创建通信拓扑（环形结构，5个智能体）
    n_agents = 5
    graph = GraphTopology(n_agents)
    graph.add_edge(0, 1)
    graph.add_edge(1, 2)
    graph.add_edge(2, 3)
    graph.add_edge(3, 4)
    graph.add_edge(4, 0)  # 形成环
    
    print(f"\n通信拓扑（5个智能体环形连接）:")
    print(f"  邻接矩阵:\n{graph.adjacency}")
    print(f"  拉普拉斯矩阵:\n{graph.laplacian}")
    
    # 测试一阶一致性
    print("\n--- 一阶积分器一致性测试 ---")
    first_order = FirstOrderConsensus(graph)
    first_order.set_initial_state([1.0, 2.0, 3.0, 4.0, 5.0])
    print(f"  初始状态: {first_order.state}")
    
    trajectory = first_order.run(duration=2.0, dt=0.001)
    print(f"  最终状态: {first_order.state.round(6)}")
    print(f"  收敛值: {np.mean(first_order.state):.6f}")
    
    # 测试二阶一致性
    print("\n--- 二阶积分器一致性测试 ---")
    second_order = SecondOrderConsensus(graph, gamma=2.0)
    second_order.set_initial_state(
        x0=[1.0, 2.0, 3.0, 4.0, 5.0],  # 初始位置
        v0=[0.1, -0.1, 0.2, -0.2, 0.0]  # 初始速度
    )
    print(f"  初始位置: {second_order.position}")
    print(f"  初始速度: {second_order.velocity}")
    
    positions, velocities = second_order.run(duration=3.0, dt=0.001)
    print(f"  最终位置: {second_order.position.round(6)}")
    print(f"  最终速度: {second_order.velocity.round(6)}")
    print(f"  位置收敛值: {np.mean(second_order.position):.6f}")
    print(f"  速度收敛值: {np.mean(second_order.velocity):.6f}")
    
    print("\n✓ 一致性控制协议测试完成")
