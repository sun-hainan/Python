# -*- coding: utf-8 -*-

"""

算法实现：25_�������� / sdn_flowtable



本文件实现 sdn_flowtable 相关的算法功能。

"""



import re

from dataclasses import dataclass, field

from typing import List, Dict, Optional, Tuple

from enum import IntEnum

import time





class OFMatchField(IntEnum):

    """OpenFlow匹配字段"""

    IN_PORT = 0

    ETH_SRC = 1

    ETH_DST = 2

    ETH_TYPE = 3

    VLAN_VID = 4

    IP_SRC = 10

    IP_DST = 11

    IP_PROTO = 12

    TCP_SRC = 13

    TCP_DST = 14

    UDP_SRC = 15

    UDP_DST = 16





@dataclass

class Packet:

    """网络数据包"""

    in_port: int = 0

    eth_src: str = "00:00:00:00:00:00"

    eth_dst: str = "00:00:00:00:00:00"

    eth_type: int = 0x0800  # IPv4

    vlan_vid: int = 0

    ip_src: str = "0.0.0.0"

    ip_dst: str = "0.0.0.0"

    ip_proto: int = 6  # TCP

    tcp_src: int = 0

    tcp_dst: int = 0

    udp_src: int = 0

    udp_dst: int = 0

    

    def get_field(self, field: OFMatchField):

        """获取字段值"""

        return {

            OFMatchField.IN_PORT: self.in_port,

            OFMatchField.ETH_SRC: self.eth_src,

            OFMatchField.ETH_DST: self.eth_dst,

            OFMatchField.ETH_TYPE: self.eth_type,

            OFMatchField.VLAN_VID: self.vlan_vid,

            OFMatchField.IP_SRC: self.ip_src,

            OFMatchField.IP_DST: self.ip_dst,

            OFMatchField.IP_PROTO: self.ip_proto,

            OFMatchField.TCP_SRC: self.tcp_src,

            OFMatchField.TCP_DST: self.tcp_dst,

            OFMatchField.UDP_SRC: self.udp_src,

            OFMatchField.UDP_DST: self.udp_dst,

        }.get(field)

    

    @classmethod

    def from_bytes(cls, data: bytes) -> 'Packet':

        """从字节解析数据包（简化）"""

        pkt = cls()

        if len(data) >= 14:

            pkt.eth_dst = ':'.join(f'{b:02x}' for b in data[0:6])

            pkt.eth_src = ':'.join(f'{b:02x}' for b in data[6:12])

            pkt.eth_type = int.from_bytes(data[12:14], 'big')

        return pkt

    

    def __repr__(self):

        return f"Packet({self.ip_src}->{self.ip_dst}, proto={self.ip_proto})"





@dataclass 

class FlowEntry:

    """OpenFlow流表项"""

    priority: int  # 优先级（越高越先匹配）

    match: Dict[OFMatchField, any]  # 匹配字段

    idle_timeout: int = 0  # 空闲超时（秒）

    hard_timeout: int = 0  # 硬超时（秒）

    cookie: int = 0  # 控制器设置的标识

    packet_count: int = 0  # 匹配包数

    byte_count: int = 0  # 匹配字节数

    last_used: float = field(default_factory=time.time)

    instructions: List[str] = field(default_factory=list)  # 指令列表

    

    def matches(self, packet: Packet) -> bool:

        """

        检查数据包是否匹配此流表项

        

        Args:

            packet: 待匹配的数据包

        

        Returns:

            是否匹配

        """

        for field, value in self.match.items():

            if value is None:  # 通配符字段

                continue

            

            pkt_value = packet.get_field(field)

            if pkt_value != value:

                return False

        

        return True

    

    def update_stats(self, packet_size: int):

        """更新流表项统计"""

        self.packet_count += 1

        self.byte_count += packet_size

        self.last_used = time.time()

    

    def is_expired(self) -> bool:

        """检查是否超时过期"""

        now = time.time()

        if self.idle_timeout > 0 and (now - self.last_used) > self.idle_timeout:

            return True

        if self.hard_timeout > 0 and (now - self.last_used) > self.hard_timeout:

            return True

        return False





