# -*- coding: utf-8 -*-
"""
算法实现：计算机网络算法 / tcp_congestion

本文件实现 tcp_congestion 相关的算法功能。
"""

import math
import random


class CongestionControlFramework:
    """
    拥塞控制算法通用框架
    抽象了所有标准 TCP 拥塞控制算法的共同行为
    """

    # 标准 TCP 参数
    MSS = 1460
    INIT_CWND = 4 * MSS          # RFC 6928 建议初始窗口 10 MSS
    INIT_SSTHRESH = 65535
    TIMEOUT_SSTHRESH_FACTOR = 0.5

    def __init__(self, name='TCP'):
        self.name = name
        self.cwnd = self.INIT_CWND           # 拥塞窗口
        self.ssthresh = self.INIT_SSTHRESH  # 慢启动阈值
        self.rwnd = float('inf')             # 接收窗口
        self.una = 0                          # 最早未确认字节
        self.seq = 0                          # 下一个发送字节
        # 状态
        self.state = 'slow_start'
        self.dup_acks = 0
        self.recover = 0
        self.mss = self.MSS
        # 事件统计
        self.events = []  # (time, event_type, cwnd, ssthresh)

    def get_window(self):
        return min(self.cwnd, self.rwnd)

    def get_cwnd_mss(self):
        return self.cwnd / self.mss

    def send(self, data_size):
        """尝试发送数据"""
        return min(data_size, self.get_window())

    def ack_received(self, ack_bytes):
        """ACK 到达"""
        if self.state == 'slow_start':
            self.cwnd += min(ack_bytes, self.mss)
            if self.cwnd >= self.ssthresh:
                self.state = 'congestion_avoidance'

        elif self.state == 'congestion_avoidance':
            # 每确认一个 MSS 的数据，cwnd 增加 (MSS^2 / cwnd)
            self.cwnd += (self.mss * self.mss) / self.cwnd

        elif self.state == 'fast_recovery':
            if ack_bytes >= self.recover:
                # 退出快速恢复
                self.cwnd = self.ssthresh
                self.state = 'congestion_avoidance'
            else:
                self.cwnd += self.mss

    def dup_ack(self):
        """重复 ACK"""
        self.dup_acks += 1
        if self.dup_acks == 3:
            # 3 DupACK：触发快速重传
            self.ssthresh = max(self.cwnd * 0.5, 2 * self.mss)
            self.cwnd = self.ssthresh + 3 * self.mss
            self.state = 'fast_recovery'
            return 'retransmit'
        elif self.dup_acks > 3:
            self.cwnd += self.mss
        return None

    def timeout(self):
        """超时"""
        self.ssthresh = max(self.cwnd * self.TIMEOUT_SSTHRESH_FACTOR, 2 * self.mss)
        self.cwnd = self.mss
        self.state = 'slow_start'
        self.dup_acks = 0


class TCPTahoe(CongestionControlFramework):
    """TCP Tahoe：最早的完整拥塞控制（1988）"""

    def __init__(self):
        super().__init__('TCP Tahoe')
        # Tahoe vs Reno 的区别：Tahoe 没有快速恢复
        # Tahoe 在快速重传后进入慢启动（而非 Reno 的快速恢复）
        self.state = 'slow_start'

    def dup_ack(self):
        """Tahoe：快速重传后进入慢启动"""
        self.dup_acks += 1
        if self.dup_acks == 3:
            self.ssthresh = max(self.cwnd * 0.5, 2 * self.mss)
            self.cwnd = self.ssthresh
            self.state = 'slow_start'
            return 'retransmit'
        return None


class TCPBIC(CongestionControlFramework):
    """
    TCP BIC（Binary Increase Congestion Control）
    Linux 2.6.8 - 2.6.18 的默认算法
    核心思想：使用二分搜索来找到丢包前的窗口值（Max）
    窗口增长曲线接近线性，避免过冲
    """

    def __init__(self):
        super().__init__('TCP BIC')
        self.W_max = self.INIT_SSTHRESH
        self.W_min = self.ssthresh
        self.cwnd = self.INIT_CWND
        self.S_max = 32   # 最大增长步长
        self.S_min = 1    # 最小增长步长
        self.beta = 0.8   # 丢包后的乘性减因子

    def on_loss(self):
        """丢包事件：更新 W_max，减小 cwnd"""
        self.W_max = self.cwnd
        self.W_min = max(self.W_max * self.beta, self.cwnd)
        self.cwnd = self.W_max * self.beta
        self.ssthresh = self.cwnd

    def ack_received(self, ack_bytes):
        """BIC 窗口增长"""
        if self.cwnd < self.W_max:
            # 在 W_min 和 W_max 之间：二分搜索增长
            # 增长量 = S_max * (k - current_k)
            # k = (W_max - W_min) / 2
            target = (self.W_max + self.W_min) / 2
            delta = abs(target - self.cwnd)
            inc = min(self.S_max, max(self.S_min, delta / 8))
            if self.cwnd < target:
                self.cwnd += inc
            else:
                self.cwnd -= inc
        else:
            # 超过 W_max：进入探索阶段
            self.cwnd += self.S_max


