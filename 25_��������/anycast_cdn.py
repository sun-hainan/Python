# -*- coding: utf-8 -*-
"""
算法实现：25_�������� / anycast_cdn

本文件实现 anycast_cdn 相关的算法功能。
"""

import random
import heapq
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional


@dataclass
class Server:
    """服务器节点"""
    id: str
    ip: str
    region: str
    lat: float  # 纬度
    lon: float  # 经度
    load: float = 0.0  # 当前负载
    healthy: bool = True
    
    def distance_to(self, lat: float, lon: float) -> float:
        """计算到用户的大致距离（简化Haversine）"""
        dlat = self.lat - lat
        dlon = self.lon - lon
        return (dlat**2 + dlon**2) ** 0.5


class AnycastDNS:
    """
    Anycast DNS实现
    
    多个DNS服务器使用相同的IP（Anycast IP）
    用户请求被路由到最近的服务器
    """
    
    def __init__(self, anycast_ip: str):
        self.anycast_ip = anycast_ip
        self.servers: List[Server] = []
        self.domain_cache: Dict[str, str] = {}  # 域名->IP缓存
    
    def add_server(self, server: Server):
        """添加DNS服务器"""
        self.servers.append(server)
    
    def resolve(self, domain: str, user_lat: float, user_lon: float) -> Optional[str]:
        """
        解析域名
        
        Args:
            domain: 域名
            user_lat: 用户纬度
            user_lon: 用户经度
        
        Returns:
            最近的健康服务器IP
        """
        # 查找最近的健康服务器
        nearest = self._find_nearest(user_lat, user_lon)
        
        if not nearest:
            return None
        
        # 模拟DNS解析
        return nearest.ip
    
    def _find_nearest(self, lat: float, lon: float) -> Optional[Server]:
        """查找最近的健康服务器"""
        healthy = [s for s in self.servers if s.healthy]
        
        if not healthy:
            return None
        
        # 按距离排序
        healthy.sort(key=lambda s: s.distance_to(lat, lon))
        
        # 考虑负载
        candidates = healthy[:3]
        candidates.sort(key=lambda s: s.load)
        
        return candidates[0]
    
    def health_check(self) -> Dict[str, bool]:
        """健康检查"""
        results = {}
        for s in self.servers:
            # 模拟健康检查
            s.healthy = random.random() > 0.05  # 5%故障率
            results[s.id] = s.healthy
        return results


class CDNLatencyRouter:
    """
    CDN延迟路由
    
    根据实时延迟选择最优CDN节点
    """
    
    def __init__(self):
        self.nodes: List[Server] = []
        self.latency_cache: Dict[Tuple[str, str], float] = {}
    
    def add_node(self, node: Server):
        """添加CDN节点"""
        self.nodes.append(node)
    
    def update_latency(self, from_id: str, to_id: str, latency: float):
        """更新延迟"""
        self.latency_cache[(from_id, to_id)] = latency
    
    def measure_latency(self, from_id: str, to_id: str) -> float:
        """测量延迟（模拟）"""
        if (from_id, to_id) in self.latency_cache:
            return self.latency_cache[(from_id, to_id)]
        
        # 模拟测量
        return random.uniform(10, 100)
    
    def route(self, user_id: str, user_lat: float, user_lon: float, 
              content_id: str) -> Optional[Server]:
        """
        路由用户请求
        
        Args:
            user_id: 用户ID
            user_lat: 用户纬度
            user_lon: 用户经度
            content_id: 内容ID
        
        Returns:
            最优CDN节点
        """
        # 筛选健康节点
        healthy = [n for n in self.nodes if n.healthy]
        
        if not healthy:
            return None
        
        # 计算每个节点的得分
        scores = []
        for node in healthy:
            # 距离得分
            dist = node.distance_to(user_lat, user_lon)
            
            # 延迟得分（模拟）
            latency = self.measure_latency(user_id, node.id)
            
            # 负载得分
            load = node.load
            
            # 综合得分（越低越好）
            score = dist * 0.3 + latency * 0.1 + load * 0.6
            
            scores.append((score, node))
        
        scores.sort()
        return scores[0][1] if scores else None


class GeoDNS:
    """
    GeoDNS - 基于地理位置的DNS
    
    将用户路由到特定区域的服务器
    """
    
    def __init__(self):
        self.regions = {
            'us-east': {'lat_range': (25, 50), 'lon_range': (-120, -70)},
            'us-west': {'lat_range': (30, 50), 'lon_range': (-130, -110)},
            'europe': {'lat_range': (35, 65), 'lon_range': (-10, 40)},
            'asia': {'lat_range': (0, 55), 'lon_range': (60, 150)},
        }
        self.region_servers: Dict[str, List[Server]] = {}
    
    def add_server(self, server: Server):
        """添加服务器"""
        region = self._classify_region(server.lat, server.lon)
        server.region = region
        
        if region not in self.region_servers:
            self.region_servers[region] = []
        self.region_servers[region].append(server)
    
    def _classify_region(self, lat: float, lon: float) -> str:
        """分类区域"""
        for region, bounds in self.regions.items():
            lat_min, lat_max = bounds['lat_range']
            lon_min, lon_max = bounds['lon_range']
            
            if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                return region
        
        return 'other'
    
    def resolve(self, domain: str, user_lat: float, user_lon: float) -> Optional[str]:
        """
        地理位置DNS解析
        
        Returns:
            用户所在区域的服务器IP
        """
        user_region = self._classify_region(user_lat, user_lon)
        
        # 优先返回同区域服务器
        if user_region in self.region_servers:
            servers = self.region_servers[user_region]
            healthy = [s for s in servers if s.healthy]
            
            if healthy:
                # 返回负载最低的
                healthy.sort(key=lambda s: s.load)
                return healthy[0].ip
        
        # 回退到其他区域
        for region, servers in self.region_servers.items():
            if region == user_region:
                continue
            healthy = [s for s in servers if s.healthy]
            if healthy:
                return healthy[0].ip
        
        return None


