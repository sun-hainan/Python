# -*- coding: utf-8 -*-

"""

算法实现：生物信息学 / systems_biology_ode



本文件实现 systems_biology_ode 相关的算法功能。

"""



def hill_equation(L: float, K_d: float, n: float) -> float:

    """

    Hill方程（配体-受体结合）



    θ = L^n / (K_d + L^n)



    参数:

        L: 配体浓度

        K_d: 解离常数

        n: Hill系数（协同性）



    返回:

        结合分数

    """

    return L ** n / (K_d + L ** n)





def gene_expression_ode(

    t: float,

    y: np.ndarray,

    alpha: np.ndarray,

    beta: np.ndarray,

    K: np.ndarray,

    n: float

) -> np.ndarray:

    """

    基因表达ODE系统



    简化模型：dX_i/dt = α_i / (1 + Σ_j K_ij * X_j^n) - β_i * X_i



    参数:

        t: 时间

        y: 当前状态 [X_1, X_2, ...]

        alpha: 基础表达率

        beta: 降解率

        K: 调控矩阵（K_ij表示j对i的抑制强度）

        n: Hill系数



    返回:

        dy/dt

    """

    dydt = np.zeros_like(y)

    n_genes = len(y)



    for i in range(n_genes):

        # 抑制项

        inhibition = 0.0

        for j in range(n_genes):

            inhibition += K[i, j] * (y[j] ** n)



        # dX_i/dt = α_i / (1 + inhibition) - β_i * X_i

        dydt[i] = alpha[i] / (1 + inhibition) - beta[i] * y[i]



    return dydt





def simulate_gene_network(

    initial_state: np.ndarray,

    alpha: np.ndarray,

    beta: np.ndarray,

    K: np.ndarray,

    n: float = 2.0,

    t_span: Tuple[float, float] = (0, 100),

    n_points: int = 1000

) -> Tuple[np.ndarray, np.ndarray]:

    """

    模拟基因调控网络动力学



    参数:

        initial_state: 初始表达量

        alpha, beta, K: 网络参数

        n: Hill系数

        t_span: 时间范围

        n_points: 采样点数



    返回:

        (t_array, y_array)

    """

    from scipy.integrate import odeint



    t_array = np.linspace(t_span[0], t_span[1], n_points)



    def rhs(t, y):

        return gene_expression_ode(t, y, alpha, beta, K, n)



    y_array = odeint(rhs, initial_state, t_array)



    return t_array, y_array





def toggle_switch(t, y, alpha1, alpha2, beta1, beta2, n):

    """

    开关网络（Toggle Switch）



    两个相互抑制的基因：

    - 基因1抑制基因2

    - 基因2抑制基因1



    可以产生双稳态

    """

    u, v = y

    # du/dt = α_1 / (1 + v^n) - β_1 * u

    # dv/dt = α_2 / (1 + u^n) - β_2 * v

    dudt = alpha1 / (1 + v ** n) - beta1 * u

    dvdt = alpha2 / (1 + u ** n) - beta2 * v

    return [dudt, dvdt]





def repressilator(t, y, alpha, beta, n, m):

    """

    抑制振荡器（Repressilator）



    三个相互抑制的基因形成振荡回路：

    Gene1 --| Gene2 --| Gene3 --| Gene1



    参数:

        alpha: 最大表达率

        beta: 降解率

        n: Hill系数

        m: 翻译/转录延迟参数

    """

    x1, x2, x3 = y

    dx1 = -x1 + alpha / (1 + x3 ** n)

    dx2 = -x2 + alpha / (1 + x1 ** n)

    dx3 = -x3 + alpha / (1 + x2 ** n)

    return [dx1, dx2, dx3]





def find_fixed_points(

    alpha: np.ndarray,

    beta: np.ndarray,

    K: np.ndarray,

    n: float = 2.0

) -> List[np.ndarray]:

    """

    寻找ODE系统的平衡点（数值方法）



    平衡点满足 dX/dt = 0

    """

    from scipy.optimize import fsolve



    n_genes = len(alpha)

    fixed_points = []



    # 尝试多个初始点

    for _ in range(10):

        x0 = np.random.rand(n_genes) * 10



        def equations(x):

            dydt = gene_expression_ode(0, x, alpha, beta, K, n)

            return dydt



        sol, info, ier, mesg = fsolve(equations, x0, full_output=True)

        if ier == 1:  # 成功收敛

            # 检查是否在有效范围内

            if np.all(sol > 0) and np.all(sol < 1000):

                # 检查是否已存在

                is_new = True

                for fp in fixed_points:

                    if np.linalg.norm(fp - sol) < 0.01:

                        is_new = False

                        break

                if is_new:

                    fixed_points.append(sol)



    return fixed_points





