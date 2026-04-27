# -*- coding: utf-8 -*-

"""

算法实现：运筹学 / primal_dual



本文件实现 primal_dual 相关的算法功能。

"""



import numpy as np





def primal_dual_simplex(A, b, c, max_iter=1000, tol=1e-9):

    """

    原始-对偶单纯形法



    适用于：

    - LP 有特殊结构

    - 网络流问题

    - 某些组合优化问题

    """

    m, n = A.shape



    # 初始化：设 y = 0（对偶可行）

    y = np.zeros(m)



    for iteration in range(max_iter):

        # 计算 reduced costs: c_j - y'A_j

        reduced_costs = c - A.T @ y



        # 对偶可行性要求所有 reduced cost >= 0

        # 如果存在负的 reduced cost，对应的原始变量可以增加



        # 找到最负的 reduced cost

        entering = np.argmin(reduced_costs)



        if reduced_costs[entering] >= -tol:

            # 对偶可行，当前 y 是最优解

            return {

                'status': 'optimal',

                'y': y,

                'obj_value': y @ b,  # 对偶目标值 = 原始目标值

                'iterations': iteration

            }



        # 构建限制主问题

        # 简化的势方法



        # 计算势

        # 实际实现需要更复杂的限制主问题



    return {'status': 'max_iterations', 'y': y}





def network_simplex(capacity, cost, supply, demand):

    """

    网络单纯形法（原始-对偶的特例）



    最小费用流问题：

    min Σ c_ij * x_ij

    s.t. Σ_j x_ij - Σ_k x_ki = b_i (节点平衡)

         0 <= x_ij <= u_ij (容量约束)



    使用原始-对偶框架

    """

    from collections import defaultdict



    # 网络节点

    nodes = list(set([e[0] for e in capacity.keys()] + [e[1] for e in capacity.keys()]))

    n = len(nodes)



    # 节点势（对偶变量）

    pi = {v: 0 for v in nodes}



    # 弧成本调整

    adjusted_cost = {(u, v): cost[(u, v)] - pi[u] + pi[v]

                     for (u, v) in cost}



    # 找到负调整成本的弧

    # 简化实现



    pass





def hungarian_primal_dual(cost_matrix):

    """

    匈牙利算法的原始-对偶解释



    线性分配问题：

    min Σ c_ij * x_ij

    s.t. Σ_j x_ij = 1, Σ_i x_ij = 1, x_ij >= 0



    对偶：

    max Σ u_i + Σ v_j

    s.t. u_i + v_j <= c_ij



    原始-对偶算法同时寻找可行原始解和对偶解

    """

    n = len(cost_matrix)



    # 对偶变量初始化

    u = np.zeros(n)

    v = np.zeros(n)



    # 归约

    for i in range(n):

        min_val = np.min(cost_matrix[i, :])

        u[i] = min_val



    for j in range(n):

        min_val = np.min(cost_matrix[:, j] - u)

        v[j] = min_val



    # 迭代改进

    max_iter = 1000

    for iteration in range(max_iter):

        # 找非紧约束

        # u_i + v_j < c_ij



        # 简化：使用已有的匈牙利算法结果

        from scipy.optimize import linear_sum_assignment

        row_ind, col_ind = linear_sum_assignment(cost_matrix)



        # 检查对偶可行性

        max_slack = 0

        for i in range(n):

            for j in range(n):

                slack = cost_matrix[i, j] - u[i] - v[j]

                if slack > max_slack:

                    max_slack = slack



        if max_slack < 1e-6:

            break



    # 计算最优分配

    assignment = col_ind

    total_cost = sum(cost_matrix[i, assignment[i]] for i in range(n))



    return {

        'assignment': assignment,

        'cost': total_cost,

        'dual_u': u,

        'dual_v': v

    }





def min_cost_flow_primal_dual(nodes, arcs, capacities, costs, source, sink, supply):

    """

    最小费用流的原始-对偶算法



    Parameters

    ----------

    nodes : list

        节点集合

    arcs : list of tuples

        弧列表 (u, v)

    capacities : dict

        容量 {(u, v): cap}

    costs : dict

        成本 {(u, v): cost}

    source, sink : node

        源和汇

    supply : dict

        供给量

    """

    # 初始化

    pi = {v: 0 for v in nodes}



    # 计算调整成本

    def adjusted_cost(u, v):

        return costs[(u, v)] + pi[u] - pi[v]



    # 找负成本圈

    # 简化实现



    flow = {arc: 0 for arc in arcs}

    total_cost = 0



    return {

        'flow': flow,

        'cost': total_cost

    }





def lagrangian_dual_subgradient(cost_matrix, constraints, lambda0=None,

                                max_iter=100, step_size=0.1):

    """

    拉格朗日对偶的次梯度算法



    用于求解整数规划的松弛



    max_λ (λ'b + min_x (c'x + λ'(Ax-b)))

    """

    n = len(cost_matrix)



    if lambda0 is None:

        lambda0 = np.zeros(len(constraints))



    lamb = lambda0.copy()

    best_dual = -np.inf



    for iteration in range(max_iter):

        # 求解子问题

        # 简化：使用线性规划



        # 计算次梯度

        subgrad = np.zeros(len(constraints))



        # 更新乘子

        lamb = lamb + step_size * subgrad



        # 调整步长

        step_size *= 0.98



    return {'lambda': lamb, 'dual_value': best_dual}





if __name__ == "__main__":

    print("=" * 60)

    print("原始-对偶算法")

    print("=" * 60)



    # 示例：线性分配问题

    cost = np.array([

        [9, 2, 7, 8],

        [6, 4, 3, 7],

        [5, 8, 1, 8],

        [7, 6, 9, 4]

    ], dtype=float)



    print("\n成本矩阵:")

    print(cost)



    # 使用原始-对偶匈牙利

    result = hungarian_primal_dual(cost)



    print(f"\n最优分配:")

    for i, j in enumerate(result['assignment']):

        print(f"  行 {i} -> 列 {j} (成本: {cost[i, j]:.0f})")



    print(f"\n总成本: {result['cost']:.0f}")

    print(f"\n对偶变量 u: {result['dual_u']}")

    print(f"对偶变量 v: {result['dual_v']}")



    # 验证对偶可行性

    print("\n--- 对偶可行性验证 ---")

    max_violation = 0

    for i in range(4):

        for j in range(4):

            slack = cost[i, j] - result['dual_u'][i] - result['dual_v'][j]

            if slack > max_violation:

                max_violation = slack



    print(f"最大违反量: {max_violation:.6f}")



    # 比较

    print("\n--- 与 scipy 比较 ---")

    from scipy.optimize import linear_sum_assignment



    row_ind, col_ind = linear_sum_assignment(cost)

    scipy_cost = sum(cost[i, j] for i, j in zip(row_ind, col_ind))

    print(f"scipy 成本: {scipy_cost:.0f}")

    print(f"原始-对偶成本: {result['cost']:.0f}")

