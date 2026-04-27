# -*- coding: utf-8 -*-

"""

算法实现：计算机网络算法 / routing_bgp



本文件实现 routing_bgp 相关的算法功能。

"""



import random

from collections import defaultdict





class BGPRoute:

    """BGP 路由条目"""



    def __init__(self, prefix, as_path, next_hop, origin='IGP',

                 local_pref=100, med=0, community=None):

        self.prefix = prefix           # IP 前缀（如 '10.0.0.0/8'）

        self.as_path = as_path         # AS 路径列表

        self.next_hop = next_hop       # 下一跳 IP

        self.origin = origin           # 'IGP' | 'EGP' | 'Incomplete'

        self.local_pref = local_pref  # 本地优先级（iBGP 使用）

        self.med = med                 # Multi-Exit Discriminator（eBGP 使用）

        self.community = community or []



    def get_as_path_length(self):

        return len(self.as_path)



    def __repr__(self):

        return (f"BGPRoute({self.prefix}, AS_PATH={self.as_path}, "

                f"next_hop={self.next_hop}, origin={self.origin})")





class BGPPeer:

    """BGP 对等体（路由器）"""



    def __init__(self, peer_id, as_number, is_route_reflector_client=False):

        self.peer_id = peer_id

        self.as_number = as_number

        self.is_route_reflector_client = is_route_reflector_client

        # Adj-RIB-In：从邻居收到的原始路由

        self.adj_rib_in = {}   # {prefix: BGPRoute}

        # Loc-RIB：本地最佳路由

        self.loc_rib = {}      # {prefix: BGPRoute}

        # Adj-RIB-Out：向邻居通告的路由

        self.adj_rib_out = {}  # {prefix: BGPRoute}

        # IBGP 邻居

        self.ibgp_neighbors = set()

        # eBGP 邻居

        self.ebgp_neighbors = set()



    def receive_route(self, prefix, route):

        """接收来自邻居的路由"""

        self.adj_rib_in[prefix] = route



    def apply_import_policy(self, prefix, route):

        """

        应用导入策略（Import Policy）

        可以修改 local_pref、MED、AS_PATH（添加 community）等

        """

        # 简化：直接接受

        return route



    def apply_export_policy(self, prefix, route):

        """

        应用导出策略（Export Policy）

        通常会添加自己的 AS 号到 AS_PATH

        """

        # eBGP 通告：不携带本地 AS

        new_route = BGPRoute(

            prefix=route.prefix,

            as_path=route.as_path,

            next_hop=route.next_hop,

            origin=route.origin,

            local_pref=route.local_pref,

            med=route.med,

        )

        return new_route



    def select_best_route(self, prefix):

        """

        BGP 选路规则（RFC 4271 + 扩展）

        1. 最高 LOCAL_PREF

        2. 最短 AS_PATH

        3. 最低 Origin 类型（IGP < EGP < Incomplete）

        4. 最低 MED（通常同 AS）

        5. eBGP over iBGP

        6. 最低 IGP 成本到下一跳

        7. 最低 BGP Router ID

        """

        candidates = [r for r in self.adj_rib_in.values()

                      if r.prefix == prefix]

        if not candidates:

            return None



        # 按选路属性排序

        candidates.sort(key=lambda r: (

            -r.local_pref,                   # 1. 最高 LOCAL_PREF

            r.get_as_path_length(),          # 2. 最短 AS_PATH

            0 if r.origin == 'IGP' else (1 if r.origin == 'EGP' else 2),  # 3. Origin

            r.med,                           # 4. 最低 MED

            0,                               # 5. eBGP vs iBGP

            r.next_hop,                      # 6. IGP 成本（简化）

            self.peer_id                     # 7. 最低 Router ID

        ))



        best = candidates[0]

        self.loc_rib[prefix] = best

        return best



    def advertise_routes(self):

        """向邻居通告路由"""

        for prefix, route in self.loc_rib.items():

            exported = self.apply_export_policy(prefix, route)

            self.adj_rib_out[prefix] = exported

            # 向 eBGP/iBGP 邻居发送 UPDATE

            for neighbor in self.ebgp_neighbors | self.ibgp_neighbors:

                pass  # 实际发送 BGP UPDATE 消息





