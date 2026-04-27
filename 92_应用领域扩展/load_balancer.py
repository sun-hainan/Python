# -*- coding: utf-8 -*-

"""

算法实现：25_�������� / load_balancer



本文件实现 load_balancer 相关的算法功能。

"""



import random

import time

from typing import List, Dict, Optional, Callable

from dataclasses import dataclass, field

from abc import ABC, abstractmethod

import hashlib





@dataclass

class Server:

    """服务器节点"""

    id: str

    host: str

    port: int

    weight: int = 1  # 权重（用于加权算法）

    connections: int = 0  # 当前活跃连接数

    total_requests: int = 0  # 总请求数

    total_failures: int = 0  # 总失败数

    latency_samples: List[float] = field(default_factory=list)  # 延迟样本

    

    @property

    def healthy(self) -> bool:

        """健康检查"""

        return self.total_failures < self.total_requests * 0.5  # 失败率<50%

    

    @property

    def avg_latency(self) -> float:

        """平均延迟"""

        if not self.latency_samples:

            return float('inf')

        return sum(self.latency_samples) / len(self.latency_samples)

    

    def add_latency(self, latency: float):

        """添加延迟样本"""

        self.latency_samples.append(latency)

        if len(self.latency_samples) > 100:

            self.latency_samples.pop(0)





class LoadBalancer(ABC):

    """负载均衡器基类"""

    

    def __init__(self, servers: List[Server] = None):

        self.servers = servers or []

        self._server_map = {s.id: s for s in self.servers}

    

    def add_server(self, server: Server):

        """添加服务器"""

        self.servers.append(server)

        self._server_map[server.id] = server

    

    def remove_server(self, server_id: str):

        """移除服务器"""

        self.servers = [s for s in self.servers if s.id != server_id]

        if server_id in self._server_map:

            del self._server_map[server_id]

    

    @abstractmethod

    def select(self, request: dict) -> Optional[Server]:

        """

        选择服务器

        

        Args:

            request: 请求信息

        

        Returns:

            选中的服务器

        """

        pass

    

    def dispatch(self, request: dict) -> Optional[Server]:

        """分发请求"""

        # 过滤不健康的服务器

        healthy = [s for s in self.servers if s.healthy]

        

        if not healthy:

            return None

        

        server = self.select(request)

        

        if server:

            server.connections += 1

            server.total_requests += 1

        

        return server





class RoundRobin(LoadBalancer):

    """轮询负载均衡"""

    

    def __init__(self, servers: List[Server] = None):

        super().__init__(servers)

        self._counter = 0

    

    def select(self, request: dict) -> Optional[Server]:

        if not self.servers:

            return None

        

        server = self.servers[self._counter % len(self.servers)]

        self._counter += 1

        return server





class WeightedRoundRobin(LoadBalancer):

    """加权轮询负载均衡"""

    

    def __init__(self, servers: List[Server] = None):

        super().__init__(servers)

        self._counter = 0

        self._current_weight = 0

        self._gcd = self._calculate_gcd()

    

    def _calculate_gcd(self) -> int:

        """计算所有服务器权重的最大公约数"""

        if not self.servers:

            return 1

        weights = [s.weight for s in self.servers]

        return self._gcd_list(weights)

    

    def _gcd_list(self, numbers: List[int]) -> int:

        """计算列表的GCD"""

        from math import gcd

        result = numbers[0]

        for n in numbers[1:]:

            result = gcd(result, n)

        return result

    

    def select(self, request: dict) -> Optional[Server]:

        if not self.servers:

            return None

        

        while True:

            self._current_weight += 1

            for server in self.servers:

                if server.weight >= self._current_weight:

                    return server

            

            self._current_weight = 0





class LeastConnections(LoadBalancer):

    """最少连接负载均衡"""

    

    def select(self, request: dict) -> Optional[Server]:

        if not self.servers:

            return None

        

        # 选择连接数最少的服务器

        return min(self.servers, key=lambda s: s.connections)





class LeastResponseTime(LoadBalancer):

    """最小响应时间负载均衡"""

    

    def select(self, request: dict) -> Optional[Server]:

        if not self.servers:

            return None

        

        # 选择平均延迟最低的服务器

        return min(self.servers, key=lambda s: s.avg_latency)





