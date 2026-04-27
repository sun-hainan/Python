# -*- coding: utf-8 -*-
"""
算法实现：计算机网络算法 / distance_vector

本文件实现 distance_vector 相关的算法功能。
"""

import random
import math
from collections import defaultdict


class DistanceVectorRouter:
    """距离矢量路由节点"""

    INFINITY = 16  # RIP 使用 16 表示无穷（最大跳数）

    def __init__(self, node_id):
        self.node_id = node_id
        # distance_table: {dest: {neighbor: cost}}
        self.distance_table = defaultdict(dict)
        # routing_table: {dest: (next_hop, cost)}
        self.routing_table = {}
        # neighbors: {neighbor_id: link_cost}
        self.neighbors = {}
        # 统计
        self.update_count = 0

    def add_neighbor(self, neighbor_id, link_cost):
        """
        添加邻居及链路代价
        link_cost: 到达邻居的代价（如跳数、延迟、带宽倒数）
        """
        self.neighbors[neighbor_id] = link_cost
        # 初始化距离表
        for n in self.neighbors:
            self.distance_table[n][n] = self.neighbors[n]

    def initialize(self):
        """
        初始化路由表：所有直接邻居距离已知，其他为无穷
        """
        # 初始化距离表
        all_nodes = set(self.neighbors.keys())
        all_nodes.add(self.node_id)

        for dest in all_nodes:
            if dest == self.node_id:
                self.distance_table[dest] = {self.node_id: 0}
                self.routing_table[dest] = (self.node_id, 0)
            elif dest in self.neighbors:
                self.distance_table[dest] = {dest: self.neighbors[dest]}
                self.routing_table[dest] = (dest, self.neighbors[dest])
            else:
                self.distance_table[dest] = {}

    def receive_update(self, from_neighbor, their_distance_vector):
        """
        接收邻居的距离矢量（DV）更新
        their_distance_vector: {dest: cost}
        返回: 是否发生变化
        """
        self.update_count += 1
        changed = False

        # Bellman-Ford 方程：d(v) = min_u (c(u,v) + D_u(v))
        link_cost = self.neighbors.get(from_neighbor, self.INFINITY)

        for dest, cost_via_neighbor in their_distance_vector.items():
            new_cost = link_cost + cost_via_neighbor

            # 限制最大距离（防止计数到无穷）
            if new_cost > self.INFINITY:
                new_cost = self.INFINITY

            # 更新距离表
            old_cost = self.distance_table[dest].get(from_neighbor, self.INFINITY)
            self.distance_table[dest][from_neighbor] = new_cost

            # 更新路由表（如果通过此邻居更优）
            current_best = self.routing_table.get(dest, (None, self.INFINITY))
            if new_cost < current_best[1]:
                self.routing_table[dest] = (from_neighbor, new_cost)
                changed = True
            elif current_best[0] == from_neighbor:
                # 下一跳就是此邻居，需要检查是否需要更新
                if new_cost != old_cost:
                    changed = True

        return changed

    def send_distance_vector(self):
        """
        生成要发送给邻居的距离矢量
        返回: {dest: cost_to_dest}
        """
        dv = {}
        for dest, (next_hop, cost) in self.routing_table.items():
            dv[dest] = cost
        return dv

    def get_route(self, dest):
        """查询到目的地的路由"""
        return self.routing_table.get(dest, (None, self.INFINITY))


class DVRoutingSimulator:
    """
    距离矢量路由协议模拟器
    模拟分布式 Bellman-Ford 算法收敛过程
    """

    def __init__(self):
        self.nodes = {}  # node_id -> DistanceVectorRouter

    def add_node(self, node_id):
        router = DistanceVectorRouter(node_id)
        self.nodes[node_id] = router
        return router

    def link(self, node_a, node_b, cost=1):
        """在两个节点之间建立双向链路"""
        self.nodes[node_a].add_neighbor(node_b, cost)
        self.nodes[node_b].add_neighbor(node_a, cost)

    def initialize_all(self):
        """初始化所有节点的路由表"""
        for node in self.nodes.values():
            node.initialize()

    def run_convergence(self, max_iterations=30):
        """
        运行分布式 Bellman-Ford，直到收敛或达到最大迭代次数
        返回: (iterations, converged)
        """
        for iteration in range(max_iterations):
            any_change = False

            # 每个节点向邻居广播自己的 DV
            new_dvs = {}
            for node_id, node in self.nodes.items():
                new_dvs[node_id] = node.send_distance_vector()

            # 每个节点处理邻居的 DV
            for node_id, node in self.nodes.items():
                for neighbor_id, dv in new_dvs.items():
                    if neighbor_id in node.neighbors or neighbor_id == node_id:
                        changed = node.receive_update(neighbor_id, dv)
                        if changed:
                            any_change = True

            if not any_change:
                return iteration + 1, True

        return max_iterations, False

    def print_routing_tables(self):
        """打印所有节点的路由表"""
        print(f"\n{'='*70}")
        print("路由表：")
        for node_id, node in sorted(self.nodes.items()):
            print(f"\n  节点 {node_id} 的路由表：")
            print(f"  {'目的':<10} {'下一跳':<10} {'代价':<8}")
            print(f"  {'-'*30}")
            for dest in sorted(node.routing_table.keys()):
                next_hop, cost = node.routing_table[dest]
                print(f"  {dest:<10} {next_hop:<10} {cost:<8}")


