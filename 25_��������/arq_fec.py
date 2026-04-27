# -*- coding: utf-8 -*-
"""
算法实现：25_�������� / arq_fec

本文件实现 arq_fec 相关的算法功能。
"""

import random
import math
from typing import List, Tuple, Optional
from dataclasses import dataclass
import numpy as np


class Packet:
    """数据包"""
    def __init__(self, seq_num: int, data: bytes):
        self.seq_num = seq_num
        self.data = data
        self.size = len(data)


@dataclass
class ARQState:
    """ARQ状态"""
    seq_num: int
    unacked_packets: List[Packet]
    retransmit_count: int
    timeout: float


class StopAndWaitARQ:
    """
    停止等待ARQ协议
    
    发送方发送一个包，等待ACK
    - 超时未收到ACK则重传
    - 收到ACK后发送下一个包
    """
    
    def __init__(self, timeout: float = 1.0, max_retries: int = 5):
        self.timeout = timeout
        self.max_retries = max_retries
        self.state = ARQState(0, [], 0)
        
        # 统计
        self.packets_sent = 0
        self.packets_acked = 0
        self.retransmissions = 0
        self.timeouts = 0
    
    def send(self, data: bytes) -> Tuple[bool, int]:
        """
        发送数据
        
        Args:
            data: 要发送的数据
        
        Returns:
            (success, attempt_count)
        """
        packet = Packet(self.state.seq_num, data)
        self.state.unacked_packets.append(packet)
        self.packets_sent += 1
        
        attempt = 1
        while attempt <= self.max_retries:
            # 模拟传输（可能丢包）
            transmitted = self._simulate_transmit()
            
            if transmitted:
                # 模拟ACK
                ack_received = self._simulate_ack()
                if ack_received:
                    self.state.seq_num = 1 - self.state.seq_num
                    self.packets_acked += 1
                    self.state.unacked_packets.pop(0)
                    return True, attempt
            
            # 超时重传
            self.retransmissions += 1
            attempt += 1
        
        self.timeouts += 1
        return False, attempt - 1
    
    def _simulate_transmit(self) -> bool:
        """模拟传输（90%到达率）"""
        return random.random() < 0.9
    
    def _simulate_ack(self) -> bool:
        """模拟ACK（95%到达率）"""
        return random.random() < 0.95


class SlidingWindowARQ:
    """
    滑动窗口ARQ（回退N帧/选择性重传）
    
    - 发送方维护发送窗口
    - 接收方维护接收窗口
    - 可同时发送多个帧
    """
    
    def __init__(self, window_size: int = 4, max_seq: int = 8):
        self.window_size = window_size
        self.max_seq = max_seq  # 序列号范围
        
        self.send_base = 0  # 发送窗口起始
        self.next_seq = 0   # 下一个可用序列号
        
        self.recv_base = 0  # 接收窗口起始
        self.received = {}  # 已接收的包
        
        self.unacked = {}   # 未确认的包
        
        # 统计
        self.total_sent = 0
        self.total_acked = 0
        self.total_retransmit = 0
    
    def send_batch(self, data_list: List[bytes]) -> List[Tuple[int, bool]]:
        """
        批量发送
        
        Args:
            data_list: 数据列表
        
        Returns:
            [(seq_num, success), ...]
        """
        results = []
        
        for data in data_list:
            if self.next_seq < self.send_base + self.window_size:
                # 窗口内有空间，发送
                seq = self.next_seq
                packet = Packet(seq, data)
                self.unacked[seq] = packet
                
                # 模拟传输
                success = random.random() < 0.9
                self.total_sent += 1
                
                results.append((seq, success))
                self.next_seq = (self.next_seq + 1) % self.max_seq
            else:
                # 窗口满
                results.append((-1, False))
        
        return results
    
    def receive_ack(self, ack_num: int) -> bool:
        """
        接收ACK
        
        Args:
            ack_num: 确认的序列号
        
        Returns:
            是否成功
        """
        if ack_num in self.unacked:
            del self.unacked[ack_num]
            self.send_base = (ack_num + 1) % self.max_seq
            self.total_acked += 1
            return True
        return False
    
    def receive_packet(self, packet: Packet) -> Tuple[bool, Optional[bytes]]:
        """
        接收数据包
        
        Args:
            packet: 收到的包
        
        Returns:
            (accept, deliver_data)
        """
        # 顺序接收
        if packet.seq_num == self.recv_base:
            # 顺序正确，交付
            self.recv_base = (self.recv_base + 1) % self.max_seq
            return True, packet.data
        elif packet.seq_num in range(self.recv_base, self.recv_base + self.window_size):
            # 在窗口内，缓存
            self.received[packet.seq_num] = packet
            return False, None
        else:
            # 窗口外，丢弃
            return False, None


