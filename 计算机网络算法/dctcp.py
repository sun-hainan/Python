# -*- coding: utf-8 -*-

"""

算法实现：计算机网络算法 / dctcp



本文件实现 dctcp 相关的算法功能。

"""



import math





class DCTCP:

    """DCTCP 拥塞控制算法类"""



    def __init__(self, mss=1460, alpha=1.0, beta=0.8, gamma=2):

        """

        初始化 DCTCP

        

        参数:

            mss: 最大段大小（字节）

            alpha: 拥塞估计因子（初始值）

            beta: 窗口减少因子（0到1之间）

            gamma: 增益因子（控制窗口增长速率）

        """

        self.mss = mss

        # alpha: 拥塞程度的估计值（0到1之间）

        self.alpha = alpha

        # beta: 窗口减少因子

        self.beta = beta

        # gamma: 增长阶段的增益因子

        self.gamma = gamma

        # cwnd: 拥塞窗口（字节）

        self.cwnd = mss * 10

        # ssthresh: 慢启动阈值

        self.ssthresh = float('inf')

        # base_rtt: 基准 RTT（最小 RTT）

        self.base_rtt = float('inf')

        # dctcp_bytes_ecn: 当前 RTT 内标记为 ECN 的字节数

        self.dctcp_bytes_ecn = 0

        # dctcp_bytes_total: 当前 RTT 内总字节数

        self.dctcp_bytes_total = 0

        # bytes_ecn_last: 上个 RTT 的 ECN 字节数

        self.bytes_ecn_last = 0

        # 拥塞事件计数

        self.congestion_events = 0



    def _update_alpha(self):

        """

        根据当前 RTT 的 ECN 比例更新 alpha

        

        计算公式: alpha = (1 - beta) * alpha + beta * (ecn_bytes / total_bytes)

        """

        if self.dctcp_bytes_total > 0:

            # 计算当前 RTT 的 ECN 比例

            gamma_estimation = self.dctcp_bytes_ecn / self.dctcp_bytes_total

            # 更新 alpha（指数加权移动平均）

            self.alpha = (1 - self.beta) * self.alpha + self.beta * gamma_estimation

        

        # 重置计数器

        self.dctcp_bytes_ecn = 0

        self.dctcp_bytes_total = 0



    def on_ecn_mark(self, bytes_acked):

        """

        处理 ECN 标记的包被确认

        

        参数:

            bytes_acked: 确认的字节数

        """

        self.dctcp_bytes_ecn += bytes_acked

        self.dctcp_bytes_total += bytes_acked



    def on_ack(self, ack_bytes, is_ecn=False):

        """

        处理 ACK 事件

        

        参数:

            ack_bytes: 确认的字节数

            is_ecn: 是否有 ECN 标记

        """

        if is_ecn:

            self.on_ecn_mark(ack_bytes)

        else:

            self.dctcp_bytes_total += ack_bytes

        

        if self.cwnd < self.ssthresh:

            # 慢启动阶段

            self.cwnd += self.mss

        else:

            # 拥塞避免阶段：DCTCP 增长

            # 公式: cwnd += MSS * (gamma * (1 - alpha) * MSS / cwnd)

            increment = self.mss * self.gamma * (1 - self.alpha) * self.mss / self.cwnd

            self.cwnd += increment



    def on_loss(self, bytes_lost):

        """

        处理丢包事件

        

        参数:

            bytes_lost: 丢失的字节数

        """

        # DCTCP 丢包处理：根据 alpha 减少窗口

        # 如果 alpha 很小，说明拥塞不严重，减少量也小

        self.ssthresh = max(self.cwnd * (1 - self.alpha / 2), 2 * self.mss)

        self.cwnd = self.ssthresh

        self.congestion_events += 1



    def on_timeout(self):

        """处理超时事件"""

        self.ssthresh = 2 * self.mss

        self.cwnd = self.mss

        self.alpha = 1.0  # 重置 alpha

        self.congestion_events += 1



    def on_rtt_sample(self, rtt):

        """

        更新 RTT 样本

        

        参数:

            rtt: 当前 RTT 测量值

        """

        if rtt < self.base_rtt:

            self.base_rtt = rtt

        # 每 RTT 更新一次 alpha

        self._update_alpha()



    def get_cwnd(self):

        """返回当前拥塞窗口（字节）"""

        return self.cwnd



    def get_cwnd_packets(self):

        """返回当前拥塞窗口（包数）"""

        return self.cwnd / self.mss



    def get_alpha(self):

        """返回当前 alpha 值"""

        return self.alpha



    def get_throughput_estimate(self):

        """

        估计当前吞吐量

        

        返回:

            throughput: 估计的吞吐量（字节/秒）

        """

        if self.base_rtt > 0:

            return self.cwnd / self.base_rtt

        return 0