class FlowTable:

    """

    OpenFlow流表

    

    支持：

    1. 流表查找（最长匹配）

    2. 流表项添加/删除

    3. 计数器更新

    4. 超时淘汰

    """

    

    def __init__(self, table_id: int = 0):

        self.table_id = table_id

        self.entries: List[FlowEntry] = []

        self.max_entries: int = 10000  # 最大流表项数

    

    def add_entry(self, entry: FlowEntry):

        """

        添加流表项（按优先级排序）

        

        Args:

            entry: 流表项

        """

        # 插入到正确位置（按优先级降序）

        bisect_idx = 0

        for i, e in enumerate(self.entries):

            if entry.priority > e.priority:

                bisect_idx = i

                break

            bisect_idx = i + 1

        

        self.entries.insert(bisect_idx, entry)

    

    def remove_entry(self, entry: FlowEntry):

        """移除流表项"""

        if entry in self.entries:

            self.entries.remove(entry)

    

    def match(self, packet: Packet) -> Optional[FlowEntry]:

        """

        流表匹配（按优先级顺序查找）

        

        Args:

            packet: 待匹配的数据包

        

        Returns:

            匹配的流表项（优先级最高的）

        """

        for entry in self.entries:

            if entry.matches(packet):

                entry.update_stats(len(str(packet)))  # 简化

                return entry

        return None

    

    def match_all(self, packet: Packet) -> List[FlowEntry]:

        """

        返回所有匹配的流表项

        

        Args:

            packet: 待匹配的数据包

        

        Returns:

            匹配的流表项列表

        """

        return [e for e in self.entries if e.matches(packet)]

    

    def cleanup_expired(self) -> int:

        """

        清理过期流表项

        

        Returns:

            清理的流表项数量

        """

        expired = [e for e in self.entries if e.is_expired()]

        for e in expired:

            self.entries.remove(e)

        return len(expired)

    

    def dump_stats(self) -> Dict:

        """导出流表统计"""

        return {

            'table_id': self.table_id,

            'num_entries': len(self.entries),

            'total_packets': sum(e.packet_count for e in self.entries),

            'total_bytes': sum(e.byte_count for e in self.entries),

        }





class OpenFlowSwitch:

    """

    OpenFlow交换机

    

    包含多个流表（流水线处理）

    """

    

    def __init__(self, dpid: str):

        self.dpid = dpid  # 交换机ID

        self.tables: List[FlowTable] = [FlowTable(0)]  # 至少一个表

        self.ports: Dict[int, str] = {}  # 端口映射

        self.flowmods_pending = []  # 待处理的流表修改

    

    def add_flow_table(self) -> int:

        """添加新流表"""

        table_id = len(self.tables)

        self.tables.append(FlowTable(table_id))

        return table_id

    

    def install_flow(self, match: Dict, priority: int = 100, 

                    instructions: List[str] = None,

                    table_id: int = 0, **kwargs):

        """

        安装流表项

        

        Args:

            match: 匹配字段

            priority: 优先级

            instructions: 指令列表

            table_id: 流表ID

        """

        entry = FlowEntry(

            priority=priority,

            match=match,

            instructions=instructions or ['output:CONTROLLER'],

            **kwargs

        )

        

        self.tables[table_id].add_entry(entry)

    

    def process_packet(self, packet: Packet) -> Tuple[str, List[int]]:

        """

        处理数据包（流水线查找）

        

        Args:

            packet: 数据包

        

        Returns:

            (action, output_ports)

        """

        for table in self.tables:

            entry = table.match(packet)

            if entry:

                # 执行指令

                return self._execute_instructions(entry.instructions, packet)

        

        # 无匹配，上报控制器

        return ('CONTROLLER', [])

    

    def _execute_instructions(self, instructions: List[str], packet: Packet) -> Tuple[str, List[int]]:

        """

        执行指令

        

        Args:

            instructions: 指令列表

            packet: 数据包

        

        Returns:

            (action, output_ports)

        """

        output_ports = []

        action = 'FORWARD'

        

        for inst in instructions:

            if inst.startswith('OUTPUT:'):

                port = inst.split(':')[1]

                if port == 'CONTROLLER':

                    action = 'CONTROLLER'

                elif port == 'FLOOD':

                    output_ports = list(self.ports.keys())

                elif port == 'ALL':

                    output_ports = list(self.ports.keys())

                else:

                    output_ports.append(int(port))

            elif inst == 'DROP':

                action = 'DROP'

            elif inst == 'MODIFY_ETH_SRC':

                packet.eth_src = "00:00:00:00:01:00"

            elif inst == 'MODIFY_ETH_DST':

                packet.eth_dst = "00:00:00:00:01:00"

        

        return action, output_ports





