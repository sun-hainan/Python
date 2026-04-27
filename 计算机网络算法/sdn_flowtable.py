# -*- coding: utf-8 -*-

"""

算法实现：计算机网络算法 / sdn_flowtable



本文件实现 sdn_flowtable 相关的算法功能。

"""



import time

from collections import defaultdict





class FlowEntry:

    """

    OpenFlow 流表项（简化版 OF 1.0/1.3 字段）

    匹配字段 -> 动作

    """



    def __init__(self, match_fields, priority=0, idle_timeout=60, hard_timeout=0):

        """

        match_fields: 匹配字段字典

        priority: 优先级（数字越大优先级越高，默认0=低优先级）

        idle_timeout: 空闲超时（秒），超时无匹配则删除

        hard_timeout: 硬超时（秒），无论是否匹配都超时删除

        """

        self.match = match_fields

        self.priority = priority

        self.idle_timeout = idle_timeout

        self.hard_timeout = hard_timeout

        self.cookie = 0  # 控制器设置的标识符

        # 计数器

        self.packet_count = 0

        self.byte_count = 0

        # 表项状态

        self.created_at = time.time()

        self.last_match = time.time()

        self.active = True

        # 动作列表

        self.actions = []



    def add_action(self, action_type, action_data):

        """添加动作"""

        self.actions.append((action_type, action_data))



    def is_expired(self, current_time=None):

        """检查是否超时"""

        if current_time is None:

            current_time = time.time()

        if self.hard_timeout > 0:

            if current_time - self.created_at >= self.hard_timeout:

                return True

        if self.idle_timeout > 0:

            if current_time - self.last_match >= self.idle_timeout:

                return True

        return False



    def match_packet(self, packet):

        """

        判断数据包是否匹配此表项

        packet: 数据包字段字典

        """

        for key, value in self.match.items():

            if key not in packet:

                return False

            if isinstance(value, dict):

                # 掩码匹配（如 IP 地址范围）

                if 'mask' in value:

                    masked = packet[key] & value['mask']

                    if masked != value['value']:

                        return False

            elif packet[key] != value:

                return False

        return True



    def __repr__(self):

        return (f"FlowEntry(match={self.match}, priority={self.priority}, "

                f"packets={self.packet_count}, active={self.active})")





class FlowTable:

    """

    OpenFlow 流表（支持多表流水线）

    结构：Table 0 -> Table 1 -> ... -> Table N -> Drop/Forward

    """



    def __init__(self, table_id=0, max_entries=1024):

        self.table_id = table_id

        self.max_entries = max_entries

        # 流表项列表（按优先级降序排列）

        self.entries = []

        # 表级计数器

        self.stats = {

            'lookup_count': 0,

            'matched_count': 0,

        }



    def add_entry(self, entry):

        """添加流表项"""

        # 按优先级插入（保持降序）

        inserted = False

        for i, e in enumerate(self.entries):

            if entry.priority > e.priority:

                self.entries.insert(i, entry)

                inserted = True

                break

        if not inserted:

            self.entries.append(entry)



    def remove_entry(self, entry):

        """删除流表项"""

        if entry in self.entries:

            self.entries.remove(entry)



    def lookup(self, packet):

        """

        流表查找：按优先级遍历表项，返回第一个匹配的表项

        如果无匹配，返回 None（触发 Packet-In 到控制器）

        """

        self.stats['lookup_count'] += 1

        current_time = time.time()



        for entry in self.entries:

            if not entry.active:

                continue

            if entry.match_packet(packet):

                # 更新计数器

                entry.packet_count += 1

                entry.byte_count += packet.get('size', 64)

                entry.last_match = current_time

                self.stats['matched_count'] += 1

                return entry



        # 超时清理

        self._cleanup_expired(current_time)

        return None



    def _cleanup_expired(self, current_time=None):

        """删除已超时的流表项"""

        if current_time is None:

            current_time = time.time()

        expired = [e for e in self.entries if e.is_expired(current_time)]

        for e in expired:

            e.active = False

        self.entries = [e for e in self.entries if e.active]



    def get_stats(self):

        """返回表级统计"""

        return self.stats





