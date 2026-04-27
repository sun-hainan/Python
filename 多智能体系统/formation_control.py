# -*- coding: utf-8 -*-
"""
算法实现：多智能体系统 / formation_control

本文件实现 formation_control 相关的算法功能。
"""

import numpy as np
import matplotlib.pyplot as plt


class VirtualLeader:
    """虚拟领航者：定义编队的参考轨迹"""
    
    def __init__(self, initial_pos, initial_vel=np.zeros(2)):
        # initial_pos: 初始位置 [x, y]
        # initial_vel: 初始速度
        self.position = np.array(initial_pos, dtype=float)
        self.velocity = np.array(initial_vel, dtype=float)
    
    def update(self, dt, acceleration=np.zeros(2)):
        """更新领航者状态"""
        # 速度更新
        self.velocity += dt * acceleration
        # 位置更新
        self.position += dt * self.velocity
        return self.position.copy()
    
    def set_velocity(self, vx, vy):
        """设置恒定速度"""
        self.velocity = np.array([vx, vy], dtype=float)


class FormationGeometry:
    """编队几何结构：定义智能体间的期望相对位置"""
    
    def __init__(self, n_agents):
        # n_agents: 智能体数量
        self.n_agents = n_agents
        self.formation = {}  # key: agent_id, value: [dx, dy] 相对于领航者
    
    def set_formation(self, agent_id, relative_pos):
        """设置智能体agent_id相对于领航者的期望位置"""
        self.formation[agent_id] = np.array(relative_pos, dtype=float)
    
    def get_desired_position(self, agent_id, leader_pos):
        """获取智能体agent_id的期望位置"""
        if agent_id in self.formation:
            return leader_pos + self.formation[agent_id]
        return leader_pos  # 默认在领航者位置
    
    def get_relative_error(self, agent_id, current_pos, leader_pos):
        """计算相对位置误差"""
        desired_pos = self.get_desired_position(agent_id, leader_pos)
        return current_pos - desired_pos


class LeaderFollowerAgent:
    """领航-跟随者智能体"""
    
    def __init__(self, agent_id, is_leader=False, initial_pos=np.zeros(2)):
        # agent_id: 智能体ID
        # is_leader: 是否为领航者
        # initial_pos: 初始位置
        self.agent_id = agent_id
        self.is_leader = is_leader
        self.position = np.array(initial_pos, dtype=float)
        self.velocity = np.zeros(2)
        self.control_input = np.zeros(2)
    
    def update(self, dt):
        """根据控制输入更新状态"""
        # 二阶积分器模型
        self.velocity += dt * self.control_input
        self.position += dt * self.velocity


