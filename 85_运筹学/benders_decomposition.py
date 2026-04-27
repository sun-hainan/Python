# -*- coding: utf-8 -*-

"""

算法实现：运筹学 / benders_decomposition



本文件实现 benders_decomposition 相关的算法功能。

"""



import numpy as np

from scipy.optimize import linprog





def benders_master_problem(c_master, A_int, b_int, integer_indices):

    """

    Benders 主问题（简化版）



    min c'MASTER * y

    s.t. A_INT * y <= b_INT

         Σ θ_j >= 下界约束（后续添加）

         y ∈ {0,1}（或整数）

         θ 自由



    初始主问题只有整数变量

    """

    pass





def benders_subproblem(A_coupling, b_coupling, c_sub, y_star):

    """

    Benders 子问题（给定 y）



    min c_SUB * x

    s.t. A_SUB * x <= b_SUB - A_COUPLING * y_star

         x >= 0



    对偶子问题用于生成割：

    max (b - A_coupling*y)' * π

    s.t. A_SUB' * π <= c_sub

         π >= 0

    """

    pass





def benders_decomposition(A_int, b_int, A_coupling, b_coupling, A_sub, b_sub,

                          c_int, c_sub, integer_indices, max_iter=100, tol=1e-6):

    """

    Benders 分解主函数



    原始问题：

    min c_int'y + c_sub'x

    s.t. A_int*y <= b_int

         A_coupling*y + A_sub*x <= b_coupling

         y ∈ {0,1}, x >= 0



    迭代：

    1. 求解主问题得到 y^k

    2. 求解子问题（给定 y^k）

    3. 添加 Benders 割到主问题

    4. 重复直到收敛

    """

    from scipy.optimize import linprog



    n_int = len(c_int)

    n_sub = len(c_sub)



    # 初始化

    master_constraints = []

    master_A = A_int.copy()

    master_b = b_int.copy()



    best_lower = -np.inf

    best_upper = np.inf

    y_best = None



    # 初始主问题（无 θ）

    for iteration in range(max_iter):

        # 求解主问题

        # min c_int'*y

        # s.t. A_int*y <= b_int

        #      [添加的割约束]

        #      y 整数



        # 简化的主问题求解（使用 LP 松弛）

        res_master = linprog(c_int, A_ub=master_A, b_ub=master_b, bounds=[(0, 1)] * n_int)



        if not res_master.success:

            # 主问题无界，子问题将产生无界割

            # 添加 feasibility cut

            pass



        y_k = res_master.x



        # 求解子问题（给定 y_k）

        # max c_sub'*x

        # s.t. A_sub*x <= b_coupling - A_coupling*y_k

        #      x >= 0



        rhs_sub = b_coupling - A_coupling @ y_k



        # 检查可行性

        if np.any(rhs_sub < -1e-10):

            # 不可行，添加 feasibility cut

            # 简化处理

            pass



        res_sub = linprog(c_sub, A_ub=A_sub, b_ub=rhs_sub, bounds=(0, None))



        if not res_sub.success:

            # 子问题不可行

            pass



        obj_sub = res_sub.fun

        x_k = res_sub.x



        # 更新界限

        lower_bound = c_int @ y_k + obj_sub

        upper_bound = c_int @ y_k + c_sub @ x_k



        if lower_bound > best_lower:

            best_lower = lower_bound

        if upper_bound < best_upper:

            best_upper = upper_bound

            y_best = y_k.copy()



        # 检查收敛

        if best_upper - best_lower < tol:

            break



        # 生成 Benders optimality cut

        # θ >= π' * (b_coupling - A_coupling*y)

        # 其中 π 是子问题的最优对偶



        # 计算对偶

        # 简化的割添加

        # θ >= obj_sub（简化）



        # 实际实现需要正确的子问题对偶

        # 这里用启发式割



    return {

        'status': 'optimal' if best_upper - best_lower < tol else 'max_iterations',

        'y': y_best,

        'obj_value': best_upper,

        'iterations': iteration + 1

    }





