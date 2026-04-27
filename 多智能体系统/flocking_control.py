# -*- coding: utf-8 -*-
"""
算法实现：多智能体系统 / flocking_control

本文件实现 flocking_control 相关的算法功能。
"""

import numpy as np
import matplotlib.pyplot as plt


class BoidAgent:
    """Boids模型中的智能体"""
    
    def __init__(self, agent_id, initial_position, initial_velocity=None):
        # agent_id: 智能体ID
        # initial_position: 初始位置 [x, y]
        # initial_velocity: 初始速度，默认随机
        self.agent_id = agent_id
        self.position = np.array(initial_position, dtype=float)
        
        if initial_velocity is None:
            self.velocity = np.random.randn(2) * 0.5
        else:
            self.velocity = np.array(initial_velocity, dtype=float)
        
        self.acceleration = np.zeros(2)
        self.max_speed = 2.0  # 最大速度限制
        self.max_force = 0.1  # 最大加速度限制
    
    def apply_force(self, force):
        """施加力到智能体（更新加速度）"""
        self.acceleration += np.array(force, dtype=float)
    
    def update(self, dt=0.1):
        """更新智能体状态"""
        # 速度更新
        self.velocity += self.acceleration * dt
        
        # 速度限制
        speed = np.linalg.norm(self.velocity)
        if speed > self.max_speed:
            self.velocity = self.velocity / speed * self.max_speed
        
        # 位置更新
        self.position += self.velocity * dt
        
        # 重置加速度
        self.acceleration = np.zeros(2)
    
    def set_velocity(self, vx, vy):
        """设置速度（用于领导者）"""
        self.velocity = np.array([vx, vy], dtype=float)
    
    def get_speed(self):
        """获取当前速度大小"""
        return np.linalg.norm(self.velocity)


class FlockingController:
    """蜂拥控制器"""
    
    def __init__(self, agents, interaction_range=50.0):
        # agents: 智能体列表
        # interaction_range: 交互范围（感知半径）
        self.agents = agents
        self.interaction_range = interaction_range
        self.n_agents = len(agents)
        
        # 权重参数
        self.attraction_weight = 1.0    # 吸引权重
        self.repulsion_weight = 1.5     # 排斥权重
        self.alignment_weight = 1.0      # 对齐权重
        
        # 领航者（可选）
        self.leader = None
        self.leader_weight = 2.0
    
    def set_leader(self, leader_agent):
        """设置领航者智能体"""
        self.leader = leader_agent
    
    def separation(self, agent, visible_agents):
        """
        分离规则：智能体之间保持安全距离
        返回：分离力向量
        """
        separation_force = np.zeros(2)
        
        for other in visible_agents:
            if other.agent_id == agent.agent_id:
                continue
            
            distance = agent.position - other.position
            dist_norm = np.linalg.norm(distance)
            
            if dist_norm < self.interaction_range and dist_norm > 0:
                # 越近的智能体排斥力越强
                strength = 1.0 / (dist_norm ** 2)
                separation_force += distance / dist_norm * strength
        
        # 限制力的大小
        if np.linalg.norm(separation_force) > self.max_force:
            separation_force = separation_force / np.linalg.norm(separation_force) * self.max_force
        
        return separation_force * self.repulsion_weight
    
    def alignment(self, agent, visible_agents):
        """
        对齐规则：向可见邻居的平均速度靠拢
        返回：对齐力向量
        """
        alignment_force = np.zeros(2)
        count = 0
        
        for other in visible_agents:
            if other.agent_id == agent.agent_id:
                continue
            
            distance = np.linalg.norm(agent.position - other.position)
            if distance < self.interaction_range:
                alignment_force += other.velocity
                count += 1
        
        if count > 0:
            # 平均速度
            avg_velocity = alignment_force / count
            # 转向平均速度的方向
            alignment_force = (avg_velocity - agent.velocity) * 0.1
        
        return alignment_force * self.alignment_weight
    
    def cohesion(self, agent, visible_agents):
        """
        凝聚规则：向邻居的中心移动
        返回：凝聚力向量
        """
        center = np.zeros(2)
        count = 0
        
        for other in visible_agents:
            if other.agent_id == agent.agent_id:
                continue
            
            distance = np.linalg.norm(agent.position - other.position)
            if distance < self.interaction_range:
                center += other.position
                count += 1
        
        if count > 0:
            center /= count
            # 朝向中心的方向
            cohesion_direction = center - agent.position
            cohesion_force = cohesion_direction * 0.05
        else:
            cohesion_force = np.zeros(2)
        
        return cohesion_force * self.attraction_weight
    
    def leader_attraction(self, agent):
        """
        领导吸引规则：跟随者向领导者移动
        返回：领导吸引 力向量
        """
        if self.leader is None:
            return np.zeros(2)
        
        direction = self.leader.position - agent.position
        distance = np.linalg.norm(direction)
        
        if distance > 0:
            # 距离越远吸引力越强
            force = direction / distance * 0.1
        else:
            force = np.zeros(2)
        
        return force * self.leader_weight
    
    def get_visible_agents(self, agent):
        """获取在感知范围内的智能体"""
        visible = []
        for other in self.agents:
            if other.agent_id != agent.agent_id:
                distance = np.linalg.norm(agent.position - other.position)
                if distance < self.interaction_range:
                    visible.append(other)
        return visible
    
    def compute_control(self, agent):
        """计算智能体的控制力"""
        visible = self.get_visible_agents(agent)
        
        # 叠加三条规则
        sep = self.separation(agent, visible)
        ali = self.alignment(agent, visible)
        coh = self.cohesion(agent, visible)
        lead = self.leader_attraction(agent)
        
        total_force = sep + ali + coh + lead
        return total_force
    
    def step(self, dt=0.1):
        """单步仿真更新"""
        # 计算所有智能体的控制力
        for agent in self.agents:
            if self.leader and agent.agent_id == self.leader.agent_id:
                # 领导者保持恒定速度，不受控制
                continue
            
            control = self.compute_control(agent)
            agent.apply_force(control)
        
        # 更新所有智能体状态
        for agent in self.agents:
            agent.update(dt)
    
    def run(self, duration, dt=0.1, verbose=True):
        """运行蜂拥仿真"""
        n_steps = int(duration / dt)
        trajectories = []
        
        for step in range(n_steps):
            # 记录状态
            positions = np.array([a.position for a in self.agents])
            velocities = np.array([a.velocity for a in self.agents])
            trajectories.append({
                'positions': positions.copy(),
                'velocities': velocities.copy(),
                'time': step * dt
            })
            
            # 更新
            self.step(dt)
            
            # 定期输出
            if verbose and step % 50 == 0:
                center = np.mean([a.position for a in self.agents], axis=0)
                avg_speed = np.mean([a.get_speed() for a in self.agents])
                print(f"  Step {step}: 中心={center.round(2)}, "
                      f"平均速度={avg_speed:.3f}")
        
        return trajectories


