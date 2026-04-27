# -*- coding: utf-8 -*-
"""
算法实现：计算机网络算法 / sliding_window

本文件实现 sliding_window 相关的算法功能。
"""

import math
import random


class TCPSender:
    """
    TCP 发送端滑动窗口模拟器
    实现累计确认、超时重传、快速重传、拥塞窗口管理
    """

    def __init__(self, initial_seq=0, mss=1460):
        self.initial_seq = initial_seq
        self.mss = mss          # Maximum Segment Size
        self.seq = initial_seq  # 下一个要发送的字节序号
        self.una = initial_seq  # 最早未确认字节序号（发送窗口左边界）
        # cwnd: 拥塞窗口（字节）
        self.cwnd = mss         # 初始窗口 1 MSS
        # ssthresh: 慢启动阈值
        self.ssthresh = 65535
        # rwnd: 接收方通告的窗口大小（流量控制）
        self.rwnd = 65535
        # outstanding: 已发送但未确认的字节数
        self.outstanding = 0
        # send_buffer: 发送缓冲区
        self.send_buffer = {}
        # dup_acks: 累计的重复 ACK 数
        self.dup_acks = 0
        # recovery_point: 恢复点
        self.recovery_point = 0
        # mode: 'slow_start' | 'congestion_avoidance' | 'fast_recovery'
        self.mode = 'slow_start'
        # stats
        self.total_sent = 0
        self.total_retrans = 0
        self.total_dup_ack = 0

    def get_window(self):
        """有效窗口 = min(cwnd, rwnd)"""
        return min(self.cwnd, self.rwnd)

    def can_send(self, data_len=0):
        """检查是否可以发送数据"""
        effective_win = self.get_window()
        return (self.seq - self.una + data_len) <= effective_win

    def send_data(self, data_len):
        """
        发送数据（尽可能填满窗口）
        返回: 实际发送的字节数和序号
        """
        sent = []
        while self.can_send(data_len) and self.outstanding < self.get_window():
            payload_size = min(self.mss, data_len)
            seg_seq = self.seq
            self.seq += payload_size
            self.outstanding += payload_size
            self.send_buffer[seg_seq] = {
                'len': payload_size,
                'acked': False,
                'retransmitted': False,
                'send_time': 0.0
            }
            sent.append((seg_seq, payload_size))
            self.total_sent += payload_size

        return sent

    def on_ack(self, ack_num):
        """
        处理 ACK
        ack_num: 确认号
        返回: 是否正常确认，超时重传是否触发
        """
        if ack_num <= self.una:
            # 重复 ACK
            self.dup_acks += 1
            return False

        # 新数据确认
        self.dup_acks = 0
        acked_bytes = ack_num - self.una
        self.una = ack_num

        # 从发送缓冲区移除已确认的数据
        to_remove = [seq for seq in self.send_buffer if seq + self.send_buffer[seq]['len'] <= ack_num]
        for seq in to_remove:
            del self.send_buffer[seq]
        self.outstanding = sum(v['len'] for v in self.send_buffer.values())

        # 拥塞窗口增长
        if self.mode == 'slow_start':
            # 慢启动：每确认 cwnd 字节，cwnd 增加 1 MSS（指数增长）
            self.cwnd += min(acked_bytes, self.mss)
            if self.cwnd >= self.ssthresh:
                self.mode = 'congestion_avoidance'

        elif self.mode == 'congestion_avoidance':
            # 拥塞避免：每 RTT 增加 1 MSS
            self.cwnd += (self.mss * acked_bytes) / self.cwnd

        elif self.mode == 'fast_recovery':
            # 快速恢复：退出并进入拥塞避免
            self.cwnd = self.ssthresh
            self.mode = 'congestion_avoidance'

        return True

    def on_dup_ack(self):
        """
        快速重传：3次重复ACK触发
        """
        if self.dup_acks >= 3 and self.mode != 'fast_recovery':
            # 快速重传
            self.ssthresh = max(self.cwnd / 2, 2 * self.mss)
            self.cwnd = self.ssthresh + 3 * self.mss
            self.recovery_point = max(self.recovery_point, self.una)
            self.mode = 'fast_recovery'
            return True
        elif self.dup_acks >= 3 and self.mode == 'fast_recovery':
            # 额外重复ACK：窗口增加1 MSS
            self.cwnd += self.mss
        return False

    def on_timeout(self):
        """
        超时：最严重的拥塞信号
        """
        self.ssthresh = max(self.cwnd / 2, 2 * self.mss)
        self.cwnd = self.mss
        self.mode = 'slow_start'
        self.dup_acks = 0
        self.total_retrans += 1


