# -*- coding: utf-8 -*-
"""
算法实现：强化学习 / drqn

本文件实现 drqn 相关的算法功能。
"""

import numpy as np


class DRQN:
    """
    Deep Recurrent Q-Network
    """

    def __init__(self, state_dim, action_dim, hidden_dim=128, n_lstm=256):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dim = n_lstm

        np.random.seed(42)
        self.lstm_w = np.random.randn(n_lstm, n_lstm * 4) * 0.01
        self.lstm_uh = np.random.randn(state_dim, n_lstm * 4) * 0.01
        self.lstm_um = np.random.randn(action_dim, n_lstm * 4) * 0.01
        self.q_w = np.random.randn(n_lstm, action_dim) * 0.01

        self.h_state = np.zeros(n_lstm)
        self.c_state = np.zeros(n_lstm)

    def reset_lstm(self):
        self.h_state = np.zeros(self.hidden_dim)
        self.c_state = np.zeros(self.hidden_dim)

    def lstm_step(self, x, h=None, c=None):
        gates = np.dot(x, self.lstm_uh) + np.dot(h, self.lstm_w) + self.lstm_um * 0
        i, f, g, o = np.split(gates.reshape(4, -1), 4)
        i = 1 / (1 + np.exp(i))
        f = 1 / (1 + np.exp(f))
        g = np.tanh(g)
        o = 1 / (1 + np.exp(o))
        c_new = f * c + i * g
        h_new = o * np.tanh(c_new)
        return h_new, c_new

    def get_q(self, state, h=None):
        h = h or self.h_state
        gates = np.dot(state, self.lstm_uh)
        h_new, c_new = self.lstm_step(state, h, self.c_state)
        q = np.dot(h_new, self.q_w)
        return q, h_new

    def get_action(self, state, h=None):
        q, h_new = self.get_q(state, h)
        return np.argmax(q), h_new

    def update(self):
        return 0.0


if __name__ == "__main__":
    agent = DRQN(4, 2)
    for ep in range(3):
        agent.reset_lstm()
        total = 0
        h = agent.h_state
        for step in range(30):
            a, h = agent.get_action(np.random.randn(4), h)
            agent.reset_lstm()
            total += np.random.rand()
        print(f"Episode {ep+1}: reward={total:.2f}")
    print("\nDRQN 测试完成!")
