# -*- coding: utf-8 -*-
"""
算法实现：强化学习 / q_learning

本文件实现 q_learning 相关的算法功能。
"""

import numpy as np
import random


class QLearning:
    """Q-Learning 智能体"""

    def __init__(self, state_num, action_num, learning_rate=0.1, gamma=0.99, epsilon=0.1):
        # state_num: 状态空间大小
        # action_num: 动作空间大小
        # learning_rate: 学习率 α
        # gamma: 折扣因子 γ
        # epsilon: 探索率 ε（ε-贪心策略）
        self.state_num = state_num
        self.action_num = action_num
        self.lr = learning_rate
        self.gamma = gamma
        self.epsilon = epsilon
        # Q 表：Q[s, a] 表示在状态 s 下采取动作 a 的价值
        self.q_table = np.zeros((state_num, action_num))

    def choose_action(self, state):
        """ε-贪心策略选择动作"""
        if random.random() < self.epsilon:
            # 探索：随机选择动作
            return random.randint(0, self.action_num - 1)
        else:
            # 利用：选择 Q 值最大的动作
            return int(np.argmax(self.q_table[state]))

    def update(self, state, action, reward, next_state):
        """Q-Learning 更新规则: Q(s,a) <- Q(s,a) + α[r + γ max_a' Q(s',a') - Q(s,a)]"""
        # 当前 Q 值
        current_q = self.q_table[state, action]
        # 下一状态的最大 Q 值（bootstrap）
        max_next_q = np.max(self.q_table[next_state])
        # TD 目标
        td_target = reward + self.gamma * max_next_q
        # TD 误差
        td_error = td_target - current_q
        # 更新 Q 值
        self.q_table[state, action] += self.lr * td_error

    def train(self, env, episodes):
        """训练 Q-Learning 智能体"""
        # env: 环境对象，需提供 reset() 和 step(action) 接口
        # episodes: 训练回合数
        rewards = []
        for episode in range(episodes):
            state = env.reset()
            total_reward = 0
            done = False
            while not done:
                action = self.choose_action(state)
                next_state, reward, done = env.step(action)
                self.update(state, action, reward, next_state)
                state = next_state
                total_reward += reward
            rewards.append(total_reward)
        return rewards


def simple_env():
    """一个简单的格子世界环境用于测试"""
    class GridWorld:
        def __init__(self):
            self.state_num = 6  # 6个状态：0-5
            self.action_num = 2  # 0=右，1=左
            self.start_state = 0
            self.goal_state = 5

        def reset(self):
            return self.start_state

        def step(self, action):
            # action 0=右，1=左
            if action == 0:
                next_state = min(self.state_num - 1, self.current_state + 1)
            else:
                next_state = max(0, self.current_state - 1)
            self.current_state = next_state
            if next_state == self.goal_state:
                reward = 10
                done = True
            else:
                reward = -1
                done = False
            return next_state, reward, done

        def set_state(self, s):
            self.current_state = s

    return GridWorld()


if __name__ == "__main__":
    # 测试 Q-Learning
    env = simple_env()
    agent = QLearning(state_num=6, action_num=2, learning_rate=0.1, gamma=0.99, epsilon=0.1)
    rewards = agent.train(env, episodes=100)
    print(f"训练完成，平均奖励: {np.mean(rewards[-10]):.2f}")
    print(f"Q表:\n{agent.q_table}")
    print(f"最优策略: {[np.argmax(agent.q_table[s]) for s in range(6)]}")