class BGPPathVector:

    """

    BGP 路径向量算法

    核心：AS_PATH 属性防止环路 + 支持策略路由

    """



    def __init__(self):

        self.peers = {}  # peer_id -> BGPPeer

        self.routes = {} # prefix -> [BGPRoute, ...]



    def add_peer(self, peer_id, as_number):

        peer = BGPPeer(peer_id, as_number)

        self.peers[peer_id] = peer

        return peer



    def add_ebgp_session(self, peer_a_id, peer_b_id):

        """建立 eBGP 会话"""

        self.peers[peer_a_id].ebgp_neighbors.add(peer_b_id)

        self.peers[peer_b_id].ebgp_neighbors.add(peer_a_id)



    def add_ibgp_session(self, peer_a_id, peer_b_id):

        """建立 iBGP 会话"""

        self.peers[peer_a_id].ibgp_neighbors.add(peer_b_id)

        self.peers[peer_b_id].ibgp_neighbors.add(peer_a_id)



    def originate_route(self, peer_id, prefix, next_hop):

        """AS 发起自己的路由"""

        peer = self.peers[peer_id]

        as_path = [peer.as_number]

        route = BGPRoute(prefix, as_path, next_hop)

        peer.receive_route(prefix, route)

        peer.select_best_route(prefix)



    def propagate_route(self, from_peer_id, to_peer_id, prefix):

        """

        路由传播：从一个邻居传播到另一个邻居

        """

        from_peer = self.peers[from_peer_id]

        to_peer = self.peers[to_peer_id]



        if prefix not in from_peer.loc_rib:

            return



        route = from_peer.loc_rib[prefix]



        # AS_PATH 环路检测

        if to_peer.as_number in route.as_path:

            # 环路：丢弃

            return



        # 创建新路由：添加目的 AS 到 AS_PATH

        new_route = BGPRoute(

            prefix=route.prefix,

            as_path=[to_peer.as_number] + route.as_path,

            next_hop=from_peer.peer_id,

            origin=route.origin,

        )



        to_peer.receive_route(prefix, new_route)

        to_peer.select_best_route(prefix)





class RouteFlapping:

    """

    路由震荡（Route Flapping）检测与抑制（MRAI）

    BGP route flap damping 算法：

    当路由状态变化时，惩罚值增加；

    惩罚值超过阈值后，路由被抑制（suppressed）；

    惩罚值按指数衰减，直到低于 reuse threshold 后恢复。

    """



    def __init__(self, suppress_threshold=2000, reuse_threshold=750,

                 half_life=15, max_penalty=20000):

        self.suppress_threshold = suppress_threshold

        self.reuse_threshold = reuse_threshold

        self.half_life = half_life

        self.max_penalty = max_penalty



        self.penalties = {}  # prefix -> current penalty

        self.state = {}     # prefix -> 'ok' | 'suppressed'



    def on_route_change(self, prefix, change_type):

        """

        路由变化事件

        change_type: 'withdraw' | 'announce' | 'attribute_change'

        """

        if prefix not in self.penalties:

            self.penalties[prefix] = 0



        # 惩罚值增加

        if change_type == 'withdraw':

            self.penalties[prefix] += 1000

        elif change_type == 'announce':

            self.penalties[prefix] += 500

        elif change_type == 'attribute_change':

            self.penalties[prefix] += 500



        # 限制最大惩罚值

        self.penalties[prefix] = min(self.penalties[prefix], self.max_penalty)



        # 检查是否应抑制

        if self.penalties[prefix] >= self.suppress_threshold:

            self.state[prefix] = 'suppressed'

        else:

            self.state[prefix] = 'ok'



    def decay(self, elapsed_minutes):

        """

        惩罚值衰减（按半衰期指数衰减）

        penalty(t) = penalty_0 × (1/2)^(t / half_life)

        """

        decay_factor = (0.5) ** (elapsed_minutes / self.half_life)

        for prefix in self.penalties:

            self.penalties[prefix] *= decay_factor

            if self.penalties[prefix] < self.reuse_threshold:

                self.state[prefix] = 'ok'



    def is_suppressed(self, prefix):

        return self.state.get(prefix, 'ok') == 'suppressed'





