# -*- coding: utf-8 -*-

"""

算法实现：25_�������� / mac_learning



本文件实现 mac_learning 相关的算法功能。

"""



import time

from dataclasses import dataclass

from typing import Dict, List, Optional, Tuple

from collections import defaultdict





@dataclass

class MACEntry:

    """MAC地址表条目"""

    mac: str

    port: int

    vlan_id: int = 1

    timestamp: float = None

    static: bool = False  # 静态条目（不会被老化）

    

    def __post_init__(self):

        if self.timestamp is None:

            self.timestamp = time.time()

    

    def age(self) -> float:

        """获取条目年龄（秒）"""

        return time.time() - self.timestamp

    

    def is_expired(self, aging_time: float) -> bool:

        """检查是否过期"""

        if self.static:

            return False

        return self.age() > aging_time





class CAMTable:

    """

    CAM表（内容可寻址存储器）

    

    支持：

    - MAC学习

    - 查找

    - 老化

    - VLAN隔离

    - 静态条目

    """

    

    def __init__(self, aging_time: float = 300.0):

        """

        初始化CAM表

        

        Args:

            aging_time: 老化时间（秒），默认5分钟

        """

        self.aging_time = aging_time

        self.entries: Dict[str, MACEntry] = {}  # mac -> entry

        self.port_entries: Dict[int, List[str]] = defaultdict(list)  # port -> [macs]

        self.vlan_entries: Dict[int, Dict[str, MACEntry]] = defaultdict(dict)

        

        # 统计

        self.learn_count = 0

        self.lookup_count = 0

        self.miss_count = 0

        self.flood_count = 0

    

    def learn(self, mac: str, port: int, vlan_id: int = 1, static: bool = False):

        """

        学习MAC地址

        

        Args:

            mac: MAC地址

            port: 入端口

            vlan_id: VLAN ID

            static: 是否为静态条目

        """

        entry = MACEntry(mac=mac, port=port, vlan_id=vlan_id, 

                        timestamp=time.time(), static=static)

        

        old_entry = self.entries.get(mac)

        

        # 更新表项

        self.entries[mac] = entry

        self.vlan_entries[vlan_id][mac] = entry

        

        # 更新端口索引

        if old_entry and old_entry.port != port:

            self.port_entries[old_entry.port].remove(mac)

        

        if port not in self.port_entries[port] or old_entry is None:

            self.port_entries[port].append(mac)

        

        self.learn_count += 1

    

    def lookup(self, mac: str, vlan_id: int = 1) -> Optional[int]:

        """

        查找MAC地址

        

        Args:

            mac: 目标MAC

            vlan_id: VLAN ID

        

        Returns:

            出端口或None（需要泛洪）

        """

        self.lookup_count += 1

        

        entry = self.vlan_entries[vlan_id].get(mac)

        

        if entry:

            # 更新学习时间（动态条目）

            if not entry.static:

                entry.timestamp = time.time()

            return entry.port

        

        self.miss_count += 1

        return None

    

    def flood_ports(self, ingress_port: int, vlan_id: int = 1) -> List[int]:

        """

        获取泛洪端口列表

        

        Args:

            ingress_port: 入端口（排除）

            vlan_id: VLAN ID

        

        Returns:

            需要泛洪的端口列表

        """

        self.flood_count += 1

        

        # 泛洪到同一VLAN的所有端口（除了入端口）

        flood = [p for p in self.port_entries.keys() if p != ingress_port]

        

        return flood

    

    def age_out(self) -> int:

        """

        老化过期条目

        

        Returns:

            删除的条目数

        """

        expired = []

        

        for mac, entry in list(self.entries.items()):

            if entry.is_expired(self.aging_time):

                expired.append(mac)

        

        for mac in expired:

            entry = self.entries[mac]

            

            # 从各索引中移除

            if mac in self.port_entries[entry.port]:

                self.port_entries[entry.port].remove(mac)

            

            del self.vlan_entries[entry.vlan_id][mac]

            del self.entries[mac]

        

        return len(expired)

    

    def get_port_macs(self, port: int) -> List[str]:

        """获取端口上的所有MAC"""

        return self.port_entries.get(port, []).copy()

    

    def clear(self):

        """清空CAM表（保留静态条目）"""

        for mac, entry in list(self.entries.items()):

            if not entry.static:

                if mac in self.port_entries[entry.port]:

                    self.port_entries[entry.port].remove(mac)

                del self.vlan_entries[entry.vlan_id][mac]

                del self.entries[mac]

    

    def dump(self) -> Dict:

        """导出CAM表"""

        return {

            'total_entries': len(self.entries),

            'entries': [(e.mac, e.port, e.vlan_id, e.age(), e.static) 

                       for e in self.entries.values()],

            'stats': {

                'learn_count': self.learn_count,

                'lookup_count': self.lookup_count,

                'miss_count': self.miss_count,

                'flood_count': self.flood_count,

            }

        }