class IPHash(LoadBalancer):

    """IP哈希负载均衡"""

    

    def select(self, request: dict) -> Optional[Server]:

        if not self.servers:

            return None

        

        # 基于客户端IP计算哈希

        client_ip = request.get('client_ip', '')

        hash_val = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)

        

        # 选择服务器

        idx = hash_val % len(self.servers)

        return self.servers[idx]





class URLHash(LoadBalancer):

    """URL哈希负载均衡"""

    

    def select(self, request: dict) -> Optional[Server]:

        if not self.servers:

            return None

        

        # 基于URL计算哈希

        url = request.get('url', '')

        hash_val = int(hashlib.md5(url.encode()).hexdigest(), 16)

        

        idx = hash_val % len(self.servers)

        return self.servers[idx]





class PowerOfTwoChoices(LoadBalancer):

    """

    Two Choices算法

    

    核心思想：随机选择两个服务器，选择负载较轻的一个

    理论保证：最大负载不超过平均负载的O(log log n)倍

    """

    

    def select(self, request: dict) -> Optional[Server]:

        if not self.servers:

            return None

        

        if len(self.servers) == 1:

            return self.servers[0]

        

        # 随机选择两个

        candidates = random.sample(self.servers, 2)

        

        # 选择负载较轻的

        return min(candidates, key=lambda s: s.connections)





class PredictiveLoadBalancer(LoadBalancer):

    """

    预测性负载均衡

    

    考虑服务器健康趋势，预测未来状态

    """

    

    def __init__(self, servers: List[Server] = None):

        super().__init__(servers)

        self.failure_history = {s.id: [] for s in servers or []}

    

    def select(self, request: dict) -> Optional[Server]:

        if not self.servers:

            return None

        

        # 计算每台服务器的分数

        scores = {}

        for server in self.servers:

            # 基础分数（越低越好）

            base_score = server.connections

            

            # 失败率惩罚

            if server.total_requests > 0:

                failure_rate = server.total_failures / server.total_requests

                base_score *= (1 + failure_rate)

            

            # 延迟惩罚

            if server.avg_latency < float('inf'):

                base_score *= (1 + server.avg_latency / 1000)

            

            # 趋势惩罚（最近5个请求的失败情况）

            recent = self.failure_history.get(server.id, [])

            if len(recent) >= 3 and sum(recent[-3:]) >= 2:

                base_score *= 1.5  # 近期失败率高，增加惩罚

            

            scores[server.id] = base_score

        

        # 选择分数最低的

        best_id = min(scores, key=scores.get)

        return self._server_map[best_id]

    

    def record_result(self, server_id: str, success: bool, latency: float):

        """记录请求结果"""

        if server_id not in self._server_map:

            return

        

        server = self._server_map[server_id]

        server.add_latency(latency)

        

        if not success:

            server.total_failures += 1

        

        if server_id not in self.failure_history:

            self.failure_history[server_id] = []

        

        self.failure_history[server_id].append(0 if success else 1)

        if len(self.failure_history[server_id]) > 10:

            self.failure_history[server_id].pop(0)





def simulate_lb(algorithm: LoadBalancer, num_requests: int = 1000):

    """

    模拟负载均衡

    

    Args:

        algorithm: 负载均衡算法

        num_requests: 请求数量

    """

    distribution = {s.id: 0 for s in algorithm.servers}

    

    for i in range(num_requests):

        request = {

            'id': i,

            'client_ip': f"192.168.1.{random.randint(1, 255)}",

            'url': f"/api/{random.randint(1, 10)}"

        }

        

        server = algorithm.dispatch(request)

        if server:

            distribution[server.id] += 1

            # 模拟请求完成

            server.connections -= 1

            

            # 模拟一些失败

            if random.random() < 0.05:

                server.total_failures += 1

    

    return distribution





