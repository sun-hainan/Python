# -*- coding: utf-8 -*-
"""
算法实现：25_�������� / p4_basics

本文件实现 p4_basics 相关的算法功能。
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import IntEnum
import struct


class P4Field(IntEnum):
    """P4标准字段"""
    ETH_SRC = 1
    ETH_DST = 2
    ETH_TYPE = 3
    IP_SRC = 10
    IP_DST = 11
    IP_PROTO = 12
    TCP_SRC = 13
    TCP_DST = 14
    UDP_SRC = 15
    UDP_DST = 16


@dataclass
class P4Header:
    """P4头部"""
    name: str
    fields: Dict[str, int]
    
    def to_bytes(self) -> bytes:
        """序列化"""
        data = b''
        for field in sorted(self.fields.keys()):
            value = self.fields[field]
            data += struct.pack('!I', value)
        return data
    
    @classmethod
    def from_bytes(cls, name: str, data: bytes, field_spec: List[Tuple[str, int]]):
        """从字节解析"""
        fields = {}
        offset = 0
        for field_name, size in field_spec:
            if size == 4:
                fields[field_name] = struct.unpack('!I', data[offset:offset+4])[0]
            elif size == 2:
                fields[field_name] = struct.unpack('!H', data[offset:offset+2])[0]
            elif size == 1:
                fields[field_name] = data[offset]
            offset += size
        return cls(name, fields)


class EthernetHeader(P4Header):
    """以太网头部"""
    def __init__(self, dst='ff:ff:ff:ff:ff:ff', src='00:00:00:00:00:00', eth_type=0x0800):
        fields = {
            'dst': self._parse_mac(dst),
            'src': self._parse_mac(src),
            'etherType': eth_type
        }
        super().__init__('ethernet', fields)
    
    @staticmethod
    def _parse_mac(mac: str) -> int:
        """解析MAC地址"""
        return int(mac.replace(':', ''), 16)
    
    def get_dst(self) -> str:
        return ':'.join(f'{(self.fields["dst"] >> (40-6*i)) & 0xff:02x}' 
                       for i in range(6))
    
    def get_src(self) -> str:
        return ':'.join(f'{(self.fields["src"] >> (40-6*i)) & 0xff:02x}' 
                       for i in range(6))


class IPv4Header(P4Header):
    """IPv4头部"""
    def __init__(self, src='0.0.0.0', dst='0.0.0.0', proto=6, ttl=64):
        fields = {
            'version': 4,
            'ihl': 5,
            'dscp': 0,
            'ecn': 0,
            'totalLength': 20,
            'identification': 0,
            'flags': 0,
            'fragmentOffset': 0,
            'ttl': ttl,
            'protocol': proto,
            'checksum': 0,
            'srcAddr': self._parse_ip(src),
            'dstAddr': self._parse_ip(dst)
        }
        super().__init__('ipv4', fields)
    
    @staticmethod
    def _parse_ip(ip: str) -> int:
        """解析IP地址"""
        parts = ip.split('.')
        return (int(parts[0]) << 24) | (int(parts[1]) << 16) | (int(parts[2]) << 8) | int(parts[3])
    
    def get_src(self) -> str:
        addr = self.fields['srcAddr']
        return f'{(addr >> 24) & 0xff}.{(addr >> 16) & 0xff}.{(addr >> 8) & 0xff}.{addr & 0xff}'
    
    def get_dst(self) -> str:
        addr = self.fields['dstAddr']
        return f'{(addr >> 24) & 0xff}.{(addr >> 16) & 0xff}.{(addr >> 8) & 0xff}.{addr & 0xff}'


class TCPHeader(P4Header):
    """TCP头部"""
    def __init__(self, src_port=0, dst_port=0, seq=0, ack=0, flags=2):
        fields = {
            'srcPort': src_port,
            'dstPort': dst_port,
            'seqNo': seq,
            'ackNo': ack,
            'dataOffset': 5,
            'flags': flags,
            'window': 65535,
            'checksum': 0,
            'urgentPtr': 0
        }
        super().__init__('tcp', fields)


class P4Match:
    """P4匹配类型"""
    EXACT = 'exact'
    LPM = 'lpm'  # 最长前缀匹配
    TERNARY = 'ternary'
    VALID = 'valid'


@dataclass
class P4MatchEntry:
    """匹配表项"""
    match_type: str
    fields: Dict[str, any]
    priority: int
    action: str
    action_data: Dict[str, any]


class MatchActionTable:
    """
    P4 Match-Action 表
    
    核心数据结构：
    - match_fields: 匹配字段定义
    - entries: 表项列表
    - actions: 可用动作
    """
    
    def __init__(self, name: str):
        self.name = name
        self.match_fields = []  # [(field_name, match_type), ...]
        self.entries = []  # [P4MatchEntry, ...]
        self.actions = {}  # action_name -> function
    
    def add_match_field(self, field: str, match_type: str = P4Match.EXACT):
        """添加匹配字段"""
        self.match_fields.append((field, match_type))
    
    def add_entry(self, match_values: Dict[str, any], action: str, 
                  action_data: Dict[str, any] = None, priority: int = 100):
        """添加表项"""
        entry = P4MatchEntry(
            match_type=','.join(mt for _, mt in self.match_fields),
            fields=match_values,
            priority=priority,
            action=action,
            action_data=action_data or {}
        )
        self.entries.append(entry)
    
    def match(self, headers: Dict[str, P4Header]) -> Optional[P4MatchEntry]:
        """
        匹配包
        
        Args:
            headers: 已解析的头部字典
        
        Returns:
            匹配的表项
        """
        # 按优先级排序
        sorted_entries = sorted(self.entries, key=lambda e: e.priority, reverse=True)
        
        for entry in sorted_entries:
            if self._entry_matches(entry, headers):
                return entry
        
        return None
    
    def _entry_matches(self, entry: P4MatchEntry, headers: Dict) -> bool:
        """检查表项是否匹配"""
        for field_name, expected_value in entry.fields.items():
            # 从headers中获取字段值
            actual_value = self._get_field_value(field_name, headers)
            if actual_value != expected_value:
                return False
        return True
    
    def _get_field_value(self, field_path: str, headers: Dict) -> any:
        """获取字段值"""
        parts = field_path.split('.')
        if len(parts) == 2:
            header_name, field_name = parts
            if header_name in headers:
                return headers[header_name].fields.get(field_name)
        return None


class P4Parser:
    """
    P4解析器
    
    定义数据包如何被解析成头部字段
    """
    
    def __init__(self):
        self.states = {}  # state_name -> parse_function
        self.current_state = 'start'
    
    def add_state(self, state_name: str, parser_fn):
        """添加解析状态"""
        self.states[state_name] = parser_fn
    
    def parse(self, data: bytes) -> Dict[str, P4Header]:
        """
        解析数据包
        
        Returns:
            headers字典
        """
        headers = {}
        state = 'start'
        
        while state and state != 'accept' and state != 'reject':
            if state in self.states:
                state = self.states[state](data, headers)
            else:
                break
        
        return headers


class P4Control:
    """
    P4控制块
    
    定义数据包的匹配-动作处理流程
    """
    
    def __init__(self, name: str):
        self.name = name
        self.tables = {}  # table_name -> MatchActionTable
        self.local_metadata = {}
    
    def add_table(self, table: MatchActionTable):
        """添加表"""
        self.tables[table.name] = table
    
    def apply(self, headers: Dict[str, P4Header], payload: bytes) -> Tuple[List[str], bytes]:
        """
        应用控制逻辑
        
        Returns:
            (actions, modified_payload)
        """
        actions_taken = []
        
        # 按顺序应用表
        for table_name, table in self.tables.items():
            match_result = table.match(headers)
            
            if match_result:
                action = match_result.action
                actions_taken.append(f"{action}({match_result.action_data})")
                
                # 执行动作
                self._execute_action(action, match_result.action_data, headers)
        
        return actions_taken, payload
    
    def _execute_action(self, action: str, action_data: Dict, headers: Dict):
        """执行动作"""
        if action == 'drop':
            pass
        elif action == '转发':
            pass
        elif action == 'modify_field':
            pass


class P4Program:
    """
    完整P4程序
    """
    
    def __init__(self):
        self.parser = P4Parser()
        self.control = P4Control('ingress')
        self.deparser = None
    
    def compile(self, packet: bytes) -> Tuple[bool, Dict, List[str]]:
        """
        编译数据包
        
        Returns:
            (accepted, headers, actions)
        """
        # 解析
        headers = self.parser.parse(packet)
        
        # 控制逻辑
        actions, payload = self.control.apply(headers, packet)
        
        return True, headers, actions


def demo_parser():
    """
    演示P4解析器
    """
    print("=== P4 Parser演示 ===\n")
    
    # 创建简单的解析器
    parser = P4Parser()
    
    def parse_ethernet(data: bytes, headers: dict):
        if len(data) < 14:
            return 'reject'
        
        eth = EthernetHeader()
        eth.fields['dst'] = struct.unpack('!Q', b'\x00' * 2 + data[0:6])[0]
        eth.fields['src'] = struct.unpack('!Q', b'\x00' * 2 + data[6:12])[0]
        eth.fields['etherType'] = struct.unpack('!H', data[12:14])[0]
        headers['ethernet'] = eth
        
        # 根据etherType选择下一个状态
        if eth.fields['etherType'] == 0x0800:
            return 'parse_ipv4'
        return 'accept'
    
    def parse_ipv4(data: bytes, headers: dict):
        if len(data) < 34:
            return 'reject'
        
        ip = IPv4Header()
        ip_hdr = data[14:34]
        ip.fields['version'] = (ip_hdr[0] >> 4) & 0xF
        ip.fields['ihl'] = ip_hdr[0] & 0xF
        ip.fields['totalLength'] = struct.unpack('!H', ip_hdr[2:4])[0]
        ip.fields['protocol'] = ip_hdr[9]
        ip.fields['srcAddr'] = struct.unpack('!I', ip_hdr[12:16])[0]
        ip.fields['dstAddr'] = struct.unpack('!I', ip_hdr[16:20])[0]
        headers['ipv4'] = ip
        
        return 'accept'
    
    parser.add_state('start', parse_ethernet)
    parser.add_state('parse_ipv4', parse_ipv4)
    
    # 测试
    print("解析以太网/IPv4包:")
    packet = struct.pack('!6s6sHH',
        b'\xff\xff\xff\xff\xff\xff',
        b'\x00\x11\x22\x33\x44\x55',
        0x0800,
        20  # IP长度
    ) + struct.pack('!BBHHHBBHII',
        0x45, 0, 20, 0, 0, 64, 6, 0,
        0x0a000001,  # 10.0.0.1
        0x0a000002   # 10.0.0.2
    )
    
    headers = parser.parse(packet)
    
    for name, header in headers.items():
        print(f"\n{name}头部:")
        if name == 'ethernet':
            print(f"  源MAC: {header.get_src()}")
            print(f"  目的MAC: {header.get_dst()}")
            print(f"  EtherType: 0x{header.fields['etherType']:04x}")
        elif name == 'ipv4':
            print(f"  源IP: {header.get_src()}")
            print(f"  目的IP: {header.get_dst()}")
            print(f"  协议: {header.fields['protocol']}")


def demo_match_action():
    """
    演示Match-Action表
    """
    print("\n=== Match-Action表演示 ===\n")
    
    # 创建路由表
    routing_table = MatchActionTable('ipv4_lpm')
    
    # 添加匹配字段
    routing_table.add_match_field('ipv4.dstAddr', P4Match.LPM)
    
    # 添加表项
    routing_table.add_entry(
        {'ipv4.dstAddr': 0x0a000000, 'prefix_len': 24},
        'forward',
        {'port': 1},
        priority=100
    )
    routing_table.add_entry(
        {'ipv4.dstAddr': 0x0b000000, 'prefix_len': 24},
        'forward',
        {'port': 2},
        priority=100
    )
    routing_table.add_entry(
        {'ipv4.dstAddr': 0x0a000000, 'prefix_len': 16},
        'forward',
        {'port': 0},
        priority=50
    )
    
    # 测试匹配
    ip_header = IPv4Header(src='10.0.0.1', dst='10.0.1.1')
    headers = {'ipv4': ip_header}
    
    print("查找 10.0.1.1 的路由:")
    result = routing_table.match(headers)
    if result:
        print(f"  匹配: {result.action}")
        print(f"  动作数据: {result.action_data}")
    
    print("\n查找 11.0.0.1 的路由:")
    ip_header.fields['dstAddr'] = 0x0b000001
    result = routing_table.match(headers)
    if result:
        print(f"  匹配: {result.action}")
        print(f"  动作数据: {result.action_data}")


def demo_simple_switch():
    """
    演示简单P4交换机
    """
    print("\n=== 简单P4交换机演示 ===\n")
    
    # 创建P4程序
    p4 = P4Program()
    
    # 创建控制块
    control = P4Control('ingress')
    
    # 创建L2转发表
    mac_table = MatchActionTable('forward')
    mac_table.add_match_field('ethernet.dstAddr', P4Match.EXACT)
    mac_table.add_entry({'ethernet.dstAddr': 0xffffffffffff}, 'flood', {})
    mac_table.add_entry({'ethernet.dstAddr': 0x001122334455}, 'forward', {'port': 1})
    mac_table.add_entry({'ethernet.dstAddr': 0x001122334466}, 'forward', {'port': 2})
    
    control.add_table(mac_table)
    p4.control = control
    
    # 测试
    print("L2转发测试:")
    
    test_macs = [
        0xffffffffffff,  # 广播
        0x001122334455,
        0x001122334466,
        0x001122334477,  # 未知
    ]
    
    for mac in test_macs:
        eth = EthernetHeader()
        eth.fields['dst'] = mac
        headers = {'ethernet': eth}
        
        result = mac_table.match(headers)
        if result:
            print(f"  MAC 0x{mac:012x} -> {result.action} port={result.action_data.get('port', 'all')}")


if __name__ == "__main__":
    print("=" * 60)
    print("P4数据平面编程基础")
    print("=" * 60)
    
    # 解析器
    demo_parser()
    
    # Match-Action
    demo_match_action()
    
    # 简单交换机
    demo_simple_switch()
    
    print("\n" + "=" * 60)
    print("P4关键概念:")
    print("=" * 60)
    print("""
1. P4架构组件:
   - Parser: 解析数据包头部
   - Match-Action Tables: 查表执行动作
   - Control: 控制流程逻辑
   - Deparser: 重新组装数据包

2. P4可编程性:
   - 定义新的协议头
   - 实现自定义转发逻辑
   - 无需硬件更改

3. Match类型:
   - Exact: 精确匹配
   - LPM: 最长前缀匹配
   - Ternary: 三元匹配（带掩码）
   - Valid: 头部有效性检查

4. 与OpenFlow对比:
   - OpenFlow: 固定-match + 厂商定义_action
   - P4: 自定义_match + 自定义_action
   - P4更灵活，但需要编译器支持
""")