class ReynoldsFlocking(FlockingController):
    """基于Reynolds规则的蜂拥控制"""
    
    def __init__(self, agents, interaction_range=50.0):
        super().__init__(agents, interaction_range)
        
        # Reynolds规则特定参数
        self.separation_distance = 20.0  # 安全距离
        self.neighbor_distance = 50.0    # 邻居感知距离


if __name__ == "__main__":
    # 测试蜂拥控制算法
    print("=" * 50)
    print("蜂拥控制(Flocking)算法测试")
    print("=" * 50)
    
    # 创建智能体群
    n_agents = 20
    agents = []
    
    # 随机初始化位置（在一个圆内）
    for i in range(n_agents):
        angle = np.random.uniform(0, 2 * np.pi)
        radius = np.random.uniform(0, 30)
        pos = np.array([radius * np.cos(angle), radius * np.sin(angle)])
        agent = BoidAgent(i, pos)
        agents.append(agent)
    
    print(f"\n创建{n_agents}个智能体")
    
    # 创建蜂拥控制器
    controller = FlockingController(agents, interaction_range=50.0)
    
    # 设置领航者（第一个智能体）
    leader = agents[0]
    leader.set_velocity(1.0, 0.5)  # 领航者恒定速度
    controller.set_leader(leader)
    print(f"  领航者: Agent 0, 速度={leader.velocity}")
    
    # 运行仿真
    print("\n运行蜂拥控制仿真...")
    trajectories = controller.run(duration=5.0, dt=0.1)
    
    # 分析最终状态
    final_state = trajectories[-1]
    final_positions = final_state['positions']
    final_velocities = final_state['velocities']
    
    # 计算群体指标
    center = np.mean(final_positions, axis=0)
    velocities_magnitude = np.linalg.norm(final_velocities, axis=1)
    
    # 计算分散度
    distances_to_center = np.linalg.norm(final_positions - center, axis=1)
    dispersion = np.std(distances_to_center)
    
    # 计算速度一致性
    velocity_directions = final_velocities / velocities_magnitude[:, np.newaxis]
    avg_velocity = np.mean(final_velocities, axis=0)
    avg_direction = avg_velocity / np.linalg.norm(avg_velocity)
    alignment = np.mean(np.dot(velocity_directions, avg_direction))
    
    print(f"\n===== 蜂拥控制结果 =====")
    print(f"  群体中心: {center.round(2)}")
    print(f"  分散度: {dispersion:.3f}")
    print(f"  平均速度: {np.mean(velocities_magnitude):.3f}")
    print(f"  速度一致性: {alignment:.3f}")
    print(f"  最终位置范围: [{np.min(distances_to_center):.2f}, "
          f"{np.max(distances_to_center):.2f}]")
    
    print("\n✓ 蜂拥控制算法测试完成")
