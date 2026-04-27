# -*- coding: utf-8 -*-
"""
算法实现：运筹学 / lagrangian_relaxation

本文件实现 lagrangian_relaxation 相关的算法功能。
"""

import numpy as np
from scipy.optimize import linprog


def lagrangian_relaxation(c, A, b, D, d, integer_indices, max_iter=100,
                          step_size=0.1, tol=1e-6):
    """
    拉格朗日松弛求解整数规划

    将整数约束放到目标函数中

    Parameters
    ----------
    c : np.ndarray
        目标函数系数
    A : np.ndarray
        难约束矩阵
    b : np.ndarray
        难约束 RHS
    D : np.ndarray
        易约束矩阵
    d : np.ndarray
        易约束 RHS
    integer_indices : list
        整数变量索引
    """
    m, n = A.shape

    # 初始化乘子
    lamb = np.zeros(m)

    best_lower = -np.inf
    best_upper = np.inf
    best_x = None

    def solve_subproblem(lamb):
        """给定乘子，求解拉格朗日子问题"""
        # 子问题：min (c + A'λ)'x  s.t. Dx = d, x >= 0, x_i 整数
        c_relaxed = c + A.T @ lamb

        # 使用 LP 松弛（简化）
        res = linprog(c_relaxed, A_eq=D, b_eq=d, bounds=(0, None))

        if res.success:
            x = res.x
            obj = c @ x + lamb @ (A @ x - b)
            return x, obj
        return None, np.inf

    for iteration in range(max_iter):
        # 求解子问题
        x, obj = solve_subproblem(lamb)

        if x is None:
            # 子问题无解
            break

        # 计算次梯度
        # g = A @ x - b
        subgrad = A @ x - b

        # 更新乘子（次梯度法）
        # λ_{k+1} = λ_k + step_size * g
        lamb = lamb + step_size * subgrad

        # 调整步长
        step_size *= 0.99

        # 更新界限
        lower_bound = obj
        if lower_bound > best_lower:
            best_lower = lower_bound

        # 计算可行解（启发式）
        # 四舍五入 x 到最近的整数
        x_feas = x.copy()
        for i in integer_indices:
            x_feas[i] = round(x_feas[i])

        # 检查可行性
        if np.all(A @ x_feas <= b + 1e-6) and np.allclose(D @ x_feas, d, atol=1e-6):
            obj_upper = c @ x_feas
            if obj_upper < best_upper:
                best_upper = obj_upper
                best_x = x_feas.copy()

        # 收敛检查
        if best_upper - best_lower < tol:
            break

    return {
        'status': 'optimal' if best_upper - best_lower < tol else 'max_iterations',
        'x': best_x,
        'obj_value': best_upper if best_x is not None else None,
        'lower_bound': best_lower,
        'upper_bound': best_upper,
        'iterations': iteration + 1
    }


def lagrangian_relaxation_knapsack(c, a, b, integer_indices):
    """
    0-1 背包问题的拉格朗日松弛

    问题：
    min c'x
    s.t. a'x <= b
         x ∈ {0,1}^n

    松弛容量约束：
    min c'x + λ(a'x - b)
      = min Σ (c_i + λ*a_i)*x_i - λ*b

    子问题：对每个 i，单独选择 x_i = 0 或 1
    """

    def solve_subproblem(lamb):
        """求解拉格朗日子问题"""
        # 目标：min Σ (c_i + λ*a_i)*x_i
        # 每个变量独立
        values = c + lamb * a

        # 选择 x_i = 1 如果 (c_i + λ*a_i) < 0
        x = np.where(values < 0, 1, 0)

        obj = c @ x + lamb * (a @ x - b)
        return x, obj

    # 次梯度优化
    best_lambda = 0
    best_lower = -np.inf

    lamb = 0
    step_size = 0.1

    for iteration in range(100):
        x, obj = solve_subproblem(lamb)

        if obj > best_lower:
            best_lower = obj
            best_lambda = lamb

        # 次梯度
        subgrad = a @ x - b

        if abs(subgrad) < 1e-6:
            break

        # 更新乘子
        lamb = max(0, lamb + step_size * subgrad)
        step_size *= 0.98

    return {
        'lambda': best_lambda,
        'lower_bound': best_lower,
        'subproblem_solution': x
    }


