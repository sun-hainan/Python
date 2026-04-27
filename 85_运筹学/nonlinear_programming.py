# -*- coding: utf-8 -*-

"""

算法实现：运筹学 / nonlinear_programming



本文件实现 nonlinear_programming 相关的算法功能。

"""



import numpy as np

from scipy.optimize import minimize





def lagrangian_multipliers_objective(x, f, constraints, lambdas, mus):

    """

    拉格朗日函数

    L(x, λ, μ) = f(x) + λ' * h(x) + μ' * g(x)

    """

    L = f(x)



    # 等式约束

    for i, h in enumerate(constraints['eq']):

        L += lambdas[i] * h(x)



    # 不等式约束（KKT 条件：μ >= 0, μ * g(x) = 0）

    for i, g in enumerate(constraints['ineq']):

        L += mus[i] * g(x)



    return L





def compute_gradient(x, f, h=None, g=None, eps=1e-8):

    """

    数值梯度计算

    """

    n = len(x)

    grad = np.zeros(n)



    for i in range(n):

        x_plus = x.copy()

        x_minus = x.copy()

        x_plus[i] += eps

        x_minus[i] -= eps



        grad[i] = (f(x_plus) - f(x_minus)) / (2 * eps)



    return grad





def lagrange_multipliers_solve(f, h_eq, g_ineq, x0, max_iter=100, tol=1e-6):

    """

    拉格朗日乘子法求解 NLP



    使用梯度下降/上升交替迭代

    """

    n = len(x0)



    x = x0.copy()

    lamb = np.zeros(len(h_eq)) if h_eq else np.zeros(0)

    mu = np.zeros(len(g_ineq)) if g_ineq else np.zeros(0)



    def objective_combined(x_and_params):

        x = x_and_params[:n]

        lambdas = x_and_params[n:n + len(lamb)]

        mus = x_and_params[n + len(lamb):]



        L = f(x)



        if h_eq:

            for i, h in enumerate(h_eq):

                L += lambdas[i] * h(x)



        if g_ineq:

            for i, g in enumerate(g_ineq):

                if mus[i] > 0:

                    L += mus[i] * g(x)



        return L



    for iteration in range(max_iter):

        # 优化 x（固定乘子）

        x_new = x.copy()

        for _ in range(50):

            grad_f = compute_gradient(x_new, f)

            grad_h = np.zeros(n)

            if h_eq:

                for i, h in enumerate(h_eq):

                    grad_h += lamb[i] * compute_gradient(x_new, h)

            grad_g = np.zeros(n)

            if g_ineq:

                for i, g in enumerate(g_ineq):

                    grad_g += mus[i] * compute_gradient(x_new, g)



            grad = grad_f + grad_h + grad_g

            x_new = x_new - 0.01 * grad



            if np.linalg.norm(grad) < tol:

                break



        x = x_new



        # 更新乘子

        if h_eq:

            for i, h in enumerate(h_eq):

                lamb[i] += 0.1 * h(x)



        if g_ineq:

            for i, g in enumerate(g_ineq):

                g_val = g(x)

                if g_val > 0:

                    mu[i] += 0.1 * g_val

                else:

                    mu[i] = max(0, mu[i] - 0.1 * (-g_val))



        # 检查 KKT 条件

        if h_eq:

            h_norm = np.max(np.abs([h(x) for h in h_eq]))

        else:

            h_norm = 0



        if g_ineq:

            g_max = max(0, np.max([g(x) for g in g_ineq]))

        else:

            g_max = 0



        if h_norm < tol and g_max < tol:

            break



    return {

        'x': x,

        'lambda': lamb,

        'mu': mu,

        'iterations': iteration + 1

    }





