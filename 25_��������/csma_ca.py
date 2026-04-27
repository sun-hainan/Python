# -*- coding: utf-8 -*-

"""

算法实现：25_�������� / csma_ca



本文件实现 csma_ca 相关的算法功能。

"""



import random

import time

from dataclasses import dataclass

from typing import List, Tuple, Optional

from enum import Enum

import math





class ChannelState(Enum):

    """信道状态"""

    IDLE = 0

    BUSY = 1

    COLLISION = 2





class CSMACAStation:

    """

    CSMA/CA站点

    

    每个站点维护：

    - 退避计数器

    - CW窗口大小

    - 重传次数

    """

    

    def __init__(self, station_id: int, slot_time: float = 0.000009):  # 9us slot

        self.station_id = station_id

        self.slot_time = slot_time

        

        # 退避参数

        self.cw_min = 15  # 最小竞争窗口

        self.cw_max = 1023  # 最大竞争窗口

        self.cw = self.cw_min  # 当前窗口大小

        

        # 状态

        self.backoff_counter = 0  # 退避计数器（slots）

        self.backoff_stage = 0  # 退避阶段（指数）

        self.packets_to_send = []  # 待发送数据包

        

        # 统计

        self.packets_sent = 0

        self.packets_success = 0

        self.collisions = 0

        self.failed = 0

    

    def start_backoff(self, packets_count: int = 1):

        """

        开始退避（信道空闲后）

        

        Args:

            packets_count: 待发送的包数量

        """

        for _ in range(packets_count):

            # 随机选择退避计数器

            self.backoff_counter = random.randint(0, self.cw)

            self.packets_to_send.append(self.station_id)

    

    def decrement_backoff(self) -> bool:

        """

        递减退避计数器

        

        Returns:

            是否可以发送（计数器到0）

        """

        if self.backoff_counter > 0:

            self.backoff_counter -= 1

        

        if self.backoff_counter == 0 and self.packets_to_send:

            return True

        return False

    

    def on_collision(self):

        """碰撞处理"""

        self.collisions += 1

        self.backoff_stage = min(self.backoff_stage + 1, int(math.log2(self.cw_max + 1)) - 1)

        self.cw = min(2 ** (self.backoff_stage + 1) - 1, self.cw_max)

    

    def on_success(self):

        """成功传输处理"""

        self.packets_success += 1

        self.backoff_stage = 0

        self.cw = self.cw_min

        if self.packets_to_send:

            self.packets_to_send.pop(0)





class CSMCANetwork:

    """

    CSMA/CA网络模拟器

    

    模拟多个站点竞争信道的过程

    """

    

    def __init__(self, slot_time: float = 0.000009, sifs: float = 0.000016):

        """

        初始化

        

        Args:

            slot_time: 时隙时间（9us for 802.11b）

            sifs: 短帧间隔（16us）

        """

        self.slot_time = slot_time

        self.sifs = sifs

        self.stations: List[CSMACAStation] = []

        

        self.channel_state = ChannelState.IDLE

        self.current_time = 0.0

        

        # DCF参数 (802.11b)

        self.difs = slot_time * 3 + sifs  # 43us

        self.ack_timeout = 0.000064  # 64us

    

    def add_station(self, station: CSMACAStation):

        """添加站点"""

        self.stations.append(station)

    

    def sense_channel(self) -> bool:

        """

        监听信道

        

        Returns:

            信道是否空闲

        """

        return self.channel_state == ChannelState.IDLE

    

    def transmit(self, station: CSMACAStation, duration: float) -> bool:

        """

        尝试传输

        

        Args:

            station: 发送站点

            duration: 传输持续时间

        

        Returns:

            是否成功（无碰撞）

        """

        # 检查是否有其他站点同时传输

        # 简化：随机决定是否有碰撞

        collision_prob = len([s for s in self.stations 

                             if s.backoff_counter == 0]) / len(self.stations)

        

        collision_prob = max(0.1, collision_prob)  # 至少10%碰撞概率

        

        if random.random() < collision_prob:

            self.channel_state = ChannelState.COLLISION

            return False

        

        self.channel_state = ChannelState.BUSY

        return True

    

    def run_simulation(self, duration_seconds: float, verbose: bool = True) -> dict:

        """

        运行模拟

        

        Args:

            duration_seconds: 模拟时长

            verbose: 是否输出详情

        

        Returns:

            统计结果

        """

        max_slots = int(duration_seconds / self.slot_time)

        

        for slot in range(max_slots):

            self.current_time = slot * self.slot_time

            

            # 1. 信道监听

            idle_stations = [s for s in self.stations if s.packets_to_send]

            

            if not idle_stations:

                continue

            

            # 2. 递减退避计数器

            ready_stations = []

            for s in idle_stations:

                if s.decrement_backoff():

                    ready_stations.append(s)

            

            # 3. 如果有多个站点同时准备发送，发生碰撞

            if len(ready_stations) > 1:

                for s in ready_stations:

                    s.on_collision()

                    # 重新开始退避

                    s.start_backoff(1)

            

            elif len(ready_stations) == 1:

                # 4. 尝试传输

                station = ready_stations[0]

                

                if self.transmit(station, 0.001):  # 假设1ms传输时间

                    # 5. 成功

                    time.sleep(0.001)  # 传输时间

                    station.on_success()

                    station.packets_sent += 1

                    

                    if verbose and station.packets_success % 10 == 0:

                        print(f"  站点{station.station_id}: 成功发送第{station.packets_success}个包")

                else:

                    # 6. 碰撞

                    station.on_collision()

                    station.start_backoff(1)

        

        # 汇总统计

        total_sent = sum(s.packets_sent for s in self.stations)

        total_success = sum(s.packets_success for s in self.stations)

        total_collision = sum(s.collisions for s in self.stations)

        

        return {

            'total_attempts': total_sent,

            'total_success': total_success,

            'total_collisions': total_collision,

            'success_rate': total_success / total_sent if total_sent > 0 else 0,

            'collision_rate': total_collision / total_sent if total_sent > 0 else 0,

        }





