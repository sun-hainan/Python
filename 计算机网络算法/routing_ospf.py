# -*- coding: utf-8 -*-
"""
算法实现：计算机网络算法 / routing_ospf

本文件实现 routing_ospf 相关的算法功能。
"""

import heapq
import math
from collections import defaultdict


class OSPFLink:
    """OSPF 链路"""

    def __init__(self, neighbor_id, cost, network_type='broadcast'):
        self.neighbor_id = neighbor_id
        self.cost = cost
        self.network_type = network_type
        self.bandwidth = 0        # 带宽（bps）
        self.interface_cost = cost  # OSPF 接口代价 = 100Mbps / bandwidth


class OSPFArea:
    """OSPF 区域"""

    def __init__(self, area_id=0):
        self.area_id = area_id  # 0 = 主干区域 (backbone)
        # lsdb: 链路状态数据库 {router_id: LSA}
        self.lsdb = {}
        self.router_id = None


class OSPFLinkStateAdvertisement:
    """OSPF LSA 抽象"""

    TYPE_ROUTER = 1
    TYPE_NETWORK = 2
    TYPE_SUMMARY_NETWORK = 3
    TYPE_SUMMARY_ASBR = 4
    TYPE_EXTERNAL = 5

    def __init__(self, advertising_router, ls_type, link_state_id):
        self.advertising_router = advertising_router
        self.ls_type = ls_type
        self.link_state_id = link_state_id
        self.ls_age = 0
        self.sequence = 0
        self.links = []  # [{id, type, metric}]

    def add_link(self, id, link_type, metric):
        """
        添加链路
        link_type: 1=点对点, 2=Transit, 3=Stub, 4=虚拟链路
        """
        self.links.append({'id': id, 'type': link_type, 'metric': metric})


class OSPFRouter:
    """OSPF 路由器"""

    def __init__(self, router_id, area_id=0):
        self.router_id = router_id
        self.area_id = area_id
        # 链路: {interface: OSPFLink}
        self.interfaces = {}
        # 邻居: {neighbor_id: state}
        self.neighbors = {}  # state: 'full'|'2way'|'init'|'down'
        # SPF 计算结果
        self.spf_tree = {}  # {dest: (next_hop, cost, path)}
        self.lsdb = {}      # 本地 LSDB

    def add_interface(self, interface_id, neighbor_id, cost):
        """添加接口"""
        link = OSPFLink(neighbor_id, cost)
        self.interfaces[interface_id] = link
        self.neighbors[neighbor_id] = 'init'

    def receive_lsa(self, lsa):
        """接收 LSA，更新 LSDB"""
        key = (lsa.advertising_router, lsa.link_state_id)
        if key not in self.lsdb or lsa.sequence > self.lsdb[key].sequence:
            self.lsdb[key] = lsa
            return True  # LSA 是新的
        return False

    def run_spf(self, area):
        """
        运行 SPF（Dijkstra）算法
        area: 当前所属区域
        """
        # 构建本地拓扑图
        graph = defaultdict(list)
        all_nodes = {self.router_id}

        # 添加自己的链路
        for iface_id, link in self.interfaces.items():
            graph[self.router_id].append((link.neighbor_id, link.cost))
            all_nodes.add(link.neighbor_id)

        # 从 LSDB 构建完整拓扑
        for key, lsa in self.lsdb.items():
            adv_router = lsa.advertising_router
            all_nodes.add(adv_router)
            for link_info in lsa.links:
                neighbor = link_info['id']
                cost = link_info['metric']
                graph[adv_router].append((neighbor, cost))
                all_nodes.add(neighbor)

        # Dijkstra
        dist = {n: float('inf') for n in all_nodes}
        prev = {n: None for n in all_nodes}
        dist[self.router_id] = 0
        pq = [(0, self.router_id)]
        visited = set()

        while pq:
            d_u, u = heapq.heappop(pq)
            if u in visited:
                continue
            visited.add(u)

            for v, w in graph[u]:
                if v in visited:
                    continue
                alt = dist[u] + w
                if alt < dist[v]:
                    dist[v] = alt
                    prev[v] = u
                    heapq.heappush(pq, (alt, v))

        # 构建 SPF 树
        self.spf_tree = {}
        for dest in all_nodes:
            if dest == self.router_id or dist[dest] < float('inf'):
                # 重建路径找下一跳
                path = []
                current = dest
                while current is not None:
                    path.append(current)
                    current = prev[current]
                path.reverse()

                if len(path) >= 2:
                    next_hop = path[1]
                else:
                    next_hop = dest

                self.spf_tree[dest] = (next_hop, dist[dest], path)

        return self.spf_tree

    def get_route(self, dest):
        """查询到目的网络的路由"""
        return self.spf_tree.get(dest, (None, float('inf'), []))


