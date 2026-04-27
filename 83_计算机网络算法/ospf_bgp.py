# -*- coding: utf-8 -*-

"""

算法实现：计算机网络算法 / ospf_bgp



本文件实现 ospf_bgp 相关的算法功能。

"""



import heapq

from collections import defaultdict





class OSPFRouter:

    """OSPF 路由器实现"""



    def __init__(self, router_id):

        """

        初始化 OSPF 路由器

        

        参数:

            router_id: 路由器 ID（通常是 IP 地址格式）

        """

        self.router_id = router_id

        # 邻居路由器：{neighbor_id: (interface_ip, cost)}

        self.neighbors = {}

        # 链路状态数据库：{router_id: LSA}

        self.lsdb = {}

        # 路由表：{destination: (next_hop, cost)}

        self.routing_table = {}

        # 区域 ID（简化：单区域 OSPF）

        self.area_id = 0



    def add_neighbor(self, neighbor_id, interface_ip, cost):

        """

        添加邻居

        

        参数:

            neighbor_id: 邻居路由器 ID

            interface_ip: 接口 IP 地址

            cost: 链路成本

        """

        self.neighbors[neighbor_id] = (interface_ip, cost)

        # 将自己的 LSA 加入 LSDB

        self._update_lsa()



    def _update_lsa(self):

        """生成并传播链路状态广告"""

        # 简化的 LSA 生成

        lsa = {

            'router_id': self.router_id,

            'sequence': self.lsdb.get(self.router_id, {}).get('sequence', 0) + 1,

            'neighbors': {nid: cost for nid, (_, cost) in self.neighbors.items()}

        }

        self.lsdb[self.router_id] = lsa



    def receive_lsa(self, lsa):

        """

        接收链路状态广告

        

        参数:

            lsa: 链路状态广告字典

        """

        router_id = lsa['router_id']

        seq = lsa['sequence']

        

        # 如果是新的或更新的 LSA，更新 LSDB

        if router_id not in self.lsdb or seq > self.lsdb[router_id]['sequence']:

            self.lsdb[router_id] = lsa

            # 触发路由计算

            self.compute_routes()

            return True  # LSA 有更新

        return False  # LSA 无更新



    def compute_routes(self):

        """

        使用 Dijkstra 算法计算最短路径

        

        基于链路状态数据库计算到所有目的地的最短路径

        """

        self.routing_table.clear()

        

        # Dijkstra 算法

        # 使用 (cost, router_id) 作为优先队列元素

        visited = set()

        distances = {self.router_id: 0}

        predecessors = {self.router_id: None}

        

        pq = [(0, self.router_id)]

        

        while pq:

            dist, current = heapq.heappop(pq)

            

            if current in visited:

                continue

            

            visited.add(current)

            

            # 获取当前路由器的 LSA

            if current not in self.lsdb:

                continue

            

            lsa = self.lsdb[current]

            

            # 遍历邻居

            for neighbor_id, link_cost in lsa.get('neighbors', {}).items():

                new_dist = dist + link_cost

                

                if neighbor_id not in distances or new_dist < distances[neighbor_id]:

                    distances[neighbor_id] = new_dist

                    predecessors[neighbor_id] = current

                    heapq.heappush(pq, (new_dist, neighbor_id))

        

        # 构建路由表

        for dest, cost in distances.items():

            if dest == self.router_id:

                continue

            

            # 找到下一跳

            next_hop = self._get_next_hop(dest, predecessors)

            

            self.routing_table[dest] = {

                'next_hop': next_hop,

                'cost': cost,

                'path': self._get_path(dest, predecessors)

            }



    def _get_next_hop(self, destination, predecessors):

        """

        获取目的地的下一跳

        

        参数:

            destination: 目的地路由器 ID

            predecessors: 前驱节点映射

        返回:

            next_hop: 下一跳路由器 ID

        """

        current = destination

        while predecessors.get(current) != self.router_id:

            if predecessors.get(current) is None:

                return None

            current = predecessors[current]

        return current



    def _get_path(self, destination, predecessors):

        """获取路由路径"""

        path = []

        current = destination

        while current is not None:

            path.append(current)

            current = predecessors.get(current)

        path.reverse()

        return path



    def get_route(self, destination):

        """查询到目的地的路由"""

        return self.routing_table.get(destination)