class EthernetSwitch:

    """

    以太网交换机

    """

    

    def __init__(self, num_ports: int, aging_time: float = 300.0):

        self.num_ports = num_ports

        self.cam_table = CAMTable(aging_time)

        self.vlan_enabled = False

        self.vlans: Dict[int, List[int]] = {1: list(range(1, num_ports + 1))}  # 默认VLAN 1

    

    def receive_frame(self, port: int, src_mac: str, dst_mac: str, 

                     vlan_id: int = 1) -> Tuple[bool, List[int]]:

        """

        接收帧并处理

        

        Args:

            port: 接收端口

            src_mac: 源MAC

            dst_mac: 目标MAC

            vlan_id: VLAN ID

        

        Returns:

            (forwarded, output_ports)

            - forwarded: 是否转发

            - output_ports: 输出端口列表

        """

        # 1. 学习源MAC

        self.cam_table.learn(src_mac, port, vlan_id)

        

        # 2. 查找目标MAC

        output_port = self.cam_table.lookup(dst_mac, vlan_id)

        

        if output_port is not None:

            # 单播转发

            return True, [output_port]

        else:

            # 泛洪

            return True, self.cam_table.flood_ports(port, vlan_id)

    

    def age_cam(self) -> int:

        """老化CAM表"""

        return self.cam_table.age_out()





def simulate_mac_learning():

    """模拟MAC地址学习"""

    print("=== MAC地址学习模拟 ===\n")

    

    switch = EthernetSwitch(num_ports=4)

    

    # 模拟帧到达

    scenarios = [

        # (src_mac, dst_mac, port, 说明)

        ("00:11:22:33:44:55", "00:aa:bb:cc:dd:ee", 1, "PC1发送帧给PC5"),

        ("00:aa:bb:cc:dd:ee", "00:11:22:33:44:55", 2, "PC5回复PC1"),

        ("00:11:22:33:44:55", "00:aa:bb:cc:dd:ee", 1, "PC1再次发送帧给PC5"),

        ("00:cc:dd:ee:ff:00", "00:11:22:33:44:55", 3, "PC7发送帧给PC1"),

    ]

    

    print("帧处理过程:")

    for src, dst, port, desc in scenarios:

        forwarded, out_ports = switch.receive_frame(port, src, dst)

        

        print(f"\n  {desc}")

        print(f"    {src} -> {dst}")

        print(f"    入端口: {port}")

        

        if out_ports:

            print(f"    出端口: {out_ports[0] if len(out_ports) == 1 else out_ports}")

            print(f"    动作: {'单播转发' if len(out_ports) == 1 else '泛洪'}")

        else:

            print(f"    动作: 丢弃")

    

    # 打印CAM表

    print("\n\nCAM表状态:")

    dump = switch.cam_table.dump()

    for mac, port, vlan, age, is_static in dump['entries']:

        static_str = " [静态]" if is_static else ""

        print(f"  {mac}: port={port}, vlan={vlan}, age={age:.1f}s{static_str}")

    

    print(f"\n统计:")

    stats = dump['stats']

    print(f"  学习: {stats['learn_count']}")

    print(f"  查找: {stats['lookup_count']}")

    print(f"  未命中: {stats['miss_count']}")

    print(f"  泛洪: {stats['flood_count']}")





def demo_aging():

    """演示MAC老化"""

    print("\n=== MAC老化演示 ===\n")

    

    cam = CAMTable(aging_time=5.0)  # 5秒老化

    

    # 学习MAC

    cam.learn("00:11:22:33:44:55", 1, vlan_id=1)

    cam.learn("00:aa:bb:cc:dd:ee", 2, vlan_id=1)

    

    print(f"学习后: {len(cam.entries)} 条目")

    

    # 老化

    expired = cam.age_out()

    print(f"立即老化: {expired} 条目")

    

    print("\n等待5秒...")

    time.sleep(5.1)

    

    expired = cam.age_out()

    print(f"5秒后老化: {expired} 条目")

    

    # 添加静态条目

    cam.learn("00:cc:dd:ee:ff:00", 3, vlan_id=1, static=True)

    print(f"\n添加静态条目后: {len(cam.entries)} 条目")

    

    time.sleep(6)

    expired = cam.age_out()

    print(f"6秒后老化（静态不老化）: {expired} 条目")

    print(f"剩余: {len(cam.entries)} 条目")





