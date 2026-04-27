# -*- coding: utf-8 -*-
"""
算法实现：博弈论扩展 / shapley_value

本文件实现 shapley_value 相关的算法功能。
"""

import random
from typing import List, Dict, Callable
from itertools import combinations


def shapley_value(n_players: int, value_function: Callable[[Set[int]], float]) -> Dict[int, float]:
    """
    计算Shapley值

    参数：
        n_players: 玩家数量
        value_function: 联盟值函数 v(S) -> 数值

    返回：每个玩家的Shapley值
    """
    shapley = {i: 0.0 for i in range(n_players)}

    # 枚举所有非空联盟
    for s_size in range(1, n_players + 1):
        for coalition in combinations(range(n_players), s_size):
            coalition_set = set(coalition)
            s_size_float = len(coalition_set)

            # 计算这个联盟的边际贡献
            for player in coalition:
                # v(S) - v(S - {i})
                coalition_without_i = coalition_set - {player}
                marginal_contribution = value_function(coalition_set) - value_function(coalition_without_i)

                # Shapley权重
                weight = math.factorial(s_size_float - 1) * math.factorial(n_players - s_size_float) / math.factorial(n_players)
                # 使用阶乘的对数避免溢出
                import math
                log_weight = (math.log(math.factorial(s_size_float - 1)) + \
                            math.log(math.factorial(n_players - s_size_float)) - \
                            math.log(math.factorial(n_players))

                shapley[player] += math.exp(log_weight) * marginal_contribution

    return shapley


def shapley_value_monte_carlo(n_players: int, value_function: Callable[[Set[int]], float],
                             n_samples: int = 10000) -> Dict[int, float]:
    """
    蒙特卡洛估计Shapley值

    当玩家数很大时使用采样估计
    """
    shapley = {i: 0.0 for i in range(n_players)}

    for _ in range(n_samples):
        # 随机排列
        perm = list(range(n_players))
        random.shuffle(perm)

        # 计算边际贡献
        coalition = set()
        prev_value = 0.0

        for player in perm:
            coalition.add(player)
            new_value = value_function(coalition)
            marginal = new_value - prev_value
            shapley[player] += marginal
            prev_value = new_value

    # 归一化
    for i in range(n_players):
        shapley[i] /= n_samples

    return shapley


def simple_example():
    """简单示例：三人合作项目"""
    print("=== 三人合作项目 Shapley值 ===\n")

    n = 3

    # 定义联盟值函数
    def v(s: Set[int]) -> float:
        if len(s) == 0:
            return 0.0
        if len(s) == 1:
            return 10.0  # 每个人单独价值10
        if len(s) == 2:
            return 30.0  # 两人合作价值30
        if len(s) == 3:
            return 100.0  # 三人合作价值100
        return 0.0

    print("联盟值函数:")
    print("  v(∅) = 0")
    print("  v({i}) = 10 (每个人单独)")
    print("  v({i,j}) = 30 (两人合作)")
    print("  v({1,2,3}) = 100 (三人合作)")
    print()

    sv = shapley_value(n, v)

    print("Shapley值:")
    for player, value in sv.items():
        print(f"  玩家{player + 1}: {value:.2f}")

    total = sum(sv.values())
    print(f"总和: {total:.2f} (应等于100)")


def game_theory_example():
    """投票游戏的Shapley值"""
    print("\n=== 投票游戏 Shapley值 ===\n")

    n = 5  # 5个玩家
    threshold = 3  # 需要3票才能通过

    def voting_power(s: Set[int]) -> float:
        return 1.0 if len(s) >= threshold else 0.0

    sv = shapley_value_monte_carlo(n, voting_power, n_samples=50000)

    print(f"{n}个玩家，门槛={threshold}")
    print("Shapley值 (投票权力):")
    for player, value in sorted(sv.items()):
        print(f"  玩家{player + 1}: {value:.4f}")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    import random
    random.seed(42)

    simple_example()
    game_theory_example()

    print("\n说明：")
    print("  - Shapley值满足效率性、对称性、可加性")
    print("  - 实际应用：利润分配、投票权计算、特征贡献")
    print("  - 当n很大时用蒙特卡洛估计")
