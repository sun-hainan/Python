# -*- coding: utf-8 -*-
"""
算法实现：多智能体系统 / multiagent_reinforcement

本文件实现 multiagent_reinforcement 相关的算法功能。
"""

import numpy as np
from collections import deque
import random


class MultiAgentEnvironment:
    """多智能体环境基类"""
    
    def __init__(self, n_agents, obs_dims, n_actions):
        # n_agents: 智能体数量
        # obs_dims: 各智能体观测维度列表
        # n_actions: 动作空间大小
        self.n_agents = n_agents
        self.obs_dims = obs_dims
        self.n_actions = n_actions
        
        self.state = None
    
    def reset(self):
        """重置环境"""
        raise NotImplementedError
    
    def step(self, actions):
        """执行动作"""
        raise NotImplementedError
    
    def get_obs(self):
        """获取各智能体观测"""
        raise NotImplementedError


class SimpleGridWorld(MultiAgentEnvironment):
    """简化的多智能体格子世界环境"""
    
    def __init__(self, n_agents=3, grid_size=5):
        # grid_size: 格子世界大小
        self.grid_size = grid_size
        self.n_actions = 5  # 上、下、左、右、停留
        
        super().__init__(n_agents, [4] * n_agents, self.n_actions)
        
        # 目标位置
        self.target = (grid_size - 1, grid_size - 1)
        
        # 智能体位置
        self.agent_positions = [
            (0, 0), (0, grid_size - 1), (grid_size - 1, 0)
        ][:n_agents]
        
        self.max_steps = 100
        self.current_step = 0
    
    def reset(self):
        """重置环境"""
        self.current_step = 0
        
        # 随机初始化位置
        for i in range(self.n_agents):
            x = random.randint(0, self.grid_size - 1)
            y = random.randint(0, self.grid_size - 1)
            self.agent_positions[i] = (x, y)
        
        return self.get_obs()
    
    def step(self, actions):
        """执行动作"""
        self.current_step += 1
        
        rewards = []
        dones = []
        
        for i, action in enumerate(actions):
            x, y = self.agent_positions[i]
            
            # 动作映射
            if action == 0:  # 上
                x = max(0, x - 1)
            elif action == 1:  # 下
                x = min(self.grid_size - 1, x + 1)
            elif action == 2:  # 左
                y = max(0, y - 1)
            elif action == 3:  # 右
                y = min(self.grid_size - 1, y + 1)
            # action == 4: 停留
            
            self.agent_positions[i] = (x, y)
        
        # 计算奖励
        for i in range(self.n_agents):
            pos = self.agent_positions[i]
            
            # 到达目标奖励
            if pos == self.target:
                reward = 10.0
                done = True
            else:
                # 与目标距离的负奖励
                dist = abs(pos[0] - self.target[0]) + abs(pos[1] - self.target[1])
                reward = -0.1 * dist
                done = self.current_step >= self.max_steps
            
            rewards.append(reward)
            dones.append(done)
        
        obs = self.get_obs()
        info = {'positions': self.agent_positions.copy()}
        
        return obs, rewards, dones, info
    
    def get_obs(self):
        """获取观测（智能体位置相对于目标的四维特征）"""
        obs_list = []
        for pos in self.agent_positions:
            obs = [
                pos[0] / self.grid_size,
                pos[1] / self.grid_size,
                (pos[0] - self.target[0]) / self.grid_size,
                (pos[1] - self.target[1]) / self.grid_size
            ]
            obs_list.append(np.array(obs))
        return obs_list


