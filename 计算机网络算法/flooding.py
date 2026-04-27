# -*- coding: utf-8 -*-

"""

算法实现：计算机网络算法 / flooding



本文件实现 flooding 相关的算法功能。

"""



import random

import math

from collections import defaultdict, deque





class NetworkNode:

    """网络节点"""



    def __init__(self, node_id):

        self.node_id = node_id

        self.neighbors = set()

        # seen_messages: {(source_id, sequence_number)} 已接收/转发的消息

        self.seen_messages = set()

        # 统计

        self.stats = {'received': 0, 'forwarded': 0, 'duplicate_dropped': 0}





class FloodingProtocol:

    """

    序列号泛洪协议（Sequence Number Flooding）

    最可靠的泛洪算法之一，被广泛应用于链路状态路由协议（OSPF、IS-IS）

    """



    def __init__(self):

        self.nodes = {}

        self.sequence_numbers = {}  # {node_id: current_seq_num}



    def add_node(self, node_id):

        self.nodes[node_id] = NetworkNode(node_id)



    def add_link(self, node_a, node_b):

        """添加双向链路"""

        self.nodes[node_a].neighbors.add(node_b)

        self.nodes[node_b].neighbors.add(node_a)



    def _get_next_seq(self, source_id):

        """获取下一个序列号"""

        if source_id not in self.sequence_numbers:

            self.sequence_numbers[source_id] = 0

        else:

            self.sequence_numbers[source_id] += 1

        return self.sequence_numbers[source_id]



    def flood(self, source_id, message, ttl=10):

        """

        从 source_id 发起泛洪广播

        返回: 所有收到消息的节点及跳数

        """

        msg_id = (source_id, self._get_next_seq(source_id))

        # BFS 泛洪

        results = {source_id: 0}  # node -> hop_count

        queue = deque([(source_id, 0, source_id)])  # (current, hop, from)



        while queue:

            current, hop, from_node = queue.popleft()



            for neighbor in self.nodes[current].neighbors:

                if neighbor == from_node:

                    continue  # 不回传给来源

                if hop + 1 >= ttl:

                    continue  # TTL 限制



                msg_key = (msg_id[0], msg_id[1], neighbor)

                if msg_key not in self.nodes[current].seen_messages:

                    self.nodes[current].seen_messages.add(msg_key)

                    self.nodes[current].stats['forwarded'] += 1



                if neighbor not in results or results[neighbor] > hop + 1:

                    results[neighbor] = hop + 1

                    queue.append((neighbor, hop + 1, current))



        return results, msg_id





class GossipProtocol:

    """

    Gossip（流行病）协议：概率性泛洪

    每个节点收到消息后，以概率 p 随机选择部分邻居转发

    优势：消息数量从 O(E) 降至 O(p × E)

    特性：最终一致性（Eventually Consistent）

    典型应用：Redis Cluster 心跳、Cassandra 去中心化、DynamoDB 复制

    """



    def __init__(self, fanout=3):

        self.fanout = fanout  # 每次 gossip 传播的邻居数

        self.nodes = {}

        self.message_history = {}  # node -> set of seen messages



    def add_node(self, node_id):

        self.nodes[node_id] = {

            'peers': set(),

            'received': set(),

        }



    def add_peer(self, node_a, node_b):

        self.nodes[node_a]['peers'].add(node_b)

        self.nodes[node_b]['peers'].add(node_a)



    def gossip(self, source_id, message_id, max_rounds=10):

        """

        执行一轮 Gossip 传播

        返回: 每轮的覆盖节点数

        """

        if source_id not in self.message_history:

            self.message_history[source_id] = set()



        infected = {source_id}

        self.message_history[source_id].add(message_id)



        for round_num in range(max_rounds):

            new_infections = set()



            for node_id in infected:

                node = self.nodes[node_id]

                # 随机选择 fanout 个邻居

                peers = list(node['peers'] - infected)

                if len(peers) > self.fanout:

                    selected = random.sample(peers, self.fanout)

                else:

                    selected = peers



                for peer in selected:

                    new_infections.add(peer)

                    self.nodes[peer]['received'].add(message_id)



            infected |= new_infections



            yield round_num + 1, len(infected), infected.copy()





