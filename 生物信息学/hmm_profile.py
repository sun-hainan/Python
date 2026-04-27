# -*- coding: utf-8 -*-

"""

算法实现：生物信息学 / hmm_profile



本文件实现 hmm_profile 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Optional





class HiddenMarkovModel:

    """隐马尔可夫模型"""



    def __init__(self, states: List[str], observations: List[str]):

        self.states = states

        self.observations = observations

        self.n_states = len(states)

        self.n_obs = len(observations)



        self.state_to_idx = {s: i for i, s in enumerate(states)}

        self.obs_to_idx = {o: i for i, o in enumerate(observations)}



        # 参数

        self.A = np.zeros((self.n_states, self.n_states))  # 转移概率

        self.B = np.zeros((self.n_states, self.n_obs))     # 发射概率

        self.pi = np.zeros(self.n_states)                   # 初始概率



    def set_transition(self, from_state: str, to_state: str, prob: float):

        """设置转移概率 A[i][j] = P(state_j | state_i)"""

        i = self.state_to_idx[from_state]

        j = self.state_to_idx[to_state]

        self.A[i][j] = prob



    def set_emission(self, state: str, obs: str, prob: float):

        """设置发射概率 B[i][o] = P(obs | state_i)"""

        i = self.state_to_idx[state]

        o = self.obs_to_idx[obs]

        self.B[i][o] = prob



    def set_initial(self, state: str, prob: float):

        """设置初始概率"""

        i = self.state_to_idx[state]

        self.pi[i] = prob



    def forward(self, obs_seq: List[str]) -> float:

        """

        前向算法：计算P(obs | model)



        时间：O(n_states² * T)

        """

        T = len(obs_seq)

        alpha = np.zeros((T, self.n_states))



        # 初始化

        o = self.obs_to_idx[obs_seq[0]]

        alpha[0] = self.pi * self.B[:, o]



        # 递推

        for t in range(1, T):

            o = self.obs_to_idx[obs_seq[t]]

            for j in range(self.n_states):

                alpha[t][j] = np.sum(alpha[t-1] * self.A[:, j]) * self.B[j][o]



        # 终止

        return np.sum(alpha[-1])



    def viterbi(self, obs_seq: List[str]) -> Tuple[float, List[str]]:

        """

        Viterbi算法：找到最可能的状态序列



        返回：(概率, 状态序列)

        """

        T = len(obs_seq)

        delta = np.zeros((T, self.n_states))

        psi = np.zeros((T, self.n_states), dtype=int)



        # 初始化

        o = self.obs_to_idx[obs_seq[0]]

        delta[0] = self.pi * self.B[:, o]



        # 递推

        for t in range(1, T):

            o = self.obs_to_idx[obs_seq[t]]

            for j in range(self.n_states):

                trans = delta[t-1] * self.A[:, j]

                delta[t][j] = np.max(trans) * self.B[j][o]

                psi[t][j] = np.argmax(trans)



        # 回溯

        states_idx = [np.argmax(delta[-1])]

        for t in range(T-1, 0, -1):

            states_idx.append(psi[t][states_idx[-1]])

        states_idx.reverse()



        states_seq = [self.states[i] for i in states_idx]

        prob = np.max(delta[-1])



        return prob, states_seq





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== HMM测试 ===\n")



    # 天气-冰淇淋例子

    states = ['Sunny', 'Rainy']

    observations = ['IceCream_Many', 'IceCream_Few']



    hmm = HiddenMarkovModel(states, observations)



    # 设置参数

    # 初始概率

    hmm.set_initial('Sunny', 0.6)

    hmm.set_initial('Rainy', 0.4)



    # 转移概率

    hmm.set_transition('Sunny', 'Sunny', 0.7)

    hmm.set_transition('Sunny', 'Rainy', 0.3)

    hmm.set_transition('Rainy', 'Sunny', 0.4)

    hmm.set_transition('Rainy', 'Rainy', 0.6)



    # 发射概率

    hmm.set_emission('Sunny', 'IceCream_Many', 0.8)

    hmm.set_emission('Sunny', 'IceCream_Few', 0.2)

    hmm.set_emission('Rainy', 'IceCream_Many', 0.2)

    hmm.set_emission('Rainy', 'IceCream_Few', 0.8)



    # 观测序列

    obs_seq = ['IceCream_Many', 'IceCream_Many', 'IceCream_Few']



    print(f"观测序列: {obs_seq}")



    # 前向算法

    prob = hmm.forward(obs_seq)

    print(f"P(观测|模型) = {prob:.6f}")



    # Viterbi解码

    best_prob, best_states = hmm.viterbi(obs_seq)

    print(f"\n最可能的状态序列: {best_states}")

    print(f"概率: {best_prob:.6f}")



    print("\n说明：")

    print("  - HMM广泛用于：语音识别、NLP、生物序列分析")

    print("  - 前向算法：评估序列概率")

    print("  - Viterbi算法：找到最可能的状态路径")