class IndependentQAgent:
    """独立Q学习智能体"""
    
    def __init__(self, obs_dim, n_actions, learning_rate=0.1, epsilon=1.0):
        # obs_dim: 观测维度
        # n_actions: 动作空间大小
        # learning_rate: 学习率
        # epsilon: 探索率
        self.obs_dim = obs_dim
        self.n_actions = n_actions
        self.lr = learning_rate
        self.epsilon = epsilon
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.05
        
        # Q表（简化：使用字典）
        self.q_table = {}
    
    def get_q_values(self, obs):
        """获取Q值"""
        obs_tuple = tuple(obs.round(2))
        if obs_tuple not in self.q_table:
            self.q_table[obs_tuple] = np.zeros(self.n_actions)
        return self.q_table[obs_tuple]
    
    def select_action(self, obs):
        """epsilon-贪婪动作选择"""
        if random.random() < self.epsilon:
            return random.randint(0, self.n_actions - 1)
        
        q_values = self.get_q_values(obs)
        return np.argmax(q_values)
    
    def update(self, obs, action, reward, next_obs, done, gamma=0.99):
        """更新Q表"""
        obs_tuple = tuple(obs.round(2))
        next_obs_tuple = tuple(next_obs.round(2))
        
        if obs_tuple not in self.q_table:
            self.q_table[obs_tuple] = np.zeros(self.n_actions)
        if next_obs_tuple not in self.q_table:
            self.q_table[next_obs_tuple] = np.zeros(self.n_actions)
        
        # TD目标
        if done:
            td_target = reward
        else:
            td_target = reward + gamma * np.max(self.q_table[next_obs_tuple])
        
        # TD误差
        td_error = td_target - self.q_table[obs_tuple][action]
        
        # Q表更新
        self.q_table[obs_tuple][action] += self.lr * td_error
        
        return td_error
    
    def decay_epsilon(self):
        """衰减探索率"""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)


class ValueDecompositionNetwork:
    """值分解网络(VDN)简化实现
    
    VDN通过将全局Q值分解为各智能体Q值的和来实现信用分配
    Q_total = sum_i Q_i(obs_i, action_i)
    """
    
    def __init__(self, n_agents, obs_dim, n_actions, hidden_dim=32):
        # n_agents: 智能体数量
        # obs_dim: 观测维度
        # n_actions: 动作空间大小
        # hidden_dim: 隐藏层维度
        self.n_agents = n_agents
        self.obs_dim = obs_dim
        self.n_actions = n_actions
        
        # 各智能体的Q网络（共享参数简化）
        self.w1 = np.random.randn(obs_dim, hidden_dim) * 0.1
        self.b1 = np.zeros(hidden_dim)
        self.w2 = np.random.randn(hidden_dim, n_actions) * 0.1
        self.b2 = np.zeros(n_actions)
    
    def forward(self, obs_list):
        """前向传播，返回各智能体的Q值"""
        q_values_list = []
        
        for obs in obs_list:
            hidden = np.tanh(np.dot(obs, self.w1) + self.b1)
            q_values = np.dot(hidden, self.w2) + self.b2
            q_values_list.append(q_values)
        
        return q_values_list
    
    def get_actions(self, obs_list, epsilon=0.1):
        """选择动作（独立贪婪）"""
        q_values_list = self.forward(obs_list)
        actions = []
        
        for q_values in q_values_list:
            if random.random() < epsilon:
                actions.append(random.randint(0, self.n_actions - 1))
            else:
                actions.append(np.argmax(q_values))
        
        return actions
    
    def update(self, obs_list, actions, rewards, next_obs_list, done, gamma=0.99, lr=0.01):
        """VDN更新"""
        q_list = self.forward(obs_list)
        next_q_list = self.forward(next_obs_list)
        
        # 计算全局Q值
        q_total = sum(q[a] for q, a in zip(q_list, actions))
        
        # 计算目标Q值
        if done:
            q_next_total = 0
        else:
            q_next_total = sum(np.max(next_q) for next_q in next_q_list)
        
        td_error = (sum(rewards) + gamma * q_next_total) - q_total
        
        # 更新网络（简化梯度下降）
        for obs, action, next_q in zip(obs_list, actions, next_q_list):
            # 各智能体的梯度
            hidden = np.tanh(np.dot(obs, self.w1) + self.b1)
            grad_q = np.zeros(self.n_actions)
            grad_q[action] = 1.0
            
            # 更新权重
            self.w2 -= lr * td_error * np.outer(hidden, grad_q)
            self.b2 -= lr * td_error * grad_q
            
            hidden_grad = np.dot(self.w2, grad_q) * (1 - hidden**2)
            self.w1 -= lr * td_error * np.outer(obs, hidden_grad)
            self.b1 -= lr * td_error * hidden_grad
        
        return td_error