def demo_anycast_dns():
    """演示Anycast DNS"""
    print("=== Anycast DNS演示 ===\n")
    
    dns = AnycastDNS("192.0.2.1")  # Anycast IP
    
    # 添加DNS服务器
    servers = [
        Server("ns1", "198.51.100.1", "us-east", 40.7, -74.0),
        Server("ns2", "198.51.100.2", "us-west", 37.8, -122.4),
        Server("ns3", "198.51.100.3", "europe", 51.5, -0.1),
        Server("ns4", "198.51.100.4", "asia", 35.7, 139.7),
    ]
    
    for s in servers:
        dns.add_server(s)
    
    # 模拟不同位置用户
    users = [
        ("纽约用户", 40.7, -74.0),
        ("洛杉矶用户", 34.1, -118.2),
        ("伦敦用户", 51.5, -0.1),
        ("东京用户", 35.7, 139.7),
    ]
    
    print("DNS解析测试:")
    for name, lat, lon in users:
        ip = dns.resolve("example.com", lat, lon)
        print(f"  {name}: {ip}")


def demo_cdn_routing():
    """演示CDN路由"""
    print("\n=== CDN延迟路由演示 ===\n")
    
    router = CDNLatencyRouter()
    
    # 添加CDN节点
    nodes = [
        Server("cdn1", "203.0.113.1", "us-east", 40.7, -74.0, load=0.3),
        Server("cdn2", "203.0.113.2", "us-west", 37.8, -122.4, load=0.5),
        Server("cdn3", "203.0.113.3", "europe", 51.5, -0.1, load=0.7),
        Server("cdn4", "203.0.113.4", "asia", 35.7, 139.7, load=0.2),
    ]
    
    for n in nodes:
        router.add_node(n)
    
    # 模拟用户
    print("CDN路由选择:")
    for name, lat, lon in [("纽约", 40.7, -74.0), ("东京", 35.7, 139.7)]:
        node = router.route(f"user-{name}", lat, lon, "video-123")
        if node:
            print(f"  {name}用户 -> {node.id} ({node.region}), 负载={node.load}")
    
    # 模拟故障转移
    print("\n模拟cdn1故障:")
    nodes[0].healthy = False
    
    node = router.route("user-newyork", 40.7, -74.0, "video-123")
    if node:
        print(f"  纽约用户 -> {node.id} ({node.region})")


def demo_geodns():
    """演示GeoDNS"""
    print("\n=== GeoDNS演示 ===\n")
    
    geo = GeoDNS()
    
    # 添加服务器
    servers = [
        Server("www-us", "203.0.113.10", "us-east", 40.7, -74.0),
        Server("www-eu", "203.0.113.11", "europe", 51.5, -0.1),
        Server("www-asia", "203.0.113.12", "asia", 35.7, 139.7),
    ]
    
    for s in servers:
        geo.add_server(s)
    
    # 测试
    print("GeoDNS解析:")
    for name, lat, lon in [("纽约", 40.7, -74.0), ("巴黎", 48.9, 2.4), ("北京", 39.9, 116.4)]:
        ip = geo.resolve("example.com", lat, lon)
        print(f"  {name}: {ip}")


def demo_dns_anycast_vs_unicast():
    """对比Anycast与Unicast DNS"""
    print("\n=== Anycast vs Unicast DNS ===\n")
    
    print("Anycast DNS:")
    print("  - 多个服务器共享同一IP")
    print("  - 路由器自动选择最近路径")
    print("  - 自动故障转移")
    print("  - 广泛用于.root服务器、CDN")
    
    print("\nUnicast DNS:")
    print("  - 每个服务器有唯一IP")
    print("  - 需要客户端选择")
    print("  - 依赖负载均衡器")
    print("  - 传统DNS架构")
    
    print("\n| 特性      | Anycast | Unicast |")
    print("|-----------|---------|---------|")
    print("| 延迟      | 更低   | 可变   |")
    print("| 可用性    | 更高   | 依赖LB |")
    print("| 复杂性    | 网络侧 | 应用侧 |")
    print("| 适用      | 根/CDN | 权威DNS|")


if __name__ == "__main__":
    print("=" * 60)
    print("Anycast DNS/CDN重定向算法")
    print("=" * 60)
    
    demo_anycast_dns()
    demo_cdn_routing()
    demo_geodns()
    demo_dns_anycast_vs_unicast()
    
    print("\n" + "=" * 60)
    print("应用场景:")
    print("=" * 60)
    print("""
1. DNS Anycast:
   - 根DNS服务器(TLD)
   - 大型CDN的DNS
   - DDoS防护

2. CDN路由:
   - 视频流媒体
   - 软件分发
   - Web加速

3. 故障转移:
   - 自动切换到健康节点
   - 区域故障隔离
   - 滚动更新支持
""")
