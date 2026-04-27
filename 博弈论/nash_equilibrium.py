# -*- coding: utf-8 -*-
"""
算法实现：博弈论 / nash_equilibrium

本文件实现 nash_equilibrium 相关的算法功能。
"""

from typing import List, Tuple, Optional
import numpy as np


class NashEquilibrium:
    """纳什均衡求解器（简化版：2x2 双矩阵博弈）"""

    @staticmethod
    def solve_2x2(payoff_a: List[List[float]], payoff_b: List[List[float]]) -> List[Tuple[float, float]]:
        """
        求解 2x2 博弈的纳什均衡
        payoff_a: 玩家 A 的收益矩阵（行=玩家A策略，列=玩家B策略）
        payoff_b: 玩家 B 的收益矩阵
        返回：纳什均衡列表 [(prob_A1, prob_A2), (prob_B1, prob_B2)]
        """
        equilibria = []

        # 方法：枚举所有可能的混合策略组合，检验是否为均衡

        # 1. 检查纯策略均衡
        for i in range(2):
            for j in range(2):
                # 玩家 A 选择 i，玩家 B 选择 j
                a_pay = payoff_a[i][j]
                b_pay = payoff_b[i][j]

                # 检查：玩家 A 的策略 i 是否是其对 j 的最优反应
                # 即：对玩家 A，策略 i 的收益 >= 其他策略的收益
                a_best = all(a_pay >= payoff_a[k][j] for k in range(2))

                # 检查：玩家 B 的策略 j 是否是其对 i 的最优反应
                b_best = all(b_pay >= payoff_b[i][k] for k in range(2))

                if a_best and b_best:
                    equilibria.append(((1.0 if i == 0 else 0.0, 1.0 if i == 1 else 0.0),
                                      (1.0 if j == 0 else 0.0, 1.0 if j == 1 else 0.0)))

        # 2. 检查混合策略均衡
        # 对于 2x2，至少有一个玩家使用混合策略的均衡
        # 设玩家 A 以 p 概率选择策略1，玩家 B 以 q 概率选择策略1

        # 玩家 A 混合（玩家 B 纯策略）
        for b_col in range(2):
            p = NashEquilibrium._solve_mixed_a(payoff_a, payoff_b, b_col)
            if p is not None:
                # 验证均衡条件
                q = 1.0 if b_col == 0 else 0.0
                if NashEquilibrium._is_equilibrium(p, q, payoff_a, payoff_b):
                    equilibria.append(((p, 1-p), (q, 1-q)))

        # 玩家 B 混合（玩家 A 纯策略）
        for a_row in range(2):
            q = NashEquilibrium._solve_mixed_b(payoff_a, payoff_b, a_row)
            if q is not None:
                p = 1.0 if a_row == 0 else 0.0
                if NashEquilibrium._is_equilibrium(p, q, payoff_a, payoff_b):
                    equilibria.append(((p, 1-p), (q, 1-q)))

        # 3. 双方混合
        p, q = NashEquilibrium._solve_both_mixed(payoff_a, payoff_b)
        if p is not None and NashEquilibrium._is_equilibrium(p, q, payoff_a, payoff_b):
            equilibria.append(((p, 1-p), (q, 1-q)))

        return equilibria

    @staticmethod
    def _solve_mixed_a(payoff_a, payoff_b, b_col: int) -> Optional[float]:
        """玩家 A 混合，玩家 B 固定选择 b_col"""
        # 期望收益 = p * payoff[i][b_col] + (1-p) * payoff[1-i][b_col]
        # 均衡条件：两策略收益相等
        # p * A[0][j] + (1-p) * A[1][j] 相等
        a0 = payoff_a[0][b_col]
        a1 = payoff_a[1][b_col]
        if abs(a0 - a1) < 1e-9:
            return None  # 任意 p 都可以
        p = (a1 - a0) / (a1 - a0)  # 这会得到 0 或 1，不算混合
        return None

    @staticmethod
    def _solve_mixed_b(payoff_a, payoff_b, a_row: int) -> Optional[float]:
        """玩家 B 混合，玩家 A 固定选择 a_row"""
        b0 = payoff_b[a_row][0]
        b1 = payoff_b[a_row][1]
        if abs(b0 - b1) < 1e-9:
            return None
        return None

    @staticmethod
    def _solve_both_mixed(payoff_a, payoff_b) -> Tuple[Optional[float], Optional[float]]:
        """
        双方混合：在均衡处，每个玩家的策略对对方都是最优的
        E[payoff_A | A用p] = E[payoff_A | A用1-p] => p = ...
        """
        # 玩家 A 的混合概率 p：使 B 的两个策略无差异
        # B 选择策略1的期望 = p*B[0][0] + (1-p)*B[1][0]
        # B 选择策略2的期望 = p*B[0][1] + (1-p)*B[1][1]
        # 无差异 => 两者相等
        b00 = payoff_b[0][0]; b10 = payoff_b[1][0]
        b01 = payoff_b[0][1]; b11 = payoff_b[1][1]

        denom = (b00 - b10) - (b01 - b11)
        if abs(denom) < 1e-9:
            return None, None
        q = (b10 - b00) / denom  # B 选策略1的概率
        q = max(0, min(1, q))  # clamp

        # 玩家 B 的混合概率 q：使 A 的两个策略无差异
        a00 = payoff_a[0][0]; a01 = payoff_a[0][1]
        a10 = payoff_a[1][0]; a11 = payoff_a[1][1]

        denom2 = (a00 - a01) - (a10 - a11)
        if abs(denom2) < 1e-9:
            return None, None
        p = (a01 - a00) / denom2
        p = max(0, min(1, p))

        return p, q

    @staticmethod
    def _is_equilibrium(p: float, q: float, payoff_a, payoff_b) -> bool:
        """检验 (p, q) 是否为均衡"""
        tol = 1e-9
        # 玩家 A：比较策略1和策略2的期望收益
        e_a1 = q * payoff_a[0][0] + (1-q) * payoff_a[0][1]
        e_a2 = q * payoff_a[1][0] + (1-q) * payoff_a[1][1]
        # 若 p in (0,1)，则两个收益应相等（或非常接近）
        if 0 < p < 1 and abs(e_a1 - e_a2) > tol:
            return False
        # 若 p=1，则 e_a1 >= e_a2
        if abs(p - 1.0) < tol and e_a1 < e_a2 - tol:
            return False
        # 若 p=0，则 e_a2 >= e_a1
        if abs(p) < tol and e_a2 < e_a1 - tol:
            return False

        # 玩家 B：比较策略1和策略2的期望收益
        e_b1 = p * payoff_b[0][0] + (1-p) * payoff_b[1][0]
        e_b2 = p * payoff_b[0][1] + (1-p) * payoff_b[1][1]
        if 0 < q < 1 and abs(e_b1 - e_b2) > tol:
            return False
        if abs(q - 1.0) < tol and e_b1 < e_b2 - tol:
            return False
        if abs(q) < tol and e_b2 < e_b1 - tol:
            return False

        return True