class MultiAgentActorCritic:
    """多智能体Actor-Critic (MAC)"""
    
    def __init__(self, n_agents, obs_dim, n_actions, actor_lr=0.001, critic_lr=0.001):
        self.n_agents = n_agents
        self.obs_dim = obs_dim
        self.n_actions = n_actions
        
        # Actor网络（策略）
        self.actors = [self._init_actor() for _ in range(n_agents)]
        
        # Critic网络（全局值函数）
        self.critic = self._init_critic()
        
        self.actor_lr = actor_lr
        self.critic_lr = critic_lr
        self.gamma = 0.99
    
    def _init_actor(self):
        """初始化Actor网络"""
        return {
            'w1': np.random.randn(self.obs_dim, 32) * 0.1,
            'b1': np.zeros(32),
            'w2': np.random.randn(32, self.n_actions) * 0.1,
            'b2': np.zeros(self.n_actions)
        }
    
    def _init_critic(self):
        """初始化Critic网络"""
        return {
            'w1': np.random.randn(self.obs_dim * self.n_agents, 64) * 0.1,
            'b1': np.zeros(64),
            'w2': np.random.randn(64, 1) * 0.1,
            'b2': np.zeros(1)
        }
    
    def get_policy(self, obs, actor_id):
        """获取策略概率分布"""
        actor = self.actors[actor_id]
        hidden = np.tanh(np.dot(obs, actor['w1']) + actor['b1'])
        logits = np.dot(hidden, actor['w2']) + actor['b2']
        
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / np.sum(exp_logits)
        return probs
    
    def get_action(self, obs, actor_id):
        """采样动作"""
        probs = self.get_policy(obs, actor_id)
        return np.random.choice(self.n_actions, p=probs)
    
    def get_v_value(self, obs_list):
        """计算状态值"""
        concat_obs = np.concatenate(obs_list)
        hidden = np.tanh(np.dot(concat_obs, self.critic['w1']) + self.critic['b1'])
        v = np.dot(hidden, self.critic['w2']) + self.critic['b2']
        return v[0]
    
    def update(self, obs_list, actions, rewards, next_obs_list, done):
        """更新Actor和Critic"""
        # 计算TD目标
        v_current = self.get_v_value(obs_list)
        v_next = 0 if done else self.get_v_value(next_obs_list)
        td_target = sum(rewards) + self.gamma * v_next
        td_error = td_target - v_current
        
        # 更新Critic
        concat_obs = np.concatenate(obs_list)
        hidden = np.tanh(np.dot(concat_obs, self.critic['w1']) + self.critic['b1'])
        
        grad_w2 = td_error * hidden
        grad_b2 = td_error
        hidden_grad = np.dot(self.critic['w2'], [td_error]) * (1 - hidden**2)
        grad_w1 = np.outer(concat_obs, hidden_grad)
        
        self.critic['w1'] -= self.critic_lr * grad_w1
        self.critic['b1'] -= self.critic_lr * hidden_grad
        self.critic['w2'] -= self.critic_lr * grad_w2
        self.critic['b2'] -= self.critic_lr * grad_b2
        
        # 更新Actor（策略梯度）
        for i, (obs, action) in enumerate(zip(obs_list, actions)):
            probs = self.get_policy(obs, i)
            
            # 梯度计算
            grad_log_prob = np.zeros(self.n_actions)
            grad_log_prob[action] = 1.0 / (probs[action] + 1e-8)
            
            # 简化更新
            actor = self.actors[i]
            hidden = np.tanh(np.dot(obs, actor['w1']) + actor['b1'])
            
            actor['w2'] -= self.actor_lr * td_error * np.outer(hidden, grad_log_prob)
            actor['b2'] -= self.actor_lr * td_error * grad_log_prob
            
            hidden_grad = np.dot(actor['w2'], grad_log_prob) * (1 - hidden**2)
            actor['w1'] -= self.actor_lr * td_error * np.outer(obs, hidden_grad)
            actor['b1'] -= self.actor_lr * td_error * hidden_grad


