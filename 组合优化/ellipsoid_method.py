# -*- coding: utf-8 -*-

"""

算法实现：组合优化 / ellipsoid_method



本文件实现 ellipsoid_method 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple





class EllipsoidMethod:

    """椭球法"""



    def __init__(self, A: np.ndarray, b: np.ndarray):

        """

        参数：

            A: 约束矩阵 (Ax ≤ b)

            b: 约束右端

        """

        self.A = A

        self.b = b

        self.m, self.n = A.shape



    def solve(self, c: np.ndarray, max_iter: int = 100) -> Tuple[np.ndarray, float]:

        """

        求解线性规划



        min c^T x

        s.t. Ax ≤ b



        返回：(最优解, 最优值)

        """

        # 初始化椭球（包含可行域）

        x_center = np.zeros(self.n)

        Q = np.eye(self.n) * 1e6  # 初始椭球



        for iteration in range(max_iter):

            # 检查中心是否可行

            if self._is_feasible(x_center):

                return x_center, np.dot(c, x_center)



            # 找到一个违反的约束

            for i in range(self.m):

                if np.dot(self.A[i], x_center) > self.b[i] + 1e-6:

                    # 更新椭球

                    a = self.A[i]

                    a_norm_sq = np.dot(a, np.dot(Q, a))



                    # 新的中心和矩阵

                    alpha = (np.dot(a, x_center) - self.b[i]) / a_norm_sq



                    x_new = x_center - alpha * np.dot(Q, a)

                    beta = (self.n + 1) / (self.n - 1)



                    Q_new = beta * (Q - 2 * alpha / (a_norm_sq + alpha) *

                                np.outer(np.dot(Q, a), np.dot(Q, a)))



                    x_center = x_new

                    Q = Q_new

                    break



        return x_center, np.dot(c, x_center)



    def _is_feasible(self, x: np.ndarray, eps: float = 1e-6) -> bool:

        """检查可行性"""

        for i in range(self.m):

            if np.dot(self.A[i], x) > self.b[i] + eps:

                return False

        return True





def ellipsoid_vs_simplex():

    """椭球法 vs 单纯形法"""

    print("=== 椭球法 vs 单纯形法 ===")

    print()

    print("单纯形法：")

    print("  - 指数最坏情况")

    print("  - 在实践中快")

    print("  - 沿着可行域边界移动")

    print()

    print("椭球法：")

    print("  - 多项式时间保证")

    print("  - 在实践中慢")

    print("  - 在可行域内部移动")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 椭球法测试 ===\n")



    # 简单问题：min x1 + x2

    # s.t. x1 + x2 ≤ 4

    #      x1 - x2 ≤ 1

    #      -x1 + 2x2 ≤ 2

    #      x1, x2 ≥ 0



    A = np.array([

        [1, 1],

        [1, -1],

        [-1, 2],

        [-1, 0],

        [0, -1]

    ])

    b = np.array([4, 1, 2, 0, 0])



    c = np.array([1, 1])



    ellipsoid = EllipsoidMethod(A, b)

    x, value = ellipsoid.solve(c)



    print(f"问题：min x1 + x2")

    print(f"约束：Ax ≤ b")

    print()

    print(f"解：x1={x[0]:.4f}, x2={x[1]:.4f}")

    print(f"最优值：{value:.4f}")

    print(f"验证可行：{ellipsoid._is_feasible(x)}")



    print()

    ellipsoid_vs_simplex()



    print()

    print("说明：")

    print("  - 椭球法是理论重大突破")

    print("  - 实际中不如单纯形法")

    print("  - 用于证明多项式时间可解性")

