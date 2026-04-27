# -*- coding: utf-8 -*-
"""
算法实现：计算机网络算法 / csma_ca

本文件实现 csma_ca 相关的算法功能。
"""

import random
import math
import time


class CSMACAStation:
    """CSMA/CA 站点"""

    def __init__(self, station_id, slot_time=0.000009, sifs=0.000016, 
                 difs=0.000034, cw_min=15, cw_max=1023):
        """
        初始化站点
        
        参数:
            station_id: 站点 ID
            slot_time: 时隙时间（秒），802.11g 为 9us
            sifs: 短帧间间隔（秒），802.11g 为 16us
            difs: DCF 帧间间隔（秒），802.11g 为 34us
            cw_min: 最小竞争窗口
            cw_max: 最大竞争窗口
        """
        self.station_id = station_id
        self.slot_time = slot_time
        self.sifs = sifs
        self.difs = difs
        self.cw_min = cw_min
        self.cw_max = cw_max
        # 当前竞争窗口
        self.cw = cw_min
        # 后退计数
        self.backoff_counter = 0
        # 状态
        self.state = 'idle'  # idle, sensing, backoff, transmitting, waiting_ack
        # 信道状态
        self.channel_busy = False
        # 统计数据
        self.packets_sent = 0
        self.packets_failed = 0
        self.collisions = 0
        self.total_backoff_slots = 0

    def start_transmission(self):
        """
        开始传输（触发载波侦听和退避）
        
        返回:
            backoff_slots: 需要退避的时隙数
        """
        if self.state == 'idle':
            self.state = 'sensing'
            self.cw = self.cw_min
        
        return self._backoff()

    def _backoff(self):
        """
        执行退避算法
        
        返回:
            backoff_slots: 需要退避的时隙数
        """
        # 选择随机退避计数
        self.backoff_counter = random.randint(0, self.cw)
        self.total_backoff_slots += self.backoff_counter
        
        if self.backoff_counter > 0:
            self.state = 'backoff'
        
        return self.backoff_counter

    def decrement_backoff(self):
        """
        递减退避计数（在每个时隙结束时调用）
        
        返回:
            can_transmit: 是否可以发送
        """
        if self.state == 'backoff' and self.backoff_counter > 0:
            self.backoff_counter -= 1
            
            if self.backoff_counter == 0:
                self.state = 'transmitting'
                return True
        
        return False

    def on_channel_busy(self):
        """信道变忙时的处理"""
        if self.state == 'backoff':
            # 停止递减，保存当前计数
            pass

    def on_channel_idle(self):
        """信道变空闲时的处理"""
        if self.state == 'sensing' or self.state == 'backoff':
            # DIFS 后开始递减
            self.state = 'backoff'

    def on_transmit_success(self, ack_received=True):
        """
        传输成功
        
        参数:
            ack_received: 是否收到 ACK
        """
        self.packets_sent += 1
        self.state = 'idle'
        self.cw = self.cw_min

    def on_transmit_failure(self):
        """传输失败（冲突或超时）"""
        self.packets_failed += 1
        self.collisions += 1
        # 增加竞争窗口
        self.cw = min(2 * self.cw + 1, self.cw_max)
        self.state = 'idle'

    def get_stats(self):
        """获取统计信息"""
        total = self.packets_sent + self.packets_failed
        return {
            'sent': self.packets_sent,
            'failed': self.packets_failed,
            'collisions': self.collisions,
            'success_rate': self.packets_sent / total if total > 0 else 0,
            'avg_backoff': self.total_backoff_slots / total if total > 0 else 0
        }


class ChannelState:
    """共享信道状态"""

    def __init__(self):
        """初始化信道"""
        # 正在传输的站点集合
        self.active_transmissions = set()
        # 信道是否忙碌
        self.busy = False
        # 传输事件
        self.transmission_events = []

    def start_transmission(self, station_id, duration):
        """
        开始传输
        
        参数:
            station_id: 站点 ID
            duration: 传输持续时间
        """
        self.active_transmissions.add(station_id)
        self.busy = True
        self.transmission_events.append({
            'station': station_id,
            'type': 'start',
            'time': time.time()
        })

    def end_transmission(self, station_id):
        """
        结束传输
        
        参数:
            station_id: 站点 ID
        """
        self.active_transmissions.discard(station_id)
        if not self.active_transmissions:
            self.busy = False
        self.transmission_events.append({
            'station': station_id,
            'type': 'end',
            'time': time.time()
        })

    def is_busy(self):
        """检查信道是否忙碌"""
        return self.busy


