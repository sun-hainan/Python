# -*- coding: utf-8 -*-

"""

算法实现：25_�������� / tcp_vegas



本文件实现 tcp_vegas 相关的算法功能。

"""



import numpy as np

import matplotlib.pyplot as plt





class TCPVegas:

    """

    TCP Vegas拥塞控制算法

    

    与Reno/CUBIC的区别：

    - Vegas基于RTT检测拥塞，而非丢包

    - 在队列堆积前就调整窗口

    - 更精细的拥塞控制

    """

    

    def __init__(self, mss=1500, alpha=2, beta=4):

        """

        初始化Vegas算法

        

        Args:

            mss: 最大报文段大小

            alpha: 下阈值，diff < alpha时增加窗口

            beta: 上阈值，diff > beta时减少窗口

        """

        self.mss = mss

        self.cwnd = mss  # 拥塞窗口

        self.base_rtt = float('inf')  # 最小RTT（基准RTT）

        self.current_rtt = 0  # 当前RTT

        

        self.alpha = alpha  # 下阈值

        self.beta = beta  # 上阈值

        

        self.ssthresh = float('inf')  # 慢启动阈值

        

        self.state = "SLOW_START"  # SLOW_START / CONGESTION_AVOID

        

        # 统计

        self.rtt_samples = []

        self.diff_history = []

        

    def _compute_diff(self):

        """

        计算Vegas的diff值

        

        diff = (cwnd / base_rtt) - (cwnd / current_rtt)

             = cwnd * (current_rtt - base_rtt) / (base_rtt * current_rtt)

        

        diff正比于队列中积压的数据包数量

        """

        if self.base_rtt == float('inf') or self.current_rtt == 0:

            return 0

        

        # 期望吞吐率 - 实际吞吐率（转换为packets/ms）

        expected = self.cwnd / self.base_rtt

        actual = self.cwnd / self.current_rtt

        diff = expected - actual

        

        # 归一化到数据包数量

        diff_packets = diff * self.current_rtt / self.mss

        

        return diff_packets

    

    def update_rtt(self, rtt_sample):

        """

        更新RTT样本

        

        Args:

            rtt_sample: 新的RTT测量值

        """

        self.current_rtt = rtt_sample

        self.rtt_samples.append(rtt_sample)

        

        # 更新base_rtt（每5个RTT更新一次，取最小值）

        if len(self.rtt_samples) >= 5:

            min_rtt = min(self.rtt_samples[-5:])

            self.base_rtt = min(self.base_rtt, min_rtt)

    

    def slow_start(self):

        """

        慢启动阶段

        

        Vegas的慢启动与Reno不同：

        - 每2个RTT将窗口翻倍

        - 当RTT超过base_rtt的1.5倍时退出慢启动

        """

        # 每收到一个ACK，窗口增加1个MSS

        self.cwnd += self.mss

        

        # 如果当前RTT超过base_rtt的1.5倍，退出慢启动

        if self.base_rtt != float('inf') and self.current_rtt > self.base_rtt * 1.5:

            self.ssthresh = self.cwnd

            self.state = "CONGESTION_AVOID"

    

    def congestion_avoidance(self):

        """

        拥塞避免阶段（Vegas核心算法）

        

        每个RTT根据diff调整窗口：

        - diff < alpha: 增加窗口（网络空闲）

        - alpha <= diff <= beta: 保持窗口（最优）

        - diff > beta: 减少窗口（队列积压）

        """

        diff = self._compute_diff()

        self.diff_history.append(diff)

        

        if diff < self.alpha:

            # 网络未充分利用，增加窗口

            self.cwnd += self.mss

        elif diff > self.beta:

            # 网络拥塞，减少窗口

            self.cwnd -= self.mss

        # alpha <= diff <= beta: 保持窗口不变

        

    def on_ack(self, rtt_sample, ack_bytes):

        """

        处理ACK事件

        

        Args:

            rtt_sample: RTT测量值

            ack_bytes: 确认的字节数

        """

        self.update_rtt(rtt_sample)

        

        if self.state == "SLOW_START":

            self.slow_start()

        elif self.state == "CONGESTION_AVOID":

            # 每经过一个RTT才调整一次窗口

            # 这里简化处理：每个ACK都尝试调整

            if ack_bytes >= self.cwnd * 0.9:  # 相当于一个RTT的确认

                self.congestion_avoidance()

    

    def on_timeout(self):

        """

        超时事件处理（作为备份）

        """

        self.ssthresh = self.cwnd / 2

        self.cwnd = self.mss

        self.base_rtt = float('inf')

        self.state = "SLOW_START"