class ECNMarker:

    """ECN（Explicit Congestion Notification）标记器"""



    def __init__(self, threshold=20):

        """

        初始化 ECN 标记器

        

        参数:

            threshold: 队列长度阈值，超过此值标记数据包

        """

        self.threshold = threshold

        # 当前队列长度（模拟）

        self.queue_length = 0

        # 标记计数

        self.marked_packets = 0

        self.total_packets = 0



    def enqueue(self, packet_size):

        """

        入队数据包，可能进行 ECN 标记

        

        参数:

            packet_size: 数据包大小

        返回:

            is_marked: 是否被 ECN 标记

        """

        self.queue_length += packet_size

        self.total_packets += 1

        

        # 简单模拟：队列长度超过阈值则标记

        if self.queue_length > self.threshold:

            self.marked_packets += 1

            is_marked = True

        else:

            is_marked = False

        

        return is_marked



    def dequeue(self, packet_size):

        """

        出队数据包

        

        参数:

            packet_size: 数据包大小

        """

        self.queue_length = max(0, self.queue_length - packet_size)



    def get_mark_ratio(self):

        """获取标记比例"""

        if self.total_packets > 0:

            return self.marked_packets / self.total_packets

        return 0





if __name__ == "__main__":

    # 测试 DCTCP 算法

    print("=== DCTCP 算法测试 ===\n")



    dctcp = DCTCP(mss=1460, alpha=1.0, beta=0.8, gamma=2)



    print(f"初始窗口: {dctcp.get_cwnd_packets():.1f} 包")

    print(f"初始 alpha: {dctcp.get_alpha():.3f}")



    # 模拟慢启动

    print("\n--- 慢启动阶段 ---")

    for i in range(6):

        # 每 RTT 窗口翻倍

        dctcp.cwnd = min(dctcp.cwnd * 2, dctcp.ssthresh if dctcp.ssthresh != float('inf') else float('inf'))

        print(f"RTT {i+1}: cwnd={dctcp.get_cwnd_packets():.1f} 包")



    # 进入拥塞避免

    dctcp.ssthresh = dctcp.cwnd / 2

    dctcp.base_rtt = 0.001  # 1ms 基准 RTT（数据中心场景）



    print(f"\n进入拥塞避免，ssthresh={dctcp.ssthresh/1460:.1f} 包")



    # 模拟拥塞避免阶段

    print("\n--- DCTCP 拥塞避免阶段 ---")

    for i in range(20):

        # 模拟 ACK

        ack_bytes = dctcp.mss * 10

        # 模拟 ECN 标记（随着窗口增大，ECN 标记概率增加）

        is_ecn = (i > 10) and (random.random() < 0.2)

        dctcp.on_ack(ack_bytes, is_ecn)

        # 模拟 RTT 采样

        rtt = dctcp.base_rtt * (1 + 0.1 * i / 20)  # RTT 逐渐增加

        dctcp.on_rtt_sample(rtt)

        

        if i % 5 == 0:

            print(f"RTT {i+1}: cwnd={dctcp.get_cwnd_packets():.2f} 包, "

                  f"alpha={dctcp.get_alpha():.3f}, RTT={rtt*1000:.2f}ms")



    # 模拟丢包

    print("\n--- 丢包事件 ---")

    dctcp.on_loss(1460)

    print(f"丢包后: cwnd={dctcp.get_cwnd_packets():.1f} 包, alpha={dctcp.get_alpha():.3f}")

    print(f"拥塞事件数: {dctcp.congestion_events}")



    # 测试 ECN 标记器

    print("\n=== ECN 标记器测试 ===")

    import random

    marker = ECNMarker(threshold=50)



    print(f"阈值: {marker.threshold}")

    print("\n模拟数据包入队:")

    for i in range(20):

        pkt_size = random.randint(100, 500)

        is_marked = marker.enqueue(pkt_size)

        if i % 5 == 0:

            print(f"  包 {i+1}: 大小={pkt_size}, ECN标记={is_marked}, "

                  f"队列={marker.queue_length}, 标记率={marker.get_mark_ratio():.2%}")