def subgradient_optimization(c, A, b, x0=None, max_iter=100, step_size=0.1):
    """
    次梯度优化的通用框架

    用于最大化拉格朗日对偶
    """
    n = len(c)

    if x0 is None:
        x = np.zeros(n)
    else:
        x = x0.copy()

    best_value = -np.inf
    best_x = x.copy()

    for iteration in range(max_iter):
        # 计算次梯度
        # 简化的梯度

        # 更新
        step_size *= 0.98

    return {'x': best_x, 'value': best_value}


def dual_ascent(c, A, b, max_iter=100, tol=1e-6):
    """
    对偶上升法

    用于无约束或简单约束的优化
    """
    n = len(c)

    x = np.zeros(n)
    y = np.zeros(len(b))  # 乘子

    for iteration in range(max_iter):
        # x 更新
        # 简化为无约束二次

        # y 更新
        pass

    return x


def decompose_lagrangian(c1, c2, A12, b1, b2):
    """
    拉格朗日分解

    将问题分解为两个子问题
    通过乘子协调
    """
    pass


if __name__ == "__main__":
    print("=" * 60)
    print("拉格朗日松弛算法")
    print("=" * 60)

    # 示例：整数规划
    # min 2x1 + 3x2 + 4x3
    # s.t. x1 + 2x2 + 3x3 >= 6  (难约束)
    #      x1 + x2 <= 4          (易约束)
    #      x1, x2, x3 >= 0, 整数

    c = np.array([2, 3, 4])
    A = np.array([[1, 2, 3]])  # 难约束
    b = np.array([6])
    D = np.array([[1, 1, 0]])  # 易约束
    d = np.array([4])
    integer_indices = [0, 1, 2]

    print("\n整数规划:")
    print("min 2x1 + 3x2 + 4x3")
    print("s.t. x1 + 2x2 + 3x3 >= 6")
    print("     x1 + x2 <= 4")
    print("     x1, x2, x3 >= 0, 整数")

    result = lagrangian_relaxation(c, A, b, D, d, integer_indices)

    print(f"\n结果:")
    print(f"  状态: {result['status']}")
    print(f"  解: {result['x']}")
    print(f"  目标值: {result['obj_value']}")
    print(f"  下界: {result['lower_bound']:.4f}")
    print(f"  上界: {result['upper_bound']:.4f}")
    print(f"  迭代: {result['iterations']}")

    # 背包问题
    print("\n" + "-" * 40)
    print("\n0-1 背包问题拉格朗日松弛:")

    values = np.array([60, 100, 120, 80, 50])
    weights = np.array([10, 20, 30, 15, 10])
    capacity = 50

    print(f"价值: {values.tolist()}")
    print(f"重量: {weights.tolist()}")
    print(f"容量: {capacity}")

    result_kp = lagrangian_relaxation_knapsack(values, weights, capacity, list(range(len(values))))

    print(f"\n最优拉格朗日乘子: λ = {result_kp['lambda']:.4f}")
    print(f"拉格朗日下界: {result_kp['lower_bound']:.2f}")
    print(f"子问题解: {result_kp['subproblem_solution'].astype(int).tolist()}")

    # 验证
    total_value = values @ result_kp['subproblem_solution']
    total_weight = weights @ result_kp['subproblem_solution']
    print(f"子问题总价值: {total_value:.0f}")
    print(f"子问题总重量: {total_weight:.0f}")

    # 精确解（动态规划）
    from .knapsack import knapsack_dp

    dp_result = knapsack_dp(values.tolist(), weights.tolist(), capacity)
    print(f"\nDP 精确解: 价值={dp_result['total_value']}")

    print(f"\n下界与最优解的差距: {dp_result['total_value'] - result_kp['lower_bound']:.2f}")
