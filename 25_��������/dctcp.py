# -*- coding: utf-8 -*-
"""
算法实现：25_�������� / dctcp

本文件实现 dctcp 相关的算法功能。
"""

import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import List


@dataclass
class DCTCPState:
    """DCTCP连接状态"""
    cwnd: float  # 拥塞窗口
    ssthresh: float  # 慢启动阈值
    bytes_in_flight: int  # 飞行字节数
    
    # DCTCP特有状态
    dctcp_alpha: float  # 拥塞估计参数α
    ecn_alpha: float  # ECN标记比例
    last_seq: int  # 最后确认的序列号
    
    # 统计
    packets_acked: int = 0
    packets_lost: int = 0
    ecn_marks: int = 0


class DCTCPReceiver:
    """
    DCTCP接收方
    
    职责：
    - 检测CE(Congestion Experienced)标记
    - 生成ECT标记
    - 报告ECN反馈
    """
    
    def __init__(self):
        self.ce_count = 0  # CE标记数量
        self.total_count = 0  # 总包数
        
    def receive_packet(self, is_ect: bool, is_ce: bool) -> bool:
        """
        接收数据包
        
        Args:
            is_ect: 是否ECT(ECN-Capable Transport)标记
            is_ce: 是否CE标记
        
        Returns:
            是否需要发送ECT回执
        """
        if is_ect:
            self.total_count += 1
            if is_ce:
                self.ce_count += 1
        
        # 返回是否收到CE
        return is_ce
    
    def get_ecn_feedback(self) -> float:
        """
        获取ECN反馈（CE分数）
        
        Returns:
            0-1之间的分数，表示拥塞程度
        """
        if self.total_count == 0:
            return 0.0
        
        # 返回CE标记的比例
        return self.ce_count / self.total_count
    
    def reset_counters(self):
        """重置计数器（在窗口级别）"""
        self.ce_count = 0
        self.total_count = 0


class DCTCPsender:
    """
    DCTCP发送方
    
    核心算法：
    1. 窗口更新：cwnd = cwnd * (1 - α/2)
       - α是ECN标记比例
       - α=0时窗口不变，α=1时窗口减半
    2. 丢包处理：与传统TCP相同
    """
    
    def __init__(self, mss=1500, init_cwnd=10):
        """
        初始化DCTCP发送方
        
        Args:
            mss: 最大报文段大小
            init_cwnd: 初始窗口大小
        """
        self.mss = mss
        self.state = DCTCPState(
            cwnd=init_cwnd * mss,
            ssthresh=float('inf'),
            bytes_in_flight=0,
            dctcp_alpha=0,
            ecn_alpha=0.0,
            last_seq=0
        )
        
        self.receiver = DCTCPReceiver()
        self.history = []  # 历史记录
    
    def on_ack(self, ack_bytes: int, is_ce: bool, rtt: float):
        """
        处理ACK
        
        Args:
            ack_bytes: 确认的字节数
            is_ce: 是否有CE标记
            rtt: 往返时间
        """
        # 更新接收方ECN统计
        self.receiver.receive_packet(is_ect=True, is_ce=is_ce)
        
        # 更新飞行字节数
        self.state.bytes_in_flight = max(0, self.state.bytes_in_flight - ack_bytes)
        
        # 获取ECN反馈
        self.state.ecn_alpha = self.receiver.get_ecn_feedback()
        
        # 慢启动
        if self.state.cwnd < self.state.ssthresh:
            self.state.cwnd += ack_bytes
        
        # 拥塞避免（传统TCP部分）
        else:
            # DCTCP核心：使用α调整窗口
            # cwnd = cwnd * (1 - α/2)
            reduction = self.state.dctcp_alpha / 2.0
            self.state.cwnd = self.state.cwnd * (1.0 - reduction)
            
            # DCTCP特有：根据α直接调整
            # 使用更平滑的α估计
            self.state.dctcp_alpha = (1.0 - 0.0625) * self.state.dctcp_alpha + 0.0625 * self.state.ecn_alpha
            
            # 窗口增加
            self.state.cwnd += self.mss * ack_bytes / self.state.cwnd
        
        self.state.packets_acked += 1
        self.state.last_seq += ack_bytes
    
    def on_loss(self, lost_bytes: int):
        """
        处理丢包（与TCP Reno相同）
        
        Args:
            lost_bytes: 丢失的字节数
        """
        # 缩减ssthresh
        self.state.ssthresh = max(self.state.cwnd / 2, 2 * self.mss)
        
        # 缩减窗口
        self.state.cwnd = self.state.ssthresh
        
        self.state.bytes_in_flight = max(0, self.state.bytes_in_flight - lost_bytes)
        self.state.packets_lost += 1
        
        # 重置DCTCP α（与Reno一样，丢包后重置）
        self.state.dctcp_alpha = 0
    
    def send(self, bytes_to_send: int) -> int:
        """
        发送数据
        
        Args:
            bytes_to_send: 要发送的字节数
        
        Returns:
            实际发送的字节数
        """
        available = self.state.cwnd - self.state.bytes_in_flight
        sent = min(bytes_to_send, available)
        
        self.state.bytes_in_flight += sent
        return sent
    
    def get_alpha(self) -> float:
        """获取当前α值"""
        return self.state.dctcp_alpha


