# -*- coding: utf-8 -*-
"""
算法实现：细粒度复杂性 / all_pairs_spth

本文件实现 all_pairs_spth 相关的算法功能。
"""

import numpy as np
from typing import List, Tuple


class APSPComplexity:
    """APSP复杂度分析"""

    def __init__(self, n: int):
        """
        参数：
            n: 顶点数
        """
        self.n = n

    def estimate_lower_bound(self) -> str:
        """
        估计下界

        返回：下界描述
        """
        # 已知下界：Ω(n³ / log n)
        # 如果 n=100，复杂度至少是 1000000 量级

        lower = self.n ** 3 / (np.log(self.n) + 1)

        if lower < 1e6:
            return f"Ω({lower:.0f}) 操作"
        else:
            return f"Ω({lower/1e6:.1f}M) 操作"

    def dijkstra_complexity(self) -> Tuple[str, str]:
        """
        Dijkstra方法的复杂度

        返回：(时间, 空间)
        """
        time_complexity = f"O(n(m + n log n))"
        space_complexity = "O(n²) 存储距离矩阵"

        return time_complexity, space_complexity

    def matrix_multiplication_apsp(self) -> Tuple[str, str]:
        """
        矩阵乘法APSP的复杂度

        返回：(时间, 空间)
        """
        # 用 Floyd-Warshall: O(n³)
        time_complexity = "O(n³)"
        space_complexity = "O(n²)"

        return time_complexity, space_complexity

    def seidel_algorithm(self) -> Tuple[str, str]:
        """
        Seidel算法的复杂度（用于整数权重）

        返回：(时间, 空间)
        """
        # O(n^ω log n) 其中 ω < 2.373
        time_complexity = "O(n^{2.373} log n)"
        space_complexity = "O(n²)"

        return time_complexity, space_complexity


def apsp_lower_bounds():
    """APSP下界"""
    print("=== APSP下界 ===")
    print()
    print("已知下界：")
    print("  - 组合下界：Ω(n² log n) 操作")
    print("  - 代数下界：Ω(n^{ω}) 其中 ω > 2")
    print()
    print("条件下界：")
    print("  - 如果APSP可以在 O(n^{3-ε}) 解决")
    print("  - 则某些困难假设失败")
    print()
    print("应用：")
    print("  - 图算法设计")
    print("  - 路由协议")
    print("  - 距离数据库")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== APSP复杂度测试 ===\n")

    for n in [10, 50, 100, 200]:
        apsp = APSPComplexity(n)

        print(f"n = {n}:")
        print(f"  下界: {apsp.estimate_lower_bound()}")

        time_str, space_str = apsp.matrix_multiplication_apsp()
        print(f"  Floyd-Warshall: {time_str}, 空间 {space_str}")

        time_str, space_str = apsp.seidel_algorithm()
        print(f"  Seidel算法: {time_str}, 空间 {space_str}")
        print()

    apsp_lower_bounds()

    print()
    print("说明：")
    print("  - APSP是图算法的经典问题")
    print("  - 已知下界 Ω(n³/log n)")
    print("  - Seidel算法接近下界")