class RTSCTSHandler:
    """RTS/CTS 握手机制"""

    def __init__(self, station, rts_threshold=2346):
        """
        初始化 RTS/CTS 处理器
        
        参数:
            station: 所属站点
            rts_threshold: RTS 阈值（字节），超过此值才使用 RTS/CTS
        """
        self.station = station
        self.rts_threshold = rts_threshold
        # RTS/CTS 状态
        self.rts_pending = False
        self.cts_pending = False
        self.cts_received = False

    def should_use_rts_cts(self, packet_size):
        """
        判断是否应使用 RTS/CTS
        
        参数:
            packet_size: 数据包大小（字节）
        返回:
            use_rts_cts: 是否使用
        """
        return packet_size >= self.rts_threshold

    def send_rts(self, packet_size, duration):
        """
        发送 RTS 帧
        
        参数:
            packet_size: 数据包大小
            duration: 传输持续时间
        返回:
            rts_frame: RTS 帧
        """
        self.rts_pending = True
        return {
            'type': 'rts',
            'station': self.station.station_id,
            'duration': duration
        }

    def on_cts_received(self):
        """收到 CTS 帧"""
        if self.rts_pending:
            self.cts_pending = True
            self.cts_received = True

    def on_rts_sent(self):
        """RTS 发送完成"""
        pass  # 实际应该等待 CTS

    def reset(self):
        """重置状态"""
        self.rts_pending = False
        self.cts_pending = False
        self.cts_received = False


class CSMACANetwork:
    """CSMA/CA 网络模拟器"""

    def __init__(self, num_stations, slot_time=0.000009):
        """
        初始化网络
        
        参数:
            num_stations: 站点数量
            slot_time: 时隙时间
        """
        self.num_stations = num_stations
        self.slot_time = slot_time
        # 创建站点
        self.stations = [
            CSMACAStation(f"STA_{i}", slot_time=slot_time)
            for i in range(num_stations)
        ]
        # 信道
        self.channel = ChannelState()
        # 当前时隙
        self.current_slot = 0
        # 时间
        self.current_time = 0.0
        # 事件队列
        self.event_queue = []

    def attempt_transmission(self, station_id):
        """
        站点尝试传输
        
        参数:
            station_id: 站点 ID
        """
        station = self.stations[station_id]
        
        if station.state == 'idle':
            backoff_slots = station.start_transmission()
            if backoff_slots > 0:
                # 调度退避
                self._schedule_event(
                    self.current_time + backoff_slots * self.slot_time,
                    'backoff_expire',
                    station_id
                )

    def _schedule_event(self, time, event_type, station_id):
        """调度事件"""
        self.event_queue.append({
            'time': time,
            'type': event_type,
            'station_id': station_id
        })
        self.event_queue.sort(key=lambda e: e['time'])

    def _process_event(self, event):
        """处理事件"""
        self.current_time = event['time']
        station_id = event['station_id']
        station = self.stations[station_id]
        
        if event['type'] == 'backoff_expire':
            # 退避结束，检查信道
            if not self.channel.is_busy():
                # 开始传输
                self._start_transmission(station_id)
            else:
                # 信道忙，继续等待
                station.on_channel_busy()
                # 当信道空闲时重新开始退避
                self._schedule_event(
                    self.current_time + self.slot_time,
                    'retry_backoff',
                    station_id
                )
        
        elif event['type'] == 'retry_backoff':
            if not self.channel.is_busy():
                station.on_channel_idle()
                # 继续递减
                if station.decrement_backoff():
                    self._start_transmission(station_id)
            else:
                self._schedule_event(
                    self.current_time + self.slot_time,
                    'retry_backoff',
                    station_id
                )
        
        elif event['type'] == 'transmission_end':
            self.channel.end_transmission(station_id)
            # 传输成功
            station.on_transmit_success()
            # 通知其他站点信道空闲
            for other in self.stations:
                if other.station_id != station_id:
                    other.on_channel_idle()

    def _start_transmission(self, station_id):
        """开始传输"""
        station = self.stations[station_id]
        station.state = 'transmitting'
        
        # 模拟传输时间
        tx_duration = random.uniform(0.001, 0.005)  # 1-5ms
        self.channel.start_transmission(station_id, tx_duration)
        
        # 调度传输结束事件
        self._schedule_event(
            self.current_time + tx_duration,
            'transmission_end',
            station_id
        )

    def run_simulation(self, duration, packets_per_station=10):
        """
        运行模拟
        
        参数:
            duration: 模拟时长（秒）
            packets_per_station: 每个站点要发送的包数
        """
        print(f"=== CSMA/CA 网络模拟 ===")
        print(f"站点数: {self.num_stations}")
        print(f"模拟时长: {duration} 秒")
        print(f"每站点包数: {packets_per_station}")
        print()
        
        # 为每个站点调度初始传输尝试
        for station in self.stations:
            self.attempt_transmission(station.station_id)
        
        # 事件循环
        end_time = self.current_time + duration
        while self.event_queue and self.current_time < end_time:
            event = self.event_queue.pop(0)
            if event['time'] > end_time:
                break
            self._process_event(event)
        
        # 汇总统计
        print("--- 模拟结果 ---")
        total_sent = sum(s.packets_sent for s in self.stations)
        total_failed = sum(s.packets_failed for s in self.stations)
        total_collisions = sum(s.collisions for s in self.stations)
        
        print(f"总发送: {total_sent}")
        print(f"总失败: {total_failed}")
        print(f"总冲突: {total_collisions}")
        print(f"成功率: {total_sent/(total_sent+total_failed) if total_sent+total_failed > 0 else 0:.2%}")
        
        print(f"\n各站点统计:")
        for station in self.stations[:5]:  # 显示前5个
            stats = station.get_stats()
            print(f"  {station.station_id}: 发送={stats['sent']}, "
                  f"失败={stats['failed']}, 平均退避={stats['avg_backoff']:.1f} 槽")