class MARLTrainer:
    """多智能体强化学习训练器"""
    
    def __init__(self, env, algorithm='iql'):
        # env: 多智能体环境
        # algorithm: 算法选择 ('iql', 'vdn', 'mac')
        self.env = env
        self.algorithm = algorithm
        
        if algorithm == 'iql':
            self.agents = [
                IndependentQAgent(env.obs_dims[i], env.n_actions)
                for i in range(env.n_agents)
            ]
        elif algorithm == 'vdn':
            self.vdn = ValueDecompositionNetwork(
                env.n_agents, env.obs_dims[0], env.n_actions
            )
        elif algorithm == 'mac':
            self.mac = MultiAgentActorCritic(
                env.n_agents, env.obs_dims[0], env.n_actions
            )
        
        # 经验回放
        self.replay_buffer = deque(maxlen=10000)
    
    def collect_episode(self, epsilon=0.1):
        """收集一个episode的数据"""
        obs_list = self.env.reset()
        episode_data = []
        
        done = False
        while not done:
            # 选择动作
            if self.algorithm == 'iql':
                actions = [agent.select_action(obs) for agent, obs in zip(self.agents, obs_list)]
            elif self.algorithm == 'vdn':
                actions = self.vdn.get_actions(obs_list, epsilon)
            elif self.algorithm == 'mac':
                actions = [self.mac.get_action(obs, i) for i, obs in enumerate(obs_list)]
            
            # 执行
            next_obs_list, rewards, dones, info = self.env.step(actions)
            done = all(dones)
            
            # 存储
            episode_data.append({
                'obs': obs_list,
                'actions': actions,
                'rewards': rewards,
                'next_obs': next_obs_list,
                'done': done
            })
            
            obs_list = next_obs_list
        
        return episode_data
    
    def train_step(self, batch_size=32):
        """训练一步"""
        if len(self.replay_buffer) < batch_size:
            return 0
        
        batch = random.sample(self.replay_buffer, batch_size)
        
        total_loss = 0
        for sample in batch:
            obs_list = sample['obs']
            actions = sample['actions']
            rewards = sample['rewards']
            next_obs_list = sample['next_obs']
            done = sample['done']
            
            if self.algorithm == 'iql':
                for i, agent in enumerate(self.agents):
                    agent.update(obs_list[i], actions[i], rewards[i],
                               next_obs_list[i], done)
            elif self.algorithm == 'vdn':
                loss = self.vdn.update(obs_list, actions, rewards, next_obs_list, done)
                total_loss += loss ** 2
            elif self.algorithm == 'mac':
                self.mac.update(obs_list, actions, rewards, next_obs_list, done)
        
        return total_loss
    
    def run(self, n_episodes=100, batch_size=32, epsilon_start=1.0, epsilon_end=0.05):
        """运行训练"""
        print(f"\n===== 多智能体强化学习训练 ({self.algorithm.upper()}) =====")
        
        epsilon = epsilon_start
        epsilon_decay = (epsilon_end / epsilon_start) ** (1 / n_episodes)
        
        for episode in range(n_episodes):
            # 收集episode
            episode_data = self.collect_episode(epsilon)
            
            # 存储到回放缓冲区
            for step in episode_data:
                self.replay_buffer.append(step)
            
            # 训练
            loss = self.train_step(batch_size)
            
            # 衰减epsilon
            epsilon *= epsilon_decay
            
            if episode % 20 == 0:
                total_reward = sum(step['rewards'][0] for step in episode_data)
                print(f"  Episode {episode}: reward={total_reward:.2f}, "
                      f"epsilon={epsilon:.4f}, loss={loss:.4f}")
        
        return self


if __name__ == "__main__":
    # 测试多智能体强化学习
    print("=" * 50)
    print("多智能体强化学习测试")
    print("=" * 50)
    
    # 创建环境
    env = SimpleGridWorld(n_agents=3, grid_size=5)
    
    print(f"\n环境: {env.n_agents}个智能体, {env.n_actions}个动作")
    
    # 测试IQL
    print("\n--- 独立Q学习(IQL)测试 ---")
    trainer_iql = MARLTrainer(env, algorithm='iql')
    trainer_iql.run(n_episodes=50, batch_size=16)
    
    # 测试VDN
    print("\n--- 值分解网络(VDN)测试 ---")
    env_vdn = SimpleGridWorld(n_agents=3, grid_size=5)
    trainer_vdn = MARLTrainer(env_vdn, algorithm='vdn')
    trainer_vdn.run(n_episodes=50, batch_size=16)
    
    # 测试MAC
    print("\n--- 多智能体Actor-Critic(MAC)测试 ---")
    env_mac = SimpleGridWorld(n_agents=3, grid_size=5)
    trainer_mac = MARLTrainer(env_mac, algorithm='mac')
    trainer_mac.run(n_episodes=50, batch_size=16)
    
    print("\n✓ 多智能体强化学习测试完成")
