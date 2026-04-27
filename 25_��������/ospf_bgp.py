# -*- coding: utf-8 -*-
"""
算法实现：25_�������� / ospf_bgp

本文件实现 ospf_bgp 相关的算法功能。
"""

import heapq
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict
import random


@dataclass
class OSPFLink:
    """OSPF链路"""
    router_id: str
    neighbor_id: str
    cost: float  # 链路成本
    bandwidth: float  # 带宽（可选）


@dataclass
class OSPFRouter:
    """OSPF路由器"""
    router_id: str
    links: List[OSPFLink] = field(default_factory=list)
    adjacency_db: Dict[str, 'OSPFLink'] = field(default_factory=dict)  # 邻居表
    
    def add_link(self, neighbor_id: str, cost: float):
        """添加链路"""
        link = OSPFLink(self.router_id, neighbor_id, cost)
        self.links.append(link)
        self.adjacency_db[neighbor_id] = link


class OSPFProtocol:
    """
    OSPF路由协议
    
    使用Dijkstra算法计算最短路径
    特点：
    - 链路状态广播（LSA）
    - 区域支持（Area）
    - 快速收敛
    """
    
    def __init__(self):
        self.routers: Dict[str, OSPFRouter] = {}
        self.lsa_db: Dict[str, List[OSPFLink]] = {}  # 链路状态数据库
    
    def add_router(self, router_id: str):
        """添加路由器"""
        self.routers[router_id] = OSPFRouter(router_id)
        self.lsa_db[router_id] = []
    
    def add_link(self, router_a: str, router_b: str, cost: float):
        """添加链路"""
        self.routers[router_a].add_link(router_b, cost)
        self.routers[router_b].add_link(router_a, cost)
        
        # 更新LSA数据库
        self.lsa_db[router_a].append(OSPFLink(router_a, router_b, cost))
        self.lsa_db[router_b].append(OSPFLink(router_b, router_a, cost))
    
    def dijkstra(self, source: str) -> Dict[str, Tuple[float, List[str]]]:
        """
        Dijkstra最短路径算法
        
        Args:
            source: 源路由器ID
        
        Returns:
            {router_id: (distance, path)}
        """
        distances = {router: float('inf') for router in self.routers}
        previous = {router: None for router in self.routers}
        distances[source] = 0
        
        # (distance, router_id)
        pq = [(0, source)]
        visited = set()
        
        while pq:
            dist, current = heapq.heappop(pq)
            
            if current in visited:
                continue
            visited.add(current)
            
            # 遍历邻居
            router = self.routers[current]
            for link in router.links:
                neighbor = link.neighbor_id
                new_dist = dist + link.cost
                
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    previous[neighbor] = current
                    heapq.heappush(pq, (new_dist, neighbor))
        
        # 重建路径
        paths = {}
        for router in self.routers:
            if distances[router] == float('inf'):
                paths[router] = (float('inf'), [])
            else:
                path = self._reconstruct_path(previous, source, router)
                paths[router] = (distances[router], path)
        
        return paths
    
    def _reconstruct_path(self, previous: Dict, source: str, target: str) -> List[str]:
        """重建从source到target的路径"""
        path = []
        current = target
        
        while current is not None:
            path.append(current)
            current = previous[current]
        
        path.reverse()
        return path if path[0] == source else []
    
    def compute_routing_table(self, router_id: str) -> Dict[str, Tuple[str, float]]:
        """
        计算指定路由器的路由表
        
        Args:
            router_id: 路由器ID
        
        Returns:
            {destination: (next_hop, distance)}
        """
        paths = self.dijkstra(router_id)
        routing_table = {}
        
        for dest, (distance, path) in paths.items():
            if dest == router_id or not path:
                continue
            
            next_hop = path[1] if len(path) > 1 else path[0]
            routing_table[dest] = (next_hop, distance)
        
        return routing_table


@dataclass
class BGPRoute:
    """BGP路由"""
    prefix: str  # IP前缀
    next_hop: str  # 下一跳
    as_path: List[str]  # AS路径
    origin: str  # 起源（IGP/EGP/INCOMPLETE）
    local_pref: int = 100  # 本地优先级
    med: int = 0  # MED
    communities: List[str] = field(default_factory=list)
    
    @property
    def as_path_length(self) -> int:
        """AS路径长度"""
        return len(self.as_path)


class BGPPeer:
    """BGP对等体"""
    def __init__(self, peer_id: str, as_number: int):
        self.peer_id = peer_id
        self.as_number = as_number
        self.routes: Dict[str, BGPRoute] = {}  # 学习的路由
        self.advertised_routes: Dict[str, BGPRoute] = {}  # 通告的路由


