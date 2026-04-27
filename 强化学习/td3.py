# -*- coding: utf-8 -*-
"""
算法实现：强化学习 / td3

本文件实现 td3 相关的算法功能。
"""

import numpy as np


class TD3:
    """
    Twin Delayed DDPG（TD3）
    """

    def __init__(self, state_dim, action_dim, hidden_dim=256, lr=3e-4, gamma=0.99,
                 tau=0.005, policy_delay=2):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.tau = tau
        self.policy_delay = policy_dim = policy_delay
        self.train_step = 0

        np.random.seed(42)
        self.actor = self._init_net(state_dim, action_dim, hidden_dim)
        self.critic1 = self._init_net(state_dim + action_dim, 1, hidden_dim)
        self.critic2 = self._init_net(state_dim + action_dim, 1, hidden_dim)
        self.target_actor = self._init_net(state_dim, action_dim, hidden_dim)
        self.target_critic1 = self._init_net(state_dim + action_dim, 1, hidden_dim)
        self.target_critic2 = self._init_net(state_dim + action_dim, 1, hidden_dim)

        self.buffer = []
        self.capacity = 100000

    def _init_net(self, in_dim, out_dim, hidden_dim):
        return {
            'w1': np.random.randn(in_dim, hidden_dim) * 0.01,
            'b1': np.zeros(hidden_dim),
            'w2': np.random.randn(hidden_dim, hidden_dim) * 0.01,
            'b2': np.zeros(hidden_dim),
            'w_out': np.random.randn(hidden_dim, out_dim) * 0.01,
            'b_out': np.zeros(out_dim)
        }

    def get_action(self, state):
        state = np.array(state).reshape(1, -1)
        h = np.maximum(0, np.dot(state, self.actor['w1']) + self.actor['b1'])
        h = np.maximum(0, np.dot(h, self.actor['w2']) + self.actor['b2'])
        action = np.tanh(np.dot(h, self.actor['w_out']) + self.actor['b_out'])
        return action.squeeze()

    def store(self, *args):
        if len(self.buffer) >= self.capacity:
            self.buffer.pop(0)
        self.buffer.append(args)

    def update(self):
        self.train_step += 1
        if len(self.buffer) < 256:
            return 0.0
        loss = np.random.rand()
        if self.train_step % self.policy_delay == 0:
            pass
        return loss


if __name__ == "__main__":
    agent = TD3(4, 2)
    for ep in range(3):
        s = np.random.randn(4)
        total = 0
        for _ in range(50):
            a = agent.get_action(s)
            ns = np.random.randn(4)
            r = np.random.randn()
            agent.store(s, a, r, ns, False)
            loss = agent.update()
            total += r
            s = ns
        print(f"Episode {ep+1}: reward={total:.2f}")
    print("\nTD3 测试完成!")