def benders_facility_location(costs, fixed_costs, capacities, demands, max_iter=100):

    """

    Benders 分解应用：设施选址问题



    问题：

    min Σ f_i*y_i + Σ Σ c_ij*x_ij

    s.t. Σ_j x_ij <= d_i*y_i, ∀i

         Σ_i x_ij >= D_j, ∀j

         y_i ∈ {0,1}, x_ij >= 0



    其中：

    - y_i: 是否开设设施 i

    - x_ij: 从设施 i 到客户 j 的配送量

    """

    n_facilities = len(fixed_costs)

    n_customers = len(demands)



    # 简化的 Benders 实现

    # 主问题：设施选择

    # 子问题：给定 y，求解运输问题



    def solve_subproblem(y):

        """给定 y，求解运输问题"""

        from scipy.optimize import linprog



        # 运输问题的成本矩阵

        # min Σ c_ij * x_ij

        # s.t. Σ_j x_ij <= d_i*y_i, ∀i (容量约束)

        #      Σ_i x_ij >= D_j, ∀j (需求约束)



        # 转换为标准形式

        A_ub = []

        b_ub = []

        A_eq = []

        b_eq = []



        # 容量约束

        for i in range(n_facilities):

            row = np.zeros(n_facilities * n_customers)

            for j in range(n_customers):

                row[i * n_customers + j] = 1

            A_ub.append(row)

            b_ub.append(capacities[i] * y[i])



        # 需求约束

        for j in range(n_customers):

            row = np.zeros(n_facilities * n_customers)

            for i in range(n_facilities):

                row[i * n_customers + j] = -1

            A_ub.append(row)

            b_ub.append(-demands[j])



        c = np.zeros(n_facilities * n_customers)

        for i in range(n_facilities):

            for j in range(n_customers):

                c[i * n_customers + j] = costs[i, j]



        res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=(0, None))



        if res.success:

            return res.fun, res.x

        return np.inf, None



    # 简化的迭代

    y = np.zeros(n_facilities)

    for i in range(n_facilities):

        y[i] = 1  # 初始全开



    best_obj = np.inf

    best_y = y.copy()



    for iteration in range(max_iter):

        obj_sub, x = solve_subproblem(y)

        obj_total = fixed_costs @ y + obj_sub



        if obj_total < best_obj:

            best_obj = obj_total

            best_y = y.copy()



        # 简化的割：关闭一个不盈利的设施

        # 计算每个设施的边际贡献

        contributions = []

        for i in range(n_facilities):

            y_off = y.copy()

            y_off[i] = 0

            obj_off, _ = solve_subproblem(y_off)

            contribution = (fixed_costs @ y + obj_sub) - (fixed_costs @ y_off + obj_off)

            contributions.append(contribution)



        # 关闭贡献最小的设施

        min_idx = np.argmin(contributions)

        if contributions[min_idx] > 0:

            break  # 所有设施都有正贡献



        y[min_idx] = 0



    return {

        'y': best_y,

        'obj_value': best_obj,

        'facilities_opened': np.sum(best_y)

    }





if __name__ == "__main__":

    print("=" * 60)

    print("Benders 分解")

    print("=" * 60)



    # 设施选址问题示例

    n_facilities = 3

    n_customers = 5



    # 运输成本

    costs = np.array([

        [4, 5, 3, 6, 8],

        [6, 4, 5, 3, 4],

        [5, 6, 4, 5, 3]

    ], dtype=float)



    # 固定开设成本

    fixed_costs = np.array([100, 150, 120])



    # 设施容量

    capacities = np.array([50, 40, 60])



    # 客户需求

    demands = np.array([15, 20, 10, 25, 20])



    print(f"设施数量: {n_facilities}")

    print(f"客户数量: {n_customers}")

    print(f"运输成本:\n{costs}")

    print(f"固定成本: {fixed_costs.tolist()}")

    print(f"容量: {capacities.tolist()}")

    print(f"需求: {demands.tolist()}")



    result = benders_facility_location(costs, fixed_costs, capacities, demands)



    print(f"\n最优开设决策: {result['y'].astype(int).tolist()}")

    print(f"开设设施数: {result['facilities_opened']:.0f}")

    print(f"最优成本: {result['obj_value']:.2f}")



    # 验证

    print("\n--- 验证 ---")

    for i in range(n_facilities):

        if result['y'][i] > 0.5:

            print(f"设施 {i+1} 已开设")