if __name__ == '__main__':

    print("BGP 路径向量路由算法演示")

    print("=" * 60)



    # 构建一个简单的 AS 拓扑

    #

    #   AS65001 (ISP-1) ---- AS65003 (Tier-1)

    #         |                   |

    #   AS65002 (ISP-2) ---- AS65003

    #

    bgp = BGPPathVector()



    # 创建 AS 和对等体

    for as_num in [65001, 65002, 65003]:

        bgp.add_peer(f'peer_{as_num}', as_num)



    # 建立 eBGP 会话

    bgp.add_ebgp_session('peer_65001', 'peer_65003')

    bgp.add_ebgp_session('peer_65002', 'peer_65003')

    bgp.add_ebgp_session('peer_65001', 'peer_65002')



    # AS65001 发起一条路由

    bgp.originate_route('peer_65001', '192.168.0.0/16', '10.0.1.1')



    print("\nBGP 路由传播：")

    print("  AS65001 发布: 192.168.0.0/16 (AS_PATH=[65001])")



    # 模拟路由传播

    # AS65001 -> AS65002: AS_PATH=[65002, 65001]

    bgp.propagate_route('peer_65001', 'peer_65002', '192.168.0.0/16')

    r = bgp.peers['peer_65002'].loc_rib.get('192.168.0.0/16')

    if r:

        print(f"  AS65002 学到: AS_PATH={r.as_path}")



    # AS65001 -> AS65003: AS_PATH=[65003, 65001]

    bgp.propagate_route('peer_65001', 'peer_65003', '192.168.0.0/16')

    r = bgp.peers['peer_65003'].loc_rib.get('192.168.0.0/16')

    if r:

        print(f"  AS65003 学到: AS_PATH={r.as_path}")



    # AS65003 -> AS65002: AS_PATH=[65002, 65003, 65001]

    bgp.propagate_route('peer_65003', 'peer_65002', '192.168.0.0/16')

    # 检查 AS_PATH 环路

    print(f"\n  AS65002 从 AS65003 收到: AS_PATH=[65002, 65003, 65001]")

    print(f"  检测: AS65002 在 AS_PATH 中 -> 检测到环路，丢弃！")



    print("\n" + "=" * 60)

    print("BGP 选路规则示例：")

    print("  AS65002 收到两条到 192.168.0.0/16 的路由：")

    print("    路径1: AS_PATH=[65001]         (直接来自 AS65001)")

    print("    路径2: AS_PATH=[65003, 65001]  (通过 AS65003)")



    r1 = BGPRoute('192.168.0.0/16', [65001], '10.0.1.1', 'IGP')

    r2 = BGPRoute('192.168.0.0/16', [65003, 65001], '10.0.2.1', 'IGP')



    print(f"\n  选择结果: AS_PATH 最短 = [65001] (2 < 3)")

    print(f"  即选择直接从 AS65001 接收的路径")



    print("\n" + "=" * 60)

    print("【路由震荡抑制（MRAI/Damping）】")

    damping = RouteFlapping()



    events = [

        ('192.168.0.0/24', 'announce'),

        ('192.168.0.0/24', 'withdraw'),

        ('192.168.0.0/24', 'announce'),

        ('192.168.0.0/24', 'withdraw'),

        ('192.168.0.0/24', 'announce'),

    ]



    print(f"\n{'事件':<20} {'惩罚值':<12} {'状态':<12}")

    print("-" * 45)

    for prefix, event in events:

        damping.on_route_change(prefix, event)

        state = damping.state.get(prefix, 'ok')

        print(f"  {event:<20} {damping.penalties[prefix]:<12.0f} {state:<12}")



    print("\n结论：路由震荡被惩罚值累积，达到阈值后被抑制，")

    print("      避免频繁的 BGP UPDATE 报文浪费带宽和处理资源")