class SwarmGossipProtocol:

    """

    SWAN（Gossip with Random Walkers）：随机游走 + Gossip 结合

    消息通过多个随机游走者（Random Walkers）传播，提高可靠性

    """



    def __init__(self, num_walkers=3, max_hops=10):

        self.num_walkers = num_walkers

        self.max_hops = max_hops

        self.nodes = {}



    def add_node(self, node_id):

        self.nodes[node_id] = {'neighbors': set()}



    def add_link(self, node_a, node_b):

        self.nodes[node_a]['neighbors'].add(node_b)

        self.nodes[node_b]['neighbors'].add(node_a)



    def random_walk(self, source_id, message_id):

        """

        单个随机游走者从 source 出发

        返回: 游走经过的节点路径

        """

        current = source_id

        path = [current]

        visited = {current}



        for hop in range(self.max_hops):

            neighbors = list(self.nodes[current]['neighbors'] - visited)

            if not neighbors:

                break

            next_node = random.choice(neighbors)

            path.append(next_node)

            visited.add(next_node)

            current = next_node



        return path



    def deliver_message(self, source_id, message_id):

        """

        通过多个随机游走者分发消息

        返回: 所有游走者访问过的节点（去重）

        """

        all_visitors = set()



        for _ in range(self.num_walkers):

            path = self.random_walk(source_id, message_id)

            all_visitors |= set(path)



        return all_visitors





class ReversePathForwarding:

    """

    Reverse Path Forwarding (RPF) 多播转发

    多播路由器只在"从源到本路由器的反向路径上"时才转发数据包，

    从而构建一棵以源为根的最短路径树（SPT）。

    优点：避免泛洪的指数冗余

    """



    def __init__(self, unicast_routing_table):

        # unicast_routing_table: {node_id: {dest: (next_hop, cost)}}

        self.urt = unicast_routing_table



    def should_forward(self, router_id, source_ip, multicast_group):

        """

        判断路由器是否应该转发多播数据包

        条件：收到数据包的接口位于到源的最短路径上

        """

        if router_id not in self.urt:

            return True  # 不知道，保守转发

        route_to_source = self.urt[router_id].get(source_ip)

        if route_to_source is None:

            return False  # 不知道源在哪，不转发

        return True  # 在反向路径上





if __name__ == '__main__':

    print("泛洪（Flooding）与 Gossip 协议演示")

    print("=" * 60)



    # 构建网络拓扑

    #

    #         A --- B --- C

    #         |  X  |  X  |

    #         D --- E --- F

    #          X  |  X  |

    #             G --- H

    #



    network = FloodingProtocol()



    for nid in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:

        network.add_node(nid)



    links = [

        ('A', 'B'), ('A', 'D'),

        ('B', 'C'), ('B', 'E'),

        ('C', 'F'),

        ('D', 'E'), ('D', 'G'),

        ('E', 'F'), ('E', 'G'),

        ('F', 'H'),

        ('G', 'H'),

    ]

    for a, b in links:

        network.add_link(a, b)



    print("网络拓扑：")

    print("  A--B--C")

    print("  |  |  |")

    print("  D--E--F")

    print("   \\|/ \\|/")

    print("    G---H")



    # 序列号泛洪

    print("\n【序列号泛洪】从节点 A 广播消息到所有节点：")

    results, msg_id = network.flood('A', 'data_pkt', ttl=5)

    print(f"  消息 ID: {msg_id}")

    print(f"  覆盖节点: {sorted(results.keys())}")

    print(f"  跳数分布: { {k: v for k, v in results.items()} }")



    total_forwarded = sum(n.stats['forwarded'] for n in network.nodes.values())

    print(f"  总转发次数: {total_forwarded}（理想最小生成树 = {2 * (len(links))} = {2 * len(links)}）")



    # Gossip

    print("\n" + "=" * 60)

    print("【Gossip 协议】从节点 A 传播消息（fanout=3）：")



    gossip = GossipProtocol(fanout=3)

    for nid in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:

        gossip.add_node(nid)

    for a, b in links:

        gossip.add_peer(a, b)



    print(f"\n{'轮次':<8} {'感染节点数':<15} {'覆盖率':<10}")

    print("-" * 35)

    for round_num, count, infected in gossip.gossip('A', 'gossip_msg', max_rounds=6):

        print(f"  {round_num:<8} {count:<15} {count/8*100:.1f}%")

        if count == 8:

            print(f"  所有节点已接收，提前收敛！")

            break



    print("\n关键算法对比：")

    print("  泛洪:       100% 可靠，但转发次数 = O(E)，冗余极大")

    print("  Gossip:     概率收敛，最终一致性，冗余可控 O(log N)")

    print("  RPF:        多播专属，只在反向最短路径上转发")

    print("  随机游走:   匿名网络/结构化 P2P（DHT）中常用")

    print("\n典型应用：")

    print("  OSPF/IS-IS: 链路状态路由使用可靠泛洪同步 LSDB")

    print("  Chord DHT:   随机游走定位节点")

    print("  Cassandra:   Gossip 维护集群成员关系")

    print("  Bitcoin:     Dandelion++ 隐私广播")

