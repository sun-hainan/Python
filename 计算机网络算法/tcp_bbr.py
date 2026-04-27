# -*- coding: utf-8 -*-
"""
算法实现：计算机网络算法 / tcp_bbr

本文件实现 tcp_bbr 相关的算法功能。
"""

import time
import collections


class TCPBBR:
    """TCP BBR 拥塞控制算法类"""

    def __init__(self, mss=1460):
        # mss: 最大段大小（字节）
        self.mss = mss
        # btlBw: 测量到的瓶颈带宽（字节/秒）
        self.btlBw = 0
        # min_rtt: 测量的最小 RTT（秒）
        self.min_rtt = float('inf')
        # RTT 采样队列（用于平滑）
        self.rtt_queue = collections.deque(maxlen=100)
        # 带宽采样队列
        self.bw_queue = collections.deque(maxlen=100)
        # pacing_rate: 发送速率（字节/秒），初始设为 1.4x 初始带宽
        self.pacing_rate = self.mss * 10  # 初始化
        # cwnd: 拥塞窗口（字节）
        self.cwnd = self.mss * 10
        # 上次带宽更新时间
        self.last_update = time.time()
        # 状态机状态
        self.state = "STARTUP"  # STARTUP, DRAIN, PROBE_BW, PROBE_RTT
        # 探测 RTT 状态持续时间
        self.probe_rtt_start = 0
        # 带宽增长倍数（用于 STARTUP 阶段）
        self.bw_growth_factor = 1.0

    def _update_rtt(self, rtt):
        """
        更新 RTT 测量值
        
        参数:
            rtt: 测量的 RTT（秒）
        """
        self.rtt_queue.append(rtt)
        # 使用滑动窗口最小值作为 min_rtt
        if len(self.rtt_queue) >= 10:
            self.min_rtt = min(self.rtt_queue)
        else:
            self.min_rtt = min(self.min_rtt, rtt)

    def _update_bw(self, bytes_acked, rtt):
        """
        更新带宽估计
        
        参数:
            bytes_acked: 确认的字节数
            rtt: 对应的 RTT
        """
        if rtt > 0:
            bw = bytes_acked / rtt  # 字节/秒
            self.bw_queue.append(bw)
            # 使用中位数带宽
            sorted_bws = sorted(self.bw_queue)
            if len(sorted_bws) >= 4:
                self.btlBw = sorted_bws[len(sorted_bws) // 2]
            else:
                self.btlBw = max(self.btlBw, bw)

    def _update_pacing_rate(self):
        """
        根据当前状态更新 pacing_rate
        """
        if self.state == "STARTUP":
            # STARTUP 阶段：每 8 个 RTT 检查带宽是否增长 < 25%
            self.pacing_rate = self.btlBw * 2.0  # 2x 带宽
        elif self.state == "DRAIN":
            # DRAIN 阶段：降低发送速率至 0.75x 带宽
            self.pacing_rate = self.btlBw * 0.75
        elif self.state == "PROBE_BW":
            # PROBE_BW：周期性地略微增加带宽探测
            cycle_pos = (time.time() // 1.0) % 8
            if cycle_pos < 2:
                self.pacing_rate = self.btlBw * 1.25  # 探测
            elif cycle_pos < 5:
                self.pacing_rate = self.btlBw  # 正常
            else:
                self.pacing_rate = self.btlBw * 0.9  # 略降
        elif self.state == "PROBE_RTT":
            # PROBE_RTT：大幅降低速率
            self.pacing_rate = self.mss * 4

    def on_ack(self, bytes_acked, rtt):
        """
        处理 ACK 事件，更新状态机
        
        参数:
            bytes_acked: 确认的字节数
            rtt: 当前 RTT 估计（秒）
        """
        self._update_rtt(rtt)
        self._update_bw(bytes_acked, rtt)
        self._update_pacing_rate()

        # 状态转换逻辑
        elapsed = time.time() - self.last_update

        if self.state == "STARTUP":
            # 检查带宽是否增长缓慢（3个RTT内增长<25%）
            if elapsed > rtt * 8 and self.btlBw > 0:
                if self.bw_growth_factor < 1.25:
                    self.state = "DRAIN"
                    self.bw_growth_factor = 1.0

        elif self.state == "DRAIN":
            # inflight 降到目标以下后转入 PROBE_BW
            if elapsed > rtt * 10:
                self.state = "PROBE_BW"

        elif self.state == "PROBE_BW":
            # 每 10 秒尝试 PROBE_RTT
            if elapsed > 10.0 and self.min_rtt < float('inf'):
                self.state = "PROBE_RTT"
                self.probe_rtt_start = time.time()

        elif self.state == "PROBE_RTT":
            # PROBE_RTT 持续 200ms
            if time.time() - self.probe_rtt_start > 0.2:
                self.state = "PROBE_BW"

        # 更新 cwnd
        # BBR 的 cwnd 目标是维持适当数量的在飞数据
        target_cwnd = self.btlBw * self.min_rtt if self.min_rtt < float('inf') else self.cwnd
        self.cwnd = min(self.cwnd + bytes_acked, target_cwnd * 1.5)

    def on_loss(self, bytes_lost):
        """
        处理丢包事件（BBR 不依赖丢包做拥塞检测，但记录丢包）
        
        参数:
            bytes_lost: 丢失的字节数
        """
        # BBR 算法本身不直接对丢包做出反应
        # 丢包由上层重传机制处理
        pass

    def get_cwnd(self):
        """返回当前拥塞窗口（字节）"""
        return self.cwnd

    def get_pacing_rate(self):
        """返回当前发送速率（字节/秒）"""
        return self.pacing_rate

    def get_state(self):
        """返回当前状态"""
        return self.state


if __name__ == "__main__":
    # 测试 TCP BBR 算法
    bbr = TCPBBR(mss=1460)
    
    print("=== TCP BBR 算法测试 ===")
    print(f"初始状态: {bbr.get_state()}")
    
    # 模拟一些 ACK
    for i in range(20):
        rtt = 0.05 + (i % 5) * 0.01  # 模拟 RTT 变化 50-90ms
        bytes_acked = bbr.mss * 10
        bbr.on_ack(bytes_acked, rtt)
        
        if i % 5 == 0:
            print(f"ACK {i+1}: 状态={bbr.get_state()}, "
                  f"带宽={bbr.btlBw/1e6:.2f} MB/s, "
                  f"min_rtt={bbr.min_rtt*1000:.1f}ms, "
                  f"cwnd={bbr.get_cwnd()/1460:.1f} 包")
    
    print(f"\n最终状态: {bbr.get_state()}")
    print(f"瓶颈带宽估计: {bbr.btlBw/1e6:.2f} MB/s")
    print(f"最小 RTT 估计: {bbr.min_rtt*1000:.1f} ms")
