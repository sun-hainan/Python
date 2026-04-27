# -*- coding: utf-8 -*-
"""
算法实现：计算机网络算法 / p4_basics

本文件实现 p4_basics 相关的算法功能。
"""

import re


class PacketHeader:
    """数据包头部"""

    def __init__(self, header_type):
        """
        初始化头部
        
        参数:
            header_type: 头部类型（如 "ethernet", "ipv4"）
        """
        self.header_type = header_type
        # 字段字典
        self.fields = {}

    def set_field(self, name, value):
        """设置字段值"""
        self.fields[name] = value

    def get_field(self, name):
        """获取字段值"""
        return self.fields.get(name)

    def to_bytes(self):
        """序列化为字节"""
        result = b''
        for name, value in self.fields.items():
            if isinstance(value, bytes):
                result += value
            elif isinstance(value, int):
                # 简化的整数序列化
                size = self._get_field_size(name)
                result += value.to_bytes(size, 'big')
        return result

    def _get_field_size(self, field_name):
        """获取字段大小（字节）"""
        sizes = {
            'dst_addr': 6, 'src_addr': 6,  # MAC 地址
            'ether_type': 2,  # 以太网类型
            'version': 1, 'ihl': 1, 'tos': 1, 'total_len': 2,
            'identification': 2, 'flags': 1, 'frag_offset': 2,
            'ttl': 1, 'protocol': 1, 'checksum': 2,
            'src_addr': 4, 'dst_addr': 4,  # IPv4 地址
            'src_port': 2, 'dst_port': 2,  # 端口
        }
        return sizes.get(field_name, 4)

    @staticmethod
    def parse(header_type, data):
        """从字节解析头部"""
        header = PacketHeader(header_type)
        # 简化的解析
        if header_type == 'ethernet':
            header.set_field('dst_addr', data[0:6])
            header.set_field('src_addr', data[6:12])
            header.set_field('ether_type', int.from_bytes(data[12:14], 'big'))
        elif header_type == 'ipv4':
            header.set_field('version', (data[0] >> 4) & 0xF)
            header.set_field('ihl', data[0] & 0xF)
            header.set_field('total_len', int.from_bytes(data[2:4], 'big'))
            header.set_field('ttl', data[8])
            header.set_field('protocol', data[9])
            header.set_field('src_addr', data[12:16])
            header.set_field('dst_addr', data[16:20])
        return header


class MatchActionTable:
    """
    P4 匹配-动作表
    
    表由键（匹配字段）和动作组成
    """

    def __init__(self, table_name):
        """
        初始化表
        
        参数:
            table_name: 表名
        """
        self.table_name = table_name
        # 表项列表 [(match_fields, action, action_params), ...]
        self.entries = []
        # 默认动作
        self.default_action = None

    def add_entry(self, match_fields, action, action_params=None):
        """
        添加表项
        
        参数:
            match_fields: 匹配字段字典
            action: 动作名称
            action_params: 动作参数
        """
        if action_params is None:
            action_params = {}
        self.entries.append({
            'match': match_fields,
            'action': action,
            'params': action_params
        })

    def set_default_action(self, action, action_params=None):
        """设置默认动作"""
        if action_params is None:
            action_params = {}
        self.default_action = {'action': action, 'params': action_params}

    def lookup(self, key_fields):
        """
        查找表
        
        参数:
            key_fields: 键字段字典
        返回:
            (action, params): 匹配的动作和参数
        """
        for entry in self.entries:
            if self._match(entry['match'], key_fields):
                return entry['action'], entry['params']
        
        # 返回默认动作
        if self.default_action:
            return self.default_action['action'], self.default_action['params']
        
        return None, None

    def _match(self, pattern, key):
        """检查是否匹配"""
        for field, value in pattern.items():
            if field not in key or key[field] != value:
                return False
        return True