class ReedSolomonFEC:
    """
    Reed-Solomon前向纠错码
    
    RS(n, k)码：
    - 输入k个符号
    - 输出n个符号
    - 可以恢复任意min(n-k, t)个丢失符号
    
    特点：
    - 适用于块传输
    - 广泛用于存储、广播、传输
    """
    
    def __init__(self, n: int = 255, k: int = 223):
        """
        初始化RS码
        
        Args:
            n: 编码后符号数
            k: 原始符号数
        """
        self.n = n
        self.k = k
        self.redundancy = n - k
        
        # 简化实现：使用异或和校验
        self.field_size = 256
    
    def encode(self, data: bytes) -> List[bytes]:
        """
        编码
        
        Args:
            data: 原始数据（长度应为k的倍数）
        
        Returns:
            n个符号的列表
        """
        # 填充到k的倍数
        padding = (self.k - len(data) % self.k) % self.k
        data += b'\x00' * padding
        
        symbols = []
        for i in range(0, len(data), self.k):
            block = data[i:i + self.k]
            encoded = self._encode_block(block)
            symbols.extend(encoded)
        
        return symbols
    
    def _encode_block(self, block: bytes) -> List[bytes]:
        """编码单个块"""
        # 生成校验符号（简化版：异或和）
        n_syms = []
        
        # 前k个是原始数据
        for i in range(self.k):
            if i < len(block):
                n_syms.append(bytes([block[i]]))
            else:
                n_syms.append(bytes([0]))
        
        # 添加n-k个校验符号
        for p in range(self.n - self.k):
            checksum = 0
            for s in n_syms:
                checksum ^= s[0]
            n_syms.append(bytes([checksum]))
        
        return n_syms
    
    def decode(self, symbols: List[bytes], erasures: List[int] = None) -> Optional[bytes]:
        """
        解码
        
        Args:
            symbols: 接收到的符号
            erasures: 已知丢失的位置（可选）
        
        Returns:
            解码后的数据
        """
        if len(symbols) < self.k:
            return None  # 不可恢复
        
        # 简化：直接取前k个非丢失符号
        recovered = []
        for i in range(self.k):
            if i < len(symbols) and symbols[i]:
                recovered.append(symbols[i])
            else:
                # 丢失：尝试恢复
                recovered.append(bytes([0]))  # 简化
        
        return b''.join(recovered)


class HybridARQFEC:
    """
    混合ARQ-FEC方案
    
    策略：
    - FEC提供基础保护
    - ARQ处理极端丢包
    - 自适应调整FEC级别
    """
    
    def __init__(self, fec_redundancy: float = 0.2):
        """
        初始化
        
        Args:
            fec_redundancy: FEC冗余度（0.2=20%额外数据）
        """
        self.fec_redundancy = fec_redundancy
        self.rs = ReedSolomonFEC()
        
        # 丢包率估计
        self.estimated_loss = 0.0
        
        # 统计
        self.total_sent = 0
        self.total_recovered_fec = 0
        self.total_recovered_arq = 0
        self.total_failed = 0
    
    def send_with_fec(self, data: bytes) -> int:
        """
        发送数据（带FEC）
        
        Returns:
            发送的包数
        """
        # 编码
        symbols = self.rs.encode(data)
        
        # 添加FEC冗余
        fec_symbols = self._generate_fec(symbols)
        all_symbols = symbols + fec_symbols
        
        self.total_sent += len(all_symbols)
        
        # 模拟传输
        received = self._simulate传输(all_symbols)
        
        # FEC恢复
        recovered = self._fec_recover(received)
        
        if recovered:
            self.total_recovered_fec += 1
            return len(all_symbols)
        
        # ARQ恢复（重传丢失的包）
        if self._arq_recover(symbols):
            self.total_recovered_arq += 1
            return len(all_symbols) + self.fec_redundancy * len(symbols)
        
        self.total_failed += 1
        return len(all_symbols)
    
    def _generate_fec(self, symbols: List[bytes]) -> List[bytes]:
        """生成FEC冗余"""
        redundancy_count = int(len(symbols) * self.fec_redundancy)
        fec = []
        
        for i in range(redundancy_count):
            xor_sum = 0
            for s in symbols:
                xor_sum ^= s[0]
            fec.append(bytes([xor_sum]))
        
        return fec
    
    def _simulate传输(self, symbols: List[bytes]) -> List[bytes]:
        """模拟传输（带丢包）"""
        received = []
        for s in symbols:
            if random.random() < 0.9:  # 90%到达率
                received.append(s)
            else:
                received.append(None)  # 丢失
        return received
    
    def _fec_recover(self, received: List[bytes]) -> bool:
        """FEC恢复"""
        # 简化：只要有足够多的符号就能恢复
        valid_count = sum(1 for r in received if r is not None)
        return valid_count >= self.rs.k
    
    def _arq_recover(self, symbols: List[bytes]) -> bool:
        """ARQ恢复"""
        # 简化
        return random.random() < 0.5


