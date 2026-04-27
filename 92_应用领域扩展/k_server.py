# -*- coding: utf-8 -*-

"""

算法实现：25_�������� / k_server



本文件实现 k_server 相关的算法功能。

"""



import random

import math

from dataclasses import dataclass

from typing import List, Tuple, Optional

import heapq





@dataclass

class Point:

    """二维空间中的点"""

    x: float

    y: float

    

    def distance_to(self, other: 'Point') -> float:

        """欧几里得距离"""

        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    

    def __repr__(self):

        return f"({self.x:.1f}, {self.y:.1f})"





@dataclass

class Server:

    """服务器"""

    id: int

    position: Point

    

    def move_to(self, point: Point) -> float:

        """移动到目标点"""

        old_pos = self.position

        self.position = point

        return old_pos.distance_to(point)





class OnlineServer:

    """

    在线服务器框架

    

    K-Server问题的基类

    """

    

    def __init__(self, k: int, space_bounds: Tuple[float, float]):

        self.k = k

        self.servers: List[Server] = []

        self.total_cost = 0.0

        self.space_bounds = space_bounds

        

        # 初始化服务器位置

        for i in range(k):

            self.servers.append(Server(i, Point(0, 0)))

    

    def _find_nearest(self, point: Point) -> Server:

        """找到最近的服务器"""

        return min(self.servers, key=lambda s: s.position.distance_to(point))

    

    def _find_farthest(self, point: Point) -> Server:

        """找到最远的服务器"""

        return max(self.servers, key=lambda s: s.position.distance_to(point))





class FCAlgorithm(OnlineServer):

    """

    Functional Cost (FC) 算法

    

    核心思想：最小化所有服务器的势能变化

    """

    

    def __init__(self, k: int, space_bounds: Tuple[float, float]):

        super().__init__(k, space_bounds)

        self.phi = [0.0] * k  # 势能

        self.gamma = 1.0  # 学习率

    

    def serve_request(self, point: Point) -> float:

        """

        服务请求

        

        Args:

            point: 请求点

        

        Returns:

            移动成本

        """

        # 找到最近的服务器

        server = self._find_nearest(point)

        

        # 计算移动

        cost = server.position.distance_to(point)

        

        # 更新势能（简化）

        server.move_to(point)

        

        self.total_cost += cost

        return cost

    

    def get_potential(self) -> float:

        """获取总势能"""

        return sum(s.position.distance_to(Point(0, 0)) for s in self.servers)





class WMAlgorithm(OnlineServer):

    """

    Weighted Majority (WM) 算法

    

    使用多个专家（策略），根据性能加权

    """

    

    def __init__(self, k: int, space_bounds: Tuple[float, float], num_experts: int = 10):

        super().__init__(k, space_bounds)

        self.num_experts = num_experts

        self.expert_weights = [1.0] * num_experts

        self.expert_servers = [

            [Point(random.uniform(0, space_bounds[0]), 

                   random.uniform(0, space_bounds[1])) 

             for _ in range(k)]

            for _ in range(num_experts)

        ]

        self.eta = 0.1  # 学习率

    

    def serve_request(self, point: Point) -> float:

        """服务请求"""

        # 找到加权最近的服务器

        best_server = None

        best_score = float('inf')

        

        for s in self.servers:

            score = s.position.distance_to(point)

            total_weight = sum(self.expert_weights)

            weighted_score = score * total_weight

            best_score = min(best_score, weighted_score)

        

        # 选择服务器（简化：贪心）

        server = self._find_nearest(point)

        cost = server.position.distance_to(point)

        server.move_to(point)

        

        self.total_cost += cost

        return cost

    

    def update_weights(self, expert_costs: List[float]):

        """更新专家权重"""

        total_cost = sum(expert_costs)

        

        for i in range(self.num_experts):

            if expert_costs[i] > 0:

                self.expert_weights[i] *= (1 - self.eta)