def simulate_vegas(duration=200, link_rtt=50, background_traffic=0):

    """

    模拟Vegas在拥塞链路上的行为

    

    Args:

        duration: 模拟时间步

        link_rtt: 基础RTT（毫秒）

        background_traffic: 背景流量（影响RTT）

    """

    vegas = TCPVegas(alpha=2, beta=4)

    

    cwnd_history = []

    rtt_history = []

    diff_history = []

    

    for t in range(duration):

        # 模拟RTT变化（背景流量导致队列延迟）

        queue_delay = np.random.exponential(background_traffic)

        current_rtt = link_rtt + queue_delay * (vegas.cwnd / vegas.mss / 10)

        current_rtt = max(current_rtt, link_rtt)

        

        # Vegas处理ACK

        vegas.update_rtt(current_rtt)

        

        # 模拟每个时间步发送一些数据

        ack_bytes = min(vegas.cwnd, vegas.mss * 5)

        

        if vegas.state == "SLOW_START":

            vegas.slow_start()

        else:

            if t % 5 == 0:  # 每5步（模拟一个RTT）调整一次

                vegas.congestion_avoidance()

        

        # 记录

        cwnd_history.append(vegas.cwnd)

        rtt_history.append(current_rtt)

        diff_history.append(vegas.diff_history[-1] if vegas.diff_history else 0)

    

    # 绘图

    fig, axes = plt.subplots(3, 1, figsize=(12, 10))

    

    axes[0].plot(cwnd_history, 'b-', label='cwnd')

    axes[0].axhline(y=vegas.mss * (vegas.alpha + vegas.beta) / 2, 

                   color='g', linestyle='--', label='最优窗口估计')

    axes[0].set_ylabel('拥塞窗口 (bytes)')

    axes[0].set_title('TCP Vegas 拥塞窗口')

    axes[0].legend()

    axes[0].grid(True, alpha=0.3)

    

    axes[1].plot(rtt_history, 'r-', label='RTT')

    axes[1].axhline(y=link_rtt, color='g', linestyle='--', label='base_rtt')

    axes[1].set_ylabel('RTT (ms)')

    axes[1].set_title('RTT 变化')

    axes[1].legend()

    axes[1].grid(True, alpha=0.3)

    

    axes[2].plot(diff_history, 'm-', label='diff')

    axes[2].axhline(y=vegas.alpha, color='g', linestyle='--', label=f'alpha={vegas.alpha}')

    axes[2].axhline(y=vegas.beta, color='r', linestyle='--', label=f'beta={vegas.beta}')

    axes[2].set_xlabel('时间步')

    axes[2].set_ylabel('diff (packets)')

    axes[2].set_title('Vegas Diff 值')

    axes[2].legend()

    axes[2].grid(True, alpha=0.3)

    

    plt.tight_layout()

    plt.savefig('vegas_simulation.png', dpi=150)

    plt.show()

    

    return cwnd_history, rtt_history, diff_history





def compare_vegas_reno():

    """

    比较Vegas与Reno在不同场景下的表现

    """

    scenarios = [

        ("轻度拥塞", 0.0),  # 无额外延迟

        ("中度拥塞", 20.0),  # 20ms额外延迟

        ("严重拥塞", 50.0),  # 50ms额外延迟

    ]

    

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    

    for idx, (name, bg_traffic) in enumerate(scenarios):

        vegas = TCPVegas(alpha=2, beta=4)

        reno_cwnd = [1500]  # 简化Reno

        

        vegas_history = [vegas.cwnd]

        reno_history = [1500]

        reno_cwnd_val = 1500

        

        for t in range(150):

            # Vegas

            queue_delay = np.random.exponential(bg_traffic)

            rtt = 50 + queue_delay

            vegas.update_rtt(rtt)

            

            if t % 5 == 0:

                vegas.congestion_avoidance()

            vegas_history.append(vegas.cwnd)

            

            # Reno（简化）

            if reno_cwnd_val < float('inf'):

                reno_cwnd_val += 1500 * (1500 / reno_cwnd_val)

            if np.random.random() < 0.02:

                reno_cwnd_val = max(reno_cwnd_val / 2, 1500)

            reno_history.append(reno_cwnd_val)

        

        axes[idx].plot(vegas_history, 'b-', label='Vegas', alpha=0.7)

        axes[idx].plot(reno_history, 'r-', label='Reno', alpha=0.7)

        axes[idx].set_title(f'{name}\n背景延迟={bg_traffic:.0f}ms')

        axes[idx].set_xlabel('时间步')

        axes[idx].set_ylabel('cwnd (bytes)')

        axes[idx].legend()

        axes[idx].grid(True, alpha=0.3)

    

    plt.tight_layout()

    plt.savefig('vegas_vs_reno.png', dpi=150)

    plt.show()





