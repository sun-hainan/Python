# -*- coding: utf-8 -*-

"""

算法实现：25_�������� / tcp_cubic



本文件实现 tcp_cubic 相关的算法功能。

"""



import numpy as np

import matplotlib.pyplot as plt





class CubicCongestionControl:

    """CUBIC拥塞控制算法类"""

    

    def __init__(self, c=0.4, beta=0.7, w_max=None):

        """

        初始化CUBIC算法参数

        

        Args:

            c: 三次多项式缩放因子，通常为0.4

            beta: 乘法递减因子，丢失事件后窗口缩减比例

            w_max: 丢失事件前的最大窗口大小

        """

        self.c = c  # CUBIC缩放因子

        self.beta = beta  # 乘法递减因子

        self.w_max = w_max  # 上一次拥塞窗口最大值

        self.ssthresh = float('inf')  # 慢启动阈值

        self.cwnd = 1.0  # 当前拥塞窗口大小

        self.k = 0  # 时间偏移量

        self.t = 0  # 从丢失事件后经过的时间

        self.w_max = None  # 丢失事件前的窗口最大值

        

    def _cubic_function(self, t):

        """

        CUBIC三次多项式函数

        

        Args:

            t: 从丢失事件后的时间

            

        Returns:

            窗口大小

        """

        # 计算K值：K = (W_max * beta / C)^(1/3)

        if self.w_max is None:

            self.w_max = self.cwnd

            

        k = ((self.w_max * (1 - self.beta)) / self.c) ** (1/3)

        

        # CUBIC核心公式：W = C * (t - K)^3 + W_max

        w = self.c * ((t - k) ** 3) + self.w_max

        

        return max(w, 1.0)  # 确保窗口至少为1

    

    def _tcpFriendly_function(self, t, rtt):

        """

        TCP友好模式：基于RTT的窗口增长

        

        Args:

            t: 时间

            rtt: 往返时延

            

        Returns:

            TCP友好窗口大小

        """

        # TCP Reno平均窗口增长率

        # W_tcp = 3 * t / (2 * beta)

        w_tcp = (3.0 * t) / (2.0 * self.beta)

        return w_tcp

    

    def update(self, ack_count, rtt, bytes_acked):

        """

        更新拥塞窗口

        

        Args:

            ack_count: 确认包数量

            rtt: 往返时延（毫秒）

            bytes_acked: 确认的字节数

        """

        self.t += 1  # 时间步进

        

        # 处于慢启动阶段

        if self.cwnd < self.ssthresh:

            # 指数增长：每个ACK窗口增加一个MSS

            self.cwnd += ack_count * (self.cwnd / bytes_acked)

        else:

            # 拥塞避免阶段：使用CUBIC增长函数

            w_cubic = self._cubic_function(self.t)

            w_tcp = self._tcpFriendly_function(self.t, rtt)

            

            # 取CUBIC和TCP友好的最大值

            self.cwnd = max(w_cubic, w_tcp)

    

    def loss_event(self):

        """

        丢包事件处理：乘法递减

        """

        self.w_max = self.cwnd  # 记录丢包前的窗口

        self.ssthresh = max(self.cwnd * self.beta, 2)  # 更新阈值

        self.cwnd = self.cwnd * self.beta  # 窗口缩减

        self.t = 0  # 重置时间





