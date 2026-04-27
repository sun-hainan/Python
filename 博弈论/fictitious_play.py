# -*- coding: utf-8 -*-

"""

算法实现：博弈论 / fictitious_play



本文件实现 fictitious_play 相关的算法功能。

"""



import random

from typing import List, Tuple, Dict

import numpy as np





class FictitiousPlay:

    """虚拟博弈"""

    def __init__(self, payoff_matrix_a: List[List[float]], payoff_matrix_b: List[List[float]]):

        self.payoff_a = np.array(payoff_matrix_a, dtype=float)  # 玩家 A 收益

        self.payoff_b = np.array(payoff_matrix_b, dtype=float)  # 玩家 B 收益

        self.num_strategies_a = len(payoff_matrix_a)              # A 的策略数

        self.num_strategies_b = len(payoff_matrix_b[0])          # B 的策略数



        # 历史统计

        self.history_a: List[int] = []   # A 的历史行动

        self.history_b: List[int] = []   # B 的历史行动



        # 历史策略频率（累积均值）

        self.strategy_freq_a: np.ndarray = np.zeros(self.num_strategies_a)

        self.strategy_freq_b: np.ndarray = np.zeros(self.num_strategies_b)



    def best_response(self, opponent_strategy_freq: np.ndarray, is_player_a: bool) -> int:

        """

        计算对对手策略的最优反应（BR）

        最优反应：选择期望收益最高的纯策略

        """

        if is_player_a:

            # 计算 A 各策略的期望收益：sum_j freq_B[j] * payoff_A[i][j]

            expected_payoffs = self.payoff_a.dot(opponent_strategy_freq)

        else:

            # B 的期望收益：sum_i freq_A[i] * payoff_B[i][j]

            expected_payoffs = opponent_strategy_freq.dot(self.payoff_b)



        # 返回期望收益最高的策略

        best = np.argmax(expected_payoffs)

        return int(best)



    def mixed_strategy(self, history: List[int]) -> np.ndarray:

        """从历史计算混合策略（频率近似）"""

        freq = np.zeros(self.num_strategies_a if len(history) > 0 and isinstance(history[0], int) and self.num_strategies_a > len(history) else self.num_strategies_a)

        # 简化：计算各策略出现的频率

        if not history:

            return np.ones(len(freq)) / len(freq)  # 均匀分布

        for action in history:

            freq[action] += 1

        return freq / len(history)



    def play_round(self) -> Tuple[int, int]:

        """执行一轮虚拟博弈"""

        # 计算双方的历史平均策略

        if not self.history_a:

            freq_a = np.ones(self.num_strategies_a) / self.num_strategies_a

        else:

            freq_a = self.strategy_freq_a / len(self.history_a)



        if not self.history_b:

            freq_b = np.ones(self.num_strategies_b) / self.num_strategies_b

        else:

            freq_b = self.strategy_freq_b / len(self.history_b)



        # A 选择对 B 历史的最优反应

        action_a = self.best_response(freq_b, is_player_a=True)

        # B 选择对 A 历史的最优反应

        action_b = self.best_response(freq_a, is_player_a=False)



        # 记录

        self.history_a.append(action_a)

        self.history_b.append(action_b)

        self.strategy_freq_a[action_a] += 1

        self.strategy_freq_b[action_b] += 1



        return action_a, action_b



    def run(self, num_rounds: int) -> Dict:

        """

        运行虚拟博弈

        返回：收敛分析结果

        """

        for t in range(num_rounds):

            a, b = self.play_round()



        # 计算最终平均策略

        avg_a = self.strategy_freq_a / num_rounds

        avg_b = self.strategy_freq_b / num_rounds



        return {

            "avg_strategy_a": avg_a.tolist(),

            "avg_strategy_b": avg_b.tolist(),

            "history_a": self.history_a,

            "history_b": self.history_b

        }



    def analyze_convergence(self, nash_equilibrium: Tuple) -> Dict:

        """分析向纳什均衡的收敛程度"""

        eq_a = np.array(nash_equilibrium[0])

        eq_b = np.array(nash_equilibrium[1])



        avg_a = self.strategy_freq_a / len(self.history_a)

        avg_b = self.strategy_freq_b / len(self.history_b)



        dist_a = np.linalg.norm(avg_a - eq_a)

        dist_b = np.linalg.norm(avg_b - eq_b)



        return {

            "distance_to_eq_a": dist_a,

            "distance_to_eq_b": dist_b

        }





# ============================ 测试代码 ============================

if __name__ == "__main__":

    print("=== 虚拟博弈演示 ===")



    # 囚徒困境

    payoff_a = [[-1, -3], [0, -2]]

    payoff_b = [[-1, 0], [-3, -2]]



    print("博弈：囚徒困境")

    print("          B沉默    B背叛")

    print(f"B沉默:  A=(-1,-1), A=(-3,0)")

    print(f"B背叛:  A=(0,-3),  A=(-2,-2)")

    print()



    # 运行虚拟博弈

    fp = FictitiousPlay(payoff_a, payoff_b)

    result = fp.run(num_rounds=1000)



    print(f"运行 1000 轮后：")

    print(f"玩家 A 平均策略（沉默, 背叛）: {result['avg_strategy_a']}")

    print(f"玩家 B 平均策略（沉默, 背叛）: {result['avg_strategy_b']}")



    # 分析历史

    silence_a = result['avg_strategy_a'][0]

    silence_b = result['avg_strategy_b'][0]

    print(f"\n玩家 A 沉默概率: {silence_a:.3f}")

    print(f"玩家 B 沉默概率: {silence_b:.3f}")



    # 在囚徒困境中，虚拟博弈会收敛到（背叛，背叛）

    # 因为背叛是占优策略

    背叛_a = result['avg_strategy_a'][1]

    背叛_b = result['avg_strategy_b'][1]

    print(f"\n玩家 A 背叛概率: {背叛_a:.3f}")

    print(f"玩家 B 背叛概率: {背叛_b:.3f}")



    # 验证收敛

    expected_eq = (背叛_a > 0.9 and 背叛_b > 0.9)

    print(f"\n收敛到纳什均衡（背叛, 背叛）: {'✅ 是' if expected_eq else '⚠️ 未完全收敛'}")



    print("\n=== 另一个博弈：Matching Pennies ===")

    # Matching Pennies：零和博弈，无纯策略均衡

    payoff_a_mp = [[1, -1], [-1, 1]]  # A 选 H 若 B 也选 H 则赢

    payoff_b_mp = [[-1, 1], [1, -1]]



    fp_mp = FictitiousPlay(payoff_a_mp, payoff_b_mp)

    result_mp = fp_mp.run(num_rounds=5000)



    print(f"运行 5000 轮后：")

    print(f"玩家 A 平均策略（Head, Tail）: {result_mp['avg_strategy_a']}")

    print(f"玩家 B 平均策略（Head, Tail）: {result_mp['avg_strategy_b']}")



    # 验证：应收敛到 (0.5, 0.5)

    h_a = result_mp['avg_strategy_a'][0]

    print(f"\n收敛到 50/50 混合: {'✅ 是' if abs(h_a - 0.5) < 0.05 else '⚠️ 未收敛到 50/50'}")



    print("\n✅ 虚拟博弈通过经验学习逼近纳什均衡")

    print("时间复杂度：O(T * n^2)")

    print("空间复杂度：O(T * n)")