def parse_match_str(match_str: str) -> Dict[OFMatchField, any]:

    """

    解析匹配字段字符串

    

    Args:

        match_str: 如 "ip_src=10.0.0.1,tcp_dst=80"

    

    Returns:

        匹配字段字典

    """

    match = {}

    

    if not match_str:

        return match

    

    for pair in match_str.split(','):

        key, value = pair.split('=')

        key = key.strip()

        value = value.strip()

        

        if key == 'in_port':

            match[OFMatchField.IN_PORT] = int(value)

        elif key == 'eth_src':

            match[OFMatchField.ETH_SRC] = value

        elif key == 'eth_dst':

            match[OFMatchField.ETH_DST] = value

        elif key == 'eth_type':

            match[OFMatchField.ETH_TYPE] = int(value, 16) if value.startswith('0x') else int(value)

        elif key == 'ip_src':

            match[OFMatchField.IP_SRC] = value

        elif key == 'ip_dst':

            match[OFMatchField.IP_DST] = value

        elif key == 'ip_proto':

            match[OFMatchField.IP_PROTO] = int(value)

        elif key == 'tcp_src':

            match[OFMatchField.TCP_SRC] = int(value)

        elif key == 'tcp_dst':

            match[OFMatchField.TCP_DST] = int(value)

        elif key == 'udp_src':

            match[OFMatchField.UDP_SRC] = int(value)

        elif key == 'udp_dst':

            match[OFMatchField.UDP_DST] = int(value)

    

    return match





def demo_flow_table():

    """

    演示流表匹配

    """

    print("=== OpenFlow流表匹配演示 ===\n")

    

    # 创建交换机

    switch = OpenFlowSwitch("00:00:00:00:00:01")

    

    # 安装流表项

    print("1. 安装流表规则:")

    

    # 规则1：所有HTTP流量 -> 端口2

    switch.install_flow(

        match={OFMatchField.IP_PROTO: 6, OFMatchField.TCP_DST: 80},

        priority=100,

        instructions=['OUTPUT:2']

    )

    print("   规则1: TCP:80 -> OUTPUT:2")

    

    # 规则2：特定源IP -> 端口3

    switch.install_flow(

        match={OFMatchField.IP_SRC: "10.0.0.100", OFMatchField.IP_PROTO: 6},

        priority=200,  # 更高优先级

        instructions=['OUTPUT:3']

    )

    print("   规则2: 10.0.0.100 -> OUTPUT:3 (高优先级)")

    

    # 规则3：所有TCP -> 控制器

    switch.install_flow(

        match={OFMatchField.IP_PROTO: 6},

        priority=50,

        instructions=['OUTPUT:CONTROLLER']

    )

    print("   规则3: TCP* -> CONTROLLER")

    

    # 创建测试数据包

    print("\n2. 测试数据包匹配:")

    

    packets = [

        Packet(ip_src="10.0.0.100", ip_dst="192.168.1.10", ip_proto=6, tcp_dst=80),

        Packet(ip_src="10.0.0.200", ip_dst="192.168.1.10", ip_proto=6, tcp_dst=80),

        Packet(ip_src="10.0.0.100", ip_dst="192.168.1.10", ip_proto=6, tcp_dst=443),

    ]

    

    for pkt in packets:

        action, ports = switch.process_packet(pkt)

        print(f"   {pkt} -> action={action}, ports={ports}")





