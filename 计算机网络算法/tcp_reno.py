# -*- coding: utf-8 -*-

"""

算法实现：计算机网络算法 / tcp_reno



本文件实现 tcp_reno 相关的算法功能。

"""



import math





class TCPReno:

    """TCP Reno 拥塞控制算法类"""



    def __init__(self, mss=1460, init_cwnd=10):

        # mss: 最大段大小（字节）

        self.mss = mss

        # cwnd: 拥塞窗口（字节）

        self.cwnd = mss * init_cwnd

        # ssthresh: 慢启动阈值（字节），infinity 表示未设置

        self.ssthresh = float('inf')

        # dupacks: 重复 ACK 计数

        self.dupacks = 0

        # recover: 上次恢复点（用于区分新旧丢包）

        self.recover = 0

        # 是否处于快速恢复状态

        self.in_fast_recovery = False

        # 恢复时发送的额外包数

        self.segments_sent_in_recovery = 0



    def slow_start_increase(self):

        """

        慢启动阶段的窗口增长

        

        每收到一个 ACK，窗口增加一个 MSS（指数增长）

        """

        if self.cwnd < self.ssthresh:

            # 指数增长：每 ACK 增加 cwnd / cwnd_divisor

            self.cwnd += self.mss

            return True  # 仍在慢启动

        return False



    def 拥塞避免_increase(self):

        """

        拥塞避免阶段的窗口增长

        

        每收到一个 ACK，窗口增加 MSS^2 / cwnd（线性增长）

        """

        # 线性增长：每 RTT 增加约 1 MSS

        increment = self.mss * self.mss / self.cwnd

        self.cwnd += increment



    def on_ack(self, ack_num, ack_bytes):

        """

        处理 ACK 到达事件

        

        参数:

            ack_num: ACK 确认号

            ack_bytes: ACK 确认的字节数

        """

        if self.in_fast_recovery:

            # 快速恢复阶段

            # 部分 ACK：减少窗口但保持在恢复状态

            if ack_bytes > 0:

                self.cwnd = max(self.cwnd - ack_bytes, self.mss)

            # 全部 ACK：退出快速恢复

            else:

                self.cwnd = self.ssthresh

                self.in_fast_recovery = False

                self.dupacks = 0

        elif self.cwnd < self.ssthresh:

            # 慢启动

            self.慢启动_increase()

        else:

            # 拥塞避免

            self.拥塞避免_increase()



    def on_dupack(self):

        """

        处理重复 ACK（快速重传触发条件）

        

        收到 3 个重复 ACK 时，触发快速重传

        """

        self.dupacks += 1

        

        if self.dupacks >= 3 and not self.in_fast_recovery:

            # 3个重复ACK：触发快速重传

            # 门限减半

            self.ssthresh = max(self.cwnd / 2, 2 * self.mss)

            # 窗口设为 ssthresh + 3*MSS（快速恢复窗口膨胀）

            self.cwnd = self.ssthresh + 3 * self.mss

            self.in_fast_recovery = True

            self.segments_sent_in_recovery = 3

            return True  # 需要重传

        return False



    def on_timeout(self):

        """

        处理超时事件（RTO 到期）

        

        超时被认为是最严重的拥塞信号，窗口重置为初始值

        """

        # 超时：慢启动阈值设为当前窗口一半

        self.ssthresh = max(self.cwnd / 2, 2 * self.mss)

        # 窗口重置为 1-2 个 MSS

        self.cwnd = self.mss

        # 退出快速恢复

        self.in_fast_recovery = False

        self.dupacks = 0



    def on_retransmit(self):

        """

        重传超时时触发的数据包后，更新状态

        """

        if self.in_fast_recovery:

            # 每重传一个，窗口+1 MSS

            self.cwnd += self.mss

            self.segments_sent_in_recovery += 1



    def get_cwnd(self):

        """返回当前拥塞窗口（字节）"""

        return self.cwnd



    def get_cwnd_packets(self):

        """返回当前拥塞窗口（包数）"""

        return self.cwnd / self.mss



    def get_ssthresh(self):

        """返回慢启动阈值（字节）"""

        return self.ssthresh



    def is_in_fast_recovery(self):

        """返回是否处于快速恢复状态"""

        return self.in_fast_recovery





if __name__ == "__main__":

    # 测试 TCP Reno 算法

    reno = TCPReno(mss=1460, init_cwnd=10)

    

    print("=== TCP Reno 算法测试 ===")

    print(f"初始窗口: {reno.get_cwnd_packets():.1f} 包")

    print(f"初始 ssthresh: {'∞' if reno.ssthresh == float('inf') else reno.get_ssthresh()/1460:.1f} 包")

    

    # 模拟慢启动阶段

    print("\n--- 慢启动阶段 ---")

    for i in range(8):

        # 模拟每 RTT 收到一组 ACK

        reno.cwnd = min(reno.cwnd * 2, reno.ssthresh if reno.ssthresh != float('inf') else float('inf'))

        print(f"RTT {i+1}: cwnd={reno.get_cwnd_packets():.1f} 包")

        if reno.cwnd >= reno.ssthresh and reno.ssthresh != float('inf'):

            print(f"  → 进入拥塞避免（ssthresh={reno.get_ssthresh()/1460:.1f} 包）")

            break

    

    # 模拟拥塞避免阶段

    print("\n--- 拥塞避免阶段 ---")

    for i in range(10):

        increment = reno.mss * reno.mss / reno.cwnd

        reno.cwnd += increment

        print(f"RTT {i+1}: cwnd={reno.get_cwnd_packets():.2f} 包")

    

    # 模拟 3 个重复 ACK

    print("\n--- 触发快速重传（3个重复ACK）---")

    for i in range(3):

        triggered = reno.on_dupack()

    print(f"快速重传后: cwnd={reno.get_cwnd_packets():.1f} 包, ssthresh={reno.get_ssthresh()/1460:.1f} 包")

    print(f"快速恢复状态: {reno.is_in_fast_recovery()}")

    

    # 模拟快速恢复中的 ACK

    print("\n--- 快速恢复中的 ACK ---")

    reno.on_ack(0, 0)  # 全部 ACK

    print(f"全部 ACK 后: cwnd={reno.get_cwnd_packets():.1f} 包")

    print(f"快速恢复状态: {reno.is_in_fast_recovery()}")

    

    # 模拟超时

    print("\n--- 超时事件 ---")

    reno.cwnd = 100 * reno.mss  # 设置一个较大窗口

    reno.ssthresh = 50 * reno.mss

    reno.on_timeout()

    print(f"超时后: cwnd={reno.get_cwnd_packets():.1f} 包, ssthresh={reno.get_ssthresh()/1460:.1f} 包")