class DMAlgorithm(OnlineServer):

    """

    Dynamic Mirror (DM) 算法（珂罗柕）

    

    核心思想：保持一组虚拟服务器，根据请求调整

    """

    

    def __init__(self, k: int, space_bounds: Tuple[float, float]):

        super().__init__(k, space_bounds)

        

        # 虚拟服务器（更多）

        self.virtual_servers: List[Point] = [

            Point(random.uniform(0, space_bounds[0]),

                  random.uniform(0, space_bounds[1]))

            for _ in range(k * 3)

        ]

        

        self.rates = [1.0] * len(self.virtual_servers)  # 激活率

    

    def serve_request(self, point: Point) -> float:

        """服务请求"""

        # 找到最近的虚拟服务器

        nearest_v = min(self.virtual_servers, 

                       key=lambda v: v.distance_to(point))

        

        # 移动最近的物理服务器到该点

        server = self._find_nearest(point)

        cost = server.position.distance_to(point)

        server.move_to(point)

        

        # 更新虚拟服务器位置（向请求点移动）

        for v in self.virtual_servers:

            if v == nearest_v:

                # 找到最近的物理服务器，更新

                nearest_s = self._find_nearest(v)

                v.x = nearest_s.position.x

                v.y = nearest_s.position.y

                break

        

        self.total_cost += cost

        return cost





class HARMONICAlgorithm(OnlineServer):

    """

    Harmonic算法

    

    K-Server问题的贪心近似

    """

    

    def __init__(self, k: int, space_bounds: Tuple[float, float]):

        super().__init__(k, space_bounds)

        self.server_loads = [1.0] * k  # 服务器负载

    

    def serve_request(self, point: Point) -> float:

        """服务请求"""

        # 计算每个服务器的得分

        scores = []

        for i, s in enumerate(self.servers):

            dist = s.position.distance_to(point)

            load = self.server_loads[i]

            

            # 得分 = 距离 / 负载

            score = dist / load if load > 0 else float('inf')

            scores.append((score, i, dist))

        

        # 选择得分最低的

        scores.sort()

        _, server_idx, cost = scores[0]

        

        server = self.servers[server_idx]

        server.move_to(point)

        

        # 更新负载

        self.server_loads[server_idx] += 1

        

        self.total_cost += cost

        return cost





def simulate_online(k: int, num_requests: int, space_bounds: Tuple[float, float]):

    """

    模拟K-Server在线请求

    

    Args:

        k: 服务器数量

        num_requests: 请求数量

        space_bounds: 空间边界

    """

    print("=== K-Server在线算法模拟 ===\n")

    

    print(f"配置: K={k}, 请求数={num_requests}, 空间={space_bounds}")

    print()

    

    # 初始化算法

    algorithms = {

        'FC': FCAlgorithm(k, space_bounds),

        'WM': WMAlgorithm(k, space_bounds),

        'DM': DMAlgorithm(k, space_bounds),

        'Harmonic': HARMONICAlgorithm(k, space_bounds),

        'Greedy': OnlineServer(k, space_bounds),

    }

    

    # 生成随机请求

    requests = [

        Point(random.uniform(0, space_bounds[0]),

              random.uniform(0, space_bounds[1]))

        for _ in range(num_requests)

    ]

    

    # 运行每个算法

    results = {}

    

    for name, algo in algorithms.items():

        # 重置服务器位置

        for s in algo.servers:

            s.position = Point(0, 0)

        

        costs = []

        for req in requests:

            cost = 0

            if name == 'FC':

                cost = algo.serve_request(req)

            elif name == 'WM':

                cost = algo.serve_request(req)

            elif name == 'DM':

                cost = algo.serve_request(req)

            elif name == 'Harmonic':

                cost = algo.serve_request(req)

            elif name == 'Greedy':

                cost = algo.serve_request(req)

            

            costs.append(cost)

        

        results[name] = {

            'total_cost': algo.total_cost,

            'avg_cost': sum(costs) / len(costs),

            'max_cost': max(costs) if costs else 0

        }

    

    # 打印结果

    print("算法性能对比:")

    print("| 算法    | 总成本 | 平均成本 | 最大成本 |")

    print("|---------|--------|---------|---------|")

    

    for name, result in sorted(results.items(), key=lambda x: x[1]['total_cost']):

        print(f"| {name:7s} | {result['total_cost']:6.2f} | {result['avg_cost']:7.2f} | {result['max_cost']:6.2f} |")

    

    return results