class BGPProtocol:
    """
    BGP路由协议
    
    路径矢量协议，使用以下属性选择路由：
    1. Highest Local Preference
    2. Shortest AS Path
    3. Lowest Origin Type (IGP < EGP < INCOMPLETE)
    4. Lowest MED
    5. eBGP over iBGP
    6. Lowest IGP Metric
    """
    
    def __init__(self, as_number: int):
        self.as_number = as_number
        self.peer_id = f"Router-{as_number}"
        self.peers: Dict[str, BGPPeer] = {}
        self.routes: Dict[str, BGPRoute] = {}  # 本地路由表
        self.rib: Dict[str, BGPRoute] = {}  # 路由信息库
    
    def add_peer(self, peer_id: str, as_number: int):
        """添加BGP对等体"""
        self.peers[peer_id] = BGPPeer(peer_id, as_number)
    
    def advertise_route(self, prefix: str, next_hop: str = None):
        """通告路由"""
        if next_hop is None:
            next_hop = self.peer_id
        
        route = BGPRoute(
            prefix=prefix,
            next_hop=next_hop,
            as_path=[str(self.as_number)],
            origin="IGP"
        )
        self.routes[prefix] = route
    
    def receive_route(self, peer_id: str, route: BGPRoute):
        """
        接收对等体通告的路由
        
        Args:
            peer_id: 对等体ID
            route: 路由信息
        """
        peer = self.peers.get(peer_id)
        if not peer:
            return
        
        # 追加AS路径
        new_route = BGPRoute(
            prefix=route.prefix,
            next_hop=route.next_hop,
            as_path=[str(self.as_number)] + route.as_path,
            origin=route.origin,
            local_pref=route.local_pref,
            med=route.med,
            communities=route.communities.copy()
        )
        
        # 存储路由
        peer.routes[route.prefix] = new_route
        
        # 路由选择
        self.route_selection(route.prefix)
    
    def route_selection(self, prefix: str):
        """
        BGP路由选择算法
        
        按优先级：
        1. Local Preference
        2. AS_PATH长度
        3. Origin类型
        4. MED
        5. eBGP > iBGP
        6. 最低IGP cost
        """
        candidates = []
        
        # 本地生成的路由
        if prefix in self.routes:
            candidates.append(self.routes[prefix])
        
        # 从对等体学习的路由
        for peer in self.peers.values():
            if prefix in peer.routes:
                candidates.append(peer.routes[prefix])
        
        if not candidates:
            if prefix in self.rib:
                del self.rib[prefix]
            return
        
        # 路由选择
        best_route = self._best_route(candidates)
        self.rib[prefix] = best_route
    
    def _best_route(self, candidates: List[BGPRoute]) -> BGPRoute:
        """选择最优路由"""
        if len(candidates) == 1:
            return candidates[0]
        
        # 1. 最高Local Preference
        candidates.sort(key=lambda r: r.local_pref, reverse=True)
        if candidates[0].local_pref != candidates[1].local_pref:
            return candidates[0]
        
        # 2. 最短AS_PATH
        candidates.sort(key=lambda r: r.as_path_length)
        if candidates[0].as_path_length != candidates[1].as_path_length:
            return candidates[0]
        
        # 3. 最低Origin类型
        origin_order = {"IGP": 0, "EGP": 1, "INCOMPLETE": 2}
        candidates.sort(key=lambda r: origin_order.get(r.origin, 2))
        if candidates[0].origin != candidates[1].origin:
            return candidates[0]
        
        # 4. 最低MED
        candidates.sort(key=lambda r: r.med)
        if candidates[0].med != candidates[1].med:
            return candidates[0]
        
        # 5. eBGP > iBGP (简化)
        return candidates[0]
    
    def get_route(self, prefix: str) -> Optional[BGPRoute]:
        """获取到指定前缀的路由"""
        return self.rib.get(prefix)


def demo_ospf():
    """
    演示OSPF路由计算
    """
    print("=== OSPF 路由协议演示 ===\n")
    
    # 创建网络拓扑
    ospf = OSPFProtocol()
    
    # 添加路由器
    routers = ["R1", "R2", "R3", "R4", "R5", "R6"]
    for r in routers:
        ospf.add_router(r)
    
    # 添加链路及成本
    links = [
        ("R1", "R2", 10),
        ("R1", "R3", 5),
        ("R2", "R3", 3),
        ("R2", "R4", 4),
        ("R3", "R4", 8),
        ("R3", "R5", 2),
        ("R4", "R5", 7),
        ("R4", "R6", 5),
        ("R5", "R6", 1),
    ]
    
    for r1, r2, cost in links:
        ospf.add_link(r1, r2, cost)
    
    print("网络拓扑:")
    for r1, r2, cost in links:
        print(f"  {r1} <--{cost}--> {r2}")
    
    # 计算从R1到所有路由器的最短路径
    print("\n从 R1 出发的最短路径:")
    paths = ospf.dijkstra("R1")
    
    for router, (dist, path) in sorted(paths.items()):
        if router == "R1":
            continue
        print(f"  R1 -> {router}: 距离={dist:.1f}, 路径={' -> '.join(path)}")
    
    # R1的路由表
    print("\nR1 的路由表:")
    rt = ospf.compute_routing_table("R1")
    for dest, (next_hop, dist) in sorted(rt.items()):
        print(f"  -> {dest}: 下一跳={next_hop}, 距离={dist:.1f}")