class SlidingWindowAnalysis:
    """
    滑动窗口性能分析：吞吐率、带宽利用率、时延关系
    """

    @staticmethod
    def throughput_rtt(window_size_bits, rtt_ms, mss_bytes=1460):
        """
        计算最大吞吐率（窗口满载时）
        window_size_bits: 窗口大小（字节转位）
        rtt_ms: 往返延迟（毫秒）
        """
        window_bytes = window_size_bits
        rtt_sec = rtt_ms / 1000.0
        throughput_bps = window_bytes / rtt_sec
        throughput_mbps = throughput_bps * 8 / 1e6
        return throughput_mbps

    @staticmethod
    def bandwidth_delay_product(window_mss, rtt_ms):
        """
        计算带宽-延迟积（BDP）
        BDP = 带宽 × RTT，是保证链路充分利用所需的最小窗口大小
        """
        return window_mss * 1460 * 8 / 1e6  # Mbps

    @staticmethod
    def required_cwnd(target_mbps, rtt_ms):
        """
        计算达到目标吞吐率所需的最小 cwnd
        """
        rtt_sec = rtt_ms / 1000.0
        cwnd_bytes = target_mbps * 1e6 / 8 * rtt_sec
        return cwnd_bytes


class TCPWindowScale:
    """
    TCP 窗口扩大选项（Window Scaling）
    背景：TCP 头部窗口字段只有 16 位，最大窗口 = 65535 字节
    对于高带宽高延迟网络（BDP > 64KB），这成为瓶颈
    解决：窗口扩大选项（RFC 1323），最大扩大因子 = 14
    最大窗口 = 65535 × 2^14 = 1 GB
    """

    MAX_SCALE = 14

    @staticmethod
    def compute_scale_factor(shift_count):
        """shift_count: 扩大因子（0-14）"""
        return 1 << shift_count

    @staticmethod
    def find_optimal_scale(rwnd_max, bdp_bytes):
        """
        找到最优的窗口扩大因子
        rwnd_max: 接收方最大窗口
        bdp_bytes: 带宽-延迟积
        """
        target = max(rwnd_max, bdp_bytes)
        scale = 0
        while (65535 << scale) < target and scale < TCPWindowScale.MAX_SCALE:
            scale += 1
        return scale


if __name__ == '__main__':
    print("TCP 滑动窗口与拥塞控制算法演示")
    print("=" * 60)

    # -------------------- 滑动窗口协议演示 --------------------
    sender = TCPSender(initial_seq=0, mss=1460)
    sender.ssthresh = 10 * 1460
    sender.mode = 'congestion_avoidance'

    print("\n【TCP 滑动窗口状态】")
    print(f"  MSS={sender.mss}, cwnd={sender.cwnd/1460:.1f}MSS, "
          f"ssthresh={sender.ssthresh/1460:.1f}MSS")

    # 模拟数据发送
    print(f"\n发送阶段模拟：")
    print(f"  {'阶段':<20} {'cwnd(MSS)':<12} {'可用窗口':<12} {'可发送'}")
    print("-" * 60)

    phases = [
        ('慢启动', 'slow_start', 1),
        ('进入拥塞避免', 'congestion_avoidance', 10),
        ('接近 ssthresh', 'congestion_avoidance', 20),
    ]

    for phase_name, mode, ack_num in phases:
        sender.mode = mode
        sender.una = ack_num * sender.mss
        sender.seq = sender.una
        sender.outstanding = 0
        sender.cwnd = min(sender.cwnd, sender.ssthresh)
        effective_win = sender.get_window()
        can_send = effective_win - sender.outstanding
        print(f"  {phase_name:<20} {sender.cwnd/1460:<12.1f} "
              f"{effective_win/1460:<12.1f} {can_send/1460:.1f} MSS")

    # -------------------- BDP 分析 --------------------
    print("\n" + "=" * 60)
    print("【带宽-延迟积（BDP）与窗口大小】")

    scenarios = [
        ('WiFi (54Mbps, 5ms)', 54, 5),
        ('4G LTE (50Mbps, 30ms)', 50, 30),
        ('数据中心 (10Gbps, 0.5ms)', 10000, 0.5),
        ('卫星 (10Mbps, 600ms)', 10, 600),
    ]

    print(f"\n{'场景':<25} {'BDP(MB)':<12} {'需扩窗?':<10} {'scale'}")
    print("-" * 55)

    for name, bw_mbps, rtt_ms in scenarios:
        rtt_sec = rtt_ms / 1000.0
        bdp_bytes = bw_mbps * 1e6 / 8 * rtt_sec
        bdp_mb = bdp_bytes / 1e6

        needs_scale = bdp_bytes > 65535
        scale = TCPWindowScale.find_optimal_scale(65535, bdp_bytes)

        print(f"  {name:<25} {bdp_mb:<12.2f} {'是' if needs_scale else '否':<10} {scale}")

    print("\n关键洞察：")
    print("  BDP = 带宽(Mbps) × RTT(ms) / 8")
    print("  链路利用率 = min(1, cwnd / BDP)")
    print("  超过 BDP 继续增窗口只会排队，不会提高吞吐")
    print("\n卫星网络挑战：")
    print("  10 Mbps × 600 ms = 750 KB BDP")
    print("  需要窗口扩大因子 scale≥4 才能利用带宽")
    print("  但 RTT 太大，任何重传都代价极高（→ BBR 更适合）")