def compare_algorithms():

    """

    对比不同负载均衡算法

    """

    print("=== 负载均衡算法对比 ===\n")

    

    num_servers = 5

    servers = [

        Server(id=f"server-{i}", host=f"192.168.1.{i+10}", port=8080, weight=10-i)

        for i in range(num_servers)

    ]

    

    algorithms = {

        "Round Robin": RoundRobin,

        "Weighted RR": WeightedRoundRobin,

        "Least Conn": LeastConnections,

        "Power of 2": PowerOfTwoChoices,

    }

    

    num_requests = 10000

    

    print(f"服务器数量: {num_servers}")

    print(f"总请求数: {num_requests}")

    print()

    

    results = {}

    

    for name, algo_class in algorithms.items():

        # 重新创建服务器（避免状态污染）

        fresh_servers = [

            Server(id=f"server-{i}", host=f"192.168.1.{i+10}", port=8080, weight=10-i)

            for i in range(num_servers)

        ]

        lb = algo_class(fresh_servers)

        dist = simulate_lb(lb, num_requests)

        

        results[name] = dist

        

        print(f"{name}:")

        for sid, count in dist.items():

            pct = count / num_requests * 100

            bar = '█' * int(pct)

            print(f"  {sid}: {pct:5.2f}% {bar}")

        print()

    

    # 计算负载均衡度（标准差，越低越均衡）

    print("负载均衡度（标准差，越低越均衡）:")

    for name, dist in results.items():

        counts = list(dist.values())

        mean = sum(counts) / len(counts)

        std = (sum((c - mean) ** 2 for c in counts) / len(counts)) ** 0.5

        print(f"  {name}: {std:.2f}")





def demo_health_tracking():

    """

    演示健康追踪

    """

    print("\n=== 健康追踪演示 ===\n")

    

    lb = PredictiveLoadBalancer()

    

    servers = [

        Server(id="web-1", host="10.0.0.1", port=80),

        Server(id="web-2", host="10.0.0.2", port=80),

        Server(id="web-3", host="10.0.0.3", port=80),

    ]

    

    for s in servers:

        lb.add_server(s)

    

    # 模拟请求

    print("模拟100个请求（含失败）:")

    for i in range(100):

        server = lb.dispatch({'id': i})

        if server:

            success = random.random() > 0.1  # 10%失败率

            latency = random.gauss(50, 10)  # 50ms ± 10ms

            lb.record_result(server.id, success, latency)

            server.connections -= 1

    

    # 打印状态

    print("\n服务器状态:")

    for server in lb.servers:

        print(f"  {server.id}:")

        print(f"    总请求: {server.total_requests}")

        print(f"    失败数: {server.total_failures}")

        print(f"    失败率: {server.total_failures/server.total_requests*100:.1f}%")

        print(f"    平均延迟: {server.avg_latency:.2f}ms")





def demo_least_connections():

    """

    演示最少连接算法

    """

    print("\n=== 最少连接算法演示 ===\n")

    

    servers = [

        Server(id="s1", host="10.0.0.1", port=80),

        Server(id="s2", host="10.0.0.2", port=80),

        Server(id="s3", host="10.0.0.3", port=80),

    ]

    

    lb = LeastConnections(servers)

    

    print("初始状态（连接数=0）:")

    print(f"  选择: {lb.select({}).id}")

    

    # 模拟不同连接数

    servers[0].connections = 100

    servers[1].connections = 50

    servers[2].connections = 200

    

    print("\n设置连接数: s1=100, s2=50, s3=200")

    print(f"  选择: {lb.select({}).id} (最少连接)")

    

    servers[0].connections = 10

    servers[1].connections = 10

    servers[2].connections = 10

    

    print("\n全部连接数=10时:")

    print(f"  选择: {lb.select({}).id} (轮流出)")





if __name__ == "__main__":

    # 算法对比

    compare_algorithms()

    

    # 健康追踪

    demo_health_tracking()

    

    # 最少连接演示

    demo_least_connections()

    

    print("\n" + "=" * 60)

    print("算法总结:")

    print("=" * 60)

    print("""

| 算法             | 复杂度 | 特点                          |

|-----------------|-------|-------------------------------|

| Round Robin     | O(1)  | 简单，假设服务器性能相同         |

| Weighted RR     | O(n)  | 考虑服务器性能差异              |

| Least Conn      | O(n)  | 考虑当前负载                    |

| Least Response  | O(n)  | 考虑延迟                        |

| IP/URL Hash     | O(1)  | 会话保持                        |

| Power of 2      | O(1)  | 理论保证好，简单                 |

| Predictive      | O(n)  | 考虑趋势和健康状态              |

""")

