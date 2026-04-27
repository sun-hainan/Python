# -*- coding: utf-8 -*-
"""
算法实现：运筹学 / simplex

本文件实现 simplex 相关的算法功能。
"""

import numpy as np


def simplex(A, b, c, max_iter=1000):
    """
    原始单纯形法（两阶段法）

    Parameters
    ----------
    A : np.ndarray
        约束矩阵 (m x n)
    b : np.ndarray
        RHS 向量 (m,)
    c : np.ndarray
        目标函数系数 (n,)

    Returns
    -------
    dict
        最优解、最优值、迭代信息
    """
    m, n = A.shape

    # 转换为标准形式：Ax = b, x >= 0
    # 引入松弛变量
    # max c'x + 0's
    # s.t. [A, I] * [x; s] = b
    #      [x; s] >= 0

    # 增广矩阵 [A | I | b]
    A_aug = np.hstack([A, np.eye(m)])
    c_aug = np.concatenate([c, np.zeros(m)])

    # 相数跟踪：原始变量是 1:n, 松弛变量是 n:n+m
    basis = list(range(n, n + m))  # 初始基：松弛变量

    # 求解
    for iteration in range(max_iter):
        # 计算检验数（Reduced Cost）
        # 对于基变量，检验数为 0
        # 对于非基变量，检验数 = c_j - c_B * B^(-1) * A_j

        # 计算 B^(-1)
        try:
            B_inv = np.linalg.inv(A_aug[:, basis])
        except np.linalg.LinAlgError:
            return {'status': 'infeasible', 'iterations': iteration}

        # 计算对偶变量 π = c_B * B^(-1)
        c_B = c_aug[basis]
        pi = c_B @ B_inv

        # 检验数
        reduced_costs = c_aug - pi @ A_aug

        # 检查最优性（所有检验数 <= 0 for max problem）
        if np.all(reduced_costs <= 1e-10):
            # 最优解
            x_aug = np.zeros(n + m)
            x_aug[basis] = B_inv @ b
            x = x_aug[:n]
            obj_value = c @ x
            return {
                'status': 'optimal',
                'x': x,
                'obj_value': obj_value,
                'basis': basis,
                'iterations': iteration
            }

        # 入基：选择最正的检验数
        entering = np.argmax(reduced_costs)
        entering_col = A_aug[:, entering]

        # 出基：最小比率测试
        # min { b_i / a_ij | a_ij > 0 }
        ratios = np.full(m, np.inf)
        mask = entering_col > 1e-10
        ratios[mask] = b[mask] / entering_col[mask]

        if np.all(np.isinf(ratios)):
            return {'status': 'unbounded', 'iterations': iteration}

        leaving = np.argmin(ratios)

        # 换基
        basis[leaving] = entering

    return {'status': 'max_iterations', 'iterations': max_iter}


def simplex_tableau(c, A, b, basis, max_iter=1000):
    """
    表格形式的单纯形法（更直观）
    """
    m, n = A.shape

    # 构建单纯形表
    # [B^(-1)*A | B^(-1)*b]
    # 目标行：c - c_B*B^(-1)*A

    B = A[:, basis]
    B_inv = np.linalg.inv(B)

    for iteration in range(max_iter):
        # 典式
        B_inv_A = B_inv @ A
        b_bar = B_inv @ b

        # 目标函数系数
        c_B = c[basis]
        reduced_costs = c - c_B @ B_inv_A

        # 最优性检验
        if np.all(reduced_costs <= 1e-10):
            x = np.zeros(n)
            x[basis] = b_bar
            return {
                'status': 'optimal',
                'x': x,
                'obj_value': c @ x,
                'iterations': iteration
            }

        # 入基
        entering = np.argmax(reduced_costs)

        # 出基
        B_inv_A_j = B_inv_A[:, entering]
        if np.all(B_inv_A_j <= 0):
            return {'status': 'unbounded'}

        ratios = b_bar / B_inv_A_j
        ratios[B_inv_A_j <= 0] = np.inf
        leaving = np.argmin(ratios)

        # 枢轴操作
        pivot_row = leaving
        pivot_col = entering
        pivot_element = B_inv_A[pivot_row, pivot_col]

        # 更新逆矩阵（高斯-乔丹）
        B_inv[pivot_row, :] /= pivot_element
        for i in range(m):
            if i != pivot_row:
                factor = B_inv_A[i, pivot_col]
                B_inv[i, :] -= factor * B_inv[pivot_row, :]

        # 更新基
        basis[leaving] = entering

    return {'status': 'max_iterations'}


def dual_simplex(A, b, c, max_iter=1000):
    """
    对偶单纯形法

    适用于：
    - 初始基不可行但满足对偶可行性
    - 添加约束后重新优化
    - 目标函数有特殊结构
    """
    m, n = A.shape

    # 初始基：使用人工变量构造
    A_aug = np.hstack([A, np.eye(m)])
    c_aug = np.concatenate([c, np.zeros(m)])

    basis = list(range(n, n + m))

    for iteration in range(max_iter):
        B_inv = np.linalg.inv(A_aug[:, basis])
        b_bar = B_inv @ b

        # 检查原始可行性（所有 b_bar >= 0）
        if np.all(b_bar >= -1e-10):
            x_aug = np.zeros(n + m)
            x_aug[basis] = b_bar
            x = x_aug[:n]
            return {
                'status': 'optimal',
                'x': x,
                'obj_value': c @ x,
                'iterations': iteration
            }

        # 出基：最负的 b_bar
        leaving = np.argmin(b_bar)
        if b_bar[leaving] >= -1e-10:
            x_aug = np.zeros(n + m)
            x_aug[basis] = b_bar
            x = x_aug[:n]
            return {
                'status': 'optimal',
                'x': x,
                'obj_value': c @ x,
                'iterations': iteration
            }

        # 对偶可行方向
        # 选择最小化检验数增长的入基
        c_B = c_aug[basis]
        pi = c_B @ B_inv

        # 计算方向
        A_bar = B_inv @ A_aug

        # 选择入基：使目标函数下降最多
        best_enter = -1
        best_ratio = np.inf

        for j in range(n + m):
            if j in basis:
                continue

            a_j = A_bar[:, j]
            rc_j = c_aug[j] - pi @ A_aug[:, j]

            if a_j[leaving] < -1e-10:
                ratio = rc_j / a_j[leaving]
                if ratio < best_ratio:
                    best_ratio = ratio
                    best_enter = j

        if best_enter == -1:
            return {'status': 'unbounded'}

        # 枢轴
        pivot_element = A_bar[leaving, best_enter]
        basis[leaving] = best_enter

    return {'status': 'max_iterations'}