def simulate_dctcp(duration=200, link_capacity=1000e6, link_rtt=0.001, 
                   queue_size=100, background_flows=0):
    """
    模拟DCTCP在数据中心网络的行为
    
    Args:
        duration: 模拟时间步
        link_capacity: 链路容量（bps）
        link_rtt: 链路RTT（秒）
        queue_size: 交换机队列大小（包数）
        background_flows: 背景流数量
    """
    sender = DCTCPsender()
    
    cwnd_history = []
    alpha_history = []
    queue_history = []
    
    mss = 1500
    queue = 0  # 当前队列长度
    link_rate = link_capacity / 8 / mss  # 包/秒
    
    for t in range(duration):
        # 模拟背景流量（增加队列）
        if background_flows > 0:
            bg_arrivals = np.random.poisson(background_flows * 0.1)
            queue += bg_arrivals
        
        # 计算可用发送窗口
        available = sender.state.cwnd / mss
        arrivals = min(int(available), int(link_rate * link_rtt * 10))
        
        # 模拟ECN标记
        is_ce = queue > queue_size * 0.3  # 30%阈值开始标记
        
        if is_ce:
            queue = max(0, queue - 1)  # CE标记导致发送方减速
            sender.state.ecn_marks += arrivals
        
        # 模拟ACK
        for _ in range(arrivals):
            sender.on_ack(mss, is_ce, link_rtt * 1000)
        
        # 服务队列
        service_rate = min(link_rate, queue)
        queue = max(0, queue - int(service_rate * link_rtt * 10))
        
        # 记录
        cwnd_history.append(sender.state.cwnd / mss)
        alpha_history.append(sender.get_alpha())
        queue_history.append(queue)
    
    return cwnd_history, alpha_history, queue_history