class PoisonReverse:
    """
    毒性反转（Poison Reverse）
    解决 DV 路由环路问题：如果 A 通过 B 到达目的地 D，
    则 A 告诉 B"我到 D 的距离是无穷"，从而避免 B 继续选择 A 作为下一跳。
    """

    def __init__(self, base_router):
        self.router = base_router

    def send_poisoned_dv(self, neighbor_id, dest_to_exclude=None):
        """
        生成带有毒性反转的 DV
        neighbor_id: 接收此 DV 的邻居
        dest_to_exclude: 需要毒性反转的目的地（通过 neighbor_id 到达的）
        """
        dv = {}
        for dest, (next_hop, cost) in self.router.routing_table.items():
            if dest == dest_to_exclude and next_hop == neighbor_id:
                # 毒性反转：告知邻居我到 D 是无穷
                dv[dest] = self.router.INFINITY
            else:
                dv[dest] = cost
        return dv


if __name__ == '__main__':
    print("距离矢量路由（Distance Vector）算法演示")
    print("=" * 60)

    # 构建网络拓扑
    #
    #     A ---1--- B ---1--- C
    #     |         |         |
    #     2         1         1
    #     |         |         |
    #     D ---1--- E ---1--- F
    #
    sim = DVRoutingSimulator()

    for nid in ['A', 'B', 'C', 'D', 'E', 'F']:
        sim.add_node(nid)

    links = [
        ('A', 'B', 1), ('B', 'C', 1),
        ('A', 'D', 2), ('B', 'E', 1),
        ('D', 'E', 1), ('E', 'F', 1),
    ]
    for a, b, c in links:
        sim.link(a, b, c)

    sim.initialize_all()

    print("初始路由表（A 节点）：")
    a_routes = sim.nodes['A'].routing_table
    for dest, (nh, cost) in sorted(a_routes.items()):
        print(f"  到 {dest}: 下一跳={nh}, 代价={cost}")

    print("\n运行 Bellman-Ford 收敛...")
    iterations, converged = sim.run_convergence()

    print(f"\n收敛：{'✓' if converged else '✗'}，耗时 {iterations} 轮")

    # 打印最终路由表
    sim.print_routing_tables()

    print("\n" + "=" * 60)
    print("距离矢量路由关键问题分析：")

    # 模拟路由环路场景
    print("\n【路由环路场景】")
    print("  拓扑: A --1-- B --1-- C --1-- D")
    print("  初始: A 知道到 D = 3 (A->B->C->D)")
    print("  链路 B-C 断开")
    print("  问题: B 认为 A 能到 D（错误信息），A 认为 B 能到 D（错误信息）")
    print("  结果: B 向 A 学到 D=3, A 向 B 学到 D=4... 计数到无穷")
    print("\n  解决方案：")
    print("    1. 毒性反转：A 告诉 B'我到 D 距离无穷'（如果 A 依赖 B 到 D）")
    print("    2. 抑制计时器：B 暂时不相信其他路径（Hold-down）")
    print("    3. 水平分割：不要把从一个邻居学到的信息再告诉它")
    print("    4. 触发更新：链路变化时立即发送更新（不等待计时器）")

    print("\nRIP vs BGP：")
    print("  RIP:  使用跳数（最多15跳），适用于小型网络")
    print("  BGP:  使用路径向量（AS_PATH），支持策略路由，适用于大型互联网")
