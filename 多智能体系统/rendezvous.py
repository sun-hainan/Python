# -*- coding: utf-8 -*-
"""
算法实现：多智能体系统 / rendezvous

本文件实现 rendezvous 相关的算法功能。
"""

import numpy as np
import matplotlib.pyplot as plt


class Agent2D:
    """二维平面上的智能体"""
    
    def __init__(self, agent_id, initial_position, initial_velocity=None):
        # agent_id: 智能体ID
        # initial_position: 初始位置 [x, y]
        # initial_velocity: 初始速度
        self.agent_id = agent_id
        self.position = np.array(initial_position, dtype=float)
        self.velocity = np.array(initial_velocity, dtype=float) if initial_velocity else np.zeros(2)
    
    def update_position(self, new_position):
        """更新位置"""
        self.position = np.array(new_position, dtype=float)
    
    def apply_control(self, u, dt=0.1):
        """应用控制输入（速度直接控制）"""
        self.velocity = np.array(u, dtype=float)
        self.position += self.velocity * dt
    
    def get_distance_to(self, other):
        """计算到另一个智能体的距离"""
        return np.linalg.norm(self.position - other.position)


class RendezvousProtocol:
    """汇合协议基类"""
    
    def __init__(self, agents):
        # agents: 智能体列表
        self.agents = agents
        self.n_agents = len(agents)
    
    def compute_control(self, agent_id):
        """计算控制输入（子类实现）"""
        raise NotImplementedError
    
    def step(self, dt=0.1):
        """单步更新"""
        controls = []
        for i in range(self.n_agents):
            u = self.compute_control(i)
            controls.append(u)
            self.agents[i].apply_control(u, dt)
        
        return controls
    
    def check_convergence(self, threshold=1e-6):
        """检查是否汇合"""
        # 计算所有智能体的中心
        center = np.mean([a.position for a in self.agents], axis=0)
        
        # 计算到中心距离的最大值
        max_distance = max(np.linalg.norm(a.position - center) for a in self.agents)
        
        return max_distance < threshold
    
    def run(self, max_steps=1000, dt=0.01, verbose=True):
        """运行汇合协议"""
        trajectories = [np.array([a.position.copy()]) for a in self.agents]
        
        for step in range(max_steps):
            controls = self.step(dt)
            
            # 记录轨迹
            for i, agent in enumerate(self.agents):
                trajectories[i] = np.vstack([trajectories[i], agent.position])
            
            # 检查收敛
            if self.check_convergence():
                if verbose:
                    print(f"  在第 {step} 步汇合")
                break
            
            if verbose and step % 100 == 0:
                center = np.mean([a.position for a in self.agents], axis=0)
                distances = [np.linalg.norm(a.position - center) for a in self.agents]
                print(f"  Step {step}: 最大距离={max(distances):.6f}")
        
        return trajectories


class ContinuousRendezvous(RendezvousProtocol):
    """连续时间汇合协议
    
    基于位置的分布式控制律
    u_i = sum_{j in N_i} (x_j - x_i)
    """
    
    def __init__(self, agents, adjacency_matrix):
        # adjacency_matrix: 邻接矩阵
        super().__init__(agents)
        self.adjacency = np.array(adjacency_matrix)
    
    def compute_control(self, agent_id):
        """计算控制输入"""
        u = np.zeros(2)
        
        for j in range(self.n_agents):
            if self.adjacency[agent_id, j] > 0:
                u += self.agents[j].position - self.agents[agent_id].position
        
        return u


class DiscreteRendezvous(RendezvousProtocol):
    """离散时间汇合协议
    
    x_i(k+1) = (1/|N_i|) * sum_{j in N_i} x_j(k)
    """
    
    def __init__(self, agents, adjacency_matrix, dt=0.1):
        super().__init__(agents)
        self.adjacency = np.array(adjacency_matrix)
        self.dt = dt
    
    def compute_control(self, agent_id):
        """计算控制（位置差分）"""
        neighbors = np.where(self.adjacency[agent_id] > 0)[0]
        
        if len(neighbors) == 0:
            return np.zeros(2)
        
        # 计算邻居平均位置
        neighbor_mean = np.mean([self.agents[j].position for j in neighbors], axis=0)
        
        # 控制输入 = (目标位置 - 当前位置) / dt
        u = (neighbor_mean - self.agents[agent_id].position) / self.dt
        
        return u