class DCFAnalyzer:
    """DCF（Distributed Coordination Function）性能分析"""

    def __init__(self, params):
        """
        初始化分析器
        
        参数:
            params: DCF 参数
        """
        self.params = params

    def calculate_throughput(self, num_stations, offered_load):
        """
        计算理论吞吐量
        
        参数:
            num_stations: 站点数
            offered_load: 负载（包/秒）
        返回:
            throughput: 实际吞吐量
        """
        # 简化的吞吐量模型
        # 实际应该用 Markov chain 或 Bianchi 模型
        slot_time = self.params.get('slot_time', 9e-6)
        cw_min = self.params.get('cw_min', 15)
        sifs = self.params.get('sifs', 16e-6)
        difs = self.params.get('difs', 34e-6)
        
        # 平均退避时间
        avg_backoff = (cw_min / 2) * slot_time
        
        # 碰撞概率（简化）
        p_collision = min(1, 0.1 * num_stations * (offered_load / 1000))
        
        # 成功传输时间
        tx_time = 1500 * 8 / 54e6  # 1500B at 54Mbps = 222us
        
        # 有效吞吐量
        success_prob = 1 - p_collision
        efficiency = success_prob / (1 + p_collision)
        
        return offered_load * tx_time * efficiency

    def calculate_delay(self, num_stations, load):
        """
        计算平均延迟
        
        参数:
            num_stations: 站点数
            load: 负载
        返回:
            delay: 平均延迟（秒）
        """
        slot_time = self.params.get('slot_time', 9e-6)
        cw_min = self.params.get('cw_min', 15)
        difs = self.params.get('difs', 34e-6)
        
        # 平均退避时间
        avg_backoff = (cw_min / 2) * slot_time
        
        # 简化的延迟模型
        queuing_delay = avg_backoff * num_stations * (load / 1000)
        transmission_delay = 1500 * 8 / 54e6
        
        return queuing_delay + transmission_delay + difs


if __name__ == "__main__":
    # 测试 CSMA/CA
    print("=== CSMA/CA 算法测试 ===\n")

    # 创建站点
    station = CSMACAStation("STA_0")
    print(f"站点 {station.station_id}:")
    print(f"  初始 CW: {station.cw}")
    
    # 模拟传输尝试
    for i in range(5):
        backoff_slots = station.start_transmission()
        print(f"  传输尝试 {i+1}: 退避 {backoff_slots} 槽, CW={station.cw}")
        # 模拟成功传输
        station.on_transmit_success()
    
    stats = station.get_stats()
    print(f"\n统计: 发送={stats['sent']}, 失败={stats['failed']}, "
          f"成功率={stats['success_rate']:.1%}")

    # 测试 RTS/CTS
    print("\n--- RTS/CTS 机制 ---")
    rts_handler = RTSCTSHandler(station, rts_threshold=500)
    
    for size in [100, 1000, 5000]:
        use_rts = rts_handler.should_use_rts_cts(size)
        print(f"  包大小 {size} 字节: {'使用 RTS/CTS' if use_rts else '不使用'}")

    # 网络模拟
    print("\n--- 网络模拟 ---")
    network = CSMACANetwork(num_stations=5, slot_time=9e-6)
    network.run_simulation(duration=0.1, packets_per_station=5)
