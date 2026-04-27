# -*- coding: utf-8 -*-
"""
算法实现：强化学习 / rl_foundation

本文件实现 rl_foundation 相关的算法功能。
"""

import numpy as np
import random
from collections import deque
import os


class BaseEnv:
    """
    基础环境接口

    所有自定义环境应继承此类并实现以下方法：
    - reset(): 重置环境
    - step(action): 执行动作
    - render(): 可视化（可选）
    """

    @property
    def state_dim(self):
        """返回状态空间维度"""
        raise NotImplementedError

    @property
    def action_dim(self):
        """返回动作空间维度"""
        raise NotImplementedError

    @property
    def action_space(self):
        """返回动作空间类型 ('discrete' 或 'continuous')"""
        raise NotImplementedError

    def reset(self):
        """重置环境，返回初始状态"""
        raise NotImplementedError

    def step(self, action):
        """
        执行动作

        参数:
            action: 动作
        返回:
            next_state: 下一个状态
            reward: 奖励
            done: 是否结束
            info: 额外信息
        """
        raise NotImplementedError

    def render(self, mode='human'):
        """可视化环境（可选）"""
        pass

    def close(self):
        """关闭环境（清理资源）"""
        pass


class BaseAgent:
    """
    基础智能体接口

    所有 RL 智能体应继承此类并实现以下方法：
    - select_action(state): 选择动作
    - update(): 更新策略
    - save(path): 保存模型
    - load(path): 加载模型
    """

    def __init__(self, state_dim, action_dim, action_space='discrete'):
        """
        初始化基础智能体

        参数:
            state_dim: 状态维度
            action_dim: 动作维度
            action_space: 动作空间类型
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.action_space = action_space
        self.training = True

    def select_action(self, state, deterministic=False):
        """
        选择动作

        参数:
            state: 当前状态
            deterministic: 是否使用确定性策略
        返回:
            action: 选择的动作
        """
        raise NotImplementedError

    def update(self):
        """执行一步更新"""
        raise NotImplementedError

    def save(self, path):
        """
        保存模型

        参数:
            path: 保存路径
        """
        raise NotImplementedError

    def load(self, path):
        """
        加载模型

        参数:
            path: 加载路径
        """
        raise NotImplementedError

    def train(self):
        """设置为训练模式"""
        self.training = True

    def eval(self):
        """设置为评估模式"""
        self.training = False


class ReplayBuffer:
    """
    通用经验回放缓冲区

    支持：
    - 固定容量
    - 随机采样
    - 批量获取
    """

    def __init__(self, capacity=100000, state_dim=None, action_dim=1):
        """
        初始化经验回放缓冲区

        参数:
            capacity: 缓冲区容量
            state_dim: 状态维度
            action_dim: 动作维度
        """
        self.capacity = capacity
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.buffer = deque(maxlen=capacity)
        self.position = 0

    def push(self, state, action, reward, next_state, done):
        """
        添加经验到缓冲区

        参数:
            state: 当前状态
            action: 执行的动作
            reward: 奖励
            next_state: 下一个状态
            done: 是否结束
        """
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        """
        随机采样批次数据

        参数:
            batch_size: 批次大小
        返回:
            批次数据或 None（缓冲区不足时）
        """
        if len(self.buffer) < batch_size:
            return None

        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        return {
            'states': np.array(states),
            'actions': np.array(actions),
            'rewards': np.array(rewards),
            'next_states': np.array(next_states),
            'dones': np.array(dones)
        }

    def __len__(self):
        """返回缓冲区当前大小"""
        return len(self.buffer)

    def clear(self):
        """清空缓冲区"""
        self.buffer.clear()


class PrioritizedReplayBuffer(ReplayBuffer):
    """
    优先经验回放缓冲区（PER）

    基于 TD 误差的优先级采样，提高数据效率。
    """

    def __init__(self, capacity=100000, alpha=0.6, beta=0.4):
        """
        初始化优先经验回放

        参数:
            capacity: 容量
            alpha: 优先级指数（0=均匀，1=完全优先级）
            beta: 重要性采样指数
        """
        super().__init__(capacity)
        self.alpha = alpha
        self.beta = beta
        self.priorities = deque(maxlen=capacity)
        self.max_priority = 1.0

    def push(self, state, action, reward, next_state, done, td_error=None):
        """添加经验，赋予优先级"""
        if td_error is None:
            td_error = self.max_priority
        self.buffer.append((state, action, reward, next_state, done))
        self.priorities.append((abs(td_error) + 1e-6) ** self.alpha)
        self.max_priority = max(self.max_priority, self.priorities[-1])

    def sample(self, batch_size):
        """基于优先级采样"""
        if len(self.buffer) < batch_size:
            return None

        priorities = np.array(self.priorities)
        probs = priorities / np.sum(priorities)

        indices = np.random.choice(len(self.buffer), batch_size, p=probs)
        weights = (len(self.buffer) * probs[indices]) ** (-self.beta)
        weights = weights / np.max(weights)

        batch = [self.buffer[i] for i in indices]
        states, actions, rewards, next_states, dones = zip(*batch)

        return {
            'states': np.array(states),
            'actions': np.array(actions),
            'rewards': np.array(rewards),
            'next_states': np.array(next_states),
            'dones': np.array(dones),
            'weights': weights,
            'indices': indices
        }

    def update_priorities(self, indices, td_errors):
        """更新采样样本的优先级"""
        for idx, td in zip(indices, td_errors):
            priority = (abs(td) + 1e-6) ** self.alpha
            self.priorities[idx] = priority
            self.max_priority = max(self.max_priority, priority)


class GaussianNoise:
    """高斯噪声（用于连续动作探索）"""

    def __init__(self, dim, sigma=0.2, theta=0.15, dt=1e-2):
        """
        初始化高斯噪声

        参数:
            dim: 噪声维度
            sigma: 噪声标准差
            theta: 回归常数
            dt: 时间步长
        """
        self.dim = dim
        self.sigma = sigma
        self.theta = theta
        self.dt = dt
        self.x = np.zeros(dim)

    def reset(self):
        """重置噪声状态"""
        self.x = np.zeros(self.dim)

    def sample(self):
        """采样噪声"""
        dx = self.theta * (-self.x) * self.dt + self.sigma * np.sqrt(self.dt) * np.random.randn(self.dim)
        self.x += dx
        return self.x


class OUNoise:
    """Ornstein-Uhlenbeck 噪声（用于探索）"""

    def __init__(self, dim, mu=0.0, theta=0.15, sigma=0.2):
        """
        初始化 OU 噪声

        参数:
            dim: 维度
            mu: 均值
            theta: 回归速度
            sigma: 噪声强度
        """
        self.dim = dim
        self.mu = mu
        self.theta = theta
        self.sigma = sigma
        self.x = np.zeros(dim)

    def reset(self):
        """重置"""
        self.x = self.mu * np.ones(self.dim)

    def sample(self):
        """采样"""
        dx = self.theta * (self.mu - self.x) + self.sigma * np.random.randn(self.dim)
        self.x += dx
        return self.x


class EpsilonGreedy:
    """Epsilon-Greedy 探索策略"""

    def __init__(self, epsilon=1.0, epsilon_min=0.01, epsilon_decay=0.995):
        """
        初始化 epsilon 调度

        参数:
            epsilon: 初始探索率
            epsilon_min: 最小探索率
            epsilon_decay: 衰减率
        """
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay

    def decay(self):
        """衰减 epsilon"""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def explore(self, q_values):
        """
        基于 epsilon 探索

        参数:
            q_values: Q 值数组
        返回:
            action: 选择的动作
        """
        if random.random() < self.epsilon:
            return random.randint(0, len(q_values) - 1)
        return np.argmax(q_values)


class Trainer:
    """
    RL 训练器

    提供标准化的训练循环框架。
    """

    def __init__(self, agent, env, eval_env=None, save_dir='./models'):
        """
        初始化训练器

        参数:
            agent: 智能体
            env: 训练环境
            eval_env: 评估环境（可选）
            save_dir: 模型保存目录
        """
        self.agent = agent
        self.env = env
        self.eval_env = eval_env
        self.save_dir = save_dir
        self.global_step = 0
        self.episode_count = 0

        os.makedirs(save_dir, exist_ok=True)

    def train(self, num_episodes=1000, max_steps=1000,
              eval_freq=10, save_freq=100):
        """
        执行训练循环

        参数:
            num_episodes: 训练 episode 数
            max_steps: 每个 episode 最大步数
            eval_freq: 评估频率（episodes）
            save_freq: 保存频率（episodes）
        """
        episode_rewards = []
        best_eval_reward = -float('inf')

        for episode in range(num_episodes):
            state = self.env.reset()
            episode_reward = 0
            episode_steps = 0

            for step in range(max_steps):
                # 选择动作
                action = self.agent.select_action(state)

                # 执行
                next_state, reward, done, _ = self.env.step(action)

                # 存储
                self.agent.store(state, action, reward, next_state, done)

                # 更新
                self.agent.update()

                episode_reward += reward
                episode_steps += 1
                self.global_step += 1
                state = next_state

                if done:
                    break

            self.episode_count += 1
            episode_rewards.append(episode_reward)

            # 衰减 epsilon
            if hasattr(self.agent, 'epsilon') and hasattr(self.agent.epsilon, 'decay'):
                self.agent.epsilon.decay()

            # 评估
            if self.eval_env and episode % eval_freq == 0:
                eval_reward = self._evaluate(max_steps)
                print(f"Episode {episode+1}/{num_episodes}: "
                      f"train_reward={episode_reward:.2f}, "
                      f"eval_reward={eval_reward:.2f}, "
                      f"epsilon={getattr(self.agent, 'epsilon', 'N/A')}")

                if eval_reward > best_eval_reward:
                    best_eval_reward = eval_reward
                    self.agent.save(os.path.join(self.save_dir, 'best_model'))
            else:
                if episode % 20 == 0:
                    print(f"Episode {episode+1}/{num_episodes}: "
                          f"reward={episode_reward:.2f}, steps={episode_steps}")

            # 定期保存
            if episode > 0 and episode % save_freq == 0:
                self.agent.save(os.path.join(self.save_dir, f'checkpoint_{episode}'))

        return episode_rewards

    def _evaluate(self, max_steps):
        """评估当前策略"""
        self.agent.eval()
        total_reward = 0
        n_episodes = 5

        for _ in range(n_episodes):
            state = self.eval_env.reset()
            for _ in range(max_steps):
                action = self.agent.select_action(state, deterministic=True)
                next_state, reward, done, _ = self.eval_env.step(action)
                total_reward += reward
                state = next_state
                if done:
                    break

        self.agent.train()
        return total_reward / n_episodes


class GymWrapper:
    """
    OpenAI Gym 环境包装器

    用于将 Gym 风格环境适配到本框架。
    """

    def __init__(self, env):
        """
        初始化 Gym 包装器

        参数:
            env: Gym 环境实例
        """
        self.env = env
        self._state_dim = env.observation_space.shape[0] if hasattr(env.observation_space, 'shape') else env.observation_space.n
        self._action_dim = env.action_space.n if hasattr(env.action_space, 'n') else env.action_space.shape[0]

    @property
    def state_dim(self):
        return self._state_dim

    @property
    def action_dim(self):
        return self._action_dim

    @property
    def action_space(self):
        if hasattr(self.env.action_space, 'n'):
            return 'discrete'
        return 'continuous'

    def reset(self):
        return self.env.reset()

    def step(self, action):
        return self.env.step(action)

    def render(self):
        self.env.render()

    def close(self):
        self.env.close()


if __name__ == "__main__":
    # 示例：使用基础框架创建自定义环境

    class SimpleEnv(BaseEnv):
        """简单测试环境"""
        def __init__(self):
            self._state_dim = 4
            self._action_dim = 2

        @property
        def state_dim(self):
            return self._state_dim

        @property
        def action_dim(self):
            return self._action_dim

        @property
        def action_space(self):
            return 'discrete'

        def reset(self):
            return np.random.randn(self._state_dim)

        def step(self, action):
            next_state = np.random.randn(self._state_dim) * 0.1
            reward = -np.sum(np.random.randn(self._state_dim) ** 2)
            done = random.random() < 0.1
            return next_state, reward, done, {}

    class DummyAgent(BaseAgent):
        """虚拟智能体"""
        def __init__(self, state_dim, action_dim):
            super().__init__(state_dim, action_dim)
            self.buffer = ReplayBuffer(state_dim=state_dim, action_dim=action_dim)

        def select_action(self, state, deterministic=False):
            return random.randint(0, self.action_dim - 1)

        def store(self, *args):
            self.buffer.push(*args)

        def update(self):
            self.buffer.sample(batch_size=16)

        def save(self, path):
            pass

        def load(self, path):
            pass

    # 测试
    print("=== RL Foundation 测试 ===")
    env = SimpleEnv()
    agent = DummyAgent(env.state_dim, env.action_dim)

    # 简单训练循环
    for episode in range(5):
        state = env.reset()
        total_reward = 0
        for step in range(20):
            action = agent.select_action(state)
            next_state, reward, done, _ = env.step(action)
            agent.store(state, action, reward, next_state, done)
            agent.update()
            total_reward += reward
            state = next_state
            if done:
                break
        print(f"Episode {episode+1}: reward={total_reward:.2f}")

    # 测试噪声
    print("\n=== 噪声测试 ===")
    noise = OUNoise(dim=4)
    samples = [noise.sample() for _ in range(5)]
    print(f"OU Noise samples: {[f'{s[0]:.3f}' for s in samples]}")

    noise2 = GaussianNoise(dim=4)
    samples2 = [noise2.sample() for _ in range(5)]
    print(f"Gaussian Noise samples: {[f'{s[0]:.3f}' for s in samples2]}")

    print("\nRL Foundation 测试完成!")
