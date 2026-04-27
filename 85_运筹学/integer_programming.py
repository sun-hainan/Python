# -*- coding: utf-8 -*-

"""

算法实现：运筹学 / integer_programming



本文件实现 integer_programming 相关的算法功能。

"""



import numpy as np

from scipy.optimize import linprog





def branch_and_bound(A, b, c, integer_indices, max_nodes=10000, tol=1e-6):

    """

    分支定界法求解 MILP



    Parameters

    ----------

    integer_indices : list

        必须是整数变量的索引

    max_nodes : int

        最大节点数

    tol : float

        整数容差



    Returns

    -------

    dict

        最优解、最优值、节点数

    """

    n = len(c)



    # 节点结构：(A, b, c, integer_indices, x_lp, obj_lp)

    nodes = []



    # 初始 LP 松弛

    res_lp = linprog(c, A_ub=A, b_ub=b, bounds=(0, None))

    if not res_lp.success:

        return {'status': 'infeasible'}



    root_x = res_lp.x

    root_obj = res_lp.fun



    nodes.append({

        'A': A, 'b': b, 'c': c,

        'integer_indices': integer_indices,

        'x': root_x, 'obj': root_obj,

        'lower': root_obj, 'upper': np.inf

    })



    best_obj = np.inf

    best_x = None

    node_count = 0



    while nodes and node_count < max_nodes:

        node_count += 1



        # 选择节点（深度优先或最佳下界）

        node = nodes.pop()



        # 定界

        if node['obj'] >= best_obj:

            continue  # 剪枝



        # 检查整数可行性

        x = node['x']

        is_integer = True

        for i in integer_indices:

            if abs(x[i] - round(x[i])) > tol:

                is_integer = False

                break



        if is_integer:

            # 更新上界（对于 max 问题）

            if node['obj'] < best_obj:

                best_obj = node['obj']

                best_x = x.copy()

        else:

            # 分支：选择最分数的整数变量

            frac_vars = []

            for i in integer_indices:

                frac = abs(x[i] - round(x[i]))

                if frac > tol:

                    frac_vars.append((i, frac))



            if not frac_vars:

                continue



            # 选择分数最大的变量

            frac_vars.sort(key=lambda v: v[1], reverse=True)

            branch_var = frac_vars[0][0]



            # 创建两个子问题

            # 左分支：x_i <= floor(x_i)

            # 右分支：x_i >= ceil(x_i)



            x_i = x[branch_var]

            floor_val = int(np.floor(x_i))

            ceil_val = int(np.ceil(x_i))



            # 左分支约束

            A_left = np.vstack([node['A'], np.zeros(n)])

            A_left[-1, branch_var] = 1

            b_left = np.append(node['b'], floor_val)



            # 右分支约束

            A_right = np.vstack([node['A'], np.zeros(n)])

            A_right[-1, branch_var] = -1

            b_right = np.append(node['b'], -ceil_val)



            # 求解左子问题

            res_left = linprog(node['c'], A_ub=A_left, b_ub=b_left, bounds=(0, None))

            if res_left.success and res_left.fun < best_obj:

                nodes.append({

                    'A': A_left, 'b': b_left, 'c': node['c'],

                    'integer_indices': integer_indices,

                    'x': res_left.x, 'obj': res_left.fun

                })



            # 求解右子问题

            res_right = linprog(node['c'], A_ub=A_right, b_ub=b_right, bounds=(0, None))

            if res_right.success and res_right.fun < best_obj:

                nodes.append({

                    'A': A_right, 'b': b_right, 'c': node['c'],

                    'integer_indices': integer_indices,

                    'x': res_right.x, 'obj': res_right.fun

                })



    return {

        'status': 'optimal' if best_x is not None else 'max_nodes',

        'x': best_x,

        'obj_value': best_obj,

        'nodes_explored': node_count

    }