class BGPPeer:

    """BGP 对等体"""



    def __init__(self, as_number, peer_id):

        """

        初始化 BGP 对等体

        

        参数:

            as_number: 自治系统号

            peer_id: 对等体 ID

        """

        self.as_number = as_number

        self.peer_id = peer_id

        # 路由信息库（RIB-In）：收到的路由

        self.routes_received = {}

        # 最佳路由选择后的路由表

        self.routes_selected = {}

        # 对等体是否处于活跃状态

        self.state = 'idle'  # idle, connect, active, opensent, openconfirm, established

        # 保持时间（秒）

        self.hold_time = 180

        # 已宣告的路由

        self.advertised_routes = set()



    def receive_route(self, prefix, attributes):

        """

        接收路由宣告

        

        参数:

            prefix: 路由前缀（如 "10.0.0.0/8"）

            attributes: 路由属性

        """

        self.routes_received[prefix] = attributes



    def select_best_route(self, prefix):

        """

        选择最佳路由（BGP 路径属性决策过程）

        

        决策顺序：

        1. 最高权重（本地属性）

        2. 最高本地优先级

        3. 最短 AS_PATH

        4. 最低起源类型（IGP < EBGP < Incomplete）

        5. 最低 MED

        6. eBGP > iBGP

        7. 最低 IGP metric to next hop

        8. 最早宣告

        9. 最低 router-id

        

        参数:

            prefix: 路由前缀

        返回:

            best_route: 最佳路由属性

        """

        if prefix not in self.routes_received:

            return None

        

        candidates = []

        for prefix, attrs in self.routes_received.items():

            if prefix == prefix:

                candidates.append(attrs)

        

        if not candidates:

            return None

        

        # 简化决策：选择 AS_PATH 最短的

        best = min(candidates, key=lambda x: len(x.get('as_path', [])))

        return best



    def advertise_route(self, prefix, attributes):

        """

        宣告路由到对等体

        

        参数:

            prefix: 路由前缀

            attributes: 路由属性

        """

        # 添加自己的 AS 号到 AS_PATH

        as_path = attributes.get('as_path', [])

        as_path = [self.as_number] + as_path

        attributes['as_path'] = as_path

        

        self.advertised_routes.add(prefix)

        # 实际应该发送到对等体，这里简化处理

        return {'prefix': prefix, 'attributes': attributes}



    def withdraw_route(self, prefix):

        """

        撤销路由

        

        参数:

            prefix: 要撤销的路由前缀

        """

        if prefix in self.advertised_routes:

            self.advertised_routes.discard(prefix)

        return prefix





class BGPAS:

    """BGP 自治系统"""



    def __init__(self, as_number):

        """

        初始化 BGP 自治系统

        

        参数:

            as_number: 自治系统号

        """

        self.as_number = as_number

        # 路由器 ID

        self.router_id = f"192.168.{as_number}.1"

        # 对等体

        self.peers = {}

        # 本地生成的路由

        self.local_routes = {}

        # 路由表（合并后的）

        self.routing_table = {}



    def add_peer(self, peer_as_number, peer_id):

        """

        添加对等体

        

        参数:

            peer_as_number: 对等体 AS 号

            peer_id: 对等体 ID

        """

        peer = BGP Peer(peer_as_number, peer_id)

        self.peers[f"{peer_as_number}_{peer_id}"] = peer

        return peer



    def add_local_route(self, prefix, attributes=None):

        """

        添加本地生成的路由

        

        参数:

            prefix: 路由前缀

            attributes: 路由属性

        """

        if attributes is None:

            attributes = {}

        attributes['origin'] = 'igp'  # 本地生成的标记为 IGP

        self.local_routes[prefix] = attributes



    def run_bgp(self):

        """运行 BGP 路由选择"""

        # 收集所有路由

        all_routes = dict(self.local_routes)

        

        # 从对等体接收的路由

        for peer_key, peer in self.peers.items():

            for prefix, attrs in peer.routes_received.items():

                all_routes[prefix] = attrs

        

        # 选择最佳路由

        self.routing_table = {}

        for prefix in all_routes:

            # 简化的选择：本地路由优先

            if prefix in self.local_routes:

                self.routing_table[prefix] = {

                    'route': self.local_routes[prefix],

                    'source': 'local',

                    'as_path': [self.as_number]

                }

            else:

                # 从邻居 AS 学到的路由

                best_route = None

                best_peer = None

                for peer_key, peer in self.peers.items():

                    if prefix in peer.routes_received:

                        route = peer.routes_received[prefix]

                        if best_route is None or len(route.get('as_path', [])) < len(best_route.get('as_path', [])):

                            best_route = route

                            best_peer = peer_key

                

                if best_route:

                    self.routing_table[prefix] = {

                        'route': best_route,

                        'source': best_peer,

                        'as_path': [self.as_number] + best_route.get('as_path', [])

                    }



    def get_route(self, prefix):

        """查询路由"""

        return self.routing_table.get(prefix)





