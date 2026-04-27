# -*- coding: utf-8 -*-
"""
算法实现：密码学与安全 / side_channel_attack

本文件实现 side_channel_attack 相关的算法功能。
"""

import random
from typing import List, Tuple
import numpy as np


class PowerTraceCollector:
    """功耗轨迹收集器（模拟）"""

    def __init__(self, n_samples: int = 1000):
        """
        初始化收集器

        参数：
            n_samples: 采样点数
        """
        self.n_samples = n_samples
        self.traces = []
        self.plaintexts = []

    def collect_trace(self, plaintext: bytes, key_byte: int) -> List[float]:
        """
        收集一次功耗轨迹

        参数：
            plaintext: 明文
            key_byte: 猜测的密钥字节

        返回：功耗轨迹
        """
        # 模拟功耗轨迹（实际中需要示波器）
        trace = []

        for i in range(self.n_samples):
            # 模拟AES S盒查表功耗
            sbox_input = plaintext[key_byte % len(plaintext)]
            sbox_output = (sbox_input ^ (i % 256))  # 简化

            # 功耗模型：汉明重量（1的个数）
            hamming_weight = bin(sbox_output).count('1')

            # 添加噪声
            noise = random.gauss(0, 0.5)
            power = hamming_weight + noise

            trace.append(power)

        self.traces.append(trace)
        self.plaintexts.append(plaintext)

        return trace

    def collect_dataset(self, n_traces: int, key_byte: int) -> Tuple[List[List[float]], List[bytes]]:
        """
        收集数据集

        参数：
            n_traces: 轨迹数量
            key_byte: 密钥字节

        返回：(轨迹集, 明文集)
        """
        for _ in range(n_traces):
            plaintext = bytes([random.randint(0, 255) for _ in range(16)])
            self.collect_trace(plaintext, key_byte)

        return self.traces, self.plaintexts


class DifferentialPowerAnalysis:
    """差分功耗分析"""

    def __init__(self, traces: List[List[float]], plaintexts: List[bytes]):
        """
        初始化DPA

        参数：
            traces: 功耗轨迹列表
            plaintexts: 对应的明文列表
        """
        self.traces = traces
        self.plaintexts = plaintexts
        self.n_traces = len(traces)
        self.n_samples = len(traces[0]) if traces else 0

    def compute_difference(self, guess: int, bit_position: int) -> List[float]:
        """
        计算差分功耗

        参数：
            guess: 猜测的密钥
            bit_position: 分析的位位置

        返回：差分轨迹
        """
        # 分组：根据S盒输出某位分组
        group_0 = []  # 输出该位为0
        group_1 = []  # 输出该位为1

        for trace, pt in zip(self.traces, self.plaintexts):
            # 简化的S盒输出
            sbox_output = pt[0] ^ guess
            output_bit = (sbox_output >> bit_position) & 1

            if output_bit == 0:
                group_0.append(trace)
            else:
                group_1.append(trace)

        # 计算平均值差异
        diff_trace = []
        for sample_idx in range(self.n_samples):
            avg_0 = sum(t[sample_idx] for t in group_0) / len(group_0) if group_0 else 0
            avg_1 = sum(t[sample_idx] for t in group_1) / len(group_1) if group_1 else 0
            diff_trace.append(avg_1 - avg_0)

        return diff_trace

    def attack(self, key_range: int = 256) -> Tuple[int, float]:
        """
        执行DPA攻击

        参数：
            key_range: 密钥空间大小

        返回：(猜测的密钥, 最大差分峰值)
        """
        best_guess = 0
        max_peak = 0

        for guess in range(key_range):
            # 分析8个位位置
            for bit_pos in range(8):
                diff = self.compute_difference(guess, bit_pos)
                peak = max(abs(d) for d in diff)

                if peak > max_peak:
                    max_peak = peak
                    best_guess = guess

        return best_peak, max_peak


class CorrelationPowerAnalysis:
    """相关功耗分析（CPA）"""

    def __init__(self, traces: List[List[float]], plaintexts: List[bytes]):
        """
        初始化CPA

        参数：
            traces: 功耗轨迹列表
            plaintexts: 对应的明文列表
        """
        self.traces = traces
        self.plaintexts = plaintexts
        self.n_traces = len(traces)

    def hamming_weight_model(self, data: int) -> float:
        """
        汉明重量功耗模型

        参数：
            data: 数据字节

        返回：预测功耗
        """
        return bin(data).count('1') / 8.0

    def correlate(self, x: List[float], y: List[float]) -> float:
        """
        计算皮尔逊相关系数

        参数：
            x: 功耗轨迹
            y: 预测功耗

        返回：相关系数
        """
        n = len(x)
        mean_x = sum(x) / n
        mean_y = sum(y) / n

        num = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        den_x = sum((x[i] - mean_x) ** 2 for i in range(n)) ** 0.5
        den_y = sum((y[i] - mean_y) ** 2 for i in range(n)) ** 0.5

        if den_x * den_y == 0:
            return 0

        return num / (den_x * den_y)

    def attack(self, key_byte_position: int = 0) -> Tuple[int, float]:
        """
        执行CPA攻击

        参数：
            key_byte_position: 目标密钥字节位置

        返回：(猜测的密钥, 最大相关系数)
        """
        n_samples = len(self.traces[0])
        best_guess = 0
        best_corr = 0

        for guess in range(256):
            # 预测功耗模型
            predictions = []
            for pt in self.plaintexts:
                # S盒输出（简化）
                sbox_output = pt[key_byte_position] ^ guess
                predictions.append(self.hamming_weight_model(sbox_output))

            # 对每个采样点计算相关性
            max_corr_for_guess = 0
            for sample_idx in range(min(n_samples, 100)):  # 简化：只检查前100点
                trace_values = [t[sample_idx] for t in self.traces]
                corr = abs(self.correlate(trace_values, predictions))

                if corr > max_corr_for_guess:
                    max_corr_for_guess = corr

            if max_corr_for_guess > best_corr:
                best_corr = max_corr_for_guess
                best_guess = guess

        return best_guess, best_corr


def countermeasure_introduction():
    """防御措施介绍"""
    print("=== 侧信道防御措施 ===")
    print()
    print("1. 掩码技术")
    print("   - 将敏感数据与随机掩码异或")
    print("   - 使功耗与数据无关")
    print()
    print("2. 隐藏技术")
    print("   - 随机化操作顺序")
    print("   - 添加随机延迟")
    print()
    print("3. 恒定时间实现")
    print("   - 避免分支和缓存访问")
    print("   - 使执行时间恒定")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 侧信道功耗分析测试 ===\n")

    # 模拟功耗轨迹收集
    collector = PowerTraceCollector(n_samples=500)
    traces, plaintexts = collector.collect_dataset(n_traces=50, key_byte=0)

    print(f"收集轨迹数: {len(traces)}")
    print(f"每条轨迹采样点: {len(traces[0])}")
    print()

    # CPA攻击演示
    cpa = CorrelationPowerAnalysis(traces, plaintexts)
    guess, corr = cpa.attack(key_byte_position=0)

    print(f"CPA攻击结果:")
    print(f"  猜测密钥: {guess}")
    print(f"  相关系数: {corr:.4f}")
    print()

    # 防御措施
    countermeasure_introduction()

    print()
    print("说明：")
    print("  - 侧信道攻击是非侵入式攻击")
    print("  - 需要物理接触设备")
    print("  - 防御比攻击更复杂")
