# -*- coding: utf-8 -*-
"""
算法实现：运筹学 / cutting_planes

本文件实现 cutting_planes 相关的算法功能。
"""

import numpy as np
from scipy.optimize import linprog


def gomory_cut(A, b, c, integer_indices, max_cuts=100, max_iter=500, tol=1e-6):
    """
    Gomory 割平面法

    步骤：
    1. 求解 LP 松弛
    2. 若最优解为整数，返回
    3. 选择一个分数基变量
    4. 构造 Gomory 割
    5. 添加割平面，重新求解
    6. 重复

    Parameters
    ----------
    integer_indices : list
        整数变量的索引
    """
    m, n = A.shape

    # 增广矩阵（添加松弛变量）
    A_aug = np.hstack([A, np.eye(m)])
    c_aug = np.concatenate([c, np.zeros(m)])
    n_vars = n + m

    # 基变量初始：后 m 个（松弛变量）
    basis = list(range(n, n_vars))

    iteration = 0

    while iteration < max_iter:
        iteration += 1

        # 求解当前 LP
        # 使用单纯形表
        try:
            B = A_aug[:, basis]
            B_inv = np.linalg.inv(B)
            x_B = B_inv @ b
        except:
            return {'status': 'infeasible'}

        # 计算检验数
        c_B = c_aug[basis]
        pi = c_B @ B_inv
        reduced_costs = c_aug - pi @ A_aug

        # 检验数应该全 <= 0（最小化问题）
        if np.all(reduced_costs >= -1e-10):
            # 最优
            x = np.zeros(n_vars)
            x[basis] = x_B

            # 检查整数性
            all_int = True
            for i in integer_indices:
                if abs(x[i] - round(x[i])) > tol:
                    all_int = False
                    break

            if all_int:
                return {
                    'status': 'optimal',
                    'x': x[:n],
                    'obj_value': c @ x[:n],
                    'iterations': iteration,
                    'n_cuts': iteration - 1
                }

            # 找到分数基变量
            frac_vars = []
            for idx, bi in enumerate(basis):
                if bi in integer_indices:
                    val = x_B[idx]
                    frac = val - np.floor(val)
                    if frac > tol and frac < 1 - tol:
                        frac_vars.append((idx, bi, val, frac))

            if not frac_vars:
                # 所有基整数
                return {
                    'status': 'optimal',
                    'x': x[:n],
                    'obj_value': c @ x[:n],
                    'iterations': iteration
                }

            # 选择分数最大的基变量
            _, var_idx, val, _ = max(frac_vars, key=lambda v: v[3])

            # 构造 Gomory 割
            # 从行 var_idx 的方程提取
            # x_B[var_idx] = Σ_ij * x_j

            # 使用 B_inv * A_aug 获得系数
            row = B_inv[var_idx, :] @ A_aug  # 系数行

            # Gomory 割: Σ_j (f_ij) * x_j >= f_i
            # 其中 f_ij = row_j - floor(row_j), f_i = val - floor(val)

            cut_row = np.zeros(n_vars)
            cut_rhs = 0

            for j in range(n_vars):
                coeff = row[j]
                f_coeff = coeff - np.floor(coeff)
                cut_row[j] = f_coeff

            f_rhs = val - np.floor(val)
            cut_rhs = f_rhs

            # 添加割平面
            # cut_row * x >= cut_rhs
            # 转换为 <= 形式
            A_aug = np.vstack([A_aug, -cut_row])
            b = np.append(b, -cut_rhs)

            # 新行不是基变量
            basis.append(n_vars)
            n_vars += 1

        # 检查割的数量
        if iteration > max_cuts + 10:
            return {'status': 'max_cuts'}

    return {'status': 'max_iterations'}


def gomory_mixed_integer(A, b, c, integer_indices, max_iter=100):
    """
    混合整数 Gomory 割

    用于部分变量为整数的情况
    """
    m, n = A.shape

    # 简化实现：使用分支定界代替
    from scipy.optimize import linprog

    # 初始 LP 松弛
    res = linprog(c, A_ub=A, b_ub=b, bounds=[(0, None)] * n)

    if not res.success:
        return {'status': 'infeasible'}

    x = res.x

    # 检查整数性
    frac_vars = [i for i in integer_indices if abs(x[i] - round(x[i])) > 1e-6]

    if not frac_vars:
        return {'status': 'optimal', 'x': x, 'obj_value': res.fun}

    # 简化为分支定界
    return {'status': 'branch_needed'}