def demo_unknown_unicast():

    """演示未知单播泛洪"""

    print("\n=== 未知单播泛洪演示 ===\n")

    

    switch = EthernetSwitch(num_ports=4)

    

    # 只学习PC1

    switch.receive_frame(1, "00:11:22:33:44:55", "00:aa:bb:cc:dd:ee", vlan_id=1)

    

    print("CAM表:")

    dump = switch.cam_table.dump()

    for mac, port, vlan, age, _ in dump['entries']:

        print(f"  {mac}: port={port}")

    

    print("\nPC1发送帧给未知MAC 00:bb:cc:dd:ee:ff:")

    

    forwarded, out_ports = switch.receive_frame(1, "00:11:22:33:44:55", 

                                                 "00:bb:cc:dd:ee:ff", vlan_id=1)

    

    print(f"  出端口: {out_ports}")

    print(f"  动作: 泛洪到所有端口（除入端口）")

    print(f"  泛洪次数: {dump['stats']['flood_count']}")





def demo_vlan_isolation():

    """演示VLAN隔离"""

    print("\n=== VLAN隔离演示 ===\n")

    

    switch = EthernetSwitch(num_ports=4)

    switch.vlan_enabled = True

    

    # VLAN 10: port 1, 2

    switch.vlans[10] = [1, 2]

    # VLAN 20: port 3, 4

    switch.vlans[20] = [3, 4]

    

    print("VLAN配置:")

    print("  VLAN 10: port 1, 2")

    print("  VLAN 20: port 3, 4")

    

    # VLAN 10内通信

    print("\nVLAN 10内通信:")

    switch.receive_frame(1, "00:11:22:33:44:55", "00:aa:bb:cc:dd:ee", vlan_id=10)

    _, out = switch.cam_table.lookup("00:aa:bb:cc:dd:ee", vlan_id=10)

    print(f"  PC1 -> PC2: port={out}")

    

    # VLAN 20内通信

    print("\nVLAN 20内通信:")

    switch.receive_frame(3, "00:cc:dd:ee:ff:00", "00:ee:ff:00:11:22", vlan_id=20)

    _, out = switch.cam_table.lookup("00:ee:ff:00:11:22", vlan_id=20)

    print(f"  PC3 -> PC4: port={out}")

    

    # VLAN间通信（不应工作）

    print("\nVLAN间通信尝试:")

    print("  PC1 (VLAN 10) -> PC3 (VLAN 20)")

    _, out = switch.cam_table.lookup("00:cc:dd:ee:ff:00", vlan_id=10)

    print(f"  查找结果: port={out} (不同VLAN，无法通信)")





def demo_broadcast():

    """演示广播处理"""

    print("\n=== 广播处理演示 ===\n")

    

    switch = EthernetSwitch(num_ports=4)

    

    # 广播MAC

    broadcast_mac = "ff:ff:ff:ff:ff:ff"

    

    print(f"广播帧目标: {broadcast_mac}")

    

    forwarded, out_ports = switch.receive_frame(1, "00:11:22:33:44:55", 

                                               broadcast_mac, vlan_id=1)

    

    print(f"  出端口: {out_ports}")

    print(f"  动作: 泛洪到所有端口")





def demo_stp_prevention():

    """演示STP防止环路"""

    print("\n=== STP防止环路原理 ===\n")

    

    print("生成树协议(STP)防止广播风暴:")

    print("  1. 选举根桥")

    print("  2. 非根桥选择根端口")

    print("  3. 每个网段选择指定端口")

    print("  4. 阻塞非指定端口")

    print()

    

    print("结果:")

    print("  - 每个VLAN内只有一条活动路径")

    print("  - 冗余链路作为备份")

    print("  - 避免广播风暴")

    print("  - 链路故障时自动恢复")





if __name__ == "__main__":

    print("=" * 60)

    print("交换机MAC地址学习算法")

    print("=" * 60)

    

    # MAC学习模拟

    simulate_mac_learning()

    

    # 老化演示

    demo_aging()

    

    # 未知单播泛洪

    demo_unknown_unicast()

    

    # VLAN隔离

    demo_vlan_isolation()

    

    # 广播处理

    demo_broadcast()

    

    # STP

    demo_stp_prevention()

    

    print("\n" + "=" * 60)

    print("关键概念:")

    print("=" * 60)

    print("""

1. CAM表查找:

   - O(1)复杂度（硬件支持）

   - MAC + VLAN联合索引

   

2. 泛洪:

   - 未知单播帧发送到所有端口

   - 广播/组播帧泛洪

   - 可能导致网络拥塞

   

3. 老化机制:

   - 防止表项无限增长

   - 适应网络拓扑变化

   - 静态条目不受影响

   

4. VLAN隔离:

   - CAM表按VLAN索引

   - 不同VLAN的MAC可重叠

   - 实现二层安全隔离

""")

