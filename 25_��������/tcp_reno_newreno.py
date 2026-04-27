# -*- coding: utf-8 -*-

"""

算法实现：25_�������� / tcp_reno_newreno



本文件实现 tcp_reno_newreno 相关的算法功能。

"""



import numpy as np

import matplotlib.pyplot as plt





class TCPReno:

    """

    TCP Reno拥塞控制算法

    

    特点：

    - 快速重传：收到3个重复ACK后立即重传

    - 快速恢复：重传后进入快速恢复阶段

    - 窗口调整：ssthresh = cwnd/2, cwnd = ssthresh + 3

    """

    

    def __init__(self, mss=1500):

        """

        初始化Reno算法

        

        Args:

            mss: 最大报文段大小（字节）

        """

        self.mss = mss  # 最大报文段大小

        self.cwnd = mss  # 拥塞窗口

        self.ssthresh = float('inf')  # 慢启动阈值

        self.dup_ack_count = 0  # 重复ACK计数

        self.recover = 0  # 恢复点

        

        self.state = "SLOW_START"  # SLOW_START / CONGESTION_AVOID / FAST_RECOVERY

        

        # 统计

        self.packets_sent = 0

        self.packets_acked = 0

        self.packets_lost = 0

        self.fast_retransmit_count = 0

        

    def slow_start(self, ack_bytes):

        """

        慢启动阶段

        

        每收到一个ACK，cwnd增加一个MSS（指数增长）

        

        Args:

            ack_bytes: 确认的字节数

        """

        # cwnd指数增长：每个ACK增加cwnd/MSS个MSS

        self.cwnd += self.mss * (ack_bytes / self.mss)

        

        if self.cwnd >= self.ssthresh:

            self.state = "CONGESTION_AVOID"

    

    def congestion_avoidance(self, ack_bytes):

        """

        拥塞避免阶段

        

        每收到一个ACK，cwnd增加MSS^2/cwnd（线性增长）

        

        Args:

            ack_bytes: 确认的字节数

        """

        # cwnd线性增长：每个ACK增加MSS/cwnd个MSS

        self.cwnd += self.mss * (self.mss / self.cwnd)

    

    def on_ack(self, ack_bytes):

        """

        处理ACK事件

        

        Args:

            ack_bytes: 确认的字节数

        """

        self.packets_acked += 1

        

        if self.state == "SLOW_START":

            self.slow_start(ack_bytes)

            # 重传超时检测：ack大于recover时退出慢启动

            if ack_bytes >= self.recover and self.recover > 0:

                self.state = "CONGESTION_AVOID"

                

        elif self.state == "CONGESTION_AVOID":

            self.congestion_avoidance(ack_bytes)

            

        elif self.state == "FAST_RECOVERY":

            # 快速恢复阶段的ACK

            if ack_bytes >= self.recover:

                # 完全恢复

                self.state = "CONGESTION_AVOID"

                self.cwnd = self.ssthresh

                self.dup_ack_count = 0

            else:

                # 部分恢复，窗口缩小

                self.cwnd = self.ssthresh + self.dup_ack_count * self.mss

        

        self.packets_sent += int(ack_bytes / self.mss)

    

    def on_dup_ack(self):

        """

        处理重复ACK（触发快速重传）

        """

        self.dup_ack_count += 1

        

        if self.state == "CONGESTION_AVOID" and self.dup_ack_count == 3:

            # 3个重复ACK：触发快速重传

            self.fast_retransmit_count += 1

            self.recover = self.cwnd  # 设置恢复点

            

            # 更新ssthresh

            self.ssthresh = max(self.cwnd / 2, 2 * self.mss)

            

            # 快速恢复：cwnd = ssthresh + 3*MSS

            self.cwnd = self.ssthresh + 3 * self.mss

            

            self.state = "FAST_RECOVERY"

            

        elif self.state == "FAST_RECOVERY":

            # 快速恢复中的重复ACK

            self.cwnd += self.mss  # 窗口扩大

    

    def on_timeout(self):

        """

        处理超时事件（严重拥塞）

        """

        # 超时比重复ACK更严重，窗口缩减更多

        self.ssthresh = max(self.cwnd / 2, 2 * self.mss)

        self.cwnd = self.mss  # 回到初始窗口

        self.dup_ack_count = 0

        self.state = "SLOW_START"

        self.packets_lost += 1

    

    def on_loss(self):

        """

        处理丢包（触发快速重传）

        """

        if self.dup_ack_count < 3:

            self.dup_ack_count += 1

        

        if self.dup_ack_count == 3:

            # 触发快速重传

            self.fast_retransmit_count += 1

            self.recover = self.cwnd

            

            self.ssthresh = max(self.cwnd / 2, 2 * self.mss)

            self.cwnd = self.ssthresh + 3 * self.mss

            

            if self.state != "FAST_RECOVERY":

                self.state = "FAST_RECOVERY"

        else:

            # 快速恢复中的丢包

            self.cwnd = self.ssthresh + self.dup_ack_count * self.mss