def demo_binary_exponential_backoff():

    """

    演示二进制指数退避

    """

    print("=== 二进制指数退避演示 ===\n")

    

    station = CSMACAStation(1)

    

    print("CW (竞争窗口) 变化过程:")

    print("  初始: CW = 15 (2^4 - 1)")

    print()

    

    for i in range(6):

        station.cw = min(2 ** (i + 4) - 1, 1023)

        slots = station.cw + 1

        print(f"  第{i}次碰撞: CW = {station.cw}, 随机范围 = [0, {slots}]")

    

    station.cw = 1023

    print(f"  CWmax: {station.cw}")

    print()

    

    print("退避过程:")

    station.cw = 15

    for i in range(3):

        station.backoff_counter = random.randint(0, station.cw)

        print(f"  随机选择: {station.backoff_counter} slots = {station.backoff_counter * 9}us")





def simulate_wifi_network():

    """

    模拟WiFi网络

    """

    print("\n=== WiFi网络模拟 ===\n")

    

    # 创建网络

    network = CSMCANetwork()

    

    # 添加站点

    num_stations = 10

    for i in range(num_stations):

        station = CSMACAStation(i)

        # 每个站点有不同数量的包

        packets_count = random.randint(50, 200)

        station.start_backoff(packets_count)

        network.add_station(station)

    

    print(f"网络配置: {num_stations}个站点")

    print(f"每个站点待发送: 50-200个包")

    print()

    

    # 运行模拟（1秒）

    print("运行模拟 (1秒):")

    results = network.run_simulation(1.0, verbose=False)

    

    print(f"\n模拟结果:")

    print(f"  总尝试: {results['total_attempts']}")

    print(f"  成功: {results['total_success']}")

    print(f"  碰撞: {results['total_collisions']}")

    print(f"  成功率: {results['success_rate']:.1%}")

    print(f"  碰撞率: {results['collision_rate']:.1%}")





def demo_rts_cts():

    """

    演示RTS/CTS机制

    """

    print("\n=== RTS/CTS机制演示 ===\n")

    

    print("RTS/CTS (Request to Send / Clear to Send):")

    print()

    print("  目的: 解决隐藏终端问题")

    print()

    print("  流程:")

    print("  1. 发送方发送RTS (请求发送)")

    print("  2. 接收方回复CTS (允许发送)")

    print("  3. 其他站点听到CTS后暂停发送")

    print("  4. 发送方发送数据")

    print("  5. 接收方发送ACK")

    print()

    

    print("优点:")

    print("  - 避免隐藏终端碰撞")

    print("  - 短RTS碰撞比长数据碰撞代价小")

    print()

    

    print("缺点:")

    print("  - 增加开销")

    print("  - 适合高负载或长帧场景")

    

    # 计算效率

    rts_size = 20  # bytes

    cts_size = 14  # bytes

    ack_size = 14  # bytes

    data_size = 1500  # bytes

    overhead = rts_size + cts_size + ack_size

    

    efficiency = data_size / (data_size + overhead)

    print(f"\n效率分析:")

    print(f"  数据: {data_size} bytes")

    print(f"  RTS+CTS+ACK开销: {overhead} bytes")

    print(f"  效率: {efficiency:.1%}")

    

    # 高负载时效率更高

    print(f"\n  阈值: 当帧> RTS_threshold 时，使用RTS/CTS更高效")