def demo_table_pipeline():

    """

    演示多级流表流水线

    """

    print("\n=== 多级流表流水线演示 ===\n")

    

    switch = OpenFlowSwitch("00:00:00:00:00:02")

    switch.add_flow_table()  # 表1

    switch.add_flow_table()  # 表2

    

    # 表0：按协议分类

    switch.install_flow(

        match={OFMatchField.IP_PROTO: 6},  # TCP

        priority=100,

        instructions=['GOTO_TABLE:1'],

        table_id=0

    )

    switch.install_flow(

        match={OFMatchField.IP_PROTO: 17},  # UDP

        priority=100,

        instructions=['GOTO_TABLE:2'],

        table_id=0

    )

    

    # 表1：TCP分类

    switch.install_flow(

        match={OFMatchField.TCP_DST: 80},  # HTTP

        priority=100,

        instructions=['OUTPUT:2'],

        table_id=1

    )

    switch.install_flow(

        match={OFMatchField.TCP_DST: 443},  # HTTPS

        priority=100,

        instructions=['OUTPUT:3'],

        table_id=1

    )

    

    # 表2：UDP分类

    switch.install_flow(

        match={OFMatchField.UDP_DST: 53},  # DNS

        priority=100,

        instructions=['OUTPUT:4'],

        table_id=2

    )

    

    print("流表配置:")

    print("  表0: 按IP协议分类")

    print("  表1: TCP端口分类")

    print("  表2: UDP端口分类")

    

    print("\n数据包处理:")

    test_packets = [

        Packet(ip_proto=6, tcp_dst=80),

        Packet(ip_proto=6, tcp_dst=443),

        Packet(ip_proto=17, udp_dst=53),

    ]

    

    for pkt in test_packets:

        action, ports = switch.process_packet(pkt)

        print(f"  {pkt.ip_proto=}:{pkt.tcp_dst if pkt.ip_proto==6 else pkt.udp_dst} -> {action}:{ports}")





def demo_timeout():

    """

    演示流表项超时

    """

    print("\n=== 流表项超时演示 ===\n")

    

    table = FlowTable()

    

    # 添加一些流表项

    entry1 = FlowEntry(

        priority=100,

        match={OFMatchField.TCP_DST: 80},

        instructions=['OUTPUT:2'],

        idle_timeout=5  # 5秒空闲超时

    )

    entry2 = FlowEntry(

        priority=100,

        match={OFMatchField.TCP_DST: 443},

        instructions=['OUTPUT:3'],

        hard_timeout=10  # 10秒硬超时

    )

    

    table.add_entry(entry1)

    table.add_entry(entry2)

    

    print(f"初始流表项数: {len(table.entries)}")

    

    # 模拟时间流逝

    entry1.last_used = time.time() - 6  # 6秒前使用

    entry2.last_used = time.time() - 11  # 11秒前使用

    

    print("\n设置超时:")

    print("  entry1: idle_timeout=5s, 最后使用6秒前")

    print("  entry2: hard_timeout=10s, 最后使用11秒前")

    

    expired_count = table.cleanup_expired()

    print(f"\n清理过期项: {expired_count}")

    print(f"剩余流表项数: {len(table.entries)}")





def demo_stats():

    """

    演示流表统计

    """

    print("\n=== 流表统计演示 ===\n")

    

    switch = OpenFlowSwitch("00:00:00:00:00:03")

    

    # 安装规则

    switch.install_flow(

        match={OFMatchField.IP_DST: "192.168.1.0/24"},

        priority=100,

        instructions=['OUTPUT:1']

    )

    

    # 模拟流量

    for i in range(100):

        pkt = Packet(ip_src=f"10.0.0.{i%255}", ip_dst="192.168.1.10")

        switch.process_packet(pkt)

    

    # 打印统计

    stats = switch.tables[0].dump_stats()

    print("流表统计:")

    for k, v in stats.items():

        print(f"  {k}: {v}")





if __name__ == "__main__":

    print("=" * 60)

    print("SDN OpenFlow 流表匹配算法实现")

    print("=" * 60)

    

    # 流表匹配演示

    demo_flow_table()

    

    # 多级流表演示

    demo_table_pipeline()

    

    # 超时演示

    demo_timeout()

    

    # 统计演示

    demo_stats()

    

    print("\n" + "=" * 60)

    print("OpenFlow关键概念:")

    print("=" * 60)

    print("""

1. 流表匹配：

   - 按优先级顺序查找

   - 支持通配符（省略字段=匹配任意）

   - 支持精确匹配和掩码匹配



2. 指令类型：

   - OUTPUT: 转发到端口

   - DROP: 丢弃

   - MODIFY_*: 修改字段

   - GOTO_TABLE: 转到下一表



3. 超时机制：

   - idle_timeout: 空闲超时

   - hard_timeout: 硬超时（绝对时间）



4. 多表流水线：

   - 支持99个表

   - 表之间可以跳转

   - 实现复杂逻辑

""")

