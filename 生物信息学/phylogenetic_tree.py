# -*- coding: utf-8 -*-
"""
算法实现：生物信息学 / phylogenetic_tree

本文件实现 phylogenetic_tree 相关的算法功能。
"""

from typing import List, Tuple, Dict
import numpy as np


class UPGMA:
    """非加权组对算术平均法"""

    def __init__(self):
        self.clusters = {}  # cluster_id -> [members]
        self.heights = {}   # cluster_id -> height

    def build_tree(self, names: List[str], distance_matrix: List[List[float]]) -> Dict:
        """
        构建系统发育树

        参数：
            names: 物种/序列名称
            distance_matrix: 距离矩阵

        返回：树结构
        """
        n = len(names)
        self.n = n

        # 初始化：每个物种一个聚类
        clusters = {i: [names[i]] for i in range(n)}
        heights = {i: 0.0 for i in range(n)}

        # 距离矩阵（numpy便于操作）
        D = np.array(distance_matrix, dtype=float)
        active = set(range(n))

        # 聚类历史
        history = []

        next_id = n

        while len(active) > 1:
            # 找最近的聚类对
            min_dist = float('inf')
            pair = None

            active_list = list(active)
            for i in range(len(active_list)):
                for j in range(i+1, len(active_list)):
                    a, b = active_list[i], active_list[j]
                    if D[a][b] < min_dist:
                        min_dist = D[a][b]
                        pair = (a, b)

            if pair is None:
                break

            # 合并聚类
            c1, c2 = pair
            new_members = clusters[c1] + clusters[c2]
            new_height = min_dist / 2

            new_id = next_id
            next_id += 1

            clusters[new_id] = new_members
            heights[new_id] = new_height

            # 更新距离矩阵
            new_dist = {}
            for other in active:
                if other != c1 and other != c2:
                    d1 = D[c1][other] if c1 < len(D) and other < len(D[c1]) else D[other][c1]
                    d2 = D[c2][other] if c2 < len(D) and other < len(D[c2]) else D[other][c2]
                    new_dist[other] = (d1 + d2) / 2

            # 移除旧聚类
            active.remove(c1)
            active.remove(c2)

            # 添加新聚类
            active.add(new_id)

            # 扩展D矩阵
            new_row = np.zeros(len(clusters))
            for i in range(len(D)):
                new_row[i] = new_dist.get(i, 0.0)
            D = np.vstack([D, new_row])
            new_col = np.zeros(len(D))
            D = np.hstack([D, new_col.reshape(-1, 1)])

            history.append((c1, c2, new_id, min_dist))

        return {
            'clusters': clusters,
            'heights': heights,
            'history': history,
            'root_id': new_id
        }


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== UPGMA系统发育树测试 ===\n")

    # 示例：4个物种的距离矩阵
    names = ['Human', 'Chimp', 'Gorilla', 'Orangutan']
    # 基于真实进化距离的估计
    distance_matrix = [
        [0,    0.02, 0.04, 0.06],  # Human
        [0.02, 0,    0.03, 0.05],  # Chimp
        [0.04, 0.03, 0,    0.05],  # Gorilla
        [0.06, 0.05, 0.05, 0   ],  # Orangutan
    ]

    upgma = UPGMA()
    tree = upgma.build_tree(names, distance_matrix)

    print("聚类历史:")
    for c1, c2, new_id, dist in tree['history']:
        members = tree['clusters'][new_id]
        print(f"  合并 {members}: 距离={dist:.3f}")

    print(f"\n根节点ID: {tree['root_id']}")

    print("\n说明：")
    print("  - Human和Chimp距离最近(0.02)")
    print("  - 然后与Gorilla合并(0.03)")
    print("  - Orangutan是外群")
    print("  - UPGMA假设分子钟，适合近缘物种")
