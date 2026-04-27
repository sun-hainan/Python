# -*- coding: utf-8 -*-

"""

算法实现：14_信息论 / rate_distortion_function



本文件实现 rate_distortion_function 相关的算法功能。

"""



import numpy as np

from typing import Tuple, List, Dict

import math





def rate_distortion_gaussian(sigma_sq: float, D: float) -> float:

    """

    高斯信源的率失真函数（均方误差失真）



    R(D) = max(0, log2(sigma^2/D))  bits/sample



    参数:

        sigma_sq: 信源方差 sigma^2

        D: 允许的均方误差 D（D <= sigma^2 时有效）



    返回:

        R(D) bits/sample

    """

    if D <= 0:

        return float('inf')

    if D >= sigma_sq:

        return 0.0

    return max(0.0, math.log2(sigma_sq / D))





def distortion_gaussian(R: float, sigma_sq: float) -> float:

    """

    高斯信源的反函数：从码率R计算最小可达失真



    D(R) = sigma^2 / 2^{2R}



    参数:

        R: 码率 bits/sample

        sigma_sq: 信源方差



    返回:

        最小失真 D

    """

    return sigma_sq / (2 ** (2 * R))





def rate_distortion_laplace(alpha: float, D: float) -> float:

    """

    拉普拉斯信源的率失真函数（绝对值失真）



    简化近似（对小D）：R(D) ~= log2(1/(alpha*D)) - alpha*D/ln2



    参数:

        alpha: 拉普拉斯分布参数

        D: 允许的平均绝对误差失真



    返回:

        R(D) bits/sample（近似）

    """

    if D <= 0:

        return float('inf')

    if D >= 1/alpha:

        return 0.0

    if D < 0.1 / alpha:

        R_approx = math.log2(1.0 / (alpha * D)) - alpha * D / math.log(2)

        return max(0.0, R_approx)

    return max(0.0, math.log2(1.0 / (alpha * D + 1e-10)))





def rate_distortion_binary(epsilon: float, D: float) -> float:

    """

    二元对称信源的率失真函数



    X in {0,1}, P(X=1) = epsilon, 汉明失真 d(x,y) = 0 if x=y else 1



    R(D) = H(epsilon) - H(D)  当 D <= min(epsilon, 1-epsilon)

         = 0              当 D >= min(epsilon, 1-epsilon)



    参数:

        epsilon: P(X=1)

        D: 允许的汉明失真



    返回:

        R(D) bits/sample

    """

    def H_bin(p):

        if p <= 0 or p >= 1:

            return 0.0

        return -p * math.log2(p) - (1-p) * math.log2(1-p)



    D_thresh = min(epsilon, 1 - epsilon)

    if D >= D_thresh:

        return 0.0

    if D < 0:

        return float('inf')



    H_eps = H_bin(epsilon)

    H_D = H_bin(D)

    return max(0.0, H_eps - H_D)





def rate_distortion_gaussian_mse(sigma_sq: float, D: float) -> float:

    """

    高斯信源在均方误差（MSE）失真下的率失真函数



    R(D) = (1/2) * log2(sigma^2/D)  bits/sample



    参数:

        sigma_sq: 信源方差

        D: 允许MSE



    返回:

        R(D) bits/sample

    """

    if D <= 0:

        return float('inf')

    if D >= sigma_sq:

        return 0.0

    return max(0.0, 0.5 * math.log2(sigma_sq / D))





