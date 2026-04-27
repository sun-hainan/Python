# -*- coding: utf-8 -*-

"""

算法实现：14_信息论 / shannon_channel_capacity



本文件实现 shannon_channel_capacity 相关的算法功能。

"""



import numpy as np

from typing import Tuple, Dict, List

import math





def capacity_bsc(p: float) -> float:

    """

    计算二元对称信道（Binary Symmetric Channel）的容量



    BSC(p): 输入X in {0,1}, P(Y=X|X)=1-p, P(Y!=X|X)=p

    容量（闭式解）: C = 1 - H(p)  bits/channel use



    参数:

        p: 翻转概率（0到0.5之间）



    返回:

        C: 信道容量（bit/符号）

    """

    p = min(p, 1 - p)

    if p == 0 or p == 0.5:

        return 0.0 if p == 0.5 else 1.0

    H_p = -p * math.log2(p + 1e-10) - (1 - p) * math.log2(1 - p + 1e-10)

    C = 1 - H_p

    return max(0.0, C)





def capacity_bec(eps: float) -> float:

    """

    计算二元擦除信道（Binary Erasure Channel）的容量



    BEC(epsilon): 输入X in {0,1},

        P(Y=X|X) = 1-epsilon, P(Y=e|X) = epsilon



    容量（闭式解）: C = 1 - epsilon  bits/channel use



    参数:

        eps: 擦除概率（0到1之间）



    返回:

        C: 信道容量（bit/符号）

    """

    return max(0.0, 1.0 - eps)





def blahut_arimoto_capacity(

    P_y_given_x: np.ndarray,

    P_x_init: np.ndarray = None,

    max_iter: int = 1000,

    tol: float = 1e-6

) -> Tuple[float, np.ndarray, Dict]:

    """

    Blahut-Arimoto算法计算离散无记忆信道的容量



    参数:

        P_y_given_x: 转移概率矩阵，shape (n_inputs, n_outputs)

        P_x_init: 初始输入分布，默认均匀分布

        max_iter: 最大迭代次数

        tol: 收敛阈值



    返回:

        (C, P_x_opt, info): 信道容量、最优输入分布、迭代信息

    """

    n_inputs = P_y_given_x.shape[0]

    n_outputs = P_y_given_x.shape[1]



    if P_x_init is None:

        P_x = np.ones(n_inputs) / n_inputs

    else:

        P_x = P_x_init.copy()

        P_x = np.maximum(P_x, 0)

        P_x = P_x / P_x.sum()



    capacity_history = []



    for iteration in range(max_iter):

        P_y = np.sum(P_x[:, None] * P_y_given_x, axis=0)

        P_y = np.maximum(P_y, 1e-10)

        P_y = P_y / P_y.sum()



        I_current = 0.0

        for i in range(n_inputs):

            for j in range(n_outputs):

                if P_y_given_x[i, j] > 1e-10:

                    I_current += P_x[i] * P_y_given_x[i, j] * np.log2(

                        P_y_given_x[i, j] / P_y[j] + 1e-10

                    )

        capacity_history.append(max(0, I_current))



        I_given_x = np.zeros(n_inputs)

        for i in range(n_inputs):

            for j in range(n_outputs):

                if P_y_given_x[i, j] > 1e-10:

                    I_given_x[i] += P_y_given_x[i, j] * np.log2(

                        P_y_given_x[i, j] / P_y[j] + 1e-10

                    )



        P_x_new = P_x * np.power(2.0, I_given_x)

        P_x_new = np.maximum(P_x_new, 1e-10)

        P_x_new = P_x_new / P_x_new.sum()



        change = np.abs(P_x_new - P_x).max()

        P_x = P_x_new



        if change < tol:

            break



    P_y = np.sum(P_x[:, None] * P_y_given_x, axis=0)

    P_y = np.maximum(P_y, 1e-10)

    C = 0.0

    for i in range(n_inputs):

        for j in range(n_outputs):

            if P_y_given_x[i, j] > 1e-10:

                C += P_x[i] * P_y_given_x[i, j] * np.log2(

                    P_y_given_x[i, j] / P_y[j] + 1e-10

                )



    info = {

        'iterations': iteration + 1,

        'converged': iteration < max_iter - 1,

        'capacity_history': capacity_history,

        'P_y_final': P_y

    }



    return max(0.0, C), P_x, info





def mutual_information(P_x: np.ndarray, P_y_given_x: np.ndarray) -> float:

    """计算互信息量 I(X;Y) = sum_{x,y} P(x,y) log[P(x,y)/(P(x)P(y))]"""

    n_inputs = len(P_x)

    P_y = np.sum(P_x[:, None] * P_y_given_x, axis=0)

    P_y = np.maximum(P_y, 1e-10)



    I = 0.0

    for i in range(n_inputs):

        for j in range(len(P_y)):

            P_xy = P_x[i] * P_y_given_x[i, j]

            if P_xy > 1e-10:

                I += P_xy * np.log2(P_xy / (P_x[i] * P_y[j]) + 1e-10)

    return max(0.0, I)





if __name__ == '__main__':

    print('=== 香农信道容量测试 ===')



    print('--- 测试1: 二元对称信道(BSC)容量 ---')

    print(' BSC(p): 翻转概率p, 容量C = 1 - H(p)')

    for p in [0.0, 0.01, 0.05, 0.1, 0.2, 0.3, 0.5]:

        C = capacity_bsc(p)

        bar = '#' * int(C * 30)

        print(f'  p={p:.2f}: C={C:.4f} bits/use |{bar}')



    print('--- 测试2: 二元擦除信道(BEC)容量 ---')

    print(' BEC(epsilon): 擦除概率epsilon, 容量C = 1 - epsilon')

    for eps in [0.0, 0.1, 0.2, 0.3, 0.5, 0.6]:

        C = capacity_bec(eps)

        bar = '#' * int(C * 30)

        print(f'  eps={eps:.2f}: C={C:.4f} bits/use |{bar}')



    print('--- 测试3: 一般离散信道 Blahut-Arimoto ---')

    P_y_given_x = np.array([

        [0.9, 0.1],

        [0.5, 0.5],

        [0.1, 0.9],

    ])

    C, P_x_opt, info = blahut_arimoto_capacity(P_y_given_x, max_iter=500)

    print(f'转移矩阵:\n{P_y_given_x}')

    print(f'信道容量 C = {C:.4f} bits/channel use')

    print(f'最优输入分布: P(X=0)={P_x_opt[0]:.4f}, P(X=1)={P_x_opt[1]:.4f}, P(X=2)={P_x_opt[2]:.4f}')

    print(f'收敛: {info["converged"]}, 迭代次数: {info["iterations"]}')



    print('--- 测试4: 不同输入分布的互信息对比 ---')

    test_dists = [

        ('均匀', np.array([1/3, 1/3, 1/3])),

        ('偏0', np.array([0.8, 0.1, 0.1])),

        ('偏2', np.array([0.1, 0.1, 0.8])),

    ]

    for name, P_x_test in test_dists:

        I_test = mutual_information(P_x_test, P_y_given_x)

        print(f'  {name}: I={I_test:.4f} bits')

