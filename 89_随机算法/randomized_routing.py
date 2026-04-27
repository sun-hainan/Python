# -*- coding: utf-8 -*-

"""

算法实现：随机算法 / randomized_routing



本文件实现 randomized_routing 相关的算法功能。

"""



import random

from typing import List, Tuple





class RandomizedRouter:

    """随机路由"""



    def __init__(self, network_size: int):

        """

        参数：

            network_size: 网络节点数

        """

        self.n = network_size



    def valiant_rantage(self, sources: List[int], destinations: List[int]) -> List[List[int]]:

        """

        Valiant随机路由



        参数：

            sources: 源节点列表

            destinations: 目标节点列表



        返回：每对的路由路径

        """

        routes = []



        for src, dst in zip(sources, destinations):

            # 步骤1：随机选择中间节点

            intermediate = random.randint(0, self.n - 1)



            # 步骤2：src -> intermediate

            path1 = self._shortest_path(src, intermediate)



            # 步骤3：intermediate -> dst

            path2 = self._shortest_path(intermediate, dst)



            # 合并路径

            route = path1[:-1] + path2



            routes.append(route)



        return routes



    def _shortest_path(self, src: int, dst: int) -> List[int]:

        """简化最短路（只用直接跳转）"""

        return [src, dst]



    def analyze_congestion(self, routes: List[List[int]]) -> int:

        """

        分析网络拥塞



        返回：最大拥塞度

        """

        # 统计每条边的使用次数

        edge_counts = {}



        for route in routes:

            for i in range(len(route) - 1):

                edge = (route[i], route[i + 1])

                edge_counts[edge] = edge_counts.get(edge, 0) + 1



        if not edge_counts:

            return 0



        return max(edge_counts.values())



    def random_shortest_path(self, src: int, dst: int) -> List[int]:

        """

        随机最短路径



        返回：路径

        """

        # 简化：直接路由

        return [src, dst]





def valiant_routing_analysis():

    """Valiant路由分析"""

    print("=== Valiant随机路由 ===")

    print()

    print("问题：")

    print("  - 同时路由所有数据包")

    print("  - 最小化最大拥塞")

    print("  - 传统方法可能拥塞")

    print()

    print("Valiant方法：")

    print("  - 随机选择中间节点")

    print("  - 先到中间，再到最后")

    print("  - 保证低拥塞")

    print()

    print("分析：")

    print("  - 最大拥塞 O(log n)")

    print("  - 轮数 O(log n)")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 随机路由测试 ===\n")



    n = 16  # 网络大小

    router = RandomizedRouter(n)



    print(f"网络大小: {n} 个节点")

    print()



    # 随机生成流量

    npairs = 10

    sources = [random.randint(0, n-1) for _ in range(npairs)]

    destinations = [random.randint(0, n-1) for _ in range(npairs)]



    print(f"流量数: {npairs}")

    print(f"源: {sources}")

    print(f"目标: {destinations}")

    print()



    # Valiant路由

    routes = router.valiant_vantage(sources, destinations)



    print("路由路径:")

    for i, route in enumerate(routes):

        print(f"  {sources[i]} -> {destinations[i]}: {route}")



    print()



    # 分析拥塞

    max_congestion = router.analyze_congestion(routes)



    print(f"最大拥塞: {max_congestion}")

    print(f"平均拥塞: {sum(len(r) for r in routes) / n:.2f}")



    print()

    valiant_routing_analysis()



    print()

    print("说明：")

    print("  - Valiant路由解决网络拥塞")

    print("  - 用于并行计算机网络")

    print("  - 保证 O(log n) 轮完成")