def interior_point(A, b, c, max_iter=100, tol=1e-8):
    """
    内点法（障碍函数法）
    使用对数障碍函数处理非负约束

    中心路径：x(μ) = argmin c'x - μ * Σln(x_i)
              s.t. Ax = b

    收敛较单纯形法慢，但多项式时间
    """
    m, n = A.shape

    # 初始点（严格可行）
    x = np.ones(n)
    y = np.zeros(m)
    s = np.ones(n)

    for iteration in range(max_iter):
        # 残差
        rx = A @ x - b
        ry = A.T @ y + s - c
        rz = x * s

        # 组合残差
        norm_rx = np.linalg.norm(rx)
        norm_ry = np.linalg.norm(ry)
        norm_rz = np.linalg.norm(rz)

        if norm_rx < tol and norm_ry < tol and norm_rz < tol:
            return {
                'status': 'optimal',
                'x': x,
                'obj_value': c @ x,
                'iterations': iteration
            }

        # 简化的牛顿步
        # 实际实现需要求解KKT系统
        # 这里用简化的梯度下降

        # 障碍参数
        mu = x @ s / n

        # 方向（简化）
        grad = c - A.T @ y - s
        x = x - 0.1 * grad.clip(min=0.1)

        # 更新对偶变量
        y = y + 0.1 * rx

        # 修正保持可行性
        x = np.maximum(x, 1e-8)
        s = np.maximum(s, 1e-8)

    return {'status': 'max_iterations', 'x': x, 'obj_value': c @ x}


if __name__ == "__main__":
    print("=" * 60)
    print("单纯形法求解线性规划")
    print("=" * 60)

    # 示例1：标准 LP
    # max 2x1 + 3x2
    # s.t. x1 + 2x2 <= 6
    #      2x1 + x2 <= 8
    #      x1, x2 >= 0

    A = np.array([[1, 2], [2, 1]], dtype=float)
    b = np.array([6, 8], dtype=float)
    c = np.array([2, 3], dtype=float)

    print("\n问题:")
    print("max 2x1 + 3x2")
    print("s.t. x1 + 2x2 <= 6")
    print("      2x1 + x2 <= 8")
    print("      x1, x2 >= 0")

    result = simplex(A, b, c)

    print(f"\n状态: {result['status']}")
    if result['status'] == 'optimal':
        print(f"最优解: x1 = {result['x'][0]:.4f}, x2 = {result['x'][1]:.4f}")
        print(f"最优值: {result['obj_value']:.4f}")
        print(f"迭代次数: {result['iterations']}")

    # 示例2：需要人工变量的情况
    # max 3x1 + 2x2
    # s.t. x1 + x2 = 4
    #      2x1 + x2 <= 6
    #      x1, x2 >= 0

    print("\n" + "-" * 40)
    print("\n问题2:")
    print("max 3x1 + 2x2")
    print("s.t. x1 + x2 = 4")
    print("      2x1 + x2 <= 6")
    print("      x1, x2 >= 0")

    # 使用大M法或两阶段法
    # 简化：直接使用 scipy.optimize
    from scipy.optimize import linprog

    A_ub = np.array([[2, 1]])
    b_ub = np.array([6])
    A_eq = np.array([[1, 1]])
    b_eq = np.array([4])

    res = linprog(-c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, method='highs')

    print(f"最优解: x1 = {res.x[0]:.4f}, x2 = {res.x[1]:.4f}")
    print(f"最优值: {-res.fun:.4f}")

    # 示例3：对偶单纯形法
    print("\n" + "-" * 40)
    print("\n对偶单纯形法演示:")
    print("min 2x1 + 3x2 + 4x3")
    print("s.t. x1 + x2 + x3 >= 6")
    print("      2x1 + x2 >= 4")
    print("      x1, x2, x3 >= 0")

    # 转换为对偶形式演示
    # 原始 min = 对偶 max
    # min c'x
    # s.t. Ax >= b
    #  =>
    # max b'y
    # s.t. A'y <= c
    #      y >= 0

    A3 = np.array([[1, 1, 1], [2, 1, 0]], dtype=float)
    b3 = np.array([6, 4], dtype=float)
    c3 = np.array([2, 3, 4], dtype=float)

    # 求对偶
    A_dual = A3.T
    c_dual = b3
    b_dual = c3

    result_dual = simplex(A_dual, b_dual, c_dual)

    if result_dual['status'] == 'optimal':
        print(f"\n对偶问题最优值: {result_dual['obj_value']:.4f}")
        print(f"（原始问题的最优值也应为 {result_dual['obj_value']:.4f}）")