def simulate_cubic(duration=100, loss_rate=0.01, plot=True):

    """

    模拟CUBIC算法在丢包事件下的行为

    

    Args:

        duration: 模拟时间步数

        loss_rate: 丢包率

        plot: 是否绘图

    """

    cubic = CubicCongestionControl(c=0.4, beta=0.7)

    

    cwnd_history = [cubic.cwnd]  # 窗口历史记录

    time_steps = [0]

    

    for t in range(1, duration):

        # 模拟ACK接收

        cubic.update(ack_count=1, rtt=50, bytes_acked=1500)

        

        # 模拟随机丢包

        if np.random.random() < loss_rate:

            cubic.loss_event()

        

        cwnd_history.append(cubic.cwnd)

        time_steps.append(t)

        

        # 重传超时处理

        if t % 50 == 0 and t > 0:

            cubic.w_max = None  # 重置W_max

            cubic.t = 0

    

    if plot:

        plt.figure(figsize=(10, 6))

        plt.plot(time_steps, cwnd_history, 'b-', label='CUBIC cwnd')

        plt.xlabel('时间步 (Time Steps)')

        plt.ylabel('拥塞窗口 (Congestion Window)')

        plt.title('CUBIC拥塞控制算法模拟')

        plt.legend()

        plt.grid(True, alpha=0.3)

        plt.savefig('cubic_simulation.png', dpi=150)

        plt.show()

    

    return time_steps, cwnd_history





def compare_cubic_reno():

    """

    比较CUBIC与传统Reno算法的性能

    """

    duration = 200

    cubic = CubicCongestionControl()

    

    cwnd_cubic = [cubic.cwnd]

    cwnd_reno = [1.0]

    

    reno_cwnd = 1.0

    reno_ssthresh = float('inf')

    

    for t in range(1, duration):

        # CUBIC更新

        cubic.update(ack_count=1, rtt=50, bytes_acked=1500)

        

        # Reno简化更新（每个RTT线性增长1/MSS）

        if reno_cwnd < reno_ssthresh:

            reno_cwnd += 1

        else:

            reno_cwnd += 1.0 / reno_cwnd

        

        if np.random.random() < 0.02:  # 2%丢包率

            # Reno丢包处理

            reno_ssthresh = max(reno_cwnd / 2, 2)

            reno_cwnd = reno_cwnd / 2

            cubic.loss_event()

        

        cwnd_cubic.append(cubic.cwnd)

        cwnd_reno.append(reno_cwnd)

    

    plt.figure(figsize=(12, 5))

    plt.subplot(1, 2, 1)

    plt.plot(cwnd_cubic, 'b-', label='CUBIC', alpha=0.7)

    plt.plot(cwnd_reno, 'r-', label='Reno', alpha=0.7)

    plt.xlabel('时间步')

    plt.ylabel('拥塞窗口')

    plt.title('CUBIC vs Reno 窗口对比')

    plt.legend()

    plt.grid(True, alpha=0.3)

    

    plt.subplot(1, 2, 2)

    plt.semilogy(cwnd_cubic, 'b-', label='CUBIC', alpha=0.7)

    plt.semilogy(cwnd_reno, 'r-', label='Reno', alpha=0.7)

    plt.xlabel('时间步')

    plt.ylabel('拥塞窗口 (对数)')

    plt.title('CUBIC vs Reno 窗口对比(对数)')

    plt.legend()

    plt.grid(True, alpha=0.3)

    plt.tight_layout()

    plt.show()





if __name__ == "__main__":

    print("=== CUBIC拥塞控制算法演示 ===")

    

    # 基本模拟

    print("\n1. 运行CUBIC基本模拟...")

    times, cwds = simulate_cubic(duration=100, loss_rate=0.02, plot=False)

    print(f"   模拟完成：{len(times)}步，最终窗口={cwds[-1]:.2f}")

    

    # 丢包事件分析

    cubic = CubicCongestionControl()

    print("\n2. 丢包事件窗口缩减:")

    print(f"   丢包前窗口: {20:.2f}")

    cubic.cwnd = 20

    cubic.loss_event()

    print(f"   丢包后窗口: {cubic.cwnd:.2f}")

    print(f"   慢启动阈值: {cubic.ssthresh:.2f}")

    

    # CUBIC vs Reno对比

    print("\n3. CUBIC vs Reno对比模拟...")

    compare_cubic_reno()

    

    # 参数敏感性分析

    print("\n4. C参数敏感性分析:")

    for c in [0.1, 0.4, 0.8]:

        cubic = CubicCongestionControl(c=c)

        for _ in range(100):

            cubic.update(1, 50, 1500)

        print(f"   C={c}: 最终窗口={cubic.cwnd:.2f}")