class P4Parser:
    """P4 解析器"""

    def __init__(self):
        """初始化解析器"""
        # 解析状态
        self.states = {}
        # 当前状态
        self.current_state = None
        # 解析出的头部
        self.parsed_headers = []

    def add_state(self, state_name, transition=None):
        """
        添加解析状态
        
        参数:
            state_name: 状态名
            transition: 转换函数 (header_type, size) -> next_state
        """
        self.states[state_name] = {
            'transitions': [],
            'default': transition
        }
        if self.current_state is None:
            self.current_state = state_name

    def add_transition(self, from_state, header_type, size, next_state):
        """
        添加转换规则
        
        参数:
            from_state: 起始状态
            header_type: 要解析的头部类型
            size: 头部大小
            next_state: 下一状态
        """
        if from_state in self.states:
            self.states[from_state]['transitions'].append({
                'header': header_type,
                'size': size,
                'next': next_state
            })

    def parse(self, packet_bytes):
        """
        解析数据包
        
        参数:
            packet_bytes: 原始数据包字节
        返回:
            headers: 解析出的头部列表
        """
        self.parsed_headers = []
        current = self.current_state
        offset = 0
        
        while current and current != 'accept' and current != 'reject':
            if current not in self.states:
                break
            
            state = self.states[current]
            matched = False
            
            # 尝试转换
            for trans in state['transitions']:
                header_type = trans['header']
                size = trans['size']
                
                if offset + size <= len(packet_bytes):
                    header_data = packet_bytes[offset:offset+size]
                    header = PacketHeader.parse(header_type, header_data)
                    self.parsed_headers.append(header)
                    offset += size
                    current = trans['next']
                    matched = True
                    break
            
            # 如果没有匹配，尝试默认转换
            if not matched and state['default']:
                header_type, size, next_state = state['default'](packet_bytes, offset)
                if header_type and offset + size <= len(packet_bytes):
                    header_data = packet_bytes[offset:offset+size]
                    header = PacketHeader.parse(header_type, header_data)
                    self.parsed_headers.append(header)
                    offset += size
                    current = next_state
                else:
                    current = 'reject'
            
            if not matched and not state['transitions'] and not state['default']:
                break
        
        return self.parsed_headers


class P4Action:
    """P4 动作"""

    @staticmethod
    def drop(meta):
        """丢弃动作"""
        meta['drop'] = True

    @staticmethod
    def send_to_port(port, meta):
        """发送到指定端口"""
        meta['egress_port'] = port

    @staticmethod
    def modify_field(header_name, field_name, value, meta):
        """修改字段"""
        if header_name in meta['headers']:
            meta['headers'][header_name].set_field(field_name, value)

    @staticmethod
    def add_to_field(header_name, field_name, value, meta):
        """字段值增加"""
        if header_name in meta['headers']:
            current = meta['headers'][header_name].get_field(field_name)
            if isinstance(current, int):
                meta['headers'][header_name].set_field(field_name, current + value)

    @staticmethod
    def copy_to_cpu(meta):
        """复制到 CPU"""
        meta['copied_to_cpu'] = True


class P4Control:
    """P4 控制程序"""

    def __init__(self, name):
        """
        初始化控制程序
        
        参数:
            name: 控制程序名称
        """
        self.name = name
        # 匹配-动作表
        self.tables = {}
        # 动作函数
        self.actions = {
            'drop': P4Action.drop,
            'send_to_port': P4Action.send_to_port,
            'modify_field': P4Action.modify_field,
            'add_to_field': P4Action.add_to_field,
            'copy_to_cpu': P4Action.copy_to_cpu,
        }

    def apply_table(self, table_name, headers, meta):
        """
        应用表
        
        参数:
            table_name: 表名
            headers: 头部列表
            meta: 元数据
        返回:
            action_result: 动作执行结果
        """
        if table_name not in self.tables:
            return None
        
        table = self.tables[table_name]
        
        # 构建查找键
        key_fields = {}
        for header in headers:
            for field, value in header.fields.items():
                key_fields[field] = value
        
        # 查找表
        action_name, action_params = table.lookup(key_fields)
        
        if action_name and action_name in self.actions:
            # 执行动作
            self.actions[action_name](**action_params, meta=meta)
            return action_name
        
        return None

    def add_table(self, table_name, table):
        """添加表"""
        self.tables[table_name] = table


class P4Pipeline:
    """P4 流水线"""

    def __init__(self):
        """初始化流水线"""
        # 解析器
        self.parser = P4Parser()
        # 控制程序列表
        self.controls = []
        # 元数据
        self.metadata = {}

    def add_control(self, control):
        """添加控制程序"""
        self.controls.append(control)

    def process_packet(self, packet_bytes):
        """
        处理数据包
        
        参数:
            packet_bytes: 原始数据包
        返回:
            result: 处理结果
        """
        # 1. 解析
        headers = self.parser.parse(packet_bytes)
        
        # 2. 构建元数据
        meta = {
            'headers': {h.header_type: h for h in headers},
            'ingress_port': 1,
            'drop': False,
            'egress_port': None,
            'copied_to_cpu': False
        }
        
        # 3. 应用控制程序
        for control in self.controls:
            for table_name in control.tables:
                result = control.apply_table(table_name, headers, meta)
                if meta.get('drop'):
                    break
        
        # 4. 返回结果
        return {
            'headers': headers,
            'meta': meta,
            'drop': meta.get('drop', False),
            'egress_port': meta.get('egress_port'),
        }