def demo_bgp():
    """
    演示BGP路由选择
    """
    print("\n=== BGP 路由协议演示 ===\n")
    
    # 模拟三个AS
    as1 = BGPProtocol(65001)  # 客户端AS
    as2 = BGPProtocol(65002)  # Transit AS
    as3 = BGPProtocol(65003)  # 另一个Transit AS
    
    # 建立对等关系
    as1.add_peer("AS2_eBGP", 65002)
    as1.add_peer("AS3_eBGP", 65003)
    as2.add_peer("AS1_eBGP", 65001)
    as3.add_peer("AS1_eBGP", 65001)
    
    # AS2生成默认路由
    as2.advertise_route("0.0.0.0/0", "10.0.2.1")
    
    # AS3也生成默认路由
    as3.advertise_route("0.0.0.0/0", "10.0.3.1")
    
    # 模拟路由通告
    print("路由通告:")
    print("  AS2 通告: 0.0.0.0/0, AS_PATH=[65002], LOCAL_PREF=100")
    print("  AS3 通告: 0.0.0.0/0, AS_PATH=[65003], LOCAL_PREF=100")
    
    # AS1接收路由
    route_as2 = BGPRoute(
        prefix="0.0.0.0/0",
        next_hop="10.0.2.1",
        as_path=["65002"],
        origin="IGP",
        local_pref=100
    )
    route_as3 = BGPRoute(
        prefix="0.0.0.0/0",
        next_hop="10.0.3.1",
        as_path=["65003"],
        origin="IGP",
        local_pref=100
    )
    
    as1.receive_route("AS2_eBGP", route_as2)
    as1.receive_route("AS3_eBGP", route_as3)
    
    # 查看AS1的RIB
    print("\nAS1 路由信息库(RIB):")
    for prefix, route in as1.rib.items():
        print(f"  {prefix}:")
        print(f"    下一跳: {route.next_hop}")
        print(f"    AS路径: {' -> '.join(route.as_path)}")
        print(f"    起源: {route.origin}")


def demo_bgp_route_selection():
    """
    演示BGP路由选择规则
    """
    print("\n=== BGP 路由选择演示 ===\n")
    
    bgp = BGPProtocol(65001)
    
    # 创建多个候选路由
    routes = [
        BGPRoute("10.0.0.0/8", "192.168.1.1", ["65002", "65003"], "IGP", local_pref=100, med=50),
        BGPRoute("10.0.0.0/8", "192.168.1.2", ["65002"], "EGP", local_pref=100, med=0),
        BGPRoute("10.0.0.0/8", "192.168.1.3", ["65002", "65003", "65004"], "IGP", local_pref=100, med=30),
        BGPRoute("10.0.0.0/8", "192.168.1.4", ["65002"], "IGP", local_pref=150, med=0),  # 更高LOCAL_PREF
    ]
    
    print("候选路由:")
    for i, r in enumerate(routes, 1):
        print(f"  {i}. 下一跳={r.next_hop}, AS_PATH={r.as_path}, "
              f"LOCAL_PREF={r.local_pref}, MED={r.med}, Origin={r.origin}")
    
    # 路由选择
    best = bgp._best_route(routes)
    
    print(f"\n最优路由:")
    print(f"  下一跳: {best.next_hop}")
    print(f"  AS路径: {' -> '.join(best.as_path)}")
    print(f"  LOCAL_PREF: {best.local_pref}")
    
    print("\n选择原因:")
    print("  - LOCAL_PREF=150 > 100 (最高LOCAL_PREF获胜)")


def compare_ospf_vs_bgp():
    """
    OSPF与BGP对比
    """
    print("\n" + "=" * 60)
    print("OSPF vs BGP 对比:")
    print("=" * 60)
    print("""
| 特性       | OSPF              | BGP               |
|------------|------------------|-------------------|
| 类型       | 链路状态          | 路径矢量          |
| 范围       | IGP（自治系统内） | EGP（自治系统间） |
| 收敛速度   | 快               | 慢                |
| 算法       | Dijkstra         | 路径矢量选择      |
| 路径最优   | 是               | 需配置策略        |
| 适用场景   | 数据中心/园区网  | Internet骨干      |
""")


if __name__ == "__main__":
    print("=" * 60)
    print("OSPF与BGP路由算法实现")
    print("=" * 60)
    
    # OSPF演示
    demo_ospf()
    
    # BGP演示
    demo_bgp()
    
    # BGP路由选择
    demo_bgp_route_selection()
    
    # 对比
    compare_ospf_vs_bgp()
    
    print("\n" + "=" * 60)
    print("关键概念:")
    print("=" * 60)
    print("""
OSPF:
- 使用Dijkstra算法计算最短路径
- 链路状态(LSA)在整个区域泛洪
- 支持多区域(Area 0为骨干)
- 成本基于带宽计算

BGP:
- 路径矢量协议，记录AS_PATH
- 支持丰富的路由策略
- eBGP和iBGP有不同的下一跳规则
- 路由选择考虑多个属性
""")
