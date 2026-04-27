# -*- coding: utf-8 -*-
"""
算法实现：计算机网络算法 / mac_learning

本文件实现 mac_learning 相关的算法功能。
"""

import time
from collections import defaultdict


class MACEntry:
    """MAC 地址表条目"""

    def __init__(self, mac_address, port, vlan_id=1):
        """
        初始化 MAC 条目
        
        参数:
            mac_address: MAC 地址（字符串或字节）
            port: 端口号
            vlan_id: VLAN ID
        """
        self.mac_address = mac_address if isinstance(mac_address, str) else mac_address.hex()
        self.port = port
        self.vlan_id = vlan_id
        self.timestamp = time.time()
        self.is_static = False

    def is_expired(self, max_age):
        """检查是否过期"""
        if self.is_static:
            return False
        return (time.time() - self.timestamp) > max_age

    def touch(self):
        """刷新时间戳"""
        self.timestamp = time.time()


class CAMTable:
    """CAM（Content Addressable Memory）表 - MAC 地址学习表"""

    def __init__(self, max_age=300, max_entries=10000):
        """
        初始化 CAM 表
        
        参数:
            max_age: 条目最大存活时间（秒），默认 300 秒
            max_entries: 最大条目数
        """
        self.max_age = max_age
        self.max_entries = max_entries
        # MAC 表：{(vlan_id, mac_address): MACEntry}
        self.table = {}
        # 统计数据
        self.learned_count = 0
        self.lookups = 0
        self.hits = 0

    def learn(self, mac_address, port, vlan_id=1):
        """
        学习 MAC 地址
        
        参数:
            mac_address: MAC 地址
            port: 端口号
            vlan_id: VLAN ID
        """
        mac_str = mac_address if isinstance(mac_address, str) else mac_address.hex()
        key = (vlan_id, mac_str)
        
        entry = MACEntry(mac_address, port, vlan_id)
        self.table[key] = entry
        self.learned_count += 1

        # 如果超出容量，删除最老的条目
        if len(self.table) > self.max_entries:
            self._evict_oldest()

    def lookup(self, mac_address, vlan_id=1):
        """
        查找 MAC 地址对应的端口
        
        参数:
            mac_address: MAC 地址
            vlan_id: VLAN ID
        返回:
            port: 端口号，未找到返回 None
        """
        self.lookups += 1
        mac_str = mac_address if isinstance(mac_address, str) else mac_address.hex()
        key = (vlan_id, mac_str)
        
        entry = self.table.get(key)
        if entry:
            self.hits += 1
            entry.touch()  # 刷新时间戳
            return entry.port
        return None

    def remove(self, mac_address, vlan_id=1):
        """删除 MAC 条目"""
        mac_str = mac_address if isinstance(mac_address, str) else mac_address.hex()
        key = (vlan_id, mac_str)
        if key in self.table:
            del self.table[key]

    def age_entries(self):
        """删除过期的条目"""
        expired = []
        for key, entry in self.table.items():
            if entry.is_expired(self.max_age):
                expired.append(key)
        
        for key in expired:
            del self.table[key]
        
        return len(expired)

    def _evict_oldest(self):
        """驱逐最老的条目"""
        if not self.table:
            return
        
        oldest_key = min(self.table.items(), key=lambda x: x[1].timestamp)[0]
        del self.table[oldest_key]

    def get_stats(self):
        """获取统计信息"""
        return {
            'entries': len(self.table),
            'learned': self.learned_count,
            'lookups': self.lookups,
            'hits': self.hits,
            'hit_rate': self.hits / self.lookups if self.lookups > 0 else 0
        }


class VLANPort:
    """VLAN 端口配置"""

    def __init__(self, port_id, mode='access'):
        """
        初始化 VLAN 端口
        
        参数:
            port_id: 端口 ID
            mode: 端口模式 - 'access' 或 'trunk'
        """
        self.port_id = port_id
        self.mode = mode
        self.access_vlan = 1
        self.trunk_allowed_vlans = []
        self.tagged_vlans = []

    def set_access_vlan(self, vlan_id):
        """设置 access 端口的 VLAN"""
        self.access_vlan = vlan_id

    def add_trunk_vlan(self, vlan_id, tagged=False):
        """添加 trunk 端口允许的 VLAN"""
        if vlan_id not in self.trunk_allowed_vlans:
            self.trunk_allowed_vlans.append(vlan_id)
        if tagged and vlan_id not in self.tagged_vlans:
            self.tagged_vlans.append(vlan_id)