if __name__ == "__main__":

    # 测试 OSPF

    print("=== OSPF 路由协议测试 ===\n")



    # 创建 5 个 OSPF 路由器

    routers = {}

    router_ids = ['1.1.1.1', '2.2.2.2', '3.3.3.3', '4.4.4.4', '5.5.5.5']

    

    for rid in router_ids:

        routers[rid] = OSPFRouter(rid)



    # 建立邻居关系

    # 1 --(cost=10)-- 2 --(cost=10)-- 3

    # |                     |

    # cost=5               cost=5

    # |                     |

    # 4 --(cost=10)-- 5 --(cost=10)--

    

    routers['1.1.1.1'].add_neighbor('2.2.2.2', '10.0.1.2', 10)

    routers['1.1.1.1'].add_neighbor('4.4.4.4', '10.0.4.2', 5)

    

    routers['2.2.2.2'].add_neighbor('1.1.1.1', '10.0.1.1', 10)

    routers['2.2.2.2'].add_neighbor('3.3.3.3', '10.0.2.2', 10)

    

    routers['3.3.3.3'].add_neighbor('2.2.2.2', '10.0.2.1', 10)

    routers['3.3.3.3'].add_neighbor('5.5.5.5', '10.0.3.2', 5)

    

    routers['4.4.4.4'].add_neighbor('1.1.1.1', '10.0.4.1', 5)

    routers['4.4.4.4'].add_neighbor('5.5.5.5', '10.0.4.4', 10)

    

    routers['5.5.5.5'].add_neighbor('4.4.4.4', '10.0.4.3', 10)

    routers['5.5.5.5'].add_neighbor('3.3.3.3', '10.0.3.1', 5)



    # 模拟 LSDB 同步（简化的洪泛）

    for rid1 in router_ids:

        for rid2 in router_ids:

            if rid1 != rid2:

                lsa = routers[rid2].lsdb.get(rid2)

                if lsa:

                    routers[rid1].receive_lsa(lsa)



    # 显示路由表

    print("路由器 1.1.1.1 的路由表:")

    for dest, info in routers['1.1.1.1'].routing_table.items():

        print(f"  -> {dest}: 下一跳={info['next_hop']}, "

              f"cost={info['cost']}, 路径={info['path']}")



    # 测试 BGP

    print("\n=== BGP 路由协议测试 ===\n")



    # 创建三个 AS

    as65001 = BGPAS(65001)

    as65002 = BGPAS(65002)

    as65003 = BGPAS(65003)



    # 建立对等关系

    peer_1_2 = as65001.add_peer(65002, '2.2.2.2')

    peer_2_1 = as65002.add_peer(65001, '1.1.1.1')

    peer_2_3 = as65002.add_peer(65003, '3.3.3.3')

    peer_3_2 = as65003.add_peer(65002, '2.2.2.2')



    # AS65001 宣告本地网络

    as65001.add_local_route('192.168.1.0/24')



    # AS65003 宣告本地网络

    as65003.add_local_route('10.0.0.0/8')



    # 模拟路由宣告

    # AS65001 -> AS65002

    peer_1_2.receive_route('192.168.1.0/24', {

        'as_path': [65001],

        'origin': 'igp',

        'next_hop': '1.1.1.1',

        'local_pref': 100

    })



    # AS65003 -> AS65002

    peer_3_2.receive_route('10.0.0.0/8', {

        'as_path': [65003],

        'origin': 'igp',

        'next_hop': '3.3.3.3',

        'local_pref': 100

    })



    # 运行 BGP

    as65001.run_bgp()

    as65002.run_bgp()

    as65003.run_bgp()



    # 显示路由表

    print("AS65001 路由表:")

    for prefix, info in as65001.routing_table.items():

        print(f"  {prefix}: source={info['source']}, as_path={info['as_path']}")



    print("\nAS65002 路由表:")

    for prefix, info in as65002.routing_table.items():

        print(f"  {prefix}: source={info['source']}, as_path={info['as_path']}")



    print("\nAS65003 路由表:")

    for prefix, info in as65003.routing_table.items():

        print(f"  {prefix}: source={info['source']}, as_path={info['as_path']}")