if __name__ == "__main__":
    # 测试 P4 基础功能
    print("=== P4 基础测试 ===\n")

    # 创建数据包
    print("--- 创建数据包 ---")
    eth_header = PacketHeader('ethernet')
    eth_header.set_field('dst_addr', b'\x00\x11\x22\x33\x44\x55')
    eth_header.set_field('src_addr', b'\x66\x77\x88\x99\xaa\xbb')
    eth_header.set_field('ether_type', 0x0800)  # IPv4
    print(f"以太网头部: dst={eth_header.get_field('dst_addr').hex()}, "
          f"src={eth_header.get_field('src_addr').hex()}, "
          f"type=0x{eth_header.get_field('ether_type'):04x}")

    # 创建 IPv4 头部
    ipv4_header = PacketHeader('ipv4')
    ipv4_header.set_field('version', 4)
    ipv4_header.set_field('ihl', 5)
    ipv4_header.set_field('total_len', 40)
    ipv4_header.set_field('ttl', 64)
    ipv4_header.set_field('protocol', 6)  # TCP
    ipv4_header.set_field('src_addr', b'\x0a\x00\x00\x01')  # 10.0.0.1
    ipv4_header.set_field('dst_addr', b'\x0a\x00\x00\x02')  # 10.0.0.2
    print(f"IPv4 头部: src={ipv4_header.get_field('src_addr')}, "
          f"dst={ipv4_header.get_field('dst_addr')}")

    # 匹配-动作表
    print("\n--- 匹配-动作表 ---")
    ipv4_lpm = MatchActionTable("ipv4_lpm")
    ipv4_lpm.add_entry(
        {'dst_addr': b'\x0a\x00\x00\x02'},
        'send_to_port',
        {'port': 2}
    )
    ipv4_lpm.add_entry(
        {'dst_addr': b'\x0a\x00\x00\x03'},
        'send_to_port',
        {'port': 3}
    )
    ipv4_lpm.set_default_action('send_to_port', {'port': 1})
    
    # 查找
    print("查找 10.0.0.2 -> ", end="")
    action, params = ipv4_lpm.lookup({'dst_addr': b'\x0a\x00\x00\x02'})
    print(f"{action}, port={params['port']}")
    
    print("查找 10.0.0.99 -> ", end="")
    action, params = ipv4_lpm.lookup({'dst_addr': b'\x0a\x00\x00\x63'})
    print(f"{action}, port={params['port']}")

    # P4 控制程序
    print("\n--- P4 控制程序 ---")
    ingress = P4Control("ingress")
    
    # 添加表到控制程序
    ingress.add_table("ipv4_lpm", ipv4_lpm)
    
    # 模拟处理
    meta = {
        'headers': {'ethernet': eth_header, 'ipv4': ipv4_header},
        'ingress_port': 1,
        'drop': False,
        'egress_port': None
    }
    
    action = ingress.apply_table("ipv4_lpm", [eth_header, ipv4_header], meta)
    print(f"应用 ipv4_lpm 表: {action}")
    print(f" egress_port: {meta['egress_port']}")

    # P4 流水线
    print("\n--- P4 流水线 ---")
    pipeline = P4Pipeline()
    pipeline.add_control(ingress)
    
    # 模拟数据包处理
    # 构建模拟的以太网+IPv4 数据包
    test_packet = (
        b'\x00\x11\x22\x33\x44\x55'  # dst_mac
        b'\x66\x77\x88\x99\xaa\xbb'  # src_mac
        b'\x08\x00'                   # ether_type
        b'\x45'                       # version + ihl
        b'\x00\x00\x00\x28'           # total_len, id, flags+frag
        b'\x40\x06\x00\x00'           # ttl, protocol
        b'\x0a\x00\x00\x01'           # src_ip
        b'\x0a\x00\x00\x02'           # dst_ip
    )
    
    result = pipeline.process_packet(test_packet)
    print(f"处理结果:")
    print(f"  解析出的头部: {[h.header_type for h in result['headers']]}")
    print(f"  丢弃: {result['drop']}")
    print(f"  输出端口: {result['egress_port']}")
