# -*- coding: utf-8 -*-
"""
算法实现：强化学习 / sarsa

本文件实现 sarsa 相关的算法功能。
"""

import numpy as np
import random


class Sarsa:
    """SARSA 智能体（On-Policy TD Control）"""

    def __init__(self, state_num, action_num, learning_rate=0.1, gamma=0.99, epsilon=0.1):
        self.state_num = state_num
        self.action_num = action_num
        self.lr = learning_rate
        self.gamma = gamma
        self.epsilon = epsilon
        # Q 表
        self.q_table = np.zeros((state_num, action_num))

    def choose_action(self, state):
        """ε-贪心策略选择动作"""
        if random.random() < self.epsilon:
            return random.randint(0, self.action_num - 1)
        else:
            return int(np.argmax(self.q_table[state]))

    def update(self, state, action, reward, next_state, next_action):
        """SARSA 更新规则: Q(s,a) <- Q(s,a) + α[r + γ Q(s',a') - Q(s,a)]
        注意：使用实际选择的 next_action 而非最大 Q"""
        current_q = self.q_table[state, action]
        # SARSA 使用实际执行的 next_action 的 Q 值（on-policy）
        next_q = self.q_table[next_state, next_action]
        td_target = reward + self.gamma * next_q
        td_error = td_target - current_q
        self.q_table[state, action] += self.lr * td_error

    def train(self, env, episodes):
        """训练 SARSA 智能体"""
        rewards = []
        for episode in range(episodes):
            state = env.reset()
            # 初始动作（使用 ε-贪心）
            action = self.choose_action(state)
            total_reward = 0
            done = False
            while not done:
                next_state, reward, done = env.step(action)
                # 在下一状态选择下一动作（on-policy）
                next_action = self.choose_action(next_state) if not done else None
                self.update(state, action, reward, next_state, next_action)
                state = next_state
                action = next_action
                total_reward += reward
            rewards.append(total_reward)
        return rewards


def simple_env():
    """简单格子世界环境用于测试"""
    class GridWorld:
        def __init__(self):
            self.state_num = 6
            self.action_num = 2
            self.start_state = 0
            self.goal_state = 5

        def reset(self):
            return self.start_state

        def step(self, action):
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
    # 测试 SARSA
    env = simple_env()
    agent = Sarsa(state_num=6, action_num=2, learning_rate=0.1, gamma=0.99, epsilon=0.1)
    rewards = agent.train(env, episodes=100)
    print(f"训练完成，平均奖励: {np.mean(rewards[-10]):.2f}")
    print(f"Q表:\n{agent.q_table}")
    print(f"最优策略: {[np.argmax(agent.q_table[s]) for s in range(6)]}")