def lift_and_project(A, b, c, integer_indices):
    """
    Lift-and-Project 割平面

    针对 0-1 变量的割平面
    """
    pass


def mixed_integer_rounding(A, b, c, integer_indices):
    """
    混合整数舍入启发式

    从 LP 解出发，舍入到最近的整数
    """
    from scipy.optimize import linprog

    res = linprog(c, A_ub=A, b_ub=b, bounds=[(0, None)] * len(c))

    if not res.success:
        return None

    x_lp = res.x

    # 舍入
    x_int = np.zeros(len(c))
    for i in integer_indices:
        x_int[i] = round(x_lp[i])

    # 检查可行性
    if np.all(A @ x_int <= b + 1e-6):
        return x_int
    return None


def Chvatal_Gomory_rank(A, b, k=1):
    """
    Chvatal-Gomory 秩

    对约束矩阵应用 k 轮 CG 切割得到秩 k 不等式
    """
    m = len(b)

    # 线性组合系数
    for iteration in range(k):
        # 选择组合系数
        # 简化：使用平均
        coeffs = np.ones(m) / m

        # 组合
        A_comb = coeffs @ A
        b_comb = coeffs @ b

        # 向下取整
        A_cg = np.floor(A_comb)
        b_cg = np.floor(b_comb)

    return A_cg, b_cg


if __name__ == "__main__":
    print("=" * 60)
    print("割平面法 (Gomory 切割)")
    print("=" * 60)

    # 示例 1: 整数线性规划
    # max 3x1 + 2x2
    # s.t. 2x1 + x2 <= 6
    #      x1 + 2x2 <= 8
    #      x1, x2 >= 0, 整数

    A = np.array([[2, 1], [1, 2]], dtype=float)
    b = np.array([6, 8], dtype=float)
    c = np.array([-3, -2], dtype=float)  # max 转 min
    integer_indices = [0, 1]

    print("\n问题:")
    print("max 3x1 + 2x2")
    print("s.t. 2x1 + x2 <= 6")
    print("      x1 + 2x2 <= 8")
    print("      x1, x2 >= 0, 整数")

    # Gomory 割
    result = gomory_cut(A, b, c, integer_indices)

    if result['status'] == 'optimal':
        print(f"\n最优解: x1 = {result['x'][0]:.0f}, x2 = {result['x'][1]:.0f}")
        print(f"最优值: {-result['obj_value']:.0f}")
        print(f"迭代次数: {result['iterations']}")
        print(f"添加割数: {result.get('n_cuts', 'N/A')}")

    # LP 松弛比较
    print("\n--- LP 松弛比较 ---")
    res_lp = linprog(c, A_ub=A, b_ub=b, bounds=(0, None))
    print(f"LP 松弛解: x1 = {res_lp.x[0]:.4f}, x2 = {res_lp.x[1]:.4f}")
    print(f"LP 松弛值: {-res_lp.fun:.4f}")

    # 示例 2: 更大的问题
    print("\n" + "-" * 40)
    print("\n示例 2:")

    A2 = np.array([
        [3, 2, 1, 4],
        [1, 4, 2, 3],
        [2, 1, 5, 2]
    ], dtype=float)
    b2 = np.array([10, 8, 7], dtype=float)
    c2 = np.array([-5, -3, -4, -6], dtype=float)
    integer_indices2 = [0, 1, 2, 3]

    result2 = gomory_cut(A2, b2, c2, integer_indices2, max_iter=200)

    if result2['status'] == 'optimal':
        print(f"最优解: {result2['x'].astype(int).tolist()}")
        print(f"最优值: {-result2['obj_value']:.0f}")
        print(f"迭代次数: {result2['iterations']}")

    # 混合整数舍入启发式
    print("\n--- 混合整数舍入启发式 ---")
    x_heur = mixed_integer_rounding(A, b, c, integer_indices)
    if x_heur is not None:
        print(f"舍入可行解: {x_heur.astype(int).tolist()}")
        print(f"目标值: {-c @ x_heur:.0f}")
    else:
        print("舍入解不可行")

    # Chvatal-Gomory 秩
    print("\n--- Chvatal-Gomory 秩 1 切割 ---")
    A_cg, b_cg = Chvatal_Gomory_rank(A, b, k=1)
    print(f"原始约束: {A[0]} <= {b[0]}")
    print(f"CG 秩 1: {A_cg} <= {b_cg}")