class OpenFlowSwitch:

    """

    OpenFlow 交换机模拟器

    """



    # 常见动作类型

    ACTION_OUTPUT = 'output'        # 输出到端口

    ACTION_CONTROLLER = 'controller'  # 发送到控制器

    ACTION_DROP = 'drop'            # 丢弃

    ACTION_MODIFY_FIELD = 'modify'  # 修改字段



    def __init__(self, dpid, name='OF-Switch'):

        self.dpid = dpid

        self.name = name

        # 流表（支持多表流水线）

        self.tables = [FlowTable(table_id=0)]

        # 端口状态

        self.ports = {}

        # MAC 地址表（学习型交换机行为）

        self.mac_table = {}

        # 连接到的控制器

        self.controller = None



    def add_flow(self, match_fields, actions, priority=100, idle_timeout=60):

        """添加流表项（快捷方法）"""

        entry = FlowEntry(match_fields, priority=priority,

                          idle_timeout=idle_timeout)

        for action_type, action_data in actions:

            entry.add_action(action_type, action_data)

        self.tables[0].add_entry(entry)

        return entry



    def process_packet(self, packet):

        """

        处理输入数据包

        packet: dict，包含 in_port, src_mac, dst_mac, src_ip, dst_ip, ...

        返回动作（action, output）

        """

        # 步骤1：流表查找

        matched_entry = self.tables[0].lookup(packet)



        if matched_entry:

            # 执行动作

            return self._execute_actions(matched_entry.actions, packet)

        else:

            # 无匹配：发送到控制器（Packet-In）

            return ('packet_in', packet)



    def _execute_actions(self, actions, packet):

        """执行动作列表"""

        for action_type, action_data in actions:

            if action_type == self.ACTION_OUTPUT:

                port = action_data

                return ('forward', port)

            elif action_type == self.ACTION_CONTROLLER:

                return ('packet_in', packet)

            elif action_type == self.ACTION_DROP:

                return ('drop', None)

            elif action_type == self.ACTION_MODIFY_FIELD:

                field, value = action_data

                packet[field] = value

        return ('drop', None)



    def install_reactive_flow(self, match, actions):

        """控制器通过 Packet-In 安装反应式流表项"""

        self.add_flow(match, actions)



    def learn_mac(self, mac, port):

        """MAC 地址学习"""

        self.mac_table[mac] = port



    def flood(self, packet):

        """洪泛：向所有端口（除入端口）发送"""

        return ('flood', None)





class RyuController:

    """

    简化的 SDN 控制器（类似 Ryu/OpenDaylight）

    负责下发流表、处理 Packet-In、维护网络拓扑视图

    """



    def __init__(self):

        self.switches = {}  # dpid -> switch

        self.topology = defaultdict(list)  # 链路信息

        self.flow_count = 0



    def add_switch(self, switch):

        """注册交换机"""

        self.switches[switch.dpid] = switch

        switch.controller = self



    def install_flow_rule(self, switch_dpid, match, actions,

                         priority=100, idle_timeout=60):

        """安装流表规则"""

        if switch_dpid in self.switches:

            switch = self.switches[switch_dpid]

            switch.add_flow(match, actions, priority, idle_timeout)

            self.flow_count += 1



    def handle_packet_in(self, switch, packet):

        """

        处理 Packet-In 事件（核心逻辑）

        """

        in_port = packet.get('in_port')

        src_mac = packet.get('src_mac', '')

        dst_mac = packet.get('dst_mac', '')



        # MAC 学习

        switch.learn_mac(src_mac, in_port)



        if dst_mac in switch.mac_table:

            # 已知目的地：安装流表并单播转发

            out_port = switch.mac_table[dst_mac]

            match = {

                'src_mac': src_mac,

                'dst_mac': dst_mac,

            }

            actions = [(OpenFlowSwitch.ACTION_OUTPUT, out_port)]

            switch.add_flow(match, actions)

            return ('forward', out_port)

        else:

            # 未知目的地：洪泛

            return ('flood', None)





if __name__ == '__main__':

    print("SDN OpenFlow 流表模拟")

    print("=" * 60)



    # 创建交换机

    sw1 = OpenFlowSwitch(dpid=1, name='leaf-01')

    sw2 = OpenFlowSwitch(dpid=2, name='leaf-02')

    controller = RyuController()

    controller.add_switch(sw1)

    controller.add_switch(sw2)



    # 安装默认流表规则

    sw1.add_flow(

        match_fields={'eth_type': 0x0800},  # IPv4

        actions=[

            (OpenFlowSwitch.ACTION_OUTPUT, 1)  # 输出到端口 1

        ],

        priority=100,

        idle_timeout=30

    )



    print("流表安装完成：")

    for entry in sw1.tables[0].entries:

        print(f"  {entry}")



    # 模拟数据包处理

    print("\n数据包处理模拟：")

    print(f"{'#':<4} {'src_mac':<18} {'dst_mac':<18} {'结果':<25}")

    print("-" * 65)



    test_packets = [

        {'in_port': 1, 'src_mac': 'aa:bb:cc:dd:ee:01', 'dst_mac': 'aa:bb:cc:dd:ee:02',

         'eth_type': 0x0800, 'size': 128},

        {'in_port': 1, 'src_mac': 'aa:bb:cc:dd:ee:01', 'dst_mac': 'aa:bb:cc:dd:ee:02',

         'eth_type': 0x0800, 'size': 128},  # 同流第二个包，命中流表

    ]



    for i, pkt in enumerate(test_packets, 1):

        result, port = sw1.process_packet(pkt)

        print(f"{i:<4} {pkt['src_mac']:<18} {pkt['dst_mac']:<18} "

              f"{result} -> port {port}")



    print("\nSDN 架构优势：")

    print("  1. 控制平面与数据平面分离：灵活编程")

    print("  2. 集中式控制器：全局网络视图，精细流量控制")

    print("  3. OpenFlow 流表：标准化南向接口")

    print("  4. 适用场景：数据中心网络、园区网、网络虚拟化（NFV）")

