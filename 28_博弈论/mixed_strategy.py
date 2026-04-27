# -*- coding: utf-8 -*-

"""

算法实现：博弈论 / mixed_strategy



本文件实现 mixed_strategy 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict, Optional



def find_mixed_strategy_nash(payoff_matrix: np.ndarray, player: int = 0) -> Optional[np.ndarray]:

    """

    寻找2x2博弈的混合策略纳什均衡

    

    Args:

        payoff_matrix: 玩家0的收益矩阵

        player: 0或1，表示计算哪个玩家的均衡

    

    Returns:

        混合策略概率向量

    """

    # 假设两个玩家都是2个策略

    if payoff_matrix.shape != (2, 2):

        return None

    

    # 获取收益矩阵

    a, b = payoff_matrix[0, 0], payoff_matrix[0, 1]

    c, d = payoff_matrix[1, 0], payoff_matrix[1, 1]

    

    # 对player 0: 如果player 1选择策略1，player 0选择策略1的期望收益是c，选择策略2的期望收益是d

    # 玩家0的混合策略 p = (p, 1-p)

    # 玩家1选择策略1时的期望收益: p*a + (1-p)*c

    # 玩家1选择策略2时的期望收益: p*b + (1-p)*d

    

    # 均衡条件：两种选择的期望收益相等

    # p*a + (1-p)*c = p*b + (1-p)*d

    # p*(a-c) + c = p*(b-d) + d

    # p*(a-c-b+d) = d-c

    # p = (d-c) / (a-b-c+d)

    

    numerator = d - c

    denominator = a - b - c + d

    

    if abs(denominator) < 1e-10:

        # 特殊情形：所有收益相等或列是重复的

        return np.array([0.5, 0.5])

    

    p = numerator / denominator

    

    # 确保概率在[0,1]之间

    if 0 <= p <= 1:

        return np.array([p, 1 - p])

    else:

        # 不存在内部均衡，可能需要边界解

        return None



def solve_mixed_strategy_game(payoff1: np.ndarray, payoff2: np.ndarray) -> Tuple[Dict, Dict]:

    """

    求解2x2博弈的混合策略纳什均衡

    

    Args:

        payoff1: 玩家1的收益矩阵

        payoff2: 玩家2的收益矩阵

    

    Returns:

        (玩家1策略, 玩家2策略)

    """

    # 求解玩家1的混合策略

    p1_strategy = find_mixed_strategy_nash(payoff1, player=0)

    

    # 求解玩家2的混合策略 (转置矩阵)

    p2_strategy = find_mixed_strategy_nash(payoff2.T, player=0)

    

    return {"strategy": p1_strategy, "player": 1}, {"strategy": p2_strategy, "player": 2}



def compute_mixed_strategy_payoff(strategy: np.ndarray, payoff_matrix: np.ndarray) -> float:

    """计算混合策略下的期望收益"""

    return strategy @ payoff_matrix @ strategy



def find_all_nash_equilibria(payoff1: np.ndarray, payoff2: np.ndarray) -> List[Dict]:

    """

    找到所有纳什均衡（纯策略和混合策略）

    """

    equilibria = []

    

    # 1. 检查纯策略均衡

    n, m = payoff1.shape

    

    for i in range(n):

        for j in range(m):

            # 检查(i,j)是否是均衡

            # 玩家1选i时，不能通过换成其他行获得更高收益

            player1_best = np.argmax(payoff1[i, :])

            # 玩家2选j时，不能通过换成其他列获得更高收益

            player2_best = np.argmax(payoff2[:, j])

            

            if payoff1[i, j] >= payoff1[i, player1_best] and payoff2[i, j] >= payoff2[player2_best, j]:

                equilibria.append({

                    "type": "pure",

                    "player1_action": i,

                    "player2_action": j,

                    "payoffs": (payoff1[i, j], payoff2[i, j])

                })

    

    # 2. 检查混合策略均衡

    mixed_eq = solve_mixed_strategy_game(payoff1, payoff2)

    

    if mixed_eq[0]["strategy"] is not None:

        p1 = mixed_eq[0]["strategy"]

        p2 = mixed_eq[1]["strategy"]

        

        # 计算期望收益

        exp_payoff1 = compute_mixed_strategy_payoff(p1, payoff1)

        exp_payoff2 = compute_mixed_strategy_payoff(p2, payoff2)

        

        equilibria.append({

            "type": "mixed",

            "player1_strategy": p1,

            "player2_strategy": p2,

            "expected_payoffs": (exp_payoff1, exp_payoff2)

        })

    

    return equilibria



if __name__ == "__main__":

    print("=== 混合策略纳什均衡测试 ===")

    

    # 石头剪刀布

    rps_payoff1 = np.array([[0, -1, 1], [1, 0, -1], [-1, 1, 0]])

    

    print("石头剪刀布 (无纯策略均衡):")

    print("  2x2子博弈分析...")

    

    # 分析石头vs布的子博弈

    sub_payoff1 = rps_payoff1[:2, :2]  # 石头、剪刀 vs 石头、布

    print(f"\n  子博弈矩阵:")

    print(f"    石头  布")

    print(f"  石头 {sub_payoff1[0,0]:3d} {sub_payoff1[0,1]:3d}")

    print(f"  剪刀 {sub_payoff1[1,0]:3d} {sub_payoff1[1,1]:3d}")

    

    mixed = find_mixed_strategy_nash(sub_payoff1)

    if mixed is not None:

        print(f"  混合策略: {mixed}")

    

    # 性别之战

    print("\n=== 性别之战 (Battle of the Sexes) ===")

    bos_p1 = np.array([[2, 0], [0, 1]])

    bos_p2 = np.array([[1, 0], [0, 2]])

    

    print("         足球    歌剧")

    print("  足球   2,1    0,0")

    print("  歌剧   0,0    1,2")

    

    equilibria = find_all_nash_equilibria(bos_p1, bos_p2)

    print(f"\n纳什均衡:")

    for eq in equilibria:

        print(f"  {eq}")

    

    # 斗鸡博弈

    print("\n=== 斗鸡博弈 (Chicken Game) ===")

    chicken_p1 = np.array([[-10, 5], [-5, 0]])

    chicken_p2 = np.array([[-10, -5], [5, 0]])

    

    print("         前进    让路")

    print("  前进   -10,-10 5,-5")

    print("  让路   -5,5    0,0")

    

    chicken_eq = find_all_nash_equilibria(chicken_p1, chicken_p2)

    print(f"\n纳什均衡:")

    for eq in chicken_eq:

        print(f"  {eq}")

    

    # 计算期望收益

    print("\n=== 期望收益计算 ===")

    strategy = np.array([0.5, 0.5])

    

    for name, payoff in [("性别之战", bos_p1), ("斗鸡博弈", chicken_p1)]:

        exp_payoff = compute_mixed_strategy_payoff(strategy, payoff)

        print(f"{name} 混合策略{strategy}的期望收益: {exp_payoff:.2f}")

    

    # Matching Pennies

    print("\n=== 匹配硬币 (Matching Pennies) ===")

    mp_p1 = np.array([[1, -1], [-1, 1]])

    

    print("         H        T")

    print("  H     1,-1    -1,1")

    print("  T    -1,1     1,-1")

    

    mp_eq = find_all_nash_equilibria(mp_p1, -mp_p1)

    print(f"\n纳什均衡:")

    for eq in mp_eq:

        if eq["type"] == "mixed":

            print(f"  混合策略均衡: Player1={eq['player1_strategy']}, Player2={eq['player2_strategy']}")

        else:

            print(f"  纯策略均衡: {eq}")

    

    print("\n结论: 匹配硬币只有混合策略均衡，双方都以0.5的概率选择H和T")