def simulate_arq():
    """
    模拟ARQ协议
    """
    print("=== ARQ协议模拟 ===\n")
    
    # 停止等待ARQ
    saw = StopAndWaitARQ()
    
    print("停止等待ARQ模拟:")
    print(f"  超时: {saw.timeout}s, 最大重传: {saw.max_retries}")
    
    # 发送10个包
    for i in range(10):
        data = f"Packet-{i}".encode()
        success, attempts = saw.send(data)
        status = "成功" if success else "失败"
        print(f"  发送数据{i}: {status}, 尝试{attempts}次")
    
    print(f"\n统计:")
    print(f"  总发送: {saw.packets_sent}")
    print(f"  总确认: {saw.packets_acked}")
    print(f"  重传次数: {saw.retransmissions}")
    print(f"  超时次数: {saw.timeouts}")


def simulate_fec():
    """
    模拟FEC
    """
    print("\n=== FEC前向纠错模拟 ===\n")
    
    rs = ReedSolomonFEC(n=10, k=8)
    
    # 原始数据
    data = b"HelloWorld" * 10
    print(f"原始数据: {len(data)} bytes")
    
    # 编码
    symbols = rs.encode(data)
    print(f"编码后: {len(symbols)} 符号 (k={rs.k}, n={rs.n})")
    
    # 模拟丢包（丢失2个符号）
    received = symbols.copy()
    lost_indices = random.sample(range(len(symbols)), 2)
    for idx in lost_indices:
        received[idx] = None
    
    print(f"丢失符号: {lost_indices}")
    
    # 解码
    decoded = rs.decode(received)
    if decoded:
        print(f"解码成功: {len(decoded)} bytes")
        print(f"恢复数据: {decoded[:50]}...")
    else:
        print("解码失败")


def compare_approaches():
    """
    比较ARQ、FEC、混合方案
    """
    print("\n=== 方案对比 ===\n")
    
    print("| 方案    | 冗余   | 延迟 | 适用场景            |")
    print("|---------|--------|------|---------------------|")
    print("| ARQ     | 可变   | 高   | 低丢包率，可变RTT    |")
    print("| FEC     | 固定   | 低   | 实时流，广播         |")
    print("| 混合    | 中等   | 中   | 中等丢包，需低延迟   |")
    
    print("\n吞吐率分析（丢包率10%）：")
    
    # ARQ
    arq_throughput = (1 - 0.1) ** 2  # 简化
    print(f"  纯ARQ: {arq_throughput:.2%} (需要重传)")
    
    # FEC
    fec_throughput = 1.0  # FEC无重传
    print(f"  纯FEC: {fec_throughput:.2%} (无重传，但有冗余)")
    
    # 混合
    hybrid_overhead = 1.0 + 0.2  # 20% FEC冗余
    hybrid_effective = 1.0 / hybrid_overhead
    print(f"  混合: {hybrid_effective:.2%} (20%FEC冗余)")


def demo_adaptive_fec():
    """
    演示自适应FEC
    """
    print("\n=== 自适应FEC演示 ===\n")
    
    hybrid = HybridARQFEC(fec_redundancy=0.2)
    
    # 模拟不同丢包率
    print("丢包率 | FEC恢复 | ARQ恢复 | 失败")
    print("-------|---------|---------|------")
    
    for loss_rate in [0.05, 0.10, 0.20, 0.30]:
        hybrid.estimated_loss = loss_rate
        
        fec_count = 0
        arq_count = 0
        fail_count = 0
        
        # 模拟100次传输
        for _ in range(100):
            data = b"X" * 100
            symbols = hybrid.rs.encode(data)
            
            # 模拟丢包
            received = [s if random.random() > loss_rate else None for s in symbols]
            
            # FEC恢复尝试
            if sum(1 for r in received if r is not None) >= hybrid.rs.k:
                fec_count += 1
            else:
                arq_count += 1
        
        print(f"  {loss_rate:.0%}   | {fec_count}     | {arq_count}     | {fail_count}")


if __name__ == "__main__":
    print("=" * 60)
    print("ARQ与FEC纠错算法")
    print("=" * 60)
    
    # ARQ模拟
    simulate_arq()
    
    # FEC模拟
    simulate_fec()
    
    # 方案对比
    compare_approaches()
    
    # 自适应FEC
    demo_adaptive_fec()
    
    print("\n" + "=" * 60)
    print("关键概念:")
    print("=" * 60)
    print("""
ARQ类型:
1. 停止等待(Stop-and-Wait):
   - 简单但效率低
   - 适合简单协议
   
2. 滑动窗口:
   - 回退N帧(Go-Back-N)
   - 选择性重传(Selective Repeat)
   - 效率高但实现复杂

FEC类型:
1. 分组码(Reed-Solomon):
   - 块纠错
   -广泛用于存储和广播
   
2. 卷积码:
   - 时序纠错
   - Viterbi解码

3. LDPC/Turbo码:
   - 近香农极限
   - 5G/卫星通信
""")
