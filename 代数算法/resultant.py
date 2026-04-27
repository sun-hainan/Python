# -*- coding: utf-8 -*-
"""
算法实现：代数算法 / resultant

本文件实现 resultant 相关的算法功能。
"""

from typing import List, Tuple


class SylvesterMatrix:
    """Sylvester矩阵（结式计算）"""

    def __init__(self, p: List[float], q: List[float]):
        """
        参数：
            p: 多项式p的系数（从常数项开始）
            q: 多项式q的系数
        """
        self.p = p
        self.q = q
        self.n = len(p) - 1  # deg(p)
        self.m = len(q) - 1  # deg(q)

    def build_sylvester_matrix(self) -> List[List[float]]:
        """
        构建Sylvester矩阵

        返回：矩阵
        """
        size = self.n + self.m

        matrix = [[0.0] * size for _ in range(size)]

        # 填充p的部分
        for i in range(self.m):
            for j in range(self.n + 1):
                if i + j < size:
                    matrix[i][i + j] = self.p[j]

        # 填充q的部分
        for i in range(self.n):
            for j in range(self.m + 1):
                if i + j < size:
                    matrix[self.m + i][i + j] = self.q[j]

        return matrix

    def determinant(self) -> float:
        """
        计算行列式（结式）

        返回：结式值
        """
        matrix = self.build_sylvester_matrix()

        # 简化：使用高斯消元
        n = len(matrix)
        det = 1.0

        for i in range(n):
            # 找主元
            pivot = matrix[i][i]
            if abs(pivot) < 1e-10:
                # 搜索下面行
                found = False
                for k in range(i + 1, n):
                    if abs(matrix[k][i]) > 1e-10:
                        matrix[i], matrix[k] = matrix[k], matrix[i]
                        pivot = matrix[i][i]
                        det *= -1
                        found = True
                        break

                if not found:
                    return 0.0

            # 消元
            for k in range(i + 1, n):
                factor = matrix[k][i] / pivot
                for j in range(i, n):
                    matrix[k][j] -= factor * matrix[i][j]

            det *= pivot

        return det

    def has_common_root(self, eps: float = 1e-9) -> bool:
        """
        判断是否有公共根

        返回：是否有公共根
        """
        res = self.determinant()
        return abs(res) < eps


def resultant_properties():
    """结式性质"""
    print("=== 结式性质 ===")
    print()
    print("定义：")
    print("  res(p, q) = a_n^m × b_m^n × ∏(α_i - β_j)")
    print()
    print("性质：")
    print("  - res(p, q) = 0 ⟺ p 和 q 有公共根")
    print("  - res(p, q) = (-1)^{nm} res(q, p)")
    print("  - res(p, q) = a_n^m × ∏ q(α_i)")
    print()
    print("应用：")
    print("  - 多项式系统求解")
    print("  - 消去理论")
    print("  - 代数曲线交点")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 结式计算测试 ===\n")

    # 多项式 p(x) = x² - 3x + 2 = (x-1)(x-2)
    p = [2.0, -3.0, 1.0]

    # 多项式 q(x) = x - 2
    q = [-2.0, 1.0]

    sylvester = SylvesterMatrix(p, q)

    print(f"p(x) = x² - 3x + 2")
    print(f"q(x) = x - 2")
    print(f"公共根: x = 2")
    print()

    res = sylvester.determinant()
    print(f"结式: {res}")

    has_common = sylvester.has_common_root()
    print(f"有公共根: {has_common}")

    print()

    # 另一个例子：p(x) = x² + 1（无实根）
    p2 = [1.0, 0.0, 1.0]
    q2 = [1.0, -1.0]

    sylvester2 = SylvesterMatrix(p2, q2)
    res2 = sylvester2.determinant()

    print(f"p(x) = x² + 1")
    print(f"q(x) = x - 1")
    print(f"结式: {res2}")
    print(f"有公共根: {sylvester2.has_common_root()}")

    print()
    resultant_properties()

    print()
    print("说明：")
    print("  - 结式是多项式理论的重要工具")
    print("  - 用于判断公共根和求解方程组")
    print("  - Sylvester矩阵大小为 (n+m)²")
