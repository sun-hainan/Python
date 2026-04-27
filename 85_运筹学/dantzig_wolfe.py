# -*- coding: utf-8 -*-

"""

算法实现：运筹学 / dantzig_wolfe



本文件实现 dantzig_wolfe 相关的算法功能。

"""



import numpy as np

from scipy.optimize import linprog





def dantzig_wolfe_decomposition(c_blocks, A_blocks, b_blocks, F, g,

                                  max_iter=100, tol=1e-6):

    """

    Dantzig-Wolfe 分解



    Parameters

    ----------

    c_blocks : list of np.ndarray

        每个块的的目标系数

    A_blocks : list of np.ndarray

        每个块的约束矩阵

    b_blocks : list of np.ndarray

        每个块的 RHS

    F : np.ndarray

        链接约束矩阵

    g : np.ndarray

        链接约束 RHS

    """

    n_blocks = len(c_blocks)



    # 初始化主问题

    # 使用每个块的极点

    columns = []



    for i, (c_i, A_i, b_i) in enumerate(zip(c_blocks, A_blocks, b_blocks)):

        # 求一个极点（简化为原点）

        x_i = np.zeros_like(c_i)

        columns.append({

            'block': i,

            'x': x_i,

            'cost': c_i @ x_i,

            'F_contrib': F[:, i] @ x_i if F is not None else np.zeros(len(g))

        })



    # 迭代

    for iteration in range(max_iter):

        # 求解主问题（当前的列）

        # min Σ_k λ_k * c_k

        # s.t. Σ_k λ_k * F_k = g

        #      Σ_k λ_k = 1

        #      λ_k >= 0



        n_cols = len(columns)

        if n_cols == 0:

            break



        # 构建主问题

        # 简化为使用 linprog

        c_master = np.array([col['cost'] for col in columns])



        # F 约束

        A_eq_F = np.array([[col['F_contrib'][j] for col in columns]

                          for j in range(len(g))])



        # 凸性约束

        A_eq_1 = np.ones((1, n_cols))



        A_eq = np.vstack([A_eq_F, A_eq_1])

        b_eq = np.append(g, 1)



        res_master = linprog(c_master, A_eq=A_eq, b_eq=b_eq, bounds=(0, None))



        if not res_master.success:

            break



        # 对偶变量

        pi = res_master.eqlin.marginals[:len(g)]

        mu = res_master.eqlin.marginals[len(g)]



        # 求解子问题

        new_columns = []



        for i, (c_i, A_i, b_i) in enumerate(zip(c_blocks, A_blocks, b_blocks)):

            # 子问题成本

            # min (c_i - F_i'π - μ) * x_i

            # s.t. A_i * x_i = b_i, x_i >= 0



            c_sub = c_i - (F[:, i] @ pi) - mu if F is not None else c_i



            res_sub = linprog(c_sub, A_eq=A_i, b_eq=b_i, bounds=(0, None))



            if res_sub.success:

                x_i = res_sub.x

                reduced_cost = c_i @ x_i - pi @ (F[:, i] @ x_i) - mu if F is not None else c_i @ x_i - mu



                if reduced_cost < -tol:

                    # 有改善列

                    new_columns.append({

                        'block': i,

                        'x': x_i,

                        'cost': c_i @ x_i,

                        'F_contrib': F[:, i] @ x_i if F is not None else np.zeros(len(g))

                    })



        if not new_columns:

            # 没有改善列，最优

            break



        columns.extend(new_columns)



    # 计算最优解

    lambdas = res_master.x if res_master.success else np.zeros(len(columns))

    x_opt = np.zeros(sum(len(c) for c in c_blocks))

    offset = 0



    for col, lam in zip(columns, lambdas):

        n_i = len(col['x'])

        x_opt[offset:offset + n_i] += lam * col['x']

        offset += n_i



    return {

        'status': 'optimal' if not new_columns else 'max_iterations',

        'x': x_opt,

        'obj_value': res_master.fun if res_master.success else None,

        'iterations': iteration + 1,

        'n_columns': len(columns)

    }