def analyze_vegas_throughput():

    """

    分析Vegas的吞吐率与RTT关系

    """

    rtt_range = np.linspace(20, 200, 20)

    throughput_vegas = []

    throughput_reno = []

    

    for rtt in rtt_range:

        # Vegas吞吐率 = cwnd / RTT

        # Vegas尝试保持最优窗口

        optimal_cwnd = 4 * (rtt / 50) * 1500  # 假设最优是4个包

        throughput_vegas.append(optimal_cwnd / rtt * 1000)  # bytes/s

        

        # Reno吞吐率（简化）

        reno_cwnd = 1.5 * rtt * 1500

        throughput_reno.append(reno_cwnd / rtt * 1000)

    

    plt.figure(figsize=(10, 5))

    plt.plot(rtt_range, throughput_vegas, 'b-o', label='Vegas', alpha=0.7)

    plt.plot(rtt_range, throughput_reno, 'r-o', label='Reno', alpha=0.7)

    plt.xlabel('RTT (ms)')

    plt.ylabel('吞吐率 (bytes/s × 1000)')

    plt.title('Vegas vs Reno 吞吐率对比')

    plt.legend()

    plt.grid(True, alpha=0.3)

    plt.savefig('vegas_throughput.png', dpi=150)

    plt.show()





if __name__ == "__main__":

    print("=== TCP Vegas 拥塞控制算法演示 ===")

    

    # 基本模拟

    print("\n1. TCP Vegas 基本模拟:")

    vegas = TCPVegas(alpha=2, beta=4)

    for t in range(10):

        rtt = 50 + np.random.exponential(5)  # 50ms基础 + 抖动

        vegas.update_rtt(rtt)

        if t % 5 == 0:

            vegas.congestion_avoidance()

    print(f"   alpha={vegas.alpha}, beta={vegas.beta}")

    print(f"   模拟后窗口: {vegas.cwnd:.0f} bytes")

    

    # diff计算演示

    print("\n2. Vegas Diff 值计算:")

    vegas = TCPVegas()

    vegas.cwnd = 6000  # 4个MSS

    vegas.base_rtt = 50

    vegas.current_rtt = 60

    diff = vegas._compute_diff()

    print(f"   cwnd={vegas.cwnd}, base_rtt={vegas.base_rtt}, current_rtt={vegas.current_rtt}")

    print(f"   diff = {diff:.2f} packets (队列积压)")

    print(f"   解释: diff > beta({vegas.beta}) 表示拥塞，应减少窗口")

    

    # 阈值敏感性

    print("\n3. alpha/beta 阈值敏感性:")

    for alpha, beta in [(1, 3), (2, 4), (3, 6)]:

        vegas = TCPVegas(alpha=alpha, beta=beta)

        print(f"   alpha={alpha}, beta={beta}: 调整范围={beta-alpha} packets")

    

    # 模拟

    print("\n4. Vegas 模拟运行...")

    cwnd, rtt, diff = simulate_vegas(duration=100, link_rtt=50, background_traffic=10, plot=False)

    print(f"   模拟完成：{len(cwnd)}步")

    

    # Vegas vs Reno对比

    print("\n5. Vegas vs Reno 对比...")

    compare_vegas_reno()

    

    # 吞吐率分析

    print("\n6. Vegas 吞吐率分析...")

    analyze_vegas_throughput()

    

    # Vegas优缺点

    print("\n7. Vegas 算法特点:")

    print("   优点:")

    print("   - 在丢包前检测拥塞，反应更早")

    print("   - 不依赖丢包，对网络更友好")

    print("   - 在低拥塞网络中吞吐率更高")

    print("   缺点:")

    print("   - 与Reno/BBR等算法竞争时处于劣势")

    print("   - base_rtt估计可能不准确")

    print("   - 对网络动态变化反应较慢")

