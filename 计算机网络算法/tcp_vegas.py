# -*- coding: utf-8 -*-
"""
算法实现：计算机网络算法 / tcp_vegas

本文件实现 tcp_vegas 相关的算法功能。
"""

import math


class TCPVegas:
    """TCP Vegas 拥塞控制算法类"""

    def __init__(self, mss=1460, alpha=2, beta=4, gamma=1):
        # mss: 最大段大小（字节）
        self.mss = mss
        # alpha: 窗口调整下界阈值（包数）
        self.alpha = alpha
        # beta: 窗口调整上界阈值（包数）
        self.beta = beta
        # gamma: 调整因子
        self.gamma = gamma
        # cwnd: 拥塞窗口（字节）
        self.cwnd = mss * 10
        # ssthresh: 慢启动阈值
        self.ssthresh = float('inf')
        # base_rtt: 基准 RTT（无拥塞时的最小 RTT）
        self.base_rtt = float('inf')
        # rtt: 当前 RTT
        self.rtt = 0
        # diff: Expected - Actual（队列长度估计）
        self.diff = 0
        # 上次窗口更新时的 cwnd
        self.cwnd_actual = 0
        # 是否已记录 base_rtt
        self.base_rtt_recorded = False
        # RTT 采样计数
        self.rtt_sample_count = 0

    def _update_diff(self):
        """
        计算 Vegas diff = cwnd/BaseRTT - cwnd/RTT
        
        这表示"在飞"数据包中排队的数据包数量
        """
        if self.rtt > 0 and self.base_rtt < float('inf'):
            # Expected: 理想情况下一个 RTT 能处理的数据量 / BaseRTT
            expected = self.cwnd / self.base_rtt
            # Actual: 实际吞吐量
            actual = self.cwnd / self.rtt
            # diff 表示排队的数据包数
            self.diff = (expected - actual) * self.base_rtt / self.mss
        else:
            self.diff = 0

    def on_rtt_update(self, rtt):
        """
        更新 RTT 测量值
        
        参数:
            rtt: 测量的 RTT（秒）
        """
        self.rtt = rtt
        self.rtt_sample_count += 1
        
        # 更新 base_rtt（前几个 RTT 的最小值）
        if not self.base_rtt_recorded or rtt < self.base_rtt:
            self.base_rtt = rtt
            if self.rtt_sample_count >= 3:
                self.base_rtt_recorded = True
        
        self._update_diff()

    def on_ack(self, ack_bytes):
        """
        处理 ACK，更新窗口
        
        参数:
            ack_bytes: 确认的字节数
        """
        if self.cwnd < self.ssthresh:
            # 慢启动阶段：指数增长
            self.cwnd += self.mss
        else:
            # 拥塞避免阶段：根据 Vegas diff 调整
            self._adjust_window()

    def _adjust_window(self):
        """
        根据 Vegas diff 调整窗口大小
        
        diff < alpha: 增长窗口（网络空闲）
        diff > beta: 减小窗口（队列增长）
        alpha <= diff <= beta: 保持窗口
        """
        if self.diff < self.alpha:
            # 网络空闲，增加窗口
            self.cwnd += self.gamma * self.mss * self.mss / self.cwnd
        elif self.diff > self.beta:
            # 队列增长，减小窗口
            self.cwnd -= self.gamma * self.mss * (self.diff - self.alpha) / self.cwnd
        # alpha <= diff <= beta: 保持不变
        
        # 确保窗口不小于一个 MSS
        self.cwnd = max(self.cwnd, self.mss)

    def on_loss(self):
        """
        处理丢包事件（Vegas 假设丢包是拥塞信号）
        """
        self.ssthresh = self.cwnd / 2
        self.cwnd = max(self.cwnd / 2, self.mss)

    def on_timeout(self):
        """
        处理超时事件
        """
        self.ssthresh = self.cwnd / 2
        self.cwnd = self.mss
        # 重置 base_rtt（网络条件可能已变化）
        self.base_rtt = float('inf')
        self.base_rtt_recorded = False

    def get_cwnd(self):
        """返回当前拥塞窗口（字节）"""
        return self.cwnd

    def get_cwnd_packets(self):
        """返回当前拥塞窗口（包数）"""
        return self.cwnd / self.mss

    def get_diff(self):
        """返回当前 diff 值（队列估计）"""
        return self.diff

    def get_base_rtt(self):
        """返回基准 RTT（秒）"""
        return self.base_rtt if self.base_rtt < float('inf') else 0


if __name__ == "__main__":
    # 测试 TCP Vegas 算法
    vegas = TCPVegas(mss=1460, alpha=2, beta=4)
    
    print("=== TCP Vegas 算法测试 ===")
    print(f"初始窗口: {vegas.get_cwnd_packets():.1f} 包")
    
    # 模拟慢启动
    print("\n--- 慢启动阶段 ---")
    for i in range(6):
        vegas.cwnd = min(vegas.cwnd * 2, vegas.ssthresh if vegas.ssthresh != float('inf') else float('inf'))
        vegas.rtt = 0.05  # 假设 RTT = 50ms
        print(f"RTT {i+1}: cwnd={vegas.get_cwnd_packets():.1f} 包")
    
    # 进入拥塞避免
    vegas.ssthresh = vegas.cwnd / 2
    vegas.base_rtt = 0.05  # 记录基准 RTT
    
    print(f"\n进入拥塞避免，ssthresh={vegas.ssthresh/1460:.1f} 包")
    
    # 模拟拥塞避免（不同 RTT 条件）
    print("\n--- 拥塞避免阶段（不同 RTT）---")
    rtt_scenarios = [0.050, 0.060, 0.055, 0.070, 0.080, 0.065, 0.052, 0.051]
    for i, rtt in enumerate(rtt_scenarios):
        vegas.on_rtt_update(rtt)
        # 模拟每 RTT 确认所有数据
        vegas.on_ack(vegas.cwnd)
        print(f"场景 {i+1}: RTT={rtt*1000:.0f}ms, diff={vegas.get_diff():.2f}, "
              f"cwnd={vegas.get_cwnd_packets():.2f} 包")
    
    print(f"\n基准 RTT: {vegas.get_base_rtt()*1000:.0f} ms")
    
    # 模拟丢包
    print("\n--- 丢包事件 ---")
    vegas.on_loss()
    print(f"丢包后: cwnd={vegas.get_cwnd_packets():.1f} 包")
    
    # 模拟超时
    print("\n--- 超时事件 ---")
    vegas.cwnd = 50 * vegas.mss
    vegas.on_timeout()
    print(f"超时后: cwnd={vegas.get_cwnd_packets():.1f} 包, base_rtt 重置")
