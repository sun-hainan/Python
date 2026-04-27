# -*- coding: utf-8 -*-

"""

算法实现：组合优化 / caratheodory_theorem



本文件实现 caratheodory_theorem 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple





class CaratheodoryRepresentation:

    """Carathéodory表示"""



    def __init__(self, points: List[np.ndarray]):

        """

        参数：

            points: 点列表

        """

        self.points = np.array(points)

        self.n, self.d = self.points.shape



    def represents_point(self, x: np.ndarray, eps: float = 1e-9) -> bool:

        """

        检查点是否在点的仿射包中



        返回：是否可表示

        """

        # 检查x是否在 points 的仿射包中

        # 即是否存在 λ 使得 sum(λ_i * points_i) = x 且 sum(λ_i) = 1



        # 构建方程组

        A = np.vstack([self.points.T, np.ones(self.n)])

        b = np.append(x, 1)



        # 最小二乘求解

        try:

            lambdas, residuals, rank, s = np.linalg.lstsq(A, b, rcond=None)

            reconstruction = A @ lambdas

            error = np.linalg.norm(reconstruction - b)



            return error < eps

        except:

            return False



    def find_caratheodory_representation(self, x: np.ndarray) -> Tuple[List[int], List[float]]:

        """

        找到x的Carathéodory表示



        参数：

            x: 目标点



        返回：(点的索引, 系数)

        """

        # 简化：贪心搜索

        best_indices = None

        best_coeffs = None

        best_error = float('inf')



        # 尝试所有 d+1 个点的组合

        from itertools import combinations



        max_points = self.d + 1



        for r in range(1, max_points + 1):

            for indices in combinations(range(self.n), r):

                subset = self.points[list(indices)]



                try:

                    # 求解凸组合

                    A = subset.T

                    ones = np.ones(len(indices))

                    A_aug = np.vstack([A, ones])



                    b = np.append(x, 1)

                    coeffs, residuals, rank, s = np.linalg.lstsq(A_aug, b, rcond=None)



                    # 检查系数是否非负

                    if all(c >= -1e-9 for c in coeffs):

                        error = residuals[0] if len(residuals) > 0 else 0

                        if error < best_error:

                            best_error = error

                            best_indices = list(indices)

                            best_coeffs = coeffs.tolist()



                except:

                    pass



        return best_indices, best_coeffs





def caratheodory_geometric():

    """Carathéodory几何"""

    print("=== Carathéodory几何 ===")

    print()

    print("定理内容：")

    print("  在 d 维空间中")

    print("  任何仿射组合都可以用 ≤ d+1 个点表示")

    print()

    print("例子：")

    print("  d=2 (平面)")

    print("  最多3个点可以表示平面上的任何点")

    print()

    print("推论：")

    print("  - 凸包是这些单纯形的并")

    print("  - 用于计算几何算法")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== Carathéodory定理测试 ===\n")



    np.random.seed(42)



    # 在2D中测试

    points = [

        np.array([0.0, 0.0]),

        np.array([1.0, 0.0]),

        np.array([0.0, 1.0]),

        np.array([0.5, 0.5])

    ]



    carrier = CaratheodoryRepresentation(points)



    # 测试点

    test_x = np.array([0.3, 0.2])



    print(f"测试点: {test_x}")

    print(f"点集: {points}")

    print()



    # 检查表示

    can_represent = carrier.represents_point(test_x)

    print(f"可表示: {can_represent}")



    # 找表示

    indices, coeffs = carrier.find_caratheodory_representation(test_x)



    if indices:

        print(f"表示: 点{indices}")

        print(f"系数: {[f'{c:.3f}' for c in coeffs]}")



        # 验证

        reconstruction = sum(c * points[i] for c, i in zip(coeffs, indices))

        print(f"重构: {reconstruction}")

        print(f"误差: {np.linalg.norm(reconstruction - test_x):.6f}")



    print()

    caratheodory_geometric()



    print()

    print("说明：")

    print("  - Carathéodory是凸几何的基本定理")

    print("  - 用于多面体算法")

    print("  - d+1 个点形成单纯形")