class TCPNewReno(TCPReno):

    """

    TCP NewReno拥塞控制算法

    

    对Reno的改进：

    - 快速恢复期间能处理多点丢包

    - 使用"部分ACK"来提前退出快速恢复

    - 避免Reno中每个丢包都触发新快速恢复的问题

    """

    

    def __init__(self, mss=1500):

        super().__init__(mss)

        self.partial_ack_count = 0  # 部分ACK计数

        

    def on_ack(self, ack_bytes):

        """

        重写ACK处理，支持部分ACK

        

        NewReno的关键改进：

        - 部分ACK不立即退出快速恢复

        - 每个部分ACK只重传一个新包

        """

        self.packets_acked += 1

        

        if self.state == "FAST_RECOVERY":

            # NewReno在快速恢复中对部分ACK的处理

            expected_bytes = self.recover - self.packets_acked * self.mss

            

            if ack_bytes >= expected_bytes:

                # 完全恢复

                self.state = "CONGESTION_AVOID"

                self.cwnd = self.ssthresh

                self.dup_ack_count = 0

                self.partial_ack_count = 0

            else:

                # 部分ACK：只重传一个新包，窗口减1

                self.partial_ack_count += 1

                self.cwnd = max(self.cwnd - self.mss, self.ssthresh)

                

                # 如果有新的重复ACK，触发新的快速重传

                if self.dup_ack_count < 3:

                    self.state = "CONGESTION_AVOID"

                    

        elif self.state == "SLOW_START":

            self.slow_start(ack_bytes)

            

        elif self.state == "CONGESTION_AVOID":

            self.congestion_avoidance(ack_bytes)

        

        self.packets_sent += int(ack_bytes / self.mss)





def simulate_reno_vs_newreno(duration=500, loss_interval=30):

    """

    模拟Reno与NewReno在丢包事件下的行为对比

    

    Args:

        duration: 模拟时间步

        loss_interval: 丢包间隔

    """

    reno = TCPReno()

    newreno = TCPNewReno()

    

    cwnd_reno = [reno.cwnd]

    cwnd_newreno = [newreno.cwnd]

    

    for t in range(duration):

        # 模拟ACK：窗口大小成正比

        ack_reno = min(reno.cwnd, reno.mss * 10)

        ack_newreno = min(newreno.cwnd, newreno.mss * 10)

        

        reno.on_ack(ack_reno)

        newreno.on_ack(ack_newreno)

        

        # 周期性丢包

        if t > 0 and t % loss_interval == 0:

            reno.on_loss()

            newreno.on_loss()

        

        cwnd_reno.append(reno.cwnd)

        cwnd_newreno.append(newreno.cwnd)

    

    # 绘图

    plt.figure(figsize=(14, 5))

    

    plt.subplot(1, 2, 1)

    plt.plot(cwnd_reno, 'b-', label='Reno', alpha=0.7)

    plt.plot(cwnd_newreno, 'r-', label='NewReno', alpha=0.7)

    plt.xlabel('时间步')

    plt.ylabel('拥塞窗口 (bytes)')

    plt.title('Reno vs NewReno 窗口对比')

    plt.legend()

    plt.grid(True, alpha=0.3)

    

    plt.subplot(1, 2, 2)

    steps = np.arange(len(cwnd_reno))

    plt.semilogy(steps, cwnd_reno, 'b-', label='Reno', alpha=0.7)

    plt.semilogy(steps, cwnd_newreno, 'r-', label='NewReno', alpha=0.7)

    plt.xlabel('时间步')

    plt.ylabel('拥塞窗口 (bytes, 对数)')

    plt.title('Reno vs NewReno 窗口对比(对数)')

    plt.legend()

    plt.grid(True, alpha=0.3)

    

    plt.tight_layout()

    plt.savefig('reno_vs_newreno.png', dpi=150)

    plt.show()

    

    return cwnd_reno, cwnd_newreno