class RendezvousWithObstacles(RendezvousProtocol):
    """有障碍物的汇合协议"""
    
    def __init__(self, agents, obstacles):
        # obstacles: 障碍物列表 [(x1, y1, x2, y2), ...] 表示线段
        super().__init__(agents)
        self.obstacles = obstacles
    
    def check_collision(self, pos, direction):
        """检查是否与障碍物碰撞"""
        for obs in self.obstacles:
            # 简化：障碍物用圆形近似
            obs_center = np.array([(obs[0] + obs[2]) / 2, (obs[1] + obs[3]) / 2])
            obs_radius = np.linalg.norm(
                np.array([obs[2], obs[3]]) - np.array([obs[0], obs[1]])
            ) / 2
            
            if np.linalg.norm(pos - obs_center) < obs_radius + 0.1:
                return True
        return False
    
    def compute_control(self, agent_id):
        """计算控制（带避障）"""
        agent = self.agents[agent_id]
        u = np.zeros(2)
        count = 0
        
        for j in range(self.n_agents):
            if j != agent_id and self.adjacency[agent_id, j] > 0:
                target = self.agents[j].position
                direction = target - agent.position
                dist = np.linalg.norm(direction)
                
                if dist > 1e-6:
                    normalized_dir = direction / dist
                    
                    # 简单避障：如果方向上有障碍物，绕行
                    check_pos = agent.position + normalized_dir * 0.5
                    if not self.check_collision(check_pos, normalized_dir):
                        u += normalized_dir
                        count += 1
        
        if count > 0:
            u /= count
        
        return u
    
    def set_communication_topology(self, adjacency):
        """设置通信拓扑"""
        self.adjacency = np.array(adjacency)


class EventTriggeredRendezvous(RendezvousProtocol):
    """事件触发汇合协议
    
    智能体只在状态变化超过阈值时才进行通信和控制更新
    减少通信和计算负担
    """
    
    def __init__(self, agents, adjacency_matrix, trigger_threshold=0.1):
        # trigger_threshold: 触发阈值
        super().__init__(agents)
        self.adjacency = np.array(adjacency_matrix)
        self.trigger_threshold = trigger_threshold
        
        # 各智能体的触发状态
        self.last_states = [a.position.copy() for a in agents]
        self.trigger_times = [0.0] * len(agents)
    
    def should_trigger(self, agent_id):
        """检查是否应该触发"""
        current = self.agents[agent_id].position
        last = self.last_states[agent_id]
        
        change = np.linalg.norm(current - last)
        return change > self.trigger_threshold
    
    def compute_control(self, agent_id):
        """事件触发的控制"""
        if self.should_trigger(agent_id):
            self.last_states[agent_id] = self.agents[agent_id].position.copy()
        
        # 基于上次触发状态计算控制
        u = np.zeros(2)
        neighbors = np.where(self.adjacency[agent_id] > 0)[0]
        
        for j in neighbors:
            u += self.agents[j].position - self.agents[agent_id].position
        
        return u


class HeadingRendezvous(RendezvousProtocol):
    """基于航向的汇合协议
    
    智能体根据本地观测调整航向，而不是直接控制速度
    更符合实际机器人运动模型
    """
    
    def __init__(self, agents, adjacency_matrix, max_speed=1.0, turn_rate=1.0):
        super().__init__(agents)
        self.adjacency = np.array(adjacency_matrix)
        self.max_speed = max_speed
        self.turn_rate = turn_rate
    
    def compute_heading_control(self, agent_id):
        """计算航向控制"""
        agent = self.agents[agent_id]
        
        # 计算期望航向（指向邻居中心）
        neighbors = np.where(self.adjacency[agent_id] > 0)[0]
        
        if len(neighbors) == 0:
            return agent.velocity
        
        # 邻居平均位置
        neighbor_mean = np.mean([self.agents[j].position for j in neighbors], axis=0)
        direction = neighbor_mean - agent.position
        
        if np.linalg.norm(direction) < 1e-6:
            return agent.velocity
        
        # 期望航向角度
        desired_heading = np.arctan2(direction[1], direction[0])
        current_heading = np.arctan2(agent.velocity[1], agent.velocity[0]) if \
                         np.linalg.norm(agent.velocity) > 1e-6 else 0
        
        # 角度差
        heading_diff = desired_heading - current_heading
        
        # 归一化到[-pi, pi]
        while heading_diff > np.pi:
            heading_diff -= 2 * np.pi
        while heading_diff < -np.pi:
            heading_diff += 2 * np.pi
        
        # 限制转向率
        heading_diff = np.clip(heading_diff, -self.turn_rate * 0.1, self.turn_rate * 0.1)
        
        # 新航向
        new_heading = current_heading + heading_diff
        
        # 速度方向改变
        speed = np.linalg.norm(agent.velocity)
        speed = max(0.1, speed)  # 确保最小速度
        
        new_velocity = np.array([np.cos(new_heading), np.sin(new_heading)]) * speed
        
        return new_velocity
    
    def compute_control(self, agent_id):
        """计算控制输入"""
        return self.compute_heading_control(agent_id)


class SwitchingTopologyRendezvous(RendezvousProtocol):
    """切换拓扑下的汇合协议"""
    
    def __init__(self, agents, topology_sequence):
        # topology_sequence: 拓扑序列
        super().__init__(agents)
        self.topology_sequence = topology_sequence
        self.current_topology_idx = 0
        self.current_adjacency = topology_sequence[0]
        self.switching_period = 10  # 每10步切换一次
    
    def step(self, dt=0.1):
        """带拓扑切换的步进"""
        # 检查是否需要切换拓扑
        step_count = len(self.trajectories[0]) if hasattr(self, 'trajectories') else 0
        
        if step_count > 0 and step_count % self.switching_period == 0:
            self.current_topology_idx = (self.current_topology_idx + 1) % len(self.topology_sequence)
            self.current_adjacency = self.topology_sequence[self.current_topology_idx]
        
        return super().step(dt)
    
    def compute_control(self, agent_id):
        """基于当前拓扑计算控制"""
        u = np.zeros(2)
        
        for j in range(self.n_agents):
            if self.current_adjacency[agent_id, j] > 0:
                u += self.agents[j].position - self.agents[agent_id].position
        
        return u


