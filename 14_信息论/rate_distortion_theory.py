# -*- coding: utf-8 -*-

"""

算法实现：14_信息论 / rate_distortion_theory



本文件实现 rate_distortion_theory 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict

import itertools

import math





def create_binary_symmetric_dist_matrix(p: float) -> np.ndarray:

    """

    创建二元对称信源的失真矩阵（汉明失真）



    参数:

        p: 错误概率（0到1之间）



    返回:

        2x2失真矩阵：

        d(0,0)=0, d(0,1)=1

        d(1,0)=1, d(1,1)=0

        加权平均失真 = p

    """

    return np.array([[0.0, 1.0], [1.0, 0.0]]) * p





def compute_rate_distortion_binary(beta: float, D: float) -> float:

    """

    计算二元对称信源的率失真函数 R(D)



    二元信源 X in {0, 1}, P(X=0)=beta, P(X=1)=1-beta

    汉明失真 d(x,y) = 0 if x=y else 1



    率失真函数（闭式解）：

    R(D) = H(beta) - H(D),  当 D <= min(beta, 1-beta)

         = 0,             当 D >= min(beta, 1-beta)



    其中 H(D) = -D log D - (1-D) log (1-D) 为二元熵函数（以2为底）



    参数:

        beta: 信源中符号0的概率 P(X=0)

        D: 允许的失真上界



    返回:

        R(D): 最小可达码率（bit/符号）

    """

    if D <= 0:

        return float('inf')

    if D >= min(beta, 1 - beta):

        return 0.0



    def binary_entropy(p):

        if p <= 0 or p >= 1:

            return 0.0

        return -p * np.log2(p) - (1 - p) * np.log2(1 - p)



    H_beta = binary_entropy(beta)

    H_D = binary_entropy(D)

    R_D = H_beta - H_D

    return max(0.0, R_D)





def rate_distortion_iterative(

    beta: np.ndarray,

    dist_matrix: np.ndarray,

    D_max: float,

    max_iter: int = 1000,

    tol: float = 1e-6

) -> Tuple[float, Dict]:

    """

    迭代计算一般离散信源的率失真函数 R(D)



    使用 Blahut-Arimoto 算法求解



    参数:

        beta: 信源分布数组（和为1）

        dist_matrix: 失真矩阵 dist_matrix[i][j] = d(x_i, y_j)

        D_max: 最大允许失真

        max_iter: 最大迭代次数

        tol: 收敛阈值



    返回:

        (R_D, info_dict): R_D为率失真函数值，info包含迭代信息

    """

    n_states = len(beta)

    m_outputs = dist_matrix.shape[1]



    min_possible_D = sum(beta[i] * min(dist_matrix[i, :]) for i in range(n_states))

    if D_max < min_possible_D - 1e-9:

        return float('inf'), {'converged': False, 'reason': 'D too small'}



    q_y_given_x = np.ones((n_states, m_outputs)) / m_outputs

    Q_y = np.sum(beta[:, None] * q_y_given_x, axis=0)



    for iteration in range(max_iter):

        D_current = sum(beta[i] * sum(q_y_given_x[i, j] * dist_matrix[i, j]

                                       for j in range(m_outputs))

                        for i in range(n_states))



        if abs(D_current - D_max) < tol:

            break



        grad = np.zeros((n_states, m_outputs))

        for i in range(n_states):

            for j in range(m_outputs):

                grad[i, j] = beta[i] * dist_matrix[i, j] / (Q_y[j] + 1e-10)



        alpha = 0.1 * (D_current - D_max) / (D_current + 1e-10)

        alpha = max(-0.5, min(0.5, alpha))



        q_y_given_x = q_y_given_x - alpha * grad



        for i in range(n_states):

            row = q_y_given_x[i, :]

            row = np.maximum(row, 0)

            row_sum = row.sum()

            if row_sum > 1e-10:

                q_y_given_x[i, :] = row / row_sum

            else:

                q_y_given_x[i, :] = np.ones(m_outputs) / m_outputs



        Q_y = np.sum(beta[:, None] * q_y_given_x, axis=0)



    R_D = 0.0

    for i in range(n_states):

        for j in range(m_outputs):

            if q_y_given_x[i, j] > 1e-10:

                R_D += beta[i] * q_y_given_x[i, j] * np.log2(

                    q_y_given_x[i, j] / (Q_y[j] + 1e-10) + 1e-10

                )



    R_D = max(0.0, R_D)



    info = {

        'converged': iteration < max_iter - 1,

        'iterations': iteration + 1,

        'final_distortion': D_current,

        'output_dist': Q_y

    }



    return R_D, info





def compute_distortion(beta, q_y_given_x, dist_matrix):

    """计算给定编码策略下的期望失真 E[D] = sum beta(x) * sum q(y|x) * d(x,y)"""

    n_states = len(beta)

    m_outputs = dist_matrix.shape[1]

    D = 0.0

    for i in range(n_states):

        for j in range(m_outputs):

            D += beta[i] * q_y_given_x[i, j] * dist_matrix[i, j]

    return D





if __name__ == '__main__':

    print('=== 率失真理论测试 ===')



    print('--- 测试1: 二元对称信源 R(D) ---')

    for beta in [0.5, 0.3, 0.1]:

        print(f'信源分布 P(X=0) = {beta}:')

        for D in np.linspace(0.01, min(beta, 1-beta)*0.99, 5):

            R_D = compute_rate_distortion_binary(beta, D)

            print(f'  D={D:.3f} -> R(D)={R_D:.4f} bits/symbol')



    print('--- 测试2: Blahut-Arimoto迭代算法 ---')

    beta = np.array([1/3, 1/3, 1/3])

    dist_matrix = np.array([

        [0.0, 1.0, 4.0],

        [1.0, 0.0, 1.0],

        [4.0, 1.0, 0.0]

    ])

    D_max = 0.8

    R_D, info = rate_distortion_iterative(beta, dist_matrix, D_max)

    print(f'信源分布: {beta}')

    print(f'目标失真 D_max = {D_max}')

    print(f'率失真函数 R(D) = {R_D:.4f} bits/symbol')

    print(f'收敛: {info["converged"]}, 迭代次数: {info["iterations"]}')

    print(f'实际失真: {info["final_distortion"]:.4f}')



    print('--- 测试3: 率失真曲线 (二元信源, beta=0.5) ---')

    beta = 0.5

    D_range = np.linspace(0.01, 0.49, 10)

    for D in D_range:

        R_D = compute_rate_distortion_binary(beta, D)

        bar = '#' * int(R_D * 20)

        print(f'  D={D:.3f}: R(D)={R_D:.4f} |{bar}')