def demo_dcf_analysis():

    """

    DCF (Distributed Coordination Function) 分析

    """

    print("\n=== DCF性能分析 ===\n")

    

    # 802.11b参数

    slot_time = 20e-6  # 20us

    sifs = 10e-6  # 10us

    difs = 2 * slot_time + sifs  # 50us

    cw_min = 31  # 802.11b

    

    print("802.11b DCF参数:")

    print(f"  Slot time: {slot_time * 1e6:.0f} us")

    print(f"  SIFS: {sifs * 1e6:.0f} us")

    print(f"  DIFS: {difs * 1e6:.0f} us")

    print(f"  CWmin: {cw_min}")

    print()

    

    # 理论吞吐量计算

    data_rate = 11e6  # 11 Mbps

    basic_rate = 2e6  # 1 Mbps basic rate

    

    # 最大吞吐量（理想情况）

    payload = 1500 * 8  # bits

    overhead_bits = 192  # 物理层头

    tx_time = (payload + overhead_bits) / data_rate

    efficiency = payload / tx_time

    

    print("理论吞吐量 (802.11b, 1500B包):")

    print(f"  物理速率: {data_rate / 1e6:.0f} Mbps")

    print(f"  实际吞吐: {efficiency / 1e6:.1f} Mbps")

    print(f"  效率: {efficiency / data_rate:.1%}")

    print()

    

    # 不同包大小的效率

    print("不同包大小的效率:")

    print("| 包大小 | 效率 |")

    print("|--------|------|")

    for size in [64, 256, 512, 1024, 1500]:

        payload_bits = size * 8

        tx_time = (payload_bits + overhead_bits) / data_rate

        eff = payload_bits / tx_time / data_rate

        print(f"| {size}B | {eff:.1%} |")





def demo_adaptive_rate():

    """

    演示自适应速率控制

    """

    print("\n=== 自适应速率控制演示 ===\n")

    

    rates = [1, 2, 5.5, 11]  # Mbps

    distances = [100, 80, 50, 30]  # 米

    

    print("802.11b 自适应速率:")

    print("| 距离 | 推荐速率 |")

    print("|------|----------|")

    

    for d, r in zip(distances, rates):

        print(f"| {d}m | {r} Mbps |")

    

    print()

    

    # SNR-based rate selection

    print("SNR (信噪比) 速率选择:")

    print("| SNR范围 | 推荐速率 |")

    print("|---------|----------|")

    print("| > 25 dB | 11 Mbps  |")

    print("| 15-25 dB | 5.5 Mbps |")

    print("| 10-15 dB | 2 Mbps   |")

    print("| < 10 dB | 1 Mbps   |")





if __name__ == "__main__":

    print("=" * 60)

    print("CSMA/CA 介质访问控制协议")

    print("=" * 60)

    

    # 二进制指数退避

    demo_binary_exponential_backoff()

    

    # WiFi网络模拟

    simulate_wifi_network()

    

    # RTS/CTS

    demo_rts_cts()

    

    # DCF分析

    demo_dcf_analysis()

    

    # 自适应速率

    demo_adaptive_rate()

    

    print("\n" + "=" * 60)

    print("CSMA/CA vs CSMA/CD:")

    print("=" * 60)

    print("""

| 特性        | CSMA/CA (无线) | CSMA/CD (有线) |

|-------------|---------------|----------------|

| 碰撞检测    | 不可行        | 可行           |

| 碰撞避免    | 是            | 否             |

| ACK确认     | 需要          | 不需要         |

| RTS/CTS     | 可选          | 不使用         |

| 效率        | 较低          | 较高           |



CSMA/CA额外机制:

1. DIFS/SIFS间隔

2. ACK确认

3. RTS/CTS握手机制

4. 指数退避算法

5. 虚拟载波监听 (NAV)

""")

