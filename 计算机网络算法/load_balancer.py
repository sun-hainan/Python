# -*- coding: utf-8 -*-
"""
算法实现：计算机网络算法 / load_balancer

本文件实现 load_balancer 相关的算法功能。
"""

import random
import time
import hashlib
from collections import defaultdict


class LoadBalancer:
    """负载均衡器基类"""

    def __init__(self, servers):
        """
        初始化负载均衡器
        
        参数:
            servers: 后端服务器列表，每个服务器是 (host, port) 或自定义对象
        """
        self.servers = servers
        # 记录每个服务器的当前连接数
        self.connection_counts = defaultdict(int)
        # 记录每个服务器的健康状态
        self.health_status = {s: True for s in servers}
        # 健康检查间隔（秒）
        self.health_check_interval = 30
        # 上次健康检查时间
        self.last_health_check = time.time()

    def select_server(self, client_info=None):
        """
        选择一个服务器
        
        参数:
            client_info: 客户端信息（如 IP 地址）
        返回:
            server: 选中的服务器
        """
        raise NotImplementedError("子类必须实现 select_server 方法")

    def record_connection(self, server):
        """记录与服务器的连接"""
        self.connection_counts[server] += 1

    def release_connection(self, server):
        """释放与服务器的连接"""
        if self.connection_counts[server] > 0:
            self.connection_counts[server] -= 1

    def get_connection_count(self, server):
        """获取服务器的当前连接数"""
        return self.connection_counts[server]

    def set_server_health(self, server, healthy):
        """设置服务器的健康状态"""
        self.health_status[server] = healthy

    def get_healthy_servers(self):
        """获取所有健康的服务器"""
        return [s for s in self.servers if self.health_status.get(s, True)]


class RoundRobinLB(LoadBalancer):
    """轮询负载均衡器"""

    def __init__(self, servers):
        super().__init__(servers)
        # 当前轮询到的索引
        self.current_index = 0
        # 轮询计数器
        self.total_requests = 0

    def select_server(self, client_info=None):
        """轮询选择服务器"""
        healthy = self.get_healthy_servers()
        if not healthy:
            return None
        
        # 简单轮询
        server = healthy[self.current_index % len(healthy)]
        self.current_index += 1
        self.total_requests += 1
        
        return server


class WeightedRoundRobinLB(LoadBalancer):
    """加权轮询负载均衡器"""

    def __init__(self, servers_with_weights):
        """
        初始化加权轮询负载均衡器
        
        参数:
            servers_with_weights: [(server, weight), ...] 元组列表
        """
        self.servers = [s[0] for s in servers_with_weights]
        self.weights = {s[0]: s[1] for s in servers_with_weights}
        super().__init__(self.servers)
        
        # 当前权重
        self.current_weights = {s[0]: s[1] for s in servers_with_weights}
        # 最大公约数（用于算法）
        self.gcd_weight = self._gcd_of_weights()
        # 当前索引
        self.current_index = 0

    def _gcd_of_weights(self):
        """计算所有权重的最大公约数"""
        weights = list(self.weights.values())
        result = weights[0]
        for w in weights[1:]:
            result = self._gcd(result, w)
        return result

    @staticmethod
    def _gcd(a, b):
        """计算最大公约数"""
        while b:
            a, b = b, a % b
        return a

    def select_server(self, client_info=None):
        """加权轮询选择服务器"""
        healthy = self.get_healthy_servers()
        if not healthy:
            return None
        
        # 简单的加权轮询实现
        # 每次选择权重最高的服务器，然后权重减1
        max_weight_server = None
        max_weight = -1
        
        for _ in range(len(healthy)):
            server = healthy[self.current_index % len(healthy)]
            self.current_index += 1
            
            if self.current_weights[server] > max_weight:
                max_weight = self.current_weights[server]
                max_weight_server = server
        
        # 恢复权重
        for s in healthy:
            self.current_weights[s] += self.gcd_weight
        
        # 选中服务器的权重减 gcd
        self.current_weights[max_weight_server] -= self.gcd_weight
        
        return max_weight_server


class LeastConnectionsLB(LoadBalancer):
    """最少连接负载均衡器"""

    def __init__(self, servers):
        super().__init__(servers)
        # 记录每个服务器的连接历史（用于平滑计算）
        self.avg_response_times = {s: 1.0 for s in servers}

    def select_server(self, client_info=None):
        """选择连接数最少（或响应时间最短）的服务器"""
        healthy = self.get_healthy_servers()
        if not healthy:
            return None
        
        # 选择平均响应时间最短的服务器
        # 这里简化实现，实际应该考虑连接数
        best_server = min(healthy, key=lambda s: self.avg_response_times[s])
        return best_server

    def update_response_time(self, server, response_time):
        """
        更新服务器的平均响应时间（指数加权移动平均）
        
        参数:
            server: 服务器
            response_time: 本次响应时间（秒）
        """
        alpha = 0.3  # 平滑因子
        if server in self.avg_response_times:
            self.avg_response_times[server] = (
                alpha * response_time +
                (1 - alpha) * self.avg_response_times[server]
            )