# ============================ 测试代码 ============================
if __name__ == "__main__":
    print("=== 纳什均衡求解演示 ===")

    # 经典案例：囚徒困境（2x2 博弈）
    # 收益矩阵：行=玩家A（沉默/背叛），列=玩家B（沉默/背叛）
    # payoff_a = [
    #     [(-1,-1), (-3,0)],   # A沉默
    #     [(0,-3), (-2,-2)]   # A背叛
    # ]
    payoff_a = [[-1, -3], [0, -2]]
    payoff_b = [[-1, 0], [-3, -2]]

    print("囚徒困境收益矩阵：")
    print("          B沉默    B背叛")
    print(f"B沉默:  A=(-1,-1), A=(-3,0)")
    print(f"B背叛:  A=(0,-3),  A=(-2,-2)")
    print()

    eqs = NashEquilibrium.solve_2x2(payoff_a, payoff_b)
    print(f"纳什均衡数量: {len(eqs)}")
    for i, (probs_a, probs_b) in enumerate(eqs):
        print(f"均衡 {i+1}: A策略=({probs_a[0]:.2f}, {probs_a[1]:.2f}), B策略=({probs_b[0]:.2f}, {probs_b[1]:.2f})")
        p_a, q_b = probs_a[0], probs_b[0]
        expected_a = q_b * payoff_a[0][0] + (1-q_b) * payoff_a[0][1]
        print(f"  A期望收益: {expected_a:.2f}")

    # 验证：纯策略背叛是唯一均衡
    if eqs:
        pure = all(abs(p[0] - p[1]) > 0.5 for p in eqs[0])
        print(f"存在纯策略均衡: {'是' if pure else '否'}")

    print("\n=== 另一个博弈：石头剪刀布 ===")
    # 石头剪刀布没有纯策略均衡，只有混合均衡（各1/3）
    payoff_a_rock = [[0, -1, 1], [1, 0, -1], [-1, 1, 0]]
    payoff_b_rock = [[0, 1, -1], [-1, 0, 1], [1, -1, 0]]

    # 简化：只分析 2x2 子博弈（略过完整分析）
    print("石头剪刀布每个策略出现概率 1/3")
    print("（完整求解需要 Lemke-Howson 算法，3x3 以上复杂度较高）")
    print("\n✅ 纳什均衡是博弈论的核心概念，用于分析稳定策略")
