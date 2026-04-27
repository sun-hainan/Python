# -*- coding: utf-8 -*-

"""

算法实现：次线性算法 / linear_programming_test



本文件实现 linear_programming_test 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple





class LinearProgrammingTester:

    """线性规划测试器"""



    def __init__(self, A: np.ndarray, b: np.ndarray):

        self.A = A

        self.b = b

        self.m, self.n = A.shape



    def feasibility_check(self, x: np.ndarray, eps: float = 1e-6) -> Tuple[bool, List[int]]:

        """

        检查点是否可行



        返回：(是否可行, 违反约束的索引)

        """

        violations = []



        for i in range(self.m):

            if np.dot(self.A[i], x) > self.b[i] + eps:

                violations.append(i)



        return len(violations) == 0, violations



    def find_feasible_point(self) -> np.ndarray:

        """

        寻找一个可行点



        使用随机游走 + 修复

        """

        x = np.zeros(self.n)



        # 简化：从原点开始，修复约束

        for _ in range(1000):

            is_feas, violations = self.feasibility_check(x)



            if is_feas:

                return x



            # 选择一个违反的约束并修复

            if violations:

                i = violations[0]

                # 沿约束法线方向移动

                gradient = self.A[i]

                step = (np.dot(self.A[i], x) - self.b[i]) / (np.dot(gradient, gradient) + 1e-10)

                x -= step * gradient * 0.9



        return x





def separation_oracle():

    """分离Oracle"""

    print("=== 分离Oracle ===")

    print()

    print("给定 x*，判断是否在多面体内：")

    print("  - 如果在，返回 True")

    print("  - 如果不在，返回违反的约束")

    print()

    print("应用：")

    print("  - 椭球法需要分离Oracle")

    print("  - 切割平面方法")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 线性规划测试 ===\n")



    # 简单可行域：x1 + x2 ≤ 4, x1 ≥ 0, x2 ≥ 0

    A = np.array([

        [1, 1],

        [-1, 0],

        [0, -1]

    ])

    b = np.array([4, 0, 0])



    tester = LinearProgrammingTester(A, b)



    # 测试点

    test_points = [

        np.array([1.0, 1.0]),

        np.array([3.0, 3.0]),

        np.array([-1.0, 2.0])

    ]



    print("可行域：x1 + x2 ≤ 4, x1 ≥ 0, x2 ≥ 0")

    print()



    for x in test_points:

        is_feas, violations = tester.feasibility_check(x)

        print(f"点 ({x[0]:.1f}, {x[1]:.1f}): "

              f"{'可行' if is_feas else '不可行'}"

              f"{'' if is_feas else f', 违反约束 {violations}'}")



    print()

    separation_oracle()



    print()

    print("说明：")

    print("  - LP测试是优化的基础")

    print("  - 用于验证可行域")

    print("  - 组合优化中的切割平面方法")

