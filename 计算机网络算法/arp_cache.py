# -*- coding: utf-8 -*-
"""
算法实现：计算机网络算法 / arp_cache

本文件实现 arp_cache 相关的算法功能。
"""

import time
import random


class ARPCache:
    """
    ARP 缓存表：维护 IP -> MAC 的映射
    支持动态学习、静态条目、老化机制
    """

    ARP_ENTRY_TIMEOUT = 1200  # ARP 条目生存时间（秒）
    MAX_ENTRIES = 1024

    def __init__(self):
        # entries: {ip_address: {'mac': str, 'interface': str, 'age': float, 'static': bool}}
        self.entries = {}
        # pending_requests: {ip_address: [(callback, timestamp), ...]}
        self.pending_requests = {}
        # 统计
        self.stats = {'queries': 0, 'hits': 0, 'misses': 0}

    def query(self, ip_address):
        """
        查询 ARP 缓存
        返回: (mac_address, is_stale) 或 (None, None)
        """
        self.stats['queries'] += 1
        entry = self.entries.get(ip_address)

        if entry:
            age = time.time() - entry['timestamp']
            is_stale = age > self.ARP_ENTRY_TIMEOUT
            self.stats['hits'] += 1
            return entry['mac'], is_stale
        else:
            self.stats['misses'] += 1
            return None, None

    def add_entry(self, ip_address, mac_address, interface='eth0', static=False):
        """
        添加或更新 ARP 条目
        static: 是否为静态条目（永不老化）
        """
        if len(self.entries) >= self.MAX_ENTRIES and ip_address not in self.entries:
            # 淘汰最老的条目
            self._evict_oldest()

        self.entries[ip_address] = {
            'mac': mac_address,
            'interface': interface,
            'timestamp': time.time(),
            'static': static,
        }

    def remove_entry(self, ip_address):
        """删除 ARP 条目"""
        self.entries.pop(ip_address, None)

    def age_entries(self):
        """老化：删除超时的动态条目"""
        current_time = time.time()
        expired = []
        for ip, entry in self.entries.items():
            if not entry['static']:
                if current_time - entry['timestamp'] > self.ARP_ENTRY_TIMEOUT:
                    expired.append(ip)
        for ip in expired:
            del self.entries[ip]
        return expired

    def _evict_oldest(self):
        """淘汰最老的条目"""
        if not self.entries:
            return
        oldest_ip = min(self.entries,
                       key=lambda ip: self.entries[ip]['timestamp'])
        del self.entries[oldest_ip]

    def get_cache_size(self):
        return len(self.entries)

    def get_hit_rate(self):
        total = self.stats['hits'] + self.stats['misses']
        if total == 0:
            return 0.0
        return self.stats['hits'] / total


class LongestPrefixMatch:
    """
    最长前缀匹配（Longest Prefix Match, LPM）
    IP 路由查找的核心：给定目的 IP，从多个路由条目中选择前缀最长匹配的条目。

    实现方式：二叉 trie（压缩或不压缩）
    """

    class TrieNode:
        """Trie 节点"""
        def __init__(self):
            self.children = {}       # '0' -> TrieNode, '1' -> TrieNode
            self.is_leaf = False     # 是否为叶子节点（有路由）
            self.route = None        # 叶子节点存储的路由信息

    def __init__(self):
        self.root = self.TrieNode()
        self.route_count = 0

    def insert(self, prefix, prefix_len, route_info):
        """
        插入路由条目
        prefix: IP 前缀（整数，如 0xC0A80100 = 192.168.1.0）
        prefix_len: 前缀长度（0-32）
        route_info: 路由信息（如下一跳、出接口等）
        """
        node = self.root
        for i in range(prefix_len):
            bit = (prefix >> (31 - i)) & 1
            bit_str = str(bit)
            if bit_str not in node.children:
                node.children[bit_str] = self.TrieNode()
            node = node.children[bit_str]

        node.is_leaf = True
        node.route = (prefix_len, route_info)
        self.route_count += 1

    def lookup(self, ip_address):
        """
        最长前缀匹配查找
        ip_address: 目的 IP（整数或字符串）
        返回: (matched_prefix_len, route_info) 或 None
        """
        if isinstance(ip_address, str):
            # 字符串格式 -> 整数
            parts = ip_address.split('.')
            ip_address = (int(parts[0]) << 24) | (int(parts[1]) << 16) | \
                        (int(parts[2]) << 8) | int(parts[3])

        node = self.root
        best_match = None
        best_len = 0

        for i in range(32):
            bit = (ip_address >> (31 - i)) & 1
            bit_str = str(bit)
            if bit_str not in node.children:
                break
            node = node.children[bit_str]
            if node.is_leaf:
                best_match = node.route
                best_len = node.route[0]

        return best_match

    def lookup_binary(self, ip_int):
        """
        二进制遍历方式的最长前缀匹配（简化实现）
        """
        return self.lookup(ip_int)