def sqp_sequential_quadratic_programming(f, constraints, x0, max_iter=100, tol=1e-6):

    """

    序列二次规划 (SQP)



    迭代求解 QP 子问题来逼近原问题

    """

    from scipy.optimize import OptimizeResult



    x = x0.copy()

    n = len(x)



    # 初始化乘子估计

    if constraints['eq'] and constraints['ineq']:

        m = len(constraints['eq']) + len(constraints['ineq'])

    elif constraints['eq']:

        m = len(constraints['eq'])

    elif constraints['ineq']:

        m = len(constraints['ineq'])

    else:

        m = 0



    lam = np.zeros(max(m, 1))



    for iteration in range(max_iter):

        # 计算梯度

        grad_f = compute_gradient(x, f)



        # 约束雅可比

        A = np.zeros((len(constraints.get('eq', [])), n))

        if constraints.get('eq'):

            for i, h in enumerate(constraints['eq']):

                A[i, :] = compute_gradient(x, h)



        # 构造 QP 子问题

        # min ∇f' * d + 0.5 * d' * B * d

        # s.t. A * d = -h(x)  (线性化等式约束)

        #      g(x) + G * d <= 0  (线性化不等式约束)



        # 简化的 Hessian（单位矩阵）

        B = np.eye(n)



        # 求解 QP（简化为线性化）

        # 使用梯度下降方向

        d = -grad_f



        # 更新 x

        alpha = 1.0

        x_new = x + alpha * d



        # 线搜索

        for _ in range(20):

            merit = f(x_new) + 10 * sum(abs(h(x_new)) for h in constraints.get('eq', []))

            merit_old = f(x) + 10 * sum(abs(h(x)) for h in constraints.get('eq', []))



            if merit < merit_old:

                break

            alpha *= 0.5

            x_new = x + alpha * d



        # 检查收敛

        if np.linalg.norm(x_new - x) < tol:

            break



        x = x_new



    return {

        'x': x,

        'fun': f(x),

        'iterations': iteration + 1

    }





def penalty_method(f, g, x0, penalty_param=10, max_iter=100, tol=1e-6):

    """

    罚函数法



    min f(x) + ρ * Σ max(0, g_i(x))^2

    """

    x = x0.copy()



    for iteration in range(max_iter):

        def penalty_obj(xk):

            p = f(xk)

            for gi in g:

                gi_val = gi(xk)

                if gi_val > 0:

                    p += penalty_param * gi_val ** 2

            return p



        # 最小化惩罚目标

        res = minimize(penalty_obj, x, method='BFGS')



        if not res.success:

            break



        x = res.x



        # 检查约束违反

        max_violation = max(0, max(gi(x) for gi in g))



        if max_violation < tol:

            break



        # 增加惩罚参数

        penalty_param *= 2



    return {

        'x': x,

        'fun': f(x),

        'iterations': iteration + 1

    }





def barrier_method(f, g, x0, mu=1, max_iter=100, tol=1e-6):

    """

    障碍函数法（内点法）



    min f(x) + μ * Σ -log(-g_i(x))

    """

    x = x0.copy()



    for iteration in range(max_iter):

        def barrier_obj(xk):

            b = f(xk)

            for gi in g:

                gi_val = gi(xk)

                if gi_val < -1e-10:  # 严格可行

                    b += mu * (-np.log(-gi_val))

                else:

                    return 1e10

            return b



        res = minimize(barrier_obj, x, method='BFGS')



        if not res.success:

            break



        x = res.x



        # 检查收敛

        max_violation = max(0, max(gi(x) for gi in g))



        if max_violation < tol:

            break



        # 减小障碍参数

        mu *= 0.5



    return {

        'x': x,

        'fun': f(x),

        'iterations': iteration + 1

    }





def augmented_lagrangian(f, h_eq, g_ineq, x0, max_iter=100, tol=1e-6):

    """

    增广拉格朗日法



    结合了拉格朗日法和罚函数法

    """

    x = x0.copy()

    lamb = np.zeros(len(h_eq)) if h_eq else np.zeros(0)

    mu = np.zeros(len(g_ineq)) if g_ineq else np.zeros(0)

    rho = 1.0



    for iteration in range(max_iter):

        def aug_lag(xk):

            L = f(xk)



            if h_eq:

                for i, h in enumerate(h_eq):

                    L += lamb[i] * h(xk) + 0.5 * rho * h(xk) ** 2



            if g_ineq:

                for i, g in enumerate(g_ineq):

                    g_val = g(xk)

                    if g_val > 0:

                        L += mu[i] * g_val + 0.5 * rho * g_val ** 2



            return L



        res = minimize(aug_lag, x, method='BFGS')



        if not res.success:

            break



        x = res.x



        # 更新乘子

        if h_eq:

            for i, h in enumerate(h_eq):

                lamb[i] += rho * h(x)



        if g_ineq:

            for i, g in enumerate(g_ineq):

                g_val = g(x)

                mu[i] = max(0, mu[i] + rho * g_val)



        # 检查收敛

        if h_eq:

            h_norm = np.max(np.abs([h(x) for h in h_eq]))

        else:

            h_norm = 0



        if g_ineq:

            g_max = max(0, max(g(x) for g in g_ineq))

        else:

            g_max = 0



        if h_norm < tol and g_max < tol:

            break



        rho *= 1.5



    return {

        'x': x,

        'fun': f(x),

        'lambda': lamb,

        'mu': mu,

        'iterations': iteration + 1

    }