def block_diagonal_solver(c, A, b, n_blocks):

    """

    块对角矩阵的求解器



    假设 A 是块对角的

    """

    # 分割矩阵

    block_size = len(c) // n_blocks



    c_blocks = []

    A_blocks = []

    b_blocks = []



    for i in range(n_blocks):

        start = i * block_size

        end = start + block_size if i < n_blocks - 1 else len(c)



        c_blocks.append(c[start:end])

        A_blocks.append(A[start:end, start:end])

        b_blocks.append(b[start:end])



    return c_blocks, A_blocks, b_blocks





def column_generation_master(A, b, c, initial_columns):

    """

    列生成主问题求解器



    用于迭代添加列

    """

    n_cols = len(initial_columns)



    # 当前列

    columns = initial_columns.copy()



    for iteration in range(100):

        # 构建当前主问题

        A_master = np.array([[col['coef'][j] for col in columns]

                            for j in range(len(b))])



        res = linprog(c, A_eq=A_master, b_eq=b, bounds=(0, None))



        if not res.success:

            break



        # 返回对偶变量

        pi = res.eqlin.marginals



        # 计算每列的 reduced cost

        for i, col in enumerate(columns):

            rc = c[i] - pi @ col['coef']

            col['reduced_cost'] = rc



        yield {

            'columns': columns,

            'dual': pi,

            'solution': res.x,

            'obj': res.fun

        }





if __name__ == "__main__":

    print("=" * 60)

    print("Dantzig-Wolfe 分解算法")

    print("=" * 60)



    # 简单示例：2 个块

    # Block 1: min 2x1 + 3x2 s.t. x1 + x2 = 1, x >= 0

    # Block 2: min 4x3 + 5x4 s.t. x3 + x4 = 1, x >= 0

    # Link: x1 + x3 >= 0.5



    c1 = np.array([2, 3])

    A1 = np.array([[1, 1]])

    b1 = np.array([1])



    c2 = np.array([4, 5])

    A2 = np.array([[1, 1]])

    b2 = np.array([1])



    c_blocks = [c1, c2]

    A_blocks = [A1, A2]

    b_blocks = [b1, b2]



    # 链接约束

    # x1 + x3 >= 0.5 => [1, 0, 1, 0] >= 0.5

    # 转换为 <= : -x1 - x3 <= -0.5

    F = np.array([[-1, 0, -1, 0]])

    g = np.array([-0.5])



    print("\n块 1:")

    print("  min 2x1 + 3x2")

    print("  s.t. x1 + x2 = 1")

    print("  x1, x2 >= 0")



    print("\n块 2:")

    print("  min 4x3 + 5x4")

    print("  s.t. x3 + x4 = 1")

    print("  x3, x4 >= 0")



    print("\n链接约束: x1 + x3 >= 0.5")



    # 使用 Dantzig-Wolfe

    result = dantzig_wolfe_decomposition(c_blocks, A_blocks, b_blocks, F, g)



    if result['status'] == 'optimal':

        print(f"\n最优解:")

        print(f"  x1 = {result['x'][0]:.4f}, x2 = {result['x'][1]:.4f}")

        print(f"  x3 = {result['x'][2]:.4f}, x4 = {result['x'][3]:.4f}")

        print(f"  最优值: {result['obj_value']:.4f}")

        print(f"  迭代: {result['iterations']}")

        print(f"  列数: {result['n_columns']}")



    # 对比直接求解

    print("\n--- 直接求解 (scipy) ---")

    c_all = np.array([2, 3, 4, 5])

    A_eq_all = np.array([

        [1, 1, 0, 0],  # 块1约束

        [0, 0, 1, 1],  # 块2约束

        [-1, 0, -1, 0] # 链接约束

    ])

    b_eq_all = np.array([1, 1, -0.5])



    res_direct = linprog(c_all, A_eq=A_eq_all, b_eq=b_eq_all, bounds=(0, None))



    if res_direct.success:

        print(f"  x1 = {res_direct.x[0]:.4f}, x2 = {res_direct.x[1]:.4f}")

        print(f"  x3 = {res_direct.x[2]:.4f}, x4 = {res_direct.x[3]:.4f}")

        print(f"  最优值: {res_direct.fun:.4f}")



    print("\n注：Dantzig-Wolfe 分解适用于超大规模问题，")

    print("    此简单示例中两种方法应得到相同结果")

