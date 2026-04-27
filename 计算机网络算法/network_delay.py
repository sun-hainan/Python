# -*- coding: utf-8 -*-
"""
算法实现：计算机网络算法 / network_delay

本文件实现 network_delay 相关的算法功能。
"""

import random
import math


class RTTEstimator:
    """
    TCP RTT 估计器（基于 RFC 6298）
    使用指数加权移动平均（EWMA）
    EstimatedRTT = (1 - α) × EstimatedRTT + α × SampleRTT
    Timeout = 4 × EstimatedRTT（早期标准）
    """

    # α = 1/8 = 0.125（RFC 6298 推荐值）
    # β = 1/4 = 0.25（早期标准，用于 DevRTT）
    ALPHA = 0.125
    BETA = 0.25

    def __init__(self):
        self.estimated_rtt = None  # 初始为空
        self.dev_rtt = 0.0          # RTT 偏差估计
        self.sample_history = []
        self.max_history = 8

    def sample(self, sample_rtt):
        """
        记录一个 RTT 采样
        sample_rtt: 测量得到的 RTT（秒）
        """
        if sample_rtt <= 0:
            return

        self.sample_history.append(sample_rtt)
        if len(self.sample_history) > self.max_history:
            self.sample_history.pop(0)

        if self.estimated_rtt is None:
            # 第一次采样：直接使用
            self.estimated_rtt = sample_rtt
        else:
            # EWMA 更新
            self.estimated_rtt = (1 - self.ALPHA) * self.estimated_rtt + self.ALPHA * sample_rtt

        # 更新 DevRTT = (1 - β) × DevRTT + β × |SampleRTT - EstimatedRTT|
        self.dev_rtt = (1 - self.BETA) * self.dev_rtt + self.BETA * abs(sample_rtt - self.estimated_rtt)

    def get_rtt(self):
        """获取当前估计的 RTT"""
        return self.estimated_rtt

    def get_timeout(self):
        """
        获取超时值
        Timeout = EstimatedRTT + 4 × DevRTT
        """
        if self.estimated_rtt is None:
            return 1.0
        return self.estimated_rtt + 4 * self.dev_rtt

    def get_stats(self):
        return {
            'estimated_rtt_ms': self.estimated_rtt * 1000 if self.estimated_rtt else 0,
            'dev_rtt_ms': self.dev_rtt * 1000,
            'timeout_ms': self.get_timeout() * 1000,
            'sample_count': len(self.sample_history),
        }


class KalmanFilterRTT:
    """
    使用 Kalman 滤波进行 RTT 估计
    比 EWMA 更好地跟踪 RTT 的动态变化
    动态噪声估计，更精确的自适应性能
    """

    def __init__(self, initial_rtt=0.1):
        self.x = initial_rtt  # 状态估计（秒）
        self.P = 0.1          # 估计误差方差
        self.Q = 0.001       # 过程噪声方差
        self.R = 0.01        # 测量噪声方差

    def update(self, measurement):
        """
        Kalman 滤波更新
        measurement: 新的 RTT 采样（秒）
        """
        # 预测步骤
        x_pred = self.x          # 状态预测（假设恒定速度）
        P_pred = self.P + self.Q # 误差方差预测

        # 更新步骤
        K = P_pred / (P_pred + self.R)  # Kalman 增益
        self.x = x_pred + K * (measurement - x_pred)  # 状态更新
        self.P = (1 - K) * P_pred           # 协方差更新

        # 自适应调整过程噪声
        innovation = abs(measurement - x_pred)
        if innovation > 3 * math.sqrt(self.P):
            self.Q = min(self.Q * 2, 0.1)  # 增加不确定性

        return self.x

    def estimate(self):
        return self.x


class JitterEstimator:
    """
    抖动（Jitter）估计器
    抖动 = 连续 RTT 之间的差异
    用于：
      - 实时流（WebRTC）的自适应播放缓冲
      - 网络质量监控
      - AQM 参数调优
    """

    def __init__(self, smoothing_factor=0.01):
        self.smoothing = smoothing_factor
        self.jitter_ewma = 0.0
        self.last_rtt = None
        self.jitter_samples = []

    def update(self, sample_rtt):
        """更新抖动估计"""
        if self.last_rtt is None:
            self.last_rtt = sample_rtt
            return 0.0

        # 抖动 = |RTT_t - RTT_{t-1}|
        delta = abs(sample_rtt - self.last_rtt)
        self.last_rtt = sample_rtt

        # EWMA 平滑
        self.jitter_ewma = (1 - self.smoothing) * self.jitter_ewma + \
                            self.smoothing * delta

        self.jitter_samples.append(delta)
        return self.jitter_ewma

    def get_jitter_ms(self):
        return self.jitter_ewma * 1000