class OSPFSimulator:
    """
    OSPF 网络模拟器
    负责 LSA 泛洪和 SPF 触发计算
    """

    def __init__(self):
        self.routers = {}  # router_id -> OSPFRouter
        self.areas = {}    # area_id -> OSPFArea

    def add_router(self, router_id, area_id=0):
        router = OSPFRouter(router_id, area_id)
        self.routers[router_id] = router
        if area_id not in self.areas:
            self.areas[area_id] = OSPFArea(area_id)
        return router

    def add_link(self, router_a_id, router_b_id, cost):
        """添加双向链路"""
        self.routers[router_a_id].add_interface(
            f'{router_a_id}-{router_b_id}', router_b_id, cost
        )
        self.routers[router_b_id].add_interface(
            f'{router_b_id}-{router_a_id}', router_a_id, cost
        )

    def flood_lsa(self, from_router_id, lsa):
        """
        泛洪 LSA 到所有路由器
        实际网络中：只在邻居间传播，这里简化为全局同步
        """
        for router_id, router in self.routers.items():
            if router_id != from_router_id:
                router.receive_lsa(lsa)

    def trigger_spf(self, router_id):
        """触发指定路由器的 SPF 计算"""
        router = self.routers[router_id]
        router.run_spf(self.areas[router.area_id])
        return router.spf_tree


if __name__ == '__main__':
    print("OSPF（开放最短路径优先）路由算法演示")
    print("=" * 60)

    # 构建 OSPF 网络拓扑
    #
    #        R1 (Area 0)
    #       / | \\
    #      /  |  \\
    #    10  10  10
    #    /   |   \\
    #  R2---5---R3
    #   |    10   |
    #   10   |   10
    #    \\   |   /
    #     R4-R5-R6
    #         (Area 1)
    #

    sim = OSPFSimulator()

    for rid in ['R1', 'R2', 'R3', 'R4', 'R5', 'R6']:
        sim.add_router(rid, area_id=0 if rid in ['R1', 'R2', 'R3'] else 1)

    links = [
        ('R1', 'R2', 10), ('R1', 'R3', 10), ('R1', 'R5', 10),
        ('R2', 'R4', 5), ('R2', 'R3', 5),
        ('R3', 'R5', 10), ('R3', 'R6', 10),
        ('R4', 'R5', 10), ('R5', 'R6', 10),
    ]
    for a, b, c in links:
        sim.add_link(a, b, c)

    # 泛洪 LSA（简化：所有路由器都直接知道拓扑）
    print("\nOSPF 网络拓扑：")
    for a, b, c in links:
        print(f"  {a} --{c}-- {b}")

    # 触发各路由器的 SPF 计算
    print("\nSPF 计算结果：")
    print(f"{'路由器':<8} {'目的':<8} {'下一跳':<10} {'代价':<8} {'路径'}")
    print("-" * 65)

    for router_id in ['R1', 'R2', 'R3', 'R4', 'R5', 'R6']:
        rt = sim.trigger_spf(router_id)
        for dest, (next_hop, cost, path) in sorted(rt.items()):
            if dest != router_id:
                print(f"  {router_id:<8} {dest:<8} {next_hop:<10} "
                      f"{cost:<8} {'->'.join(path)}")

    print("\n" + "=" * 60)
    print("OSPF 关键机制：")
    print("\n1. LSA 泛洪（Flooding）：")
    print("   - 链路状态变化时，立即泛洪到所有邻居")
    print("   - 使用序列号 + 年龄 + 校验和 检测 LSA 新旧")
    print("   - 需要可靠传输（确认+重传）")
    print("\n2. SPF 计算（局部性）：")
    print("   - 路由变化只触发本路由器的 SPF 重算")
    print("   - 其他路由器不变（不同于 DV 的全局传播）")
    print("   - 收敛速度远快于距离矢量协议")
    print("\n3. 区域划分（Area）：")
    print("   - Area 0 = 主干区域，所有区域间流量经过主干")
    print("   - 区域间路由通过 Summary LSA（Type 3）")
    print("   - 减少 LSDB 规模，限制 SPF 计算范围")
    print("\n4. DR/BDR（指定路由器）：")
    print("   - 多路访问网络（N > 2）选 DR/BDR")
    print("   - 其他路由器只与 DR/BDR 交换 LSA，避免 N×N 泛洪")