def cutting_plane_gomory(A, b, c, integer_indices, max_cuts=100, tol=1e-6):

    """

    Gomory 割平面法



    思想：从 LP 松弛的解开始，添加割平面切除非整数极点

    Gomory 割：从最优表中提取纯整数割



    流程：

    1. 求解 LP 松弛

    2. 若解为整数，返回

    3. 否则，从最优基提取 Gomory 割

    4. 添加割平面，重新求解

    5. 重复

    """

    n = len(c)

    m = len(b)



    # 添加松弛变量

    A_aug = np.hstack([A, np.eye(m)])

    c_aug = np.concatenate([c, np.zeros(m)])



    # 基变量索引（初始：后 m 个）

    basis = list(range(n, n + m))



    iteration = 0

    while iteration < max_cuts:

        iteration += 1



        # 求解当前 LP

        # 使用单纯形表

        try:

            B = A_aug[:, basis]

            B_inv = np.linalg.inv(B)

            x_B = B_inv @ b

        except:

            return {'status': 'infeasible'}



        # 检验数

        c_B = c_aug[basis]

        pi = c_B @ B_inv

        reduced_costs = c_aug - pi @ A_aug



        # 检查最优性

        is_integer_sol = True

        for i in integer_indices:

            if abs(x_B[basis.index(i)] - round(x_B[basis.index(i)])) > tol:

                is_integer_sol = False

                break



        # 这里简化处理：直接检查所有变量的整数性

        x = np.zeros(n + m)

        x[basis] = x_B

        if is_integer_sol or all(abs(x[i] - round(x[i])) < tol for i in integer_indices):

            return {

                'status': 'optimal',

                'x': x[:n],

                'obj_value': c @ x[:n],

                'iterations': iteration

            }



        # 找到分数变量（简化：使用 x 的分数部分）

        frac_vars = [(i, x[i] - np.floor(x[i])) for i in integer_indices

                     if abs(x[i] - round(x[i])) > tol]



        if not frac_vars:

            return {

                'status': 'optimal',

                'x': x[:n],

                'obj_value': c @ x[:n],

                'iterations': iteration

            }



        # 选择分数最大的变量

        branch_var = max(frac_vars, key=lambda v: v[1])[0]



        # Gomory 割：f_i - Σ f_ij * x_j <= 0

        # 这里简化：用分支定界代替



        # 简化：添加割平面 x_i <= floor(x_i) 或 x_i >= ceil(x_i)

        floor_val = int(np.floor(x[branch_var]))

        ceil_val = int(np.ceil(x[branch_var]))



        # 添加割

        new_row_left = np.zeros(n + m)

        new_row_left[branch_var] = 1



        new_row_right = np.zeros(n + m)

        new_row_right[branch_var] = -1



        A_aug = np.vstack([A_aug, new_row_left])

        b = np.append(b, floor_val)

        A_aug = np.vstack([A_aug, new_row_right])

        b = np.append(b, -ceil_val)



    return {'status': 'max_iterations'}





def solve_mip_branch_cut(A, b, c, integer_indices, max_nodes=5000, max_cuts=50):

    """

    分支切割法：结合分支定界和割平面

    """

    from scipy.optimize import linprog



    # 简化的 MIP 求解器

    n = len(c)

    best_obj = np.inf

    best_x = None



    # 使用递归分支

    def branch(A_sub, b_sub, int_idx, x_current, obj_current):

        nonlocal best_obj, best_x



        # LP 松弛

        res = linprog(c, A_ub=A_sub, b_ub=b_sub, bounds=(0, None))

        if not res.success or res.fun >= best_obj:

            return  # 剪枝



        x = res.x



        # 检查整数性

        all_int = all(abs(x[i] - round(x[i])) < 1e-4 for i in int_idx)



        if all_int:

            if res.fun < best_obj:

                best_obj = res.fun

                best_x = x.copy()

            return



        # 分支

        frac_vars = [(i, x[i] - np.floor(x[i])) for i in int_idx

                     if abs(x[i] - round(x[i])) > 1e-4]

        if not frac_vars:

            return



        branch_var = max(frac_vars, key=lambda v: v[1])[0]

        floor_val = int(np.floor(x[branch_var]))

        ceil_val = int(np.ceil(x[branch_var]))



        # 左分支：x_i <= floor

        A_left = np.vstack([A_sub, np.zeros(n)])

        A_left[-1, branch_var] = 1

        b_left = np.append(b_sub, floor_val)



        # 右分支：x_i >= ceil

        A_right = np.vstack([A_sub, np.zeros(n)])

        A_right[-1, branch_var] = -1

        b_right = np.append(b_sub, -ceil_val)



        branch(A_left, b_left, int_idx, x, res.fun)

        branch(A_right, b_right, int_idx, x, res.fun)



    branch(A, b, integer_indices, None, -np.inf)



    if best_x is not None:

        return {

            'status': 'optimal',

            'x': best_x,

            'obj_value': best_obj,

            'integer_indices': integer_indices

        }

    return {'status': 'infeasible'}