class IPRouteTable:
    """
    IP 路由表：结合 ARP 和 LPM
    """

    def __init__(self):
        self.lpm = LongestPrefixMatch()
        self.arp_cache = ARPCache()

    def add_route(self, prefix, prefix_len, next_hop, interface='eth0'):
        """添加路由条目"""
        route_info = {
            'prefix': prefix,
            'prefix_len': prefix_len,
            'next_hop': next_hop,
            'interface': interface,
        }
        self.lpm.insert(prefix, prefix_len, route_info)

    def route_lookup(self, dest_ip):
        """
        路由查找：LPM + ARP
        返回: (next_hop_ip, mac_address, interface) 或 None
        """
        match = self.lpm.lookup(dest_ip)
        if not match:
            return None

        prefix_len, route_info = match
        next_hop_ip = route_info['next_hop']

        # ARP 查找
        mac, is_stale = self.arp_cache.query(next_hop_ip)
        if is_stale is None:
            # ARP miss，需要发起 ARP 请求
            return None

        return {
            'next_hop_ip': next_hop_ip,
            'mac_address': mac,
            'interface': route_info['interface'],
            'is_stale': is_stale,
        }

    def add_static_route(self, dest_ip, next_hop_ip, mac, interface='eth0'):
        """添加静态路由和 ARP 条目"""
        self.arp_cache.add_entry(next_hop_ip, mac, interface, static=True)


if __name__ == '__main__':
    print("ARP 缓存与最长前缀匹配（LPM）算法演示")
    print("=" * 60)

    # -------------------- ARP 缓存演示 --------------------
    arp = ARPCache()

    print("\n【ARP 缓存操作】")
    entries = [
        ('192.168.1.1', 'aa:bb:cc:dd:ee:01'),
        ('192.168.1.2', 'aa:bb:cc:dd:ee:02'),
        ('10.0.0.1', 'ff:ff:ff:ff:ff:ff'),
    ]
    for ip, mac in entries:
        arp.add_entry(ip, mac)

    for ip, _ in entries:
        mac, stale = arp.query(ip)
        print(f"  查询 {ip} -> {mac} {'(过期)' if stale else ''}")

    print(f"\nARP 命中率: {arp.get_hit_rate():.1%}")
    print(f"缓存条目数: {arp.get_cache_size()}")

    # -------------------- LPM 演示 --------------------
    print("\n" + "=" * 60)
    print("【最长前缀匹配（LPM）】")

    lpm = LongestPrefixMatch()

    # 插入路由条目（CIDR 格式）
    routes = [
        (0xC0A80100, 24, {'gw': '192.168.1.254', 'if': 'eth0'}),  # 192.168.1.0/24
        (0xC0A80000, 16, {'gw': '192.168.0.1', 'if': 'eth0'}),    # 192.168.0.0/16
        (0x0A000000, 8,  {'gw': '10.0.0.1', 'if': 'eth1'}),       # 10.0.0.0/8
        (0x00000000, 0,  {'gw': '0.0.0.0', 'if': 'eth0'}),       # 默认路由
    ]

    for prefix, plen, info in routes:
        lpm.insert(prefix, plen, info)

    print(f"路由表条目数: {lpm.route_count}")

    # 测试查找
    test_ips = ['192.168.1.100', '192.168.50.1', '10.20.30.40', '8.8.8.8']

    print(f"\n{'目的IP':<18} {'最长匹配':<10} {'下一跳':<18} {'出接口':<10}")
    print("-" * 60)

    for ip_str in test_ips:
        parts = ip_str.split('.')
        ip_int = (int(parts[0]) << 24) | (int(parts[1]) << 16) | \
                 (int(parts[2]) << 8) | int(parts[3])

        match = lpm.lookup(ip_str)
        if match:
            plen, info = match
            print(f"{ip_str:<18} /{plen:<9} {info['gw']:<18} {info['if']:<10}")
        else:
            print(f"{ip_str:<18} 未匹配")

    print("\n关键算法：")
    print("  朴素实现: 遍历所有路由表 O(N)，太慢")
    print("  二叉 Trie:  O(W)，W=32 位，适中")
    print("  LC-trie:    压缩 Trie，路由表查找 O(log N)")
    print("  DXR:        硬件友好，Linux 使用的算法")
