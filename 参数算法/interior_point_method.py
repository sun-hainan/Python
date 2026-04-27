# -*- coding: utf-8 -*-

"""

算法实现：参数算法 / interior_point_method



本文件实现 interior_point_method 相关的算法功能。

"""



import numpy as np

from typing import Tuple





class InteriorPointMethod:

    """内点法求解器"""



    def __init__(self, max_iter: int = 100, tol: float = 1e-6):

        self.max_iter = max_iter

        self.tol = tol



    def solve_lp(self, c: np.ndarray, A: np.ndarray, b: np.ndarray) -> Tuple[np.ndarray, float]:

        """

        求解线性规划



        min c^T x

        s.t. Ax = b

             x >= 0



        参数：

            c: 目标函数系数

            A: 约束矩阵

            b: 约束右端



        返回：(最优解, 最优值)

        """

        m, n = A.shape



        # 初始可行点

        x = np.ones(n)

        s = np.ones(n)  # 松弛变量



        # 中心参数

        mu = 1.0



        for iteration in range(self.max_iter):

            # 计算残差

            r = A @ x - b

            rx = A.T @ (x * s) + c  # KKT残差



            # 检测收敛

            norm_r = np.linalg.norm(np.concatenate([r, rx]))

            if norm_r < self.tol:

                print(f"  收敛于第{iteration}次迭代")

                return x, np.dot(c, x)



            # 构建牛顿系统

            # [0   A^T] [dx]   [-rx]

            # [A   D ] [ds] =  [-rs]

            # D = X^{-1}S



            D = np.diag(x / s)

            M = A @ D @ A.T



            # 求解

            try:

                dx = -D @ (A.T @ np.linalg.solve(M, r + A @ D @ rx) - rx)

                ds = -(x / s) * (A.T @ np.linalg.solve(M, r + A @ D @ rx))

            except np.linalg.LinAlgError:

                print("  线性系统求解失败")

                break



            # 线搜索

            alpha = 1.0

            for _ in range(10):

                if np.all(x + alpha * dx > 0) and np.all(s + alpha * ds > 0):

                    break

                alpha *= 0.5



            x += alpha * dx

            s += alpha * ds



            # 更新mu

            mu *= 0.9



        return x, np.dot(c, x)





def simplex_method(c: np.ndarray, A: np.ndarray, b: np.ndarray) -> Tuple[np.ndarray, float]:

    """

    单纯形法（对比用）



    线性规划的经典求解器

    """

    m, n = A.shape



    # 添加人工变量构造可行初始基

    A_aug = np.hstack([A, np.eye(m)])

    c_aug = np.concatenate([c, np.zeros(m)])



    # 简化的两阶段法

    # ...



    return np.zeros(n), 0.0  # 占位





def barrier_function(c: np.ndarray, A: np.ndarray, b: np.ndarray) -> np.ndarray:

    """

    障碍函数法



    在目标函数中加入-log(x)的障碍



    min c^T x - mu * sum(log(x_i))

    """

    mu_values = [1.0, 0.1, 0.01, 0.001]



    x = np.ones(len(c))



    for mu in mu_values:

        # 梯度：c - mu * X^{-1} * 1

        gradient = c - mu * (1.0 / x)



        # 简化梯度下降

        alpha = 0.1

        x = x - alpha * gradient

        x = np.maximum(x, 1e-6)  # 保持正



    return x





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 内点法测试 ===\n")



    # 简单线性规划

    # min -x1 - x2

    # s.t. x1 + x2 <= 2

    #      x1 <= 1

    #      x2 <= 1

    #      x1, x2 >= 0



    print("线性规划问题:")

    print("  min -x1 - x2")

    print("  s.t. x1 + x2 <= 2")

    print("         x1 <= 1")

    print("         x2 <= 1")

    print("         x1, x2 >= 0")

    print()



    # 转化为标准形式

    c = np.array([-1.0, -1.0])



    # Ax = b

    # x1 + s1 = 1 (x1 <= 1 -> x1 + s1 = 1, s1 >= 0)

    # x2 + s2 = 1 (x2 <= 1)

    # x1 + x2 + s3 = 2 (x1 + x2 <= 2)

    # x1, x2, s1, s2, s3 >= 0



    # 简化为等式约束

    A = np.array([

        [1, 0],  # x1

        [0, 1],  # x2

        [1, 1],  # x1 + x2

    ])

    b = np.array([1, 1, 2])



    solver = InteriorPointMethod(max_iter=50)



    try:

        x, obj = solver.solve_lp(c, A, b)

        print(f"内点法结果:")

        print(f"  x1 = {x[0]:.4f}")

        print(f"  x2 = {x[1]:.4f}")

        print(f"  最优值 = {-obj:.4f}")



        print()

        print("验证:")

        print(f"  x1 + x2 = {x[0] + x[1]:.4f} <= 2")

        print(f"  最优解应该是 x1=1, x2=1, 值=-2")

    except Exception as e:

        print(f"求解失败: {e}")



    print("\n说明：")

    print("  - 内点法复杂度 O(n^3)")

    print("  - 比单纯形法更适合大规模问题")

    print("  - 用于LP、QP、SDP")

