# -*- coding: utf-8 -*-
"""
算法实现：细粒度复杂性 / diameter_lower_bound

本文件实现 diameter_lower_bound 相关的算法功能。
"""

from typing import List, Tuple
import random


class DiameterComplexity:
    """直径复杂度分析"""

    def __init__(self, n: int):
        """
        参数：
            n: 顶点数
        """
        self.n = n

    def dijkstra_diameter(self, adj_matrix: List[List[int]]) -> int:
        """
        用Dijkstra求直径

        返回：直径
        """
        from collections import deque

        def bfs(start: int) -> List[int]:
            """BFS求单源最短路"""
            dist = [-1] * self.n
            dist[start] = 0
            queue = deque([start])

            while queue:
                v = queue.popleft()
                for u in range(self.n):
                    if adj_matrix[v][u] > 0 and dist[u] == -1:
                        dist[u] = dist[v] + 1
                        queue.append(u)

            return dist

        max_dist = 0

        for i in range(self.n):
            dist = bfs(i)
            max_dist = max(max_dist, max(dist))

        return max_dist

    def estimate_lower_bound(self) -> dict:
        """
        估计下界

        返回：下界信息
        """
        return {
            'n': self.n,
            'time_lower_bound': f"Ω({self.n}^{2})",  # 组合下界
            'apsp_relation': '是APSP的特殊情况',
            'tight_bound': '如果APSP需要 Ω(n³/log n)，直径需要 Ω(n²)'
        }


def diameter_applications():
    """直径应用"""
    print("=== 直径应用 ===")
    print()
    print("1. 网络分析")
    print("   - 网络直径反映延迟")
    print("   - 优化网络结构")
    print()
    print("2. 图聚类")
    print("   - 直径用于衡量图的紧密度")
    print("   - 层次聚类")
    print()
    print("3. 社交网络")
    print("   - 最短路径分析")
    print("   - 影响范围估计")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 直径问题下界测试 ===\n")

    n = 10
    diameter = DiameterComplexity(n)

    # 创建简单图（完全图）
    adj_matrix = [[1 if i != j else 0 for j in range(n)] for i in range(n)]

    print(f"图：{n}个顶点的完全图")
    print()

    # 计算直径
    d = diameter.dijkstra_diameter(adj_matrix)

    print(f"直径: {d}")
    print()

    # 下界估计
    info = diameter.estimate_lower_bound()

    print("下界信息：")
    for key, value in info.items():
        print(f"  {key}: {value}")

    print()
    diameter_applications()

    print()
    print("说明：")
    print("  - 直径是图的全局属性")
    print("  - 需要考虑所有点对")
    print("  - 下界与APSP紧密相关")
