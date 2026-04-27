# -*- coding: utf-8 -*-
"""
算法实现：计算机网络算法 / tcp_cubic

本文件实现 tcp_cubic 相关的算法功能。
"""

import math
import time


class TCPCubic:
    """TCP CUBIC 拥塞控制算法类"""

    def __init__(self, mss=1460, c=0.4, beta=0.7):
        # mss: 最大段大小（字节），默认1460
        self.mss = mss
        # c: CUBIC 缩放因子，控制增长速率
        self.c = c
        # beta: 乘法减少因子，丢包后窗口乘以此值
        self.beta = beta
        # cwnd: 拥塞窗口大小（字节）
        self.cwnd = mss * 10
        # ssthresh: 慢启动阈值
        self.ssthresh = float('inf')
        # Wmax: 丢包前的窗口大小（字节）
        self.Wmax = 0
        # t_epoch: 上次丢包后的时间戳（秒）
        self.t_epoch = 0
        # K: 时间偏移量，使窗口在 Wmax 时达到拐点
        self.K = 0
        # origin_point: 窗口恢复到 Wmax 的时间点
        self.origin_point = 0
        # 是否处于拥塞避免阶段
        self.in_cong_avoid = False
        # 初始时间基准
        self.start_time = time.time()

    def _elapsed(self):
        """返回自上次丢包事件后经过的时间（秒）"""
        return time.time() - self.t_epoch

    def _cubic_window(self, t):
        """
        计算 CUBIC 三次多项式窗口值
        
        参数:
            t: 自上次丢包后的时间
        返回:
            窗口大小（字节）
        """
        # 计算 (t - K)^3
        diff = t - self.K
        diff_cubed = diff * diff * diff
        # CUBIC 公式: W = C * (t - K)^3 + Wmax
        w = self.c * diff_cubed + self.Wmax
        # 确保窗口不小于一个 MSS
        return max(w, self.mss)

    def _tcp_reno_window(self, t):
        """
        计算标准 TCP Reno 窗口（用于比较）
        
        参数:
            t: 时间
        返回:
            TCP Reno 窗口大小
        """
        # TCP Reno 线性增长: W = Wmax * (1 - β) * t / RTT
        # 简化为每秒增长量
        rtt_estimate = 1.0  # 假设 RTT = 1秒
        return self.Wmax * (1 - self.beta) * t / rtt_estimate

    def increase(self):
        """
        每 RTT 增加窗口大小
        
        在慢启动阶段指数增长，在拥塞避免阶段使用 CUBIC 增长
        """
        if self.cwnd < self.ssthresh:
            # 慢启动：每 RTT 翻倍
            self.cwnd *= 2
        else:
            # 拥塞避免：CUBIC 增长
            self.in_cong_avoid = True
            t = self._elapsed()
            # 计算目标窗口
            target = self._cubic_window(t)
            # 计算线性增量（标准 TCP 增量）
            linear_increment = self.mss * self.mss / self.cwnd
            # 平滑过渡到目标窗口
            self.cwnd += linear_increment * (target - self.cwnd) / target

    def decrease(self):
        """
        丢包事件触发窗口减少
        
        执行乘法减少，将窗口降至 Wmax * beta
        """
        if self.cwnd >= self.Wmax or self.Wmax == 0:
            self.Wmax = self.cwnd
        # 乘法减少
        self.cwnd = max(self.cwnd * self.beta, self.mss * 2)
        # 更新 ssthresh
        self.ssthresh = self.cwnd
        # 重置 CUBIC 参数
        self.t_epoch = time.time()
        self.K = math.pow(self.Wmax * self.beta / self.c, 1.0 / 3.0)
        self.in_cong_avoid = False

    def get_cwnd(self):
        """返回当前拥塞窗口大小（字节）"""
        return self.cwnd

    def get_cwnd_packets(self):
        """返回当前拥塞窗口大小（包数）"""
        return self.cwnd / self.mss


if __name__ == "__main__":
    # 测试 TCP CUBIC 算法
    cubic = TCPCubic(mss=1460, c=0.4, beta=0.7)
    
    print("=== TCP CUBIC 算法测试 ===")
    print(f"初始窗口: {cubic.get_cwnd_packets():.2f} 包")
    
    # 模拟慢启动阶段
    print("\n--- 慢启动阶段 ---")
    for i in range(5):
        cubic.increase()
        print(f"RTT {i+1}: {cubic.get_cwnd_packets():.2f} 包, ssthresh={cubic.ssthresh}")
    
    # 设置 ssthresh 进入拥塞避免
    cubic.ssthresh = cubic.get_cwnd() * 0.5
    cubic.decrease()  # 模拟一次丢包
    
    print(f"\n丢包后窗口: {cubic.get_cwnd_packets():.2f} 包")
    print(f"Wmax: {cubic.Wmax / cubic.mss:.2f} 包")
    
    # 模拟拥塞避免阶段
    print("\n--- CUBIC 拥塞避免阶段 ---")
    for i in range(10):
        cubic.increase()
        print(f"RTT {i+1}: {cubic.get_cwnd_packets():.2f} 包")