if __name__ == "__main__":

    print("=" * 60)

    print("非线性规划（拉格朗日乘子、SQP）")

    print("=" * 60)



    # 示例 1: 简单约束优化

    # min (x1 - 2)^2 + (x2 - 1)^2

    # s.t. x1 + x2 <= 2



    def f1(x):

        return (x[0] - 2)**2 + (x[1] - 1)**2



    def g1_1(x):

        return x[0] + x[1] - 2



    print("\n问题 1:")

    print("min (x1-2)² + (x2-1)²")

    print("s.t. x1 + x2 <= 2")



    # 使用 scipy

    from scipy.optimize import minimize



    res1 = minimize(f1, x0=[0, 0], method='SLSQP',

                    constraints={'type': 'ineq', 'fun': g1_1})



    print(f"\nSciPy SLSQP 解: x1={res1.x[0]:.4f}, x2={res1.x[1]:.4f}")

    print(f"目标值: {res1.fun:.4f}")



    # 示例 2: 等式约束

    # min x1^2 + x2^2

    # s.t. x1 + x2 = 1



    def f2(x):

        return x[0]**2 + x[1]**2



    def h2_1(x):

        return x[0] + x[1] - 1



    print("\n" + "-" * 40)

    print("\n问题 2:")

    print("min x1² + x2²")

    print("s.t. x1 + x2 = 1")



    res2 = minimize(f2, x0=[0, 0], method='SLSQP',

                    constraints={'type': 'eq', 'fun': h2_1})



    print(f"\nSciPy SLSQP 解: x1={res2.x[0]:.4f}, x2={res2.x[1]:.4f}")

    print(f"目标值: {res2.fun:.4f}")



    # 分析解

    print(f"\n解析解: x1=x2=0.5, 目标值=0.5")



    # 示例 3: Rosenbrock 函数

    # min 100*(x2 - x1^2)^2 + (1-x1)^2



    def rosenbrock(x):

        return 100 * (x[1] - x[0]**2)**2 + (1 - x[0])**2



    print("\n" + "-" * 40)

    print("\n问题 3: Rosenbrock 函数")

    print("min 100*(x2-x1²)² + (1-x1)²")



    res3 = minimize(rosenbrock, x0=[-1, 1], method='BFGS')



    print(f"\nBFGS 解: x1={res3.x[0]:.6f}, x2={res3.x[1]:.6f}")

    print(f"目标值: {res3.fun:.10f}")



    # 示例 4: 约束非线性规划

    # min (x1 - 1)^2 + (x2 - 1)^2

    # s.t. x1 + x2 = 2

    #      (x1 - 1)^2 + x2^2 <= 1



    def f4(x):

        return (x[0] - 1)**2 + (x[1] - 1)**2



    def h4(x):

        return x[0] + x[1] - 2



    def g4(x):

        return (x[0] - 1)**2 + x[1]**2 - 1



    print("\n" + "-" * 40)

    print("\n问题 4:")

    print("min (x1-1)² + (x2-1)²")

    print("s.t. x1 + x2 = 2")

    print("     (x1-1)² + x2² <= 1")



    res4 = minimize(f4, x0=[0, 2], method='SLSQP',

                    constraints=[

                        {'type': 'eq', 'fun': h4},

                        {'type': 'ineq', 'fun': g4}

                    ])



    print(f"\n解: x1={res4.x[0]:.4f}, x2={res4.x[1]:.4f}")

    print(f"目标值: {res4.fun:.4f}")



    # 增广拉格朗日

    print("\n--- 增广拉格朗日法 ---")

    res_auglag = augmented_lagrangian(f4, [h4], [g4], x0=[0, 2])



    print(f"解: x1={res_auglag['x'][0]:.4f}, x2={res_auglag['x'][1]:.4f}")

    print(f"目标值: {res_auglag['fun']:.4f}")

    print(f"迭代: {res_auglag['iterations']}")

