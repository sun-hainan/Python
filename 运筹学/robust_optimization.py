# -*- coding: utf-8 -*-
"""
算法实现：运筹学 / robust_optimization

本文件实现 robust_optimization 相关的算法功能。
"""

import numpy as np


def robust_linear_program(c, A, b, u_bounds, eps=1e-9):
    """
    箱式不确定集的鲁棒 LP

    min c'x
    s.t. Σ_j a_ij * x_j <= b_i, ∀ u ∈ [u_i - ũ, u_i + ũ]

    对于每个约束 i，不确定参数只出现在 a_ij 中

    转换：
    Σ_j ā_ij * x_j + Σ_j |x_j| * tilde_ij <= b_i
    其中 tilde_ij 是波动范围
    """
    n = len(c)

    # 拆分标称值和不确定范围
    if isinstance(u_bounds, tuple):
        # u_bounds = (u_minus, u_plus)
        u_minus, u_plus = u_bounds
    else:
        # 假设对称
        u_minus = A - u_bounds
        u_plus = A + u_bounds

    # 计算标称值和范围
    A_nom = (u_minus + u_plus) / 2
    A_range = (u_plus - u_minus) / 2

    # 鲁棒约束转换
    # 约束变为：Σ_j ā_ij * x_j + Σ_j |x_j| * tilde_ij <= b_i
    A_robust = A_nom.copy()
    b_robust = b - np.sum(A_range * np.abs(A_nom), axis=1)

    # 求解确定性等价问题
    from scipy.optimize import linprog

    res = linprog(c, A_ub=A_robust, b_ub=b_robust, bounds=(0, None))

    return {
        'status': 'optimal' if res.success else res.message,
        'x': res.x if res.success else None,
        'obj_value': res.fun if res.success else None,
        'A_nominal': A_nom,
        'A_range': A_range
    }


def robust_optimization_iterative(c, A, b, uncertainty_sets, max_iter=10):
    """
    迭代鲁棒优化

    交替求解：
    1. 给定 x，求最坏情况参数
    2. 给定最坏情况参数，求解优化问题
    """
    from scipy.optimize import linprog

    n = len(c)

    # 初始化
    x = np.zeros(n)

    for iteration in range(max_iter):
        # 步骤 1：给定 x，求最坏情况参数
        worst_A = np.zeros_like(A)
        for i in range(len(b)):
            for j in range(n):
                # 最坏情况：a_ij 取使得约束最紧的值
                if x[j] > 0:
                    worst_A[i, j] = A[i, j] + uncertainty_sets[i, j]
                else:
                    worst_A[i, j] = A[i, j] - uncertainty_sets[i, j]

        # 步骤 2：求解优化问题
        res = linprog(c, A_ub=worst_A, b_ub=b, bounds=(0, None))

        if not res.success:
            break

        # 检查收敛
        if np.max(np.abs(res.x - x)) < 1e-6:
            break

        x = res.x

    return {
        'x': x,
        'obj_value': res.fun if res.success else None,
        'iterations': iteration + 1
    }


def budgeted_uncertainty_set(c, A, b, gamma):
    """
    预算不确定集

    |{j : ũ_ij ≠ 0}| <= Γ_i（每个约束最多 Γ_i 个不确定参数）

    方法：使用硫磺量不确定集
    """
    from scipy.optimize import linprog

    m, n = A.shape

    # 决策相关不确定集
    # 对于约束 i，最坏情况是最大的 Γ_i 个 x_j * ũ_ij

    # 简化为迭代
    x = np.zeros(n)
    worst_case = A.copy()

    for iteration in range(10):
        # 求最坏情况参数
        for i in range(m):
            # 计算每个系数的贡献
            contributions = np.abs(x) * uncertainty_sets[i, :] if 'uncertainty_sets' in dir() else np.zeros(n)

            # 取最大的 Γ_i 个
            sorted_idx = np.argsort(-contributions)
            worst_case[i, :] = A[i, :].copy()
            for j in sorted_idx[:gamma]:
                if x[j] > 0:
                    worst_case[i, j] = A[i, j] + uncertainty_sets[i, j]
                else:
                    worst_case[i, j] = A[i, j] - uncertainty_sets[i, j]

        # 求解
        res = linprog(c, A_ub=worst_case, b_ub=b, bounds=(0, None))

        if not res.success:
            break

        if np.max(np.abs(res.x - x)) < 1e-6:
            x = res.x
            break

        x = res.x

    return {'x': x, 'obj_value': res.fun if res.success else None}