def simulate_loss_scenarios():

    """

    模拟不同丢包场景

    """

    scenarios = [

        ("稀疏丢包", 0.01, 50),  # 1%丢包率，每50步丢一次

        ("中度丢包", 0.03, 30),

        ("频繁丢包", 0.1, 20),

    ]

    

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    

    for idx, (name, loss_rate, interval) in enumerate(scenarios):

        reno = TCPReno()

        cwnd_history = [reno.cwnd]

        

        for t in range(200):

            ack = min(reno.cwnd, reno.mss * 10)

            reno.on_ack(ack)

            

            # 随机丢包

            if np.random.random() < loss_rate:

                reno.on_loss()

            

            cwnd_history.append(reno.cwnd)

        

        axes[idx].plot(cwnd_history, 'b-', alpha=0.7)

        axes[idx].set_title(f'{name}\n丢包率={loss_rate*100:.0f}%')

        axes[idx].set_xlabel('时间步')

        axes[idx].set_ylabel('cwnd (bytes)')

        axes[idx].grid(True, alpha=0.3)

    

    plt.tight_layout()

    plt.savefig('reno_loss_scenarios.png', dpi=150)

    plt.show()





if __name__ == "__main__":

    print("=== TCP Reno/NewReno 拥塞控制算法演示 ===")

    

    # 基本模拟

    print("\n1. TCP Reno 基本模拟:")

    reno = TCPReno()

    for t in range(50):

        ack = min(reno.cwnd, reno.mss * 10)

        reno.on_ack(ack)

        if t == 20:

            reno.on_loss()  # 模拟丢包

    print(f"   初始窗口: {reno.mss} bytes")

    print(f"   50步后窗口: {reno.cwnd:.0f} bytes")

    print(f"   快速重传次数: {reno.fast_retransmit_count}")

    

    # NewReno改进

    print("\n2. TCP NewReno 改进:")

    newreno = TCPNewReno()

    print(f"   初始状态: {newreno.state}")

    print(f"   初始窗口: {newreno.mss} bytes")

    

    # 状态转换演示

    print("\n3. 状态转换:")

    reno = TCPReno()

    print(f"   初始状态: {reno.state}, cwnd={reno.cwnd}")

    

    # 慢启动到拥塞避免

    for _ in range(10):

        reno.on_ack(reno.mss * 2)

    print(f"   慢启动后: {reno.state}, cwnd={reno.cwnd:.0f}, ssthresh={reno.ssthresh:.0f}")

    

    # 丢包触发快速重传

    for _ in range(3):

        reno.on_dup_ack()

    print(f"   3个重复ACK: {reno.state}, cwnd={reno.cwnd:.0f}")

    

    # Reno vs NewReno对比

    print("\n4. Reno vs NewReno 对比模拟...")

    simulate_reno_vs_newreno()

    

    # 不同丢包场景

    print("\n5. 不同丢包场景模拟...")

    simulate_loss_scenarios()

    

    # 性能统计

    print("\n6. 性能统计:")

    reno = TCPReno()

    newreno = TCPNewReno()

    

    for t in range(500):

        ack_r = min(reno.cwnd, reno.mss * 10)

        ack_n = min(newreno.cwnd, newreno.mss * 10)

        reno.on_ack(ack_r)

        newreno.on_ack(ack_n)

        

        if t % 30 == 0 and t > 0:

            reno.on_loss()

            newreno.on_loss()

    

    print(f"   Reno: 最终窗口={reno.cwnd:.0f}, 快重传={reno.fast_retransmit_count}")

    print(f"   NewReno: 最终窗口={newreno.cwnd:.0f}, 快重传={newreno.fast_retransmit_count}")