class VLANTable:
    """VLAN 表"""

    def __init__(self):
        self.vlans = {}  # vlan_id -> {name, ports, ...}
        self.port_vlan = {}  # port_id -> vlan_id

    def create_vlan(self, vlan_id, name=""):
        """创建 VLAN"""
        self.vlans[vlan_id] = {
            'id': vlan_id,
            'name': name or f"VLAN{vlan_id}",
            'ports': set(),
            'create_time': time.time()
        }

    def delete_vlan(self, vlan_id):
        """删除 VLAN"""
        if vlan_id in self.vlans:
            del self.vlans[vlan_id]

    def add_port(self, vlan_id, port_id):
        """将端口加入 VLAN"""
        if vlan_id not in self.vlans:
            self.create_vlan(vlan_id)
        self.vlans[vlan_id]['ports'].add(port_id)
        self.port_vlan[port_id] = vlan_id

    def remove_port(self, vlan_id, port_id):
        """将端口从 VLAN 移除"""
        if vlan_id in self.vlans:
            self.vlans[vlan_id]['ports'].discard(port_id)
        if self.port_vlan.get(port_id) == vlan_id:
            del self.port_vlan[port_id]

    def get_port_vlan(self, port_id):
        """获取端口所属的 VLAN"""
        return self.port_vlan.get(port_id)

    def is_port_in_vlan(self, port_id, vlan_id):
        """检查端口是否在 VLAN 中"""
        if vlan_id not in self.vlans:
            return False
        return port_id in self.vlans[vlan_id]['ports']


class Switch:
    """以太网交换机（带 MAC 学习和 VLAN 支持）"""

    def __init__(self, switch_id):
        self.switch_id = switch_id
        self.cam_table = CAMTable()
        self.vlan_table = VLANTable()
        self.ports = {}
        self.fdb = defaultdict(list)  # 转发数据库

    def add_port(self, port_id, mode='access'):
        """添加端口"""
        self.ports[port_id] = VLANPort(port_id, mode)

    def configure_port(self, port_id, **kwargs):
        """配置端口"""
        if port_id in self.ports:
            port = self.ports[port_id]
            if 'access_vlan' in kwargs:
                port.set_access_vlan(kwargs['access_vlan'])
            if 'trunk_allowed' in kwargs:
                for vlan_id in kwargs['trunk_allowed']:
                    port.add_trunk_vlan(vlan_id)

    def process_frame(self, src_mac, dst_mac, port_id, vlan_id=1, payload=None):
        """
        处理接收到的帧
        
        参数:
            src_mac: 源 MAC 地址
            dst_mac: 目标 MAC 地址
            port_id: 接收端口
            vlan_id: VLAN ID
            payload: 数据负载
        返回:
            action: 'forward', 'flood', 'drop'
            ports: 目标端口列表
        """
        # 1. 学习源 MAC
        self.cam_table.learn(src_mac, port_id, vlan_id)
        
        # 2. 查找目标 MAC
        dst_port = self.cam_table.lookup(dst_mac, vlan_id)
        
        if dst_port is None:
            # 未知单播，泛洪
            return ('flood', self._get_flood_ports(port_id, vlan_id))
        elif dst_port == port_id:
            # 来自同一端口，丢弃
            return ('drop', [])
        else:
            # 已知单播，转发
            return ('forward', [dst_port])

    def _get_flood_ports(self, exclude_port, vlan_id):
        """获取泛洪端口"""
        ports = []
        for port_id, port in self.ports.items():
            if port_id != exclude_port:
                if port.mode == 'access' and port.access_vlan == vlan_id:
                    ports.append(port_id)
                elif port.mode == 'trunk' and vlan_id in port.trunk_allowed_vlans:
                    ports.append(port_id)
        return ports

    def age_entries(self):
        """老化 MAC 表"""
        return self.cam_table.age_entries()


if __name__ == "__main__":
    print("=== MAC 地址学习与 VLAN 测试 ===\n")

    # 创建交换机
    sw = Switch("SW1")
    
    # 添加并配置端口
    sw.add_port(1, 'access')
    sw.add_port(2, 'access')
    sw.add_port(3, 'access')
    sw.add_port(10, 'trunk')
    sw.configure_port(1, access_vlan=10)
    sw.configure_port(2, access_vlan=10)
    sw.configure_port(3, access_vlan=20)
    sw.configure_port(10, trunk_allowed=[10, 20, 30])

    # 创建 VLAN
    sw.vlan_table.create_vlan(10, "Engineering")
    sw.vlan_table.create_vlan(20, "Marketing")

    # 模拟帧到达
    test_frames = [
        ('00:11:22:33:44:55', 'aa:bb:cc:dd:ee:ff', 1, 10),
        ('aa:bb:cc:dd:ee:ff', '00:11:22:33:44:55', 2, 10),
        ('11:22:33:44:55:66', '22:33:44:55:66:77', 3, 20),
    ]
    
    print("处理帧:")
    for src, dst, port, vlan in test_frames:
        action, ports = sw.process_frame(src, dst, port, vlan)
        print(f"  {src} -> {dst} (port {port}, VLAN {vlan}): {action} -> {ports}")
        
        # 学习后再次查找
        dst_port = sw.cam_table.lookup(dst, vlan)
        print(f"    查找目标: {'命中' if dst_port else '未命中'}")
    
    # 显示 CAM 表
    print("\nCAM 表统计:")
    stats = sw.cam_table.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print(f"\n表条目数: {len(sw.cam_table.table)}")
    
    # VLAN 测试
    print("\nVLAN 测试:")
    print(f"  端口 1 在 VLAN 10: {sw.vlan_table.is_port_in_vlan(1, 10)}")
    print(f"  端口 3 在 VLAN 10: {sw.vlan_table.is_port_in_vlan(3, 10)}")
