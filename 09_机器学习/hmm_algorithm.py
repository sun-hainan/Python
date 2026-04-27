# -*- coding: utf-8 -*-
"""
算法实现：09_机器学习 / hmm_algorithm

本文件实现 hmm_algorithm 相关的算法功能。
"""

import numpy as np
from typing import Tuple, List

class HMM:
    def __init__(self, n_states, n_observations):
        self.n_states = n_states
        self.n_observations = n_observations
        self.A = np.random.rand(n_states, n_states)
        self.B = np.random.rand(n_states, n_observations)
        self.pi = np.random.rand(n_states)
        self.A /= self.A.sum(axis=1, keepdims=True)
        self.B /= self.B.sum(axis=1, keepdims=True)
        self.pi /= self.pi.sum()

    def forward(self, obs):
        T = len(obs)
        alpha = np.zeros((T, self.n_states))
        alpha[0] = self.pi * self.B[:, obs[0]]
        for t in range(1, T):
            for j in range(self.n_states):
                alpha[t, j] = np.sum(alpha[t-1] * self.A[:, j]) * self.B[j, obs[t]]
        return np.log(alpha[T-1].sum() + 1e-10), alpha

    def viterbi(self, obs):
        T = len(obs)
        delta = np.zeros((T, self.n_states))
        psi = np.zeros((T, self.n_states), dtype=int)
        delta[0] = self.pi * self.B[:, obs[0]]
        for t in range(1, T):
            for j in range(self.n_states):
                trans_probs = delta[t-1] * self.A[:, j]
                psi[t, j] = np.argmax(trans_probs)
                delta[t, j] = np.max(trans_probs) * self.B[j, obs[t]]
        best_path = [0] * T
        best_path[T-1] = np.argmax(delta[T-1])
        for t in range(T-2, -1, -1):
            best_path[t] = psi[t+1, best_path[t+1]]
        return best_path, np.log(delta[T-1].max() + 1e-10)

if __name__ == '__main__':
    print('=== HMM test ===')
    np.random.seed(42)
    hmm = HMM(n_states=2, n_observations=3)
    hmm.A = np.array([[0.7, 0.3], [0.4, 0.6]])
    hmm.B = np.array([[0.5, 0.3, 0.2], [0.1, 0.3, 0.6]])
    hmm.pi = np.array([0.6, 0.4])
    obs = np.array([0, 2, 1, 2, 0])
    log_prob, _ = hmm.forward(obs)
    best_path, _ = hmm.viterbi(obs)
    state_names = ['Sunny', 'Rainy']
    print(f'Observations: {obs.tolist()}')
    print(f'Best path: {[state_names[s] for s in best_path]}')