def parameter_estimation(

    t_data: np.ndarray,

    y_data: np.ndarray,

    initial_params: np.ndarray

) -> np.ndarray:

    """

    参数估计（最小二乘）



    参数:

        t_data: 时间数据点

        y_data: 观测数据

        initial_params: 初始参数猜测



    返回:

        估计的参数

    """

    from scipy.optimize import least_squares



    def residuals(params):

        alpha = params[:len(params)//3]

        beta = params[len(params)//3:2*len(params)//3]

        K_flat = params[2*len(params)//3:]

        n_genes = len(alpha)

        K = K_flat.reshape(n_genes, n_genes)



        y0 = y_data[0]

        t_sim, y_sim = simulate_gene_network(y0, alpha, beta, K, n=2.0,

                                               t_span=(t_data[0], t_data[-1]),

                                               n_points=len(t_data))



        return (y_sim - y_data).flatten()



    result = least_squares(residuals, initial_params, bounds=(0, 100))

    return result.x





if __name__ == '__main__':

    print('=== 系统生物学 - 基因调控网络测试 ===')



    # 测试1: 米氏动力学

    print('\n--- 测试1: 米氏动力学 ---')

    V_max = 10.0

    K_m = 2.0

    S_range = np.linspace(0, 20, 100)

    v_range = [michaelis_menten(V_max, K_m, S) for S in S_range]

    print(f'V_max={V_max}, K_m={K_m}')

    print(f'最大速率时的S: S>>K_m, v≈V_max={V_max}')



    # 测试2: Hill方程

    print('\n--- 测试2: Hill方程 ---')

    for n in [1, 2, 4]:

        for L in [0.5, 1.0, 2.0, 5.0]:

            theta = hill_equation(L, K_d=1.0, n=n)

            print(f'  n={n}, L={L}: θ={theta:.4f}')



    # 测试3: 简单基因网络

    print('\n--- 测试3: 简单基因网络模拟 ---')

    np.random.seed(42)



    n_genes = 3

    alpha = np.array([10.0, 8.0, 12.0])  # 基础表达率

    beta = np.array([1.0, 1.0, 1.0])    # 降解率

    K = np.array([

        [0.0, 1.0, 0.5],

        [0.5, 0.0, 1.0],

        [1.0, 0.5, 0.0]

    ])  # 调控强度



    y0 = np.array([1.0, 1.0, 1.0])

    t, y = simulate_gene_network(y0, alpha, beta, K, n=2.0, t_span=(0, 50))



    print(f'初始状态: {y0}')

    print(f'最终状态 (t=50): {y[-1]}')

    print(f'状态变化: {[f"{y[-1][i]-y0[i]:.2f}" for i in range(n_genes)]}')



    # 测试4: 开关网络双稳态

    print('\n--- 测试4: 开关网络双稳态 ---')

    from scipy.integrate import odeint



    alpha1, beta1 = 10.0, 1.0

    alpha2, beta2 = 10.0, 1.0

    n = 2.0



    t_span = np.linspace(0, 50, 500)



    # 两个初始条件

    y1_init = [5.0, 1.0]

    y2_init = [1.0, 5.0]



    y1 = odeint(toggle_switch, y1_init, t_span, args=(alpha1, alpha2, beta1, beta2, n))

    y2 = odeint(toggle_switch, y2_init, t_span, args=(alpha1, alpha2, beta1, beta2, n))



    print(f'初始条件1 {y1_init} -> 稳态 {y1[-1]}')

    print(f'初始条件2 {y2_init} -> 稳态 {y2[-1]}')



    # 测试5: 抑制振荡器

    print('\n--- 测试5: 抑制振荡器 ---')

    alpha = 20.0

    beta = 1.0

    n = 2.0



    y0_repress = [1.0, 1.0, 1.0]

    t_repress = np.linspace(0, 100, 1000)



    y_repress = odeint(repressilator, y0_repress, t_repress, args=(alpha, beta, n))



    # 检查是否振荡

    last_quarter = y_repress[len(y_repress)//4:]

    oscillation = np.std(last_quarter, axis=0).mean()

    print(f'振荡幅度（最后1/4的标准差）: {oscillation:.4f}')

    print(f'最终状态: {y_repress[-1]}')