def knapsack_branch_and_bound(values, weights, capacity):

    """

    0-1 背包问题的分支定界



    问题：max Σ v_i * x_i

         s.t. Σ w_i * x_i <= W

              x_i ∈ {0, 1}

    """

    n = len(values)



    # 按价值/重量比排序（贪婪启发式提供上界）

    ratios = [(i, values[i] / weights[i]) for i in range(n)]

    ratios.sort(key=lambda x: x[1], reverse=True)



    # 上界：贪婪解的值

    def upper_bound(x):

        remaining = capacity - sum(weights[j] * x[j] for j in range(n))

        ub = sum(values[j] * x[j] for j in range(n))

        for i, r in ratios:

            if weights[i] <= remaining + 1e-6:

                ub += values[i]

                remaining -= weights[i]

        return ub



    best_value = 0

    best_x = np.zeros(n, dtype=int)



    def branch(x, depth, remaining):

        nonlocal best_value, best_x



        if depth == n:

            value = sum(values[i] * x[i] for i in range(n))

            if value > best_value:

                best_value = value

                best_x = x.copy()

            return



        # 上界剪枝

        if upper_bound(x) <= best_value:

            return



        i = ratios[depth][0]



        # 尝试包含 i

        if weights[i] <= remaining:

            x[i] = 1

            branch(x, depth + 1, remaining - weights[i])

            x[i] = 0



        # 尝试不包含 i

        branch(x, depth + 1, remaining)



    branch(np.zeros(n, dtype=int), 0, capacity)



    return {

        'x': best_x,

        'value': best_value,

        'weight': sum(weights[i] * best_x[i] for i in range(n))

    }





if __name__ == "__main__":

    print("=" * 60)

    print("整数规划求解")

    print("=" * 60)



    # 示例：MIP

    # max 3x1 + 2x2

    # s.t. 2x1 + x2 <= 6

    #      x1 + 2x2 <= 8

    #      x1, x2 整数



    A = np.array([[2, 1], [1, 2]], dtype=float)

    b = np.array([6, 8], dtype=float)

    c = np.array([3, 2], dtype=float)

    integer_indices = [0, 1]



    print("\n问题:")

    print("max 3x1 + 2x2")

    print("s.t. 2x1 + x2 <= 6")

    print("      x1 + 2x2 <= 8")

    print("      x1, x2 整数\n")



    result = solve_mip_branch_cut(A, b, c, integer_indices)



    if result['status'] == 'optimal':

        print(f"最优解: x1 = {result['x'][0]:.0f}, x2 = {result['x'][1]:.0f}")

        print(f"最优值: {result['obj_value']:.0f}")



    # LP 松弛比较

    res_lp = linprog(-c, A_ub=A, b_ub=b, bounds=(0, None))

    print(f"\nLP 松弛解: x1 = {res_lp.x[0]:.4f}, x2 = {res_lp.x[1]:.4f}")

    print(f"LP 松弛值: {-res_lp.fun:.4f}")



    # 背包问题

    print("\n" + "-" * 40)

    print("\n0-1 背包问题:")

    values = [60, 100, 120, 80, 50]

    weights = [10, 20, 30, 15, 10]

    capacity = 50



    print(f"物品价值: {values}")

    print(f"物品重量: {weights}")

    print(f"背包容量: {capacity}")



    result_kp = knapsack_branch_and_bound(values, weights, capacity)



    print(f"\n最优选择: {result_kp['x'].astype(int).tolist()}")

    print(f"总价值: {result_kp['value']}")

    print(f"总重量: {result_kp['weight']}")