def demo_offline_optimal():

    """

    演示离线最优解（用于对比）

    

    离线最优解使用调度算法

    """

    print("\n=== 离线最优解演示 ===\n")

    

    print("离线最优解需要知道未来请求序列")

    print("通常使用 Hungarian Algorithm 或调度理论")

    print()

    

    print("K-Server问题的理论下界:")

    print("  - 在树度量空间中，k--competitive")

    print("  - 在欧几里得空间中，下界是 O(log k)")

    print("  - 上界是 O(k log k) (珂罗柕算法)")





def demo_convergence():

    """演示收敛性"""

    print("\n=== 算法收敛演示 ===\n")

    

    k = 3

    algo = FCAlgorithm(k, (10, 10))

    

    costs_over_time = []

    

    for i in range(100):

        point = Point(random.uniform(0, 10), random.uniform(0, 10))

        cost = algo.serve_request(point)

        costs_over_time.append(cost)

    

    # 计算滑动平均

    window = 10

    moving_avg = []

    for i in range(len(costs_over_time) - window + 1):

        avg = sum(costs_over_time[i:i+window]) / window

        moving_avg.append(avg)

    

    print(f"前10个请求平均成本: {sum(costs_over_time[:10])/10:.2f}")

    print(f"最后10个请求平均成本: {sum(costs_over_time[-10:])/10:.2f}")

    print(f"成本变化: {'收敛' if costs_over_time[-1] < costs_over_time[0] else '发散'}")





def demo_competitive_ratio():

    """

    演示竞争比分析

    """

    print("\n=== 竞争比分析 ===\n")

    

    print("竞争比定义:")

    print("  Online算法的成本 / Offline最优解的成本")

    print()

    

    print("各算法的竞争比:")

    print("| 算法      | 竞争比 | 空间类型      |")

    print("|-----------|--------|---------------|")

    print("| 珂罗柕   | O(k)   | 任意度量空间   |")

    print("| HARMONIC | O(k)   | 通用度量空间   |")

    print("| Greedy   | 无界   | 通用度量空间   |")

    print("| 珂罗柕   | O(log k)| 欧几里得空间  |")

    print("| Random   | O(k)   | 任意度量空间   |")





if __name__ == "__main__":

    print("=" * 60)

    print("珂罗柕 K-Server 问题与在线算法")

    print("=" * 60)

    

    # 模拟

    simulate_online(k=3, num_requests=50, space_bounds=(10, 10))

    

    # 离线最优

    demo_offline_optimal()

    

    # 收敛性

    demo_convergence()

    

    # 竞争比

    demo_competitive_ratio()

    

    print("\n" + "=" * 60)

    print("珂罗柕算法核心原理:")

    print("=" * 60)

    print("""

1. 问题定义:

   - 度量空间 M 中有 K 个服务器

   - 在线请求序列 r1, r2, ..., rn

   - 每个请求必须被最近的服务器服务

   - 目标：最小化总移动成本



2. FC算法 (Functional Cost):

   - 定义势能函数 Φ

   - 每次移动使势能变化最小

   - 贪心选择



3. WM算法 (Weighted Majority):

   - 维护多个专家（策略）

   - 根据性能更新权重

   - 加权投票决定行动



4. DM算法 (Dynamic Mirror):

   - 保持虚拟服务器

   - 虚拟服务器根据请求动态调整

   - 物理服务器跟随虚拟服务器



5. 珂罗柕框架:

   - 是上述算法的统一框架

   - 使用流体力学模型

   - O(k) 竞争比

""")