if __name__ == "__main__":
    # 测试多智能体汇合问题
    print("=" * 50)
    print("多智能体汇合(Rendezvous)问题测试")
    print("=" * 50)
    
    # 创建智能体
    n_agents = 5
    agents = []
    
    print(f"\n创建 {n_agents} 个智能体")
    
    for i in range(n_agents):
        angle = 2 * np.pi * i / n_agents
        radius = 5.0
        pos = np.array([radius * np.cos(angle), radius * np.sin(angle)])
        agent = Agent2D(i, pos)
        agents.append(agent)
        print(f"  Agent {i}: 位置={pos.round(2)}")
    
    # 创建通信拓扑（全连通）
    adjacency = np.ones((n_agents, n_agents)) - np.eye(n_agents)
    
    # 测试1: 连续时间汇合
    print("\n--- 连续时间汇合协议测试 ---")
    agents1 = [Agent2D(i, agents[i].position.copy()) for i in range(n_agents)]
    protocol1 = ContinuousRendezvous(agents1, adjacency)
    
    trajectories1 = protocol1.run(max_steps=500, dt=0.01, verbose=True)
    
    final_positions1 = [a.position for a in agents1]
    center1 = np.mean(final_positions1, axis=0)
    max_dist1 = max(np.linalg.norm(p - center1) for p in final_positions1)
    print(f"  最终汇合中心: {center1.round(4)}")
    print(f"  最大偏离: {max_dist1:.6f}")
    
    # 测试2: 离散时间汇合
    print("\n--- 离散时间汇合协议测试 ---")
    agents2 = [Agent2D(i, agents[i].position.copy()) for i in range(n_agents)]
    protocol2 = DiscreteRendezvous(agents2, adjacency, dt=0.1)
    
    trajectories2 = protocol2.run(max_steps=200, dt=0.1, verbose=True)
    
    final_positions2 = [a.position for a in agents2]
    center2 = np.mean(final_positions2, axis=0)
    max_dist2 = max(np.linalg.norm(p - center2) for p in final_positions2)
    print(f"  最终汇合中心: {center2.round(4)}")
    print(f"  最大偏离: {max_dist2:.6f}")
    
    # 测试3: 切换拓扑汇合
    print("\n--- 切换拓扑汇合协议测试 ---")
    agents3 = [Agent2D(i, agents[i].position.copy()) for i in range(n_agents)]
    
    # 环形拓扑和全连通拓扑交替
    ring_adj = np.zeros((n_agents, n_agents))
    for i in range(n_agents):
        ring_adj[i, (i+1) % n_agents] = 1
        ring_adj[i, (i-1) % n_agents] = 1
    
    topologies = [adjacency, ring_adj]
    
    # 简化的切换拓扑协议
    class SimpleSwitchingRendezvous(RendezvousProtocol):
        def __init__(self, agents, topologies, switch_period=20):
            super().__init__(agents)
            self.topologies = topologies
            self.switch_period = switch_period
            self.current_idx = 0
            self.adjacency = topologies[0]
        
        def step(self, dt=0.1):
            step_count = len(self.trajectories[0]) if hasattr(self, 'trajectories') else 0
            if step_count > 0 and step_count % self.switch_period == 0:
                self.current_idx = (self.current_idx + 1) % len(self.topologies)
                self.adjacency = self.topologies[self.current_idx]
            return super().step(dt)
        
        def compute_control(self, agent_id):
            u = np.zeros(2)
            for j in range(self.n_agents):
                if self.adjacency[agent_id, j] > 0:
                    u += self.agents[j].position - self.agents[agent_id].position
            return u
    
    # 需要初始化trajectories
    class TestSwitchingRendezvous(SimpleSwitchingRendezvous):
        def run(self, max_steps=1000, dt=0.01, verbose=True):
            self.trajectories = [np.array([a.position.copy()]) for a in self.agents]
            return super().run(max_steps, dt, verbose)
    
    protocol3 = TestSwitchingRendezvous(agents3, topologies, switch_period=20)
    trajectories3 = protocol3.run(max_steps=500, dt=0.01, verbose=True)
    
    final_positions3 = [a.position for a in agents3]
    center3 = np.mean(final_positions3, axis=0)
    max_dist3 = max(np.linalg.norm(p - center3) for p in final_positions3)
    print(f"  最终汇合中心: {center3.round(4)}")
    print(f"  最大偏离: {max_dist3:.6f}")
    
    print("\n✓ 多智能体汇合问题测试完成")