class TCPWestwood(CongestionControlFramework):
    """
    TCP Westwood：基于带宽估计的拥塞控制
    核心思想：丢包后不将窗口减半，而是根据估计的可用带宽减少窗口
    适合无线网络（丢包不一定代表拥塞）
    """

    def __init__(self):
        super().__init__('TCP Westwood')
        self.bw_estimate = 0.0  # 估计的可用带宽
        self.rtt_base = float('inf')
        self.sample_bw = []

    def update_bw_estimate(self, acked_bytes, rtt):
        """根据 ACK 更新带宽估计"""
        if rtt > 0:
            sample = acked_bytes / rtt
            self.sample_bw.append(sample)
            if len(self.sample_bw) > 5:
                self.sample_bw.pop(0)
            self.bw_estimate = sum(self.sample_bw) / len(self.sample_bw)

    def on_loss(self):
        """Westwood 的乘性减：根据估计带宽调整窗口"""
        if self.bw_estimate > 0:
            # 窗口 = 估计带宽 × min RTT
            self.cwnd = max(self.bw_estimate * self.rtt_base, self.mss)
        else:
            self.cwnd = max(self.cwnd * 0.5, 2 * self.mss)
        self.ssthresh = self.cwnd


class AIMDFairness:
    """
    AIMD（加性增乘性减）公平性分析
    AIMD 收敛到 max-min 公平：各流最终获得相同带宽
    """

    @staticmethod
    def simulate_aimd(num_flows=2, num_rounds=20,
                     alpha=1.0, beta=0.5):
        """
        模拟 AIMD 过程
        alpha: 加性增量
        beta: 乘性减因子
        """
        cwnds = [10.0] * num_flows  # 初始窗口

        history = [cwnds[:]]
        for r in range(num_rounds):
            # 加性增
            for i in range(num_flows):
                cwnds[i] += alpha

            # 随机选择一个流丢包
            drop_flow = random.randint(0, num_flows - 1)
            cwnds[drop_flow] *= beta

            history.append(cwnds[:])

        return history

    @staticmethod
    def compute_fairness_index(cwnds):
        """
        Jain's Fairness Index
        F = (sum x_i)^2 / (n * sum x_i^2)
        范围 [1/n, 1]，1 表示完全公平
        """
        n = len(cwnds)
        if n == 0:
            return 0
        num = sum(cwnds) ** 2
        den = n * sum(x ** 2 for x in cwnds)
        if den == 0:
            return 0
        return num / den


if __name__ == '__main__':
    print("TCP 拥塞控制综合算法框架演示")
    print("=" * 60)

    # 模拟慢启动和拥塞避免过程
    cc = CongestionControlFramework('TCP Reno')
    cc.ssthresh = 20 * cc.mss

    print("\n【慢启动 -> 拥塞避免 -> 丢包 -> 快速恢复】")
    print(f"  初始 cwnd = {cc.INIT_CWND/cc.mss:.0f} MSS, ssthresh = {cc.ssthresh/cc.mss:.0f} MSS")
    print()

    history = []
    print(f"  {'轮次':<6} {'cwnd(MSS)':<15} {'ssthresh(MSS)':<15} {'状态':<20}")
    print("  " + "-" * 60)

    for i in range(25):
        if cc.state == 'slow_start':
            cc.cwnd += cc.mss  # 每 ACK 增加 1 MSS（每 RTT 翻倍）
        elif cc.state == 'congestion_avoidance':
            cc.cwnd += cc.mss * cc.mss / cc.cwnd  # 每 RTT 增加 1 MSS
        elif cc.state == 'fast_recovery':
            cc.cwnd += cc.mss  # 每额外 DupACK 增加 1 MSS

        history.append(cc.get_cwnd_mss())

        if i == 0:
            cc.state = 'congestion_avoidance'
            cc.ssthresh = cc.cwnd / 2
        if i == 5:
            cc.state = 'slow_start'
            cc.ssthresh = cc.cwnd
        if i == 10:
            cc.state = 'fast_recovery'
            cc.cwnd = cc.ssthresh + 3 * cc.mss

        if i % 3 == 0:
            print(f"  {i+1:<6} {cc.get_cwnd_mss():<15.2f} "
                  f"{cc.ssthresh/cc.mss:<15.2f} {cc.state:<20}")

    print("\n  [模拟在第6轮进入快速恢复...]")

    print("\n" + "=" * 60)
    print("【TCP 变种算法对比】")

    algorithms = [
        ("Tahoe", "慢启动+快速重传，无快速恢复（激进）"),
        ("Reno", "Tahoe + 快速恢复（平衡）"),
        ("NewReno", "Reno 改进，支持一个 RTT 内恢复多丢包"),
        ("BIC", "二分搜索增长，Linux 2.6.8 默认"),
        ("CUBIC", "三次多项式，增长曲线平滑，高 BDP 网络最优"),
        ("BBR", "基于模型，非丢包驱动，数据中心首选"),
        ("Westwood", "带宽估计，适合无线网络"),
    ]

    for name, desc in algorithms:
        print(f"  {name:<10}: {desc}")

    print("\n【AIMD 公平性分析】")
    print("  AIMD 最终收敛到公平点：所有流获得相同带宽")
    history = AIMDFairness.simulate_aimd(num_flows=3, num_rounds=15, alpha=1.0, beta=0.5)
    print(f"  最终窗口: {[f'{c:.1f}' for c in history[-1]]}")
    fi = AIMDFairness.compute_fairness_index(history[-1])
    print(f"  Jain 公平性指数: {fi:.4f} (1.0 = 完全公平)")