def blahut_arimoto_rate_distortion(

    P_x: np.ndarray,

    dist_matrix: np.ndarray,

    D_max: float,

    max_iter: int = 500,

    tol: float = 1e-6,

    lambda_init: float = 0.0

) -> Tuple[float, np.ndarray, Dict]:

    """

    Blahut-Arimoto算法计算一般信源的率失真函数



    参数:

        P_x: 信源分布，shape (n_states,)

        dist_matrix: 失真矩阵，shape (n_states, n_outputs)

        D_max: 最大允许失真

        max_iter: 最大迭代次数

        tol: 收敛阈值

        lambda_init: 初始拉格朗日乘子



    返回:

        (R_D, Q_opt, info): R_D为率失真函数值，Q_opt为最优重构分布

    """

    n_states = P_x.shape[0]

    m_outputs = dist_matrix.shape[1]



    Q = np.ones((n_states, m_outputs)) / m_outputs

    lambda_ld = lambda_init



    for iteration in range(max_iter):

        Q_new = np.zeros((n_states, m_outputs))

        for i in range(n_states):

            denom = sum(math.exp(-lambda_ld * dist_matrix[i, j]) for j in range(m_outputs))

            for j in range(m_outputs):

                Q_new[i, j] = math.exp(-lambda_ld * dist_matrix[i, j]) / denom



        D_current = 0.0

        for i in range(n_states):

            for j in range(m_outputs):

                D_current += P_x[i] * Q_new[i, j] * dist_matrix[i, j]



        if abs(D_current - D_max) < tol:

            break



        if D_current > D_max:

            lambda_ld *= 0.5

        else:

            lambda_ld *= 1.5



        lambda_ld = np.clip(lambda_ld, -10, 10)

        Q = Q_new



    R_D = 0.0

    for i in range(n_states):

        for j in range(m_outputs):

            if Q[i, j] > 1e-10 and P_x[i] > 1e-10:

                R_D += P_x[i] * Q[i, j] * lambda_ld * dist_matrix[i, j]



    R_D = max(0.0, R_D / math.log(2))



    P_y = np.sum(P_x[:, None] * Q, axis=0)



    info = {

        'iterations': iteration + 1,

        'final_distortion': D_current,

        'lambda': lambda_ld,

        'P_y': P_y

    }



    return R_D, Q, info





if __name__ == '__main__':

    print('=== 率失真函数测试 ===')



    print('--- 测试1: 高斯信源率失真函数 R(D) ---')

    sigma_sq = 1.0

    print(f'sigma^2 = {sigma_sq}')

    print(f'{"D":>8}  {"R(D) bits":>12}  {"D(R)":>10}')

    print('  ' + '-' * 35)

    for D in [0.1, 0.2, 0.3, 0.5, 0.7, 1.0]:

        R_D = rate_distortion_gaussian(sigma_sq, D)

        D_from_R = distortion_gaussian(R_D, sigma_sq)

        bar = '#' * int(R_D * 5)

        print(f'  {D:8.2f}  {R_D:12.4f}  {D_from_R:10.4f} |{bar}')



    print('--- 测试2: 二元信源率失真函数 ---')

    eps = 0.3

    print(f'P(X=1) = {eps}')

    print(f'{"D":>8}  {"R(D) bits":>12}')

    print('  ' + '-' * 25)

    for D in np.linspace(0.01, 0.29, 10):

        R_D = rate_distortion_binary(eps, D)

        bar = '#' * int(R_D * 20)

        print(f'  {D:8.3f}  {R_D:12.4f} |{bar}')



    print('--- 测试3: 不同信源类型的率失真对比 ---')

    D_vals = np.linspace(0.05, 0.95, 20)

    print(f'{"D":>6}  {"Gaussian":>12}  {"GaussianMSE":>12}  {"Binary":>10}  {"Laplace":>10}')

    print('  ' + '-' * 55)

    for D in D_vals:

        R_g = rate_distortion_gaussian(1.0, D)

        R_gmse = rate_distortion_gaussian_mse(1.0, D)

        R_b = rate_distortion_binary(0.5, D)

        R_l = rate_distortion_laplace(1.0, D)

        print(f'  {D:6.2f}  {R_g:12.4f}  {R_gmse:12.4f}  {R_b:10.4f}  {R_l:10.4f}')



    print('--- 测试4: Blahut-Arimoto算法（一般信源）---')

    P_x = np.array([0.25, 0.25, 0.25, 0.25])

    dist_matrix = np.array([

        [0.0, 1.0, 4.0, 9.0],

        [1.0, 0.0, 1.0, 4.0],

        [4.0, 1.0, 0.0, 1.0],

        [9.0, 4.0, 1.0, 0.0]

    ])



    for D_max in [0.5, 1.0, 2.0, 3.0]:

        R_D, Q, info = blahut_arimoto_rate_distortion(P_x, dist_matrix, D_max)

        print(f'  D_max={D_max:.1f}: R(D)={R_D:.4f} bits, 实际D={info["final_distortion"]:.4f}, iter={info["iterations"]}')



    print('--- 测试5: 率失真函数性质验证 ---')

    sigma_sq = 2.0

    print(f'高斯信源 sigma^2={sigma_sq}: R(0)={rate_distortion_gaussian(sigma_sq, 0):.4f}')

    print(f'  R(sigma^2)={rate_distortion_gaussian(sigma_sq, sigma_sq):.4f} (应为0)')

    D_test = 0.5

    R_D = rate_distortion_gaussian(sigma_sq, D_test)

    D_check = distortion_gaussian(R_D, sigma_sq)

    print(f'  互逆性: D={D_test:.4f} -> R={R_D:.4f} -> D={D_check:.4f}')

