# -*- coding: utf-8 -*-

"""

算法实现：近似算法 / k_center



本文件实现 k_center 相关的算法功能。

"""



from typing import List, Set, Tuple





def greedy_k_center(points: List[Tuple[float, float]], k: int) -> List[int]:

    """

    贪心K-center算法



    参数：

        points: 点列表 [(x, y), ...]

        k: 中心点数量



    返回：被选为中心的点的索引

    """

    n = len(points)

    covered = set()

    centers = []



    # 距离函数

    def dist(i, j):

        x1, y1 = points[i]

        x2, y2 = points[j]

        return ((x1-x2)**2 + (y1-y2)**2) ** 0.5



    # 贪心选择

    # 初始随机选一个点

    centers.append(0)

    covered.add(0)



    while len(centers) < k:

        # 找距离最近中心最远的点

        best_point = None

        best_min_dist = -1



        for i in range(n):

            if i in covered:

                continue

            # 这个点到所有中心的最小距离

            min_dist = min(dist(i, c) for c in centers)

            if min_dist > best_min_dist:

                best_min_dist = min_dist

                best_point = i



        if best_point is not None:

            centers.append(best_point)

            covered.add(best_point)



    return centers





def k_center_cost(points: List[Tuple[float, float]], centers: List[int]) -> float:

    """计算K-center代价（最大覆盖半径）"""

    def dist(i, j):

        x1, y1 = points[i]

        x2, y2 = points[j]

        return ((x1-x2)**2 + (y1-y2)**2) ** 0.5



    if not centers:

        return float('inf')



    max_dist = 0

    for i in range(len(points)):

        min_dist = min(dist(i, c) for c in centers)

        max_dist = max(max_dist, min_dist)



    return max_dist





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== K-Center测试 ===\n")



    # 随机生成一些点

    import random

    random.seed(42)

    points = [(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(20)]



    print(f"生成 {len(points)} 个随机点")



    for k in [1, 2, 3, 4]:

        centers = greedy_k_center(points, k)

        cost = k_center_cost(points, centers)

        print(f"  k={k}: 中心点={centers}, 最大距离={cost:.2f}")



    print("\n说明：")

    print("  - K-center问题是NP难问题")

    print("  - 贪心算法保证2-近似")

    print("  - 应用：设施选址、传感器网络、聚类")