class LeaderFollowerFormation:
    """领航-跟随者编队控制系统"""
    
    def __init__(self, n_followers, formation_shape):
        # n_followers: 跟随者数量（不含领航者）
        # formation_shape: 编队几何形状
        self.n_agents = n_followers + 1  # 包含领航者
        self.formation = formation_shape
        
        # 创建虚拟领航者
        self.leader = VirtualLeader(initial_pos=[0.0, 0.0])
        
        # 创建跟随者
        self.followers = [
            LeaderFollowerAgent(i, is_leader=False, initial_pos=np.random.randn(2) * 2)
            for i in range(n_followers)
        ]
        
        # 控制参数
        self.kp = 2.0  # 位置误差增益
        self.kv = 1.5  # 速度误差增益
    
    def control_law(self, agent, leader_pos, leader_vel):
        """
        编队控制律
        u = -kp * (position_error) - kv * (velocity_error) + leader_acc
        """
        # 获取期望位置
        desired_pos = self.formation.get_desired_position(agent.agent_id, leader_pos)
        
        # 位置误差
        pos_error = agent.position - desired_pos
        
        # 速度误差（跟随者期望速度与领航者相同）
        vel_error = agent.velocity - leader_vel
        
        # 控制输入
        control = -self.kp * pos_error - self.kv * vel_error
        return control
    
    def step(self, dt=0.01):
        """单步仿真"""
        # 更新领航者
        leader_pos = self.leader.update(dt)
        leader_vel = self.leader.velocity.copy()
        
        # 更新跟随者
        for follower in self.followers:
            control = self.control_law(follower, leader_pos, leader_vel)
            follower.control_input = control
            follower.update(dt)
        
        return self.get_state()
    
    def get_state(self):
        """获取当前所有智能体状态"""
        state = {
            'leader': {
                'position': self.leader.position.copy(),
                'velocity': self.leader.velocity.copy()
            },
            'followers': [
                {
                    'id': f.agent_id,
                    'position': f.position.copy(),
                    'velocity': f.velocity.copy()
                }
                for f in self.followers
            ]
        }
        return state
    
    def run(self, duration, dt=0.01):
        """运行编队控制仿真"""
        n_steps = int(duration / dt)
        trajectories = []
        
        for step in range(n_steps):
            state = self.step(dt)
            trajectories.append(state)
            
            # 每100步打印状态
            if step % 100 == 0:
                pos_errors = []
                for f in self.followers:
                    desired = self.formation.get_desired_position(
                        f.agent_id, self.leader.position)
                    pos_errors.append(np.linalg.norm(f.position - desired))
                avg_error = np.mean(pos_errors)
                print(f"  Step {step}: leader={self.leader.position.round(2)}, "
                      f"avg_pos_error={avg_error:.4f}")
        
        return trajectories
    
    def set_leader_trajectory(self, trajectory_type='circle', radius=5.0, omega=0.5):
        """
        设置领航者轨迹
        trajectory_type: 'circle', 'line', 'eight'
        """
        if trajectory_type == 'circle':
            # 圆形轨迹
            self.leader_trajectory_type = trajectory_type
            self.leader_radius = radius
            self.leader_omega = omega
            self.leader_time = 0.0
        elif trajectory_type == 'line':
            # 直线轨迹
            self.leader_trajectory_type = trajectory_type
            self.leader_velocity = np.array([1.0, 0.5])
    
    def update_leader(self, dt):
        """更新领航者位置（外部控制）"""
        if hasattr(self, 'leader_trajectory_type'):
            if self.leader_trajectory_type == 'circle':
                self.leader_time += dt
                angle = self.leader_omega * self.leader_time
                x = self.leader_radius * np.cos(angle)
                y = self.leader_radius * np.sin(angle)
                self.leader.position = np.array([x, y])
                # 计算速度（切向）
                vx = -self.leader_radius * self.leader_omega * np.sin(angle)
                vy = self.leader_radius * self.leader_omega * np.cos(angle)
                self.leader.velocity = np.array([vx, vy])


if __name__ == "__main__":
    # 测试领航-跟随者编队控制
    print("=" * 50)
    print("领航-跟随者编队控制测试")
    print("=" * 50)
    
    # 设置编队形状（领航者在中心，跟随者在周围形成菱形）
    n_followers = 4
    formation = FormationGeometry(n_followers)
    
    # 定义编队形状：相对于领航者的位置
    formation.set_formation(0, [5.0, 0.0])   # 前方
    formation.set_formation(1, [0.0, 5.0])   # 左方
    formation.set_formation(2, [-5.0, 0.0])  # 后方
    formation.set_formation(3, [0.0, -5.0])  # 右方
    
    print(f"\n编队形状（{n_followers}个跟随者）:")
    for agent_id, pos in formation.formation.items():
        print(f"  跟随者{agent_id}: {pos}")
    
    # 创建编队控制系统
    system = LeaderFollowerFormation(n_followers, formation)
    
    # 设置领航者做圆周运动
    system.set_leader_trajectory(trajectory_type='circle', radius=3.0, omega=0.3)
    
    # 初始化跟随者位置（在期望位置附近）
    for i, follower in enumerate(system.followers):
        desired = formation.get_desired_position(i, system.leader.position)
        follower.position = desired + np.random.randn(2) * 0.5  # 添加小扰动
    
    print("\n领航者圆周运动: 半径=3.0, 角速度=0.3 rad/s")
    
    # 运行仿真
    print("\n运行编队控制仿真...")
    trajectories = system.run(duration=10.0, dt=0.01)
    
    # 分析结果
    final_state = trajectories[-1]
    print(f"\n编队控制结果:")
    print(f"  领航者位置: {final_state['leader']['position'].round(3)}")
    
    for f in final_state['followers']:
        desired = formation.get_desired_position(
            f['id'], final_state['leader']['position'])
        error = np.linalg.norm(f['position'] - desired)
        print(f"  跟随者{f['id']}: 位置={f['position'].round(3)}, "
              f"期望={desired.round(3)}, 误差={error:.4f}")
    
    print("\n✓ 领航-跟随者编队控制测试完成")