class IPHashLB(LoadBalancer):
    """IP 哈希负载均衡器"""

    def __init__(self, servers):
        super().__init__(servers)
        # 一致性哈希环
        self._init_hash_ring()

    def _init_hash_ring(self):
        """初始化哈希环"""
        self.hash_ring = []
        for server in self.servers:
            h = int(hashlib.md5(str(server).encode()).hexdigest()[:8], 16)
            self.hash_ring.append((h, server))
        self.hash_ring.sort(key=lambda x: x[0])

    def select_server(self, client_info=None):
        """根据客户端 IP 哈希选择服务器"""
        healthy = self.get_healthy_servers()
        if not healthy:
            return None
        
        # 如果没有 client_info，随机选择
        if not client_info or 'ip' not in client_info:
            return random.choice(healthy)
        
        # 对客户端 IP 进行哈希
        ip = client_info['ip']
        hash_val = int(hashlib.md5(ip.encode()).hexdigest()[:8], 16)
        
        # 找到环上对应的位置
        for h, server in self.hash_ring:
            if h >= hash_val and self.health_status.get(server, True):
                return server
        
        # 环尾，循环到环首
        for h, server in self.hash_ring:
            if self.health_status.get(server, True):
                return server


class LeastResponseTimeLB(LoadBalancer):
    """最短响应时间负载均衡器"""

    def __init__(self, servers):
        super().__init__(servers)
        # 服务器权重（用于计算综合得分）
        self.weights = {s: 1.0 for s in servers}
        # 平均响应时间
        self.response_times = {s: 0.0 for s in servers}
        # 活跃请求数
        self.active_requests = {s: 0 for s in servers}
        # 请求计数
        self.request_counts = {s: 0 for s in servers}

    def select_server(self, client_info=None):
        """选择响应时间最短且负载较低的服务器"""
        healthy = self.get_healthy_servers()
        if not healthy:
            return None
        
        # 计算每个服务器的综合得分
        # 得分 = 响应时间 * sqrt(活跃请求数 + 1)
        best_server = None
        best_score = float('inf')
        
        for server in healthy:
            # 综合得分（响应时间越长、活跃请求越多，得分越高）
            score = self.response_times[server] * (self.active_requests[server] ** 0.5 + 1)
            if score < best_score:
                best_score = score
                best_server = server
        
        if best_server:
            self.active_requests[best_server] += 1
        
        return best_server

    def record_request_start(self, server):
        """记录请求开始"""
        self.active_requests[server] += 1
        self.request_counts[server] += 1

    def record_request_end(self, server, response_time):
        """记录请求结束"""
        if self.active_requests[server] > 0:
            self.active_requests[server] -= 1
        
        # 更新响应时间（EWMA）
        alpha = 0.3
        self.response_times[server] = (
            alpha * response_time +
            (1 - alpha) * self.response_times[server]
        )


class Server:
    """模拟后端服务器"""

    def __init__(self, host, port, weight=1):
        self.host = host
        self.port = port
        self.weight = weight
        self.active_connections = 0
        self.total_requests = 0
        self.total_response_time = 0

    def __str__(self):
        return f"{self.host}:{self.port}"

    def __repr__(self):
        return f"Server({self.host}:{self.port}, weight={self.weight})"


if __name__ == "__main__":
    # 测试负载均衡算法
    print("=== 负载均衡算法测试 ===\n")

    # 创建服务器列表
    servers = [
        Server("192.168.1.1", 8080, weight=3),
        Server("192.168.1.2", 8080, weight=2),
        Server("192.168.1.3", 8080, weight=1),
    ]
    server_names = [str(s) for s in servers]

    # 1. 测试轮询
    print("--- 轮询负载均衡 ---")
    rr_lb = RoundRobinLB(server_names)
    for i in range(10):
        server = rr_lb.select_server()
        print(f"请求 {i+1} -> {server}")

    # 2. 测试加权轮询
    print("\n--- 加权轮询负载均衡 ---")
    weighted_servers = [(str(s), s.weight) for s in servers]
    wrr_lb = WeightedRoundRobinLB(weighted_servers)
    for i in range(18):  # 3+2+1=6 为一轮，总共3轮
        server = wrr_lb.select_server()
        print(f"请求 {i+1} -> {server}")

    # 3. 测试最少连接
    print("\n--- 最少连接负载均衡 ---")
    lc_lb = LeastConnectionsLB(server_names)
    # 模拟一些连接
    for i in range(5):
        server = lc_lb.select_server()
        lc_lb.record_connection(server)
        print(f"请求 {i+1} -> {server} (连接数: {lc_lb.get_connection_count(server)})")

    # 4. 测试 IP 哈希
    print("\n--- IP 哈希负载均衡 ---")
    ip_lb = IPHashLB(server_names)
    test_ips = ["10.0.0.1", "10.0.0.2", "10.0.0.3", "10.0.0.4"]
    for ip in test_ips:
        server = ip_lb.select_server({'ip': ip})
        print(f"IP {ip} -> {server}")

    # 5. 测试最短响应时间
    print("\n--- 最短响应时间负载均衡 ---")
    lrt_lb = LeastResponseTimeLB(server_names)
    # 模拟请求和响应
    for i in range(10):
        server = lrt_lb.select_server()
        lrt_lb.record_request_start(server)
        # 模拟响应
        response_time = random.uniform(0.01, 0.1)
        lrt_lb.record_request_end(server, response_time)
        print(f"请求 {i+1} -> {server} (响应时间: {response_time*1000:.1f}ms)")