class PassiveRTTEstimator:
    """
    被动 RTT 估计：无需发送探测包
    通过观察 TCP 重传超时等事件来估计
    用于无法直接控制发送报文的场景
    """

    def __init__(self):
        self.ack_arrivals = []
        self.packet_departures = []
        self.estimated_rtt = 0.1

    def record_departure(self, seq, timestamp):
        """记录数据包发送"""
        self.packet_departures.append((seq, timestamp))

    def record_ack(self, ack_num, timestamp):
        """记录 ACK 到达"""
        self.ack_arrivals.append((ack_num, timestamp))

    def estimate_rtt(self):
        """
        被动估计 RTT
        通过匹配 ACK 和对应的数据包
        """
        for ack_seq, ack_time in reversed(self.ack_arrivals):
            for pkt_seq, pkt_time in reversed(self.packet_departures):
                if pkt_seq <= ack_seq:
                    rtt_estimate = ack_time - pkt_time
                    if 0 < rtt_estimate < 10.0:  # 合理范围
                        return rtt_estimate
        return None


if __name__ == '__main__':
    print("网络延迟估计算法演示")
    print("=" * 60)

    import random
    random.seed(42)

    # 模拟 RTT 数据（带噪声和变化）
    def generate_rtt_samples(n=30, base=0.05, noise=0.005):
        """生成模拟 RTT 采样"""
        samples = []
        for i in range(n):
            # 添加趋势和噪声
            trend = 0.0001 * i if i < 15 else -0.0002 * (i - 15)
            spike = 0.05 if random.random() < 0.05 else 0  # 偶尔尖峰
            sample = max(0.001, base + trend + random.gauss(0, noise) + spike)
            samples.append(sample)
        return samples

    samples = generate_rtt_samples(30)

    print("\n【TCP RTT 估计器（EWMA）】")
    rtt_est = RTTEstimator()

    print(f"{'样本#':<8} {'RTT(ms)':<12} {'EstRTT(ms)':<15} {'DevRTT(ms)':<15} {'Timeout(ms)'}")
    print("-" * 70)

    for i, s in enumerate(samples):
        rtt_est.sample(s)
        stats = rtt_est.get_stats()
        if i % 5 == 0 or i < 5:
            print(f"  {i+1:<6} {s*1000:<12.2f} "
                  f"{stats['estimated_rtt_ms']:<15.2f} "
                  f"{stats['dev_rtt_ms']:<15.4f} "
                  f"{stats['timeout_ms']:.1f}")

    print("\n" + "=" * 60)
    print("【Kalman 滤波 vs EWMA 对比】")

    kalman = KalmanFilterRTT(initial_rtt=samples[0])

    print(f"\n{'样本#':<8} {'RTT(ms)':<12} {'EWMA(ms)':<12} {'Kalman(ms)'}")
    print("-" * 45)

    for i, s in enumerate(samples):
        rtt_est.sample(s)
        kalman.update(s)
        if i % 5 == 0 or i < 5:
            print(f"  {i+1:<6} {s*1000:<12.2f} "
                  f"{rtt_est.get_rtt()*1000:<12.2f} "
                  f"{kalman.estimate()*1000:.2f}")

    print("\n" + "=" * 60)
    print("【抖动（Jitter）估计】")

    jitter = JitterEstimator()

    print(f"\nRTT 抖动估计（EWMA 平滑）：")
    for i, s in enumerate(samples[:15]):
        j = jitter.update(s)
        if i % 3 == 0:
            print(f"  样本 {i+1}: RTT={s*1000:.1f}ms, jitter={j*1000:.3f}ms")

    print("\n应用场景：")
    print("  1. TCP 拥塞控制：RTT 估计决定超时重传时间")
    print("  2. WebRTC：自适应播放缓冲（jitter buffer）")
    print("  3. CDN 选择：选择延迟最低的边缘节点")
    print("  4. 网络监控：NOC 实时 RTT 热力图")
    print("  5. BBR 拥塞控制：min_rtt 窗口估计带宽延迟积")