def compare_dctcp_vs_tcp(duration=200):
    """
    对比DCTCP与传统TCP的性能
    
    Args:
        duration: 模拟时间步
    """
    # DCTCP
    dctcp = DCTCPsender()
    
    # 简化TCP Reno
    tcp_cwnd = 10 * 1500
    tcp_ssthresh = float('inf')
    
    cwnd_dctcp = []
    cwnd_tcp = []
    alpha_dctcp = []
    
    for t in range(duration):
        # DCTCP
        for _ in range(10):
            dctcp.on_ack(1500, np.random.random() < 0.1, 1.0)
        
        cwnd_dctcp.append(dctcp.state.cwnd / 1500)
        alpha_dctcp.append(dctcp.get_alpha())
        
        # TCP Reno
        tcp_cwnd += 1500 if tcp_cwnd < tcp_ssthresh else 1500 * 1500 / tcp_cwnd
        if np.random.random() < 0.05:
            tcp_ssthresh = max(tcp_cwnd / 2, 2 * 1500)
            tcp_cwnd = tcp_ssthresh
        
        cwnd_tcp.append(tcp_cwnd / 1500)
    
    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 2, 1)
    plt.plot(cwnd_dctcp, 'b-', label='DCTCP', alpha=0.7)
    plt.plot(cwnd_tcp, 'r-', label='TCP Reno', alpha=0.7)
    plt.xlabel('时间步')
    plt.ylabel('拥塞窗口 (MSS)')
    plt.title('DCTCP vs TCP 窗口对比')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(1, 2, 2)
    plt.plot(alpha_dctcp, 'g-', label='DCTCP α')
    plt.xlabel('时间步')
    plt.ylabel('α 值')
    plt.title('DCTCP α(拥塞估计)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('dctcp_vs_tcp.png', dpi=150)
    plt.show()


def analyze_ecn_thresholds():
    """
    分析不同ECN阈值的性能影响
    """
    print("=== ECN阈值分析 ===\n")
    
    thresholds = [0.1, 0.2, 0.3, 0.5]
    
    print("不同Kmin/Kmax阈值配置:")
    print("| Kmin | Kmax | 公平性 | 延迟 |")
    print("|------|------|--------|------|")
    
    for kmin_ratio in thresholds:
        print(f"| {int(kmin_ratio*100)}%  | 100% | 高     | 低   |")


def demo_dctcp_alPHA():
    """
    演示DCTCP α参数的作用
    """
    print("\n=== DCTCP α 参数演示 ===\n")
    
    sender = DCTCPsender()
    
    print("α（拥塞估计参数）的含义:")
    print("  α = 0: 无拥塞，窗口保持")
    print("  α = 1: 严重拥塞，窗口减半")
    print()
    
    # 模拟不同拥塞程度
    print("模拟ECN标记比例对窗口的影响:")
    print(f"  初始 cwnd = {sender.state.cwnd / 1500:.1f} MSS")
    
    for ecn_ratio in [0.0, 0.2, 0.5, 0.8]:
        sender.state.ecn_alpha = ecn_ratio
        sender.state.dctcp_alpha = ecn_ratio
        
        # 模拟一个RTT
        sender.on_ack(1500, ecn_ratio > 0, 1.0)
        
        print(f"  ECN比例={ecn_ratio:.1f}: cwnd = {sender.state.cwnd / 1500:.1f} MSS")
        
        # 重置
        sender.state.cwnd = 10 * 1500


def demo_algorithm_comparison():
    """
    演示DCTCP与传统TCP的算法差异
    """
    print("\n=== DCTCP vs TCP 算法对比 ===\n")
    
    print("1. 窗口缩减机制:")
    print()
    print("   传统TCP:")
    print("     - 丢包后：cwnd = cwnd / 2")
    print("     - 恢复慢，影响吞吐率")
    print()
    print("   DCTCP:")
    print("     - ECN标记：cwnd = cwnd * (1 - α/2)")
    print("     - 丢包后：ssthresh = cwnd / 2 (同TCP)")
    print("     - 平滑控制，快速恢复")
    print()
    
    print("2. α计算公式:")
    print("   α_new = (1 - 1/16) * α_old + (1/16) * F")
    print("   其中 F = CE标记包 / 总ECT包")
    print()
    
    print("3. DCTCP优势:")
    print("   - 低延迟：保持小队列")
    print("   - 高吞吐：避免不必要丢包")
    print("   - 公平性：多流共享带宽")
    print("   - 快速收敛：α平滑调整")


if __name__ == "__main__":
    print("=" * 60)
    print("数据中心TCP (DCTCP) 算法实现")
    print("=" * 60)
    
    # DCTCP vs TCP对比
    print("\n运行DCTCP vs TCP对比模拟...")
    compare_dctcp_vs_tcp(duration=150)
    
    # α参数演示
    demo_dctcp_alPHA()
    
    # 算法对比
    demo_algorithm_comparison()
    
    # ECN阈值分析
    analyze_ecn_thresholds()
    
    # 模拟DCTCP
    print("\n运行DCTCP数据中心模拟...")
    cwnd, alpha, queue = simulate_dctcp(duration=100, background_flows=5)
    print(f"模拟完成: {len(cwnd)}步")
    
    print("\n" + "=" * 60)
    print("DCTCP关键设计:")
    print("=" * 60)
    print("""
1. ECN支持：
   - 需要网络设备（交换机）支持ECN标记
   - Kmin: 开始标记的队列长度阈值
   - Kmax: 全部标记的队列长度阈值
   
2. 核心参数：
   - α: 拥塞估计，0-1之间
   - g: 平滑因子（通常1/16）
   - α = (1-g)*α + g*F
   
3. 与TCP的关系：
   - DCTCP主要用于数据中心
   - 可以与传统TCP共存
   - 但在混合网络中可能不公平

4. 适用场景：
   - 超低延迟数据中心
   - 高带宽低延迟网络
   - 短流为主的 workloads
""")
