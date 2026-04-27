# -*- coding: utf-8 -*-
"""
算法实现：计算机网络算法 / anycast_cdn

本文件实现 anycast_cdn 相关的算法功能。
"""

import math
import heapq
from collections import defaultdict


class GeoLocation:
    """地理位置"""

    def __init__(self, lat=0, lon=0):
        self.lat = lat
        self.lon = lon

    def distance_to(self, other):
        """计算到另一个位置的距离（公里），使用 Haversine 公式"""
        R = 6371
        lat1, lat2 = math.radians(self.lat), math.radians(other.lat)
        dlat, dlon = math.radians(other.lat - self.lat), math.radians(other.lon - self.lon)
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))

    def __str__(self):
        return f"({self.lat:.2f}, {self.lon:.2f})"


class CDNServer:
    """CDN 服务器节点"""

    def __init__(self, server_id, location, ip_address, capacity=10000):
        self.server_id = server_id
        self.location = location
        self.ip_address = ip_address
        self.capacity = capacity
        self.current_load = 0
        self.healthy = True

    def get_available_capacity(self):
        return max(0, self.capacity - self.current_load)

    def is_healthy(self):
        return self.healthy

    def add_load(self, requests):
        self.current_load += requests

    def remove_load(self, requests):
        self.current_load = max(0, self.current_load - requests)

    def get_load_ratio(self):
        return self.current_load / self.capacity if self.capacity > 0 else 1.0


class AnycastRouter:
    """Anycast 路由器"""

    def __init__(self, router_id, location):
        self.router_id = router_id
        self.location = location
        self.routing_table = defaultdict(list)
        self.connected_servers = []

    def add_route(self, destination, next_hop, metric):
        self.routing_table[destination].append((next_hop, metric))

    def get_best_route(self, destination):
        if not self.routing_table.get(destination):
            return None, float('inf')
        return min(self.routing_table[destination], key=lambda x: x[1])


class CDNNetwork:
    """CDN 网络（Anycast 系统）"""

    def __init__(self):
        self.servers = {}
        self.routers = {}
        self.anycast_ip = "1.1.1.1"

    def add_server(self, server_id, lat, lon, ip, capacity=10000):
        loc = GeoLocation(lat, lon)
        self.servers[server_id] = CDNServer(server_id, loc, ip, capacity)

    def add_router(self, router_id, lat, lon):
        loc = GeoLocation(lat, lon)
        self.routers[router_id] = AnycastRouter(router_id, loc)

    def select_best_server(self, client_location, strategy='geographic'):
        """
        根据策略选择最优服务器
        
        参数:
            client_location: 客户端位置
            strategy: 策略 - 'geographic', 'load', 'latency', 'hybrid'
        返回:
            server: 选中的服务器
        """
        candidates = [s for s in self.servers.values() if s.is_healthy()]
        if not candidates:
            return None
        
        if strategy == 'geographic':
            # 基于地理位置选择
            return min(candidates, key=lambda s: s.location.distance_to(client_location))
        
        elif strategy == 'load':
            # 基于负载选择
            return min(candidates, key=lambda s: s.get_load_ratio())
        
        elif strategy == 'latency':
            # 基于延迟选择（模拟）
            return min(candidates, key=lambda s: s.location.distance_to(client_location) / 200)
        
        elif strategy == 'hybrid':
            # 混合策略：地理距离 + 负载
            best = None
            best_score = float('inf')
            for s in candidates:
                dist = s.location.distance_to(client_location)
                load = s.get_load_ratio()
                score = dist * (1 + load)
                if score < best_score:
                    best_score = score
                    best = s
            return best
        
        return candidates[0]

    def route_request(self, client_lat, client_lon, content_id, strategy='hybrid'):
        """路由请求到最优服务器"""
        client_loc = GeoLocation(client_lat, client_lon)
        server = self.select_best_server(client_loc, strategy)
        if server:
            server.add_load(1)
        return server


if __name__ == "__main__":
    print("=== Anycast/CDN 测试 ===")
    cdn = CDNNetwork()
    
    # 添加服务器
    cdn.add_server("US_EAST", 40.71, -74.01, "1.1.1.10")
    cdn.add_server("US_WEST", 37.77, -122.41, "1.1.1.11")
    cdn.add_server("EU_WEST", 51.51, -0.13, "1.1.1.12")
    cdn.add_server("ASIA_EAST", 35.68, 139.69, "1.1.1.13")
    
    # 模拟请求
    test_clients = [
        (40.71, -74.01, "NYC"),
        (34.05, -118.24, "LA"),
        (48.86, 2.35, "Paris"),
        (35.68, 139.69, "Tokyo"),
    ]
    
    print("\n策略测试:")
    for lat, lon, name in test_clients:
        client_loc = GeoLocation(lat, lon)
        server = cdn.select_best_server(client_loc, 'geographic')
        print(f"  {name} ({lat:.1f}, {lon:.1f}) -> {server.server_id} (距离: {server.location.distance_to(client_loc):.0f}km)")
    
    # 负载均衡测试
    print("\n负载均衡测试:")
    for i in range(10):
        cdn.route_request(40.71, -74.01, "content1")
    
    for sid, s in cdn.servers.items():
        print(f"  {sid}: 负载 {s.current_load}/{s.capacity} ({s.get_load_ratio()*100:.1f}%)")
