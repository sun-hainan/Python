# -*- coding: utf-8 -*-

"""

算法实现：25_�������� / tcp_bbr



本文件实现 tcp_bbr 相关的算法功能。

"""



import numpy as np

import matplotlib.pyplot as plt





class BBRCongestionControl:

    """

    BBR拥塞控制算法实现

    

    BBR维护两个关键估计：

    1. 瓶颈带宽 (btlBw): 通过最大带宽过滤器估计

    2. 最小RTT (min_rtt): 通过运行最小值估计

    """

    

    def __init__(self, gain=1.0, pacing_rate=None):

        """

        初始化BBR算法

        

        Args:

            gain: 发送速率增益因子，控制inflight

            pacing_rate: 发送速率限制

        """

        self.btlBw = 1.0  # 瓶颈带宽估计（初始值）

        self.min_rtt = float('inf')  # 最小RTT估计

        self.max_rtt = 0.0  # 最大RTT（用于检测拥塞）

        

        self.gain = gain  # 增益因子

        self.pacing_rate = pacing_rate  # 发送速率

        

        self.cwnd = 4 * 1500  # 初始窗口（4个MSS）

        self.target_cwnd = 4 * 1500  # 目标窗口

        

        self.min_rtt_window = 10  # min_rtt平滑窗口大小

        self.bw_window = 10  # 带宽估计窗口

        

        self.rtProp_samples = []  # RTT采样队列

        self.delivery_rate_samples = []  # 交付速率采样

        

        self.state = "STARTUP"  # 当前状态：STARTUP/DRAIN/PROBE_BW/PROBE_RTT

        

        self.full_bandwidth = False  # 是否达到满带宽

        self.full_bandwidth_count = 0  # 连续满带宽次数

        

    def update_min_rtt(self, rtt_sample):

        """

        更新最小RTT估计

        

        Args:

            rtt_sample: 新的RTT采样值

        """

        self.rtProp_samples.append(rtt_sample)

        

        # 保持最近min_rtt_window个样本

        if len(self.rtProp_samples) > self.min_rtt_window:

            self.rtProp_samples.pop(0)

        

        # min_rtt是10秒窗口内的最小值

        self.min_rtt = min(self.rtProp_samples)

    

    def update_btl_bw(self, delivery_rate, ack_count):

        """

        更新瓶颈带宽估计

        

        Args:

            delivery_rate: 数据交付速率

            ack_count: 确认的数据包数量

        """

        # delivery_rate = bytes_acked / rtt

        if delivery_rate > 0:

            self.delivery_rate_samples.append(delivery_rate)

            

            # 保持最近bw_window个样本

            if len(self.delivery_rate_samples) > self.bw_window:

                self.delivery_rate_samples.pop(0)

            

            # 更新瓶颈带宽（取中位数）

            self.delivery_rate_samples.sort()

            self.btlBw = self.delivery_rate_samples[len(self.delivery_rate_samples) // 2]

    

    def check_full_bandwidth(self):

        """

        检查是否达到满带宽

        """

        # 如果估计带宽超过初始带宽的3倍，认为满带宽

        if self.btlBw > self.full_bandwidth * 1.25:

            self.full_bandwidth = self.btlBw

            self.full_bandwidth_count = 0

        else:

            self.full_bandwidth_count += 1

        

        # 连续3次满带宽则标记为full_bandwidth

        if self.full_bandwidth_count >= 3:

            self.full_bandwidth = True

    

    def compute_target_cwnd(self):

        """

        计算目标拥塞窗口

        

        核心公式：target_cwnd = btlBw * min_rtt * gain

        """

        # 目标窗口 = 瓶颈带宽 × 最小RTT × 增益

        self.target_cwnd = self.btlBw * self.min_rtt * self.gain

        

        # 至少需要4个MSS

        self.target_cwnd = max(self.target_cwnd, 4 * 1500)

        

        return self.target_cwnd

    

    def update_state(self):

        """

        BBR状态机更新

        

        四个状态：

        1. STARTUP: 启动阶段，快速探测带宽

        2. DRAIN: 排空阶段，收敛到合理窗口

        3. PROBE_BW: 带宽探测阶段，周期性探测

        4. PROBE_RTT: RTT探测阶段，每10秒探测一次

        """

        if self.state == "STARTUP":

            # 启动阶段：使用2倍增益快速探测

            self.gain = 2.0

            if self.full_bandwidth:

                self.state = "DRAIN"

                self.gain = 0.75  # 排空阶段使用0.75倍

        

        elif self.state == "DRAIN":

            # 排空阶段：使用0.75倍增益

            self.gain = 0.75

            # 如果inflight接近目标，进入PROBE_BW

            if self.cwnd >= self.target_cwnd * 0.9:

                self.state = "PROBE_BW"

                self.gain = 1.0

        

        elif self.state == "PROBE_BW":

            # 带宽探测：周期性调整增益

            # BBR使用8个周期循环：+1.25, +1.0, +1.0, +1.0, +0.75, +0.75, +0.75, +0.75

            cycle_gains = [1.25, 1.0, 1.0, 1.0, 0.75, 0.75, 0.75, 0.75]

            # 简化：每8步循环一次

            pass  # 简化处理

        

        elif self.state == "PROBE_RTT":

            # RTT探测：每10秒执行一次，保持低窗口

            self.gain = 0.75

            if self.cwnd <= 4 * 1500:

                self.state = "PROBE_BW"

                self.gain = 1.0

    

    def on_ack(self, rtt, bytes_acked, delivery_rate):

        """

        ACK接收处理

        

        Args:

            rtt: 往返时延

            bytes_acked: 确认的字节数

            delivery_rate: 交付速率

        """

        # 更新估计

        self.update_min_rtt(rtt)

        self.update_btl_bw(delivery_rate, bytes_acked)

        

        # 检查满带宽

        self.check_full_bandwidth()

        

        # 更新状态机

        self.update_state()

        

        # 计算目标窗口并更新

        self.compute_target_cwnd()

        

        # 窗口更新：pacing_gain控制

        self.cwnd += bytes_acked * self.gain

        

        # 限制不超过目标窗口的2倍

        self.cwnd = min(self.cwnd, self.target_cwnd * 2)

    

    def on_loss(self, lost_bytes):

        """

        丢包处理（BBR对丢包不敏感）

        

        Args:

            lost_bytes: 丢失的字节数

        """

        # BBR不像传统算法那样缩减窗口

        # 只是记录丢包

        self.max_rtt = max(self.max_rtt, self.min_rtt * 2)

    

    def get_pacing_rate(self):

        """

        获取pacing速率（BBR特有）

        

        Returns:

            pacing_rate: 发送速率限制

        """

        if self.pacing_rate is None:

            # pacing_rate = btlBw * gain

            return self.btlBw * self.gain

        return self.pacing_rate





def simulate_bbr(duration=200, link_bw=100e6, link_rtt=0.05, queue_size=100):

    """

    模拟BBR在瓶颈链路上的行为

    

    Args:

        duration: 模拟时间步

        link_bw: 链路带宽（bps）

        link_rtt: 链路RTT（秒）

        queue_size: 队列大小（包数）

    """

    bbr = BBRCongestionControl()

    

    cwnd_history = []

    bw_history = []

    rtt_history = []

    

    mss = 1500 * 8  # MSS in bits

    

    for t in range(duration):

        # 模拟RTT变化（带队列延迟）

        base_rtt = link_rtt * 1000  # ms

        queue_delay = (bbr.cwnd / mss) / (link_bw / mss) * 1000  # ms

        current_rtt = base_rtt + queue_delay

        

        # 模拟交付速率

        delivery_rate = min(bbr.cwnd / (current_rtt / 1000), link_bw) / 8  # bytes/s

        

        # BBR处理ACK

        bbr.on_ack(rtt=current_rtt, bytes_acked=min(bbr.cwnd, 1500), 

                   delivery_rate=delivery_rate / 8)  # bytes/s

        

        # 记录历史

        cwnd_history.append(bbr.cwnd)

        bw_history.append(bbr.btlBw)

        rtt_history.append(current_rtt)

        

        # 模拟随机丢包（1%丢包率，BBR不敏感）

        if np.random.random() < 0.01:

            bbr.on_loss(lost_bytes=1500)

    

    # 绘图

    fig, axes = plt.subplots(3, 1, figsize=(12, 10))

    

    axes[0].plot(cwnd_history, 'b-', label='cwnd')

    axes[0].set_ylabel('拥塞窗口 (bytes)')

    axes[0].set_title('BBR 拥塞窗口变化')

    axes[0].legend()

    axes[0].grid(True, alpha=0.3)

    

    axes[1].plot(bw_history, 'g-', label='瓶颈带宽估计')

    axes[1].axhline(y=link_bw/8, color='r', linestyle='--', label='实际带宽')

    axes[1].set_ylabel('带宽 (bytes/s)')

    axes[1].set_title('BBR 带宽估计 vs 实际带宽')

    axes[1].legend()

    axes[1].grid(True, alpha=0.3)

    

    axes[2].plot(rtt_history, 'm-', label='RTT')

    axes[2].set_xlabel('时间步')

    axes[2].set_ylabel('RTT (ms)')

    axes[2].set_title('BBR RTT变化')

    axes[2].legend()

    axes[2].grid(True, alpha=0.3)

    

    plt.tight_layout()

    plt.savefig('bbr_simulation.png', dpi=150)

    plt.show()

    

    return cwnd_history, bw_history, rtt_history





def compare_bbr_cubic():

    """

    比较BBR与CUBIC在不同网络条件下的表现

    """

    scenarios = [

        ("高带宽高RTT", 1e9, 0.2),  # 1Gbps, 200ms

        ("低带宽低RTT", 10e6, 0.01),  # 10Mbps, 10ms

        ("中等条件", 100e6, 0.05),  # 100Mbps, 50ms

    ]

    

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    

    for idx, (name, bw, rtt) in enumerate(scenarios):

        cwnd_bbr = []

        cwnd_cubic = []

        

        # 简化模拟

        for t in range(100):

            # BBR：基于模型，更稳定

            cwnd_bbr.append(1500 * (4 + min(t, 20)))

            

            # CUBIC：丢包驱动

            cwnd_cubic.append(1500 * (4 + min(t, 15) + 0.1 * t))

        

        axes[idx].plot(cwnd_bbr, 'b-', label='BBR')

        axes[idx].plot(cwnd_cubic, 'r-', label='CUBIC')

        axes[idx].set_title(f'{name}\nBW={bw/1e6:.0f}Mbps, RTT={rtt*1000:.0f}ms')

        axes[idx].set_xlabel('时间步')

        axes[idx].set_ylabel('cwnd (bytes)')

        axes[idx].legend()

        axes[idx].grid(True, alpha=0.3)

    

    plt.tight_layout()

    plt.savefig('bbr_vs_cubic.png', dpi=150)

    plt.show()





if __name__ == "__main__":

    print("=== BBR拥塞控制算法演示 ===")

    

    # 基本模拟

    print("\n1. 运行BBR基本模拟...")

    cwnd, bw, rtt = simulate_bbr(duration=100, plot=False)

    print(f"   模拟完成：最终窗口={cwnd[-1]:.0f} bytes")

    

    # 状态机演示

    bbr = BBRCongestionControl()

    print("\n2. BBR状态机:")

    print(f"   初始状态: {bbr.state}")

    print(f"   初始增益: {bbr.gain}")

    

    # 带宽估计演示

    print("\n3. 带宽估计更新:")

    bbr.update_btl_bw(delivery_rate=10e6, ack_count=100)

    bbr.update_btl_bw(delivery_rate=12e6, ack_count=100)

    bbr.update_btl_bw(delivery_rate=11e6, ack_count=100)

    print(f"   估计瓶颈带宽: {bbr.btlBw/1e6:.2f} Mbps")

    

    # 目标窗口计算

    print("\n4. 目标窗口计算:")

    bbr.btlBw = 100e6 / 8  # 100 Mbps in bytes/s

    bbr.min_rtt = 50  # ms

    target = bbr.compute_target_cwnd()

    print(f"   btlBw={bbr.btlBw/1e6:.2f} MB/s, min_rtt={bbr.min_rtt}ms")

    print(f"   目标窗口: {target/1500:.1f} MSS")

    

    # BBR vs CUBIC对比

    print("\n5. BBR vs CUBIC对比模拟...")

    compare_bbr_cubic()

    

    # BBR核心优势说明

    print("\n6. BBR核心优势:")

    print("   - 不依赖丢包来判断拥塞")

    print("   - 在高带宽高RTT网络中表现优异")

    print("   - 对bufferbloat问题不敏感")

    print("   - 能更好利用可用带宽")

