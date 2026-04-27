# -*- coding: utf-8 -*-
"""
算法实现：强化学习 / categorical_dqn

本文件实现 categorical_dqn 相关的算法功能。
"""

import numpy as np
import random


class CategoricalDQN:
    """Categorical DQN（C51）算法"""

    def __init__(self, state_dim, action_dim, n_atoms=51, v_min=-10, v_max=10,
                 hidden_dim=128, lr=0.001, gamma=0.99,
                 memory_size=10000, batch_size=64, target_update_freq=200):
        """
        初始化 Categorical DQN

        参数:
            state_dim: 状态维度
            action_dim: 动作维度
            n_atoms: 原子数量（默认51，对应C51）
            v_min: 价值分布最小值
            v_max: 价值分布最大值
            hidden_dim: 隐藏层维度
            lr: 学习率
            gamma: 折扣因子
            memory_size: 经验回放容量
            batch_size: 批次大小
            target_update_freq: 目标网络更新频率
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.n_atoms = n_atoms  # 原子数量
        self.v_min = v_min  # 价值最小值
        self.v_max = v_max  # 价值最大值
        self.gamma = gamma
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq
        self.train_step = 0

        # 计算原子间距
        self.delta_z = (v_max - v_min) / (n_atoms - 1)
        # 支撑点坐标
        self.z_atoms = np.linspace(v_min, v_max, n_atoms)

        # 经验回放
        self.memory = []
        self.memory_size = memory_size

        # 在线网络：输出每个动作的 N 个原子的概率分布
        self.q_network = self._build_network()
        self.target_network = self._build_network()
        self._sync_target()

    def _build_network(self):
        """构建网络（输出：action_dim × n_atoms）"""
        np.random.seed(42)
        return {
            'w1': np.random.randn(self.state_dim, 128) * 0.01,
            'b1': np.zeros(128),
            'w2': np.random.randn(128, 256) * 0.01,
            'b2': np.zeros(256),
            'w3': np.random.randn(256, self.action_dim * self.n_atoms) * 0.01,
            'b3': np.zeros(self.action_dim * self.n_atoms)
        }

    def _forward(self, state, network, softmax=False):
        """前向传播，返回 (batch, action_dim, n_atoms) 的概率分布"""
        h = np.maximum(0, np.dot(state, network['w1']) + network['b1'])
        h = np.maximum(0, np.dot(h, network['w2']) + network['b2'])
        logits = np.dot(h, network['w3']) + network['b3']

        # reshape 为 (batch, action_dim, n_atoms)
        logits = logits.reshape(-1, self.action_dim, self.n_atoms)

        if softmax:
            # 沿原子维度 softmax 得到概率分布
            logits_exp = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
            probs = logits_exp / np.sum(logits_exp, axis=-1, keepdims=True)
            return probs
        return logits

    def _sync_target(self):
        """同步目标网络"""
        self.target_network = {k: v.copy() for k, v in self.q_network.items()}

    def choose_action(self, state):
        """选择动作（基于期望 Q 值）"""
        state = np.array(state).reshape(1, -1)
        # 计算概率分布
        probs = self._forward(state, self.q_network, softmax=True)
        # 期望 Q = Σ p_i * z_i
        q_values = np.sum(probs * self.z_atoms, axis=-1)
        return np.argmax(q_values.squeeze())

    def store(self, state, action, reward, next_state, done):
        """存储样本"""
        if len(self.memory) >= self.memory_size:
            self.memory.pop(0)
        self.memory.append((state, action, reward, next_state, done))

    def train(self):
        """训练网络"""
        if len(self.memory) < self.batch_size:
            return 0.0

        batch = random.sample(self.memory, self.batch_size)
        states = np.array([t[0] for t in batch])
        actions = np.array([t[1] for t in batch])
        rewards = np.array([t[2] for t in batch])
        next_states = np.array([t[3] for t in batch])
        dones = np.array([t[4] for t in batch])

        # 计算当前网络的分布
        curr_logits = self._forward(states, self.q_network, softmax=False)
        # 提取选中动作的 logit
        action_indices = actions[:, None]
        batch_indices = np.arange(len(actions))[:, None]
        curr_logit_selected = np.take_along_axis(
            curr_logits, action_indices[:, :, np.newaxis], axis=1
        ).squeeze(1)  # (batch, n_atoms)

        # 计算目标分布（投影）
        # 使用目标网络计算下一个状态的分布
        next_probs = self._forward(next_states, self.target_network, softmax=True)
        # 选择期望 Q 值最大的动作
        next_q = np.sum(next_probs * self.z_atoms, axis=-1)
        best_actions = np.argmax(next_q, axis=1)

        # 取出最优动作对应的分布
        next_best_probs = np.take_along_axis(
            next_probs, best_actions[:, None, None], axis=1
        ).squeeze(1)  # (batch, n_atoms)

        # 目标价值 = rewards + gamma * z_atoms
        # 使用投影将目标分布映射回支撑
        target_z = rewards[:, None] + self.gamma * self.z_atoms[None, :] * (1 - dones[:, None])
        target_z = np.clip(target_z, self.v_min, self.v_max)

        # 投影到原子支撑
        target_probs = self._project_distribution(target_z, next_best_probs, dones)

        # KL 散度损失
        # Cross entropy between target and current distribution
        target_probs_clipped = np.clip(target_probs, 1e-8, 1 - 1e-8)
        curr_logit_selected_exp = np.exp(curr_logit_selected - np.max(curr_logit_selected, axis=-1, keepdims=True))
        curr_probs = curr_logit_selected_exp / np.sum(curr_logit_selected_exp, axis=-1, keepdims=True)
        curr_probs_clipped = np.clip(curr_probs, 1e-8, 1 - 1e-8)

        loss = -np.sum(target_probs_clipped * np.log(curr_probs_clipped), axis=-1)
        loss = np.mean(loss)

        self.train_step += 1
        if self.train_step % self.target_update_freq == 0:
            self._sync_target()

        return loss

    def _project_distribution(self, target_z, next_probs, dones):
        """
        将目标分布投影到原子支撑上

        参数:
            target_z: 目标价值支撑
            next_probs: 下一个状态的最优动作分布
            dones: 完成标志
        返回:
            投影后的概率分布
        """
        batch_size = target_z.shape[0]
        target_probs = np.zeros_like(next_probs)

        for i in range(batch_size):
            if dones[i]:
                # 终止状态：直接使用奖励
                proj_z = np.array([self.v_min + j * self.delta_z for j in range(self.n_atoms)])
                nearest_idx = np.argmin(np.abs(proj_z - rewards[i]))
                target_probs[i, nearest_idx] = 1.0
            else:
                # 正常状态：投影
                for j in range(self.n_atoms):
                    tzj = target_z[i, j]
                    # 计算投影位置
                    b = (tzj - self.v_min) / self.delta_z
                    l = int(np.floor(b))
                    u = int(np.ceil(b))
                    if l == u:
                        target_probs[i, l] += next_probs[i, j]
                    else:
                        target_probs[i, l] += next_probs[i, j] * (u - b)
                        target_probs[i, u] += next_probs[i, j] * (b - l)

        return target_probs

    def get_q_distribution(self, state):
        """获取状态的 Q 值分布（用于分析）"""
        state = np.array(state).reshape(1, -1)
        probs = self._forward(state, self.q_network, softmax=True)
        return probs, self.z_atoms


if __name__ == "__main__":
    from collections import deque

    class TestCategoricalDQN(CategoricalDQN):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.memory = deque(maxlen=10000)

    state_dim = 4
    action_dim = 2
    agent = TestCategoricalDQN(state_dim, action_dim)

    for ep in range(5):
        state = np.random.randn(state_dim)
        total_reward = 0
        for step in range(15):
            action = agent.choose_action(state)
            next_state = np.random.randn(state_dim)
            reward = random.uniform(-1, 1)
            done = random.random() < 0.1
            agent.store(state, action, reward, next_state, done)
            total_reward += reward
            state = next_state
            if done:
                break
        loss = agent.train()
        # 获取分布信息
        dist, z = agent.get_q_distribution(state)
        q_mean = np.sum(dist * z, axis=-1).mean()
        print(f"Episode {ep+1}: reward={total_reward:.2f}, loss={loss:.4f}, "
              f"Q_mean={q_mean:.4f}")

    print("\nCategorical DQN (C51) 测试完成!")