def ellipsoidal_uncertainty(A, b, Sigma):
    """
    椭球不确定集

    u ∈ {ū + Σ^(1/2) * z : ||z||_2 <= Ω}

    对于线性约束，可以转化为二阶锥约束
    """
    pass


def robust_optimization_cvx(c, A, b, u_nominal, u_uncertainty):
    """
    使用 CVX 风格的鲁棒优化

    假设：
    - 不确定参数 ũ = u_nominal + delta
    - ||delta||_∞ <= epsilon（箱式）
    """
    # 确定性等价
    # max_{||delta||_∞ <= eps} a'x + delta'b'x

    # 使用 CVXPY 或类似工具更方便
    # 这里用简化版本

    return {'status': 'requires_cvxpy'}


if __name__ == "__main__":
    print("=" * 60)
    print("鲁棒优化（箱式不确定集）")
    print("=" * 60)

    # 示例：投资组合优化
    # min -μ'x  (最大化收益)
    # s.t. Σ x_j = 1
    #      Σ |x_j| * σ_j <= ξ  (风险约束)

    # 收益率 μ 有不确定性
    mu = np.array([0.08, 0.10, 0.12, 0.06])  # 标称收益率
    sigma = np.array([0.02, 0.03, 0.04, 0.01])  # 不确定范围

    n = len(mu)

    print("\n投资组合问题:")
    print(f"资产数量: {n}")
    print(f"标称收益率: {mu.tolist()}")
    print(f"收益率不确定范围: ±{sigma.tolist()}")

    # 鲁棒优化
    # max min_j (μ_j - σ_j) * x_j
    # 等价于 min -min_j (μ_j - σ_j) * x_j
    # = min -min_j (μ_j - σ_j) * x_j

    # 简化：使用最坏情况收益率
    worst_case_return = mu - sigma

    print(f"\n最坏情况收益率: {worst_case_return.tolist()}")

    # 投资组合权重
    from scipy.optimize import linprog

    # 最大化收益 = 最小化负收益
    c = -mu  # 最小化

    # 等式约束：权重和 = 1
    A_eq = np.ones((1, n))
    b_eq = np.array([1])

    # 箱式不确定集下的鲁棒约束
    # 对于 max 问题，鲁棒等价于 min_j (μ_j - σ_j) >= R
    # 即 -Σ x_j * (μ_j - σ_j) <= -R

    # 简化为使用最坏情况
    c_robust = -worst_case_return

    res = linprog(c_robust, A_eq=A_eq, b_eq=b_eq, bounds=(0, None))

    if res.success:
        print(f"\n鲁棒最优配置:")
        for i, w in enumerate(res.x):
            print(f"  资产 {i+1}: {w:.4f} ({w*100:.2f}%)")
        print(f"最坏情况收益: {-res.fun:.4f}")

    # 对比标称最优
    print("\n--- 标称最优（不考虑不确定性）---")
    res_nom = linprog(-mu, A_eq=A_eq, b_eq=b_eq, bounds=(0, None))

    if res_nom.success:
        print(f"配置:")
        for i, w in enumerate(res_nom.x):
            print(f"  资产 {i+1}: {w:.4f} ({w*100:.2f}%)")
        print(f"期望收益: {mu @ res_nom.x:.4f}")
        print(f"最坏情况收益: {worst_case_return @ res_nom.x:.4f}")

    # 风险约束示例
    print("\n--- 带风险约束的鲁棒优化 ---")
    # max min_j μ_j * x_j
    # s.t. Σ x_j = 1
    #      x_j >= 0

    # 转换为 LP
    # min t
    # s.t. μ_j * x_j >= t, ∀j
    #      Σ x_j = 1

    # 扩展变量 (x, t)
    c_ext = np.concatenate([np.zeros(n), [1]])  # min t

    # 约束：μ_j * x_j >= t => -μ_j * x_j + t <= 0
    A_ub_ext = np.zeros((n, n + 1))
    for j in range(n):
        A_ub_ext[j, j] = -worst_case_return[j]  # 使用最坏情况
        A_ub_ext[j, n] = 1

    b_ub_ext = np.zeros(n)

    A_eq_ext = np.zeros((1, n + 1))
    A_eq_ext[0, :n] = 1
    b_eq_ext = np.array([1])

    res_robust = linprog(c_ext, A_ub=A_ub_ext, b_ub=b_ub_ext,
                         A_eq=A_eq_ext, b_eq=b_eq_ext,
                         bounds=[(0, None)] * (n + 1))

    if res_robust.success:
        print(f"最差收益下界: {res_robust.x[n]:.4f}")
        print(f"配置:")
        for i, w in enumerate(res_robust.x[:n]):
            print(f"  资产 {i+1}: {w:.4f}")
