# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / fir_filter

本文件实现 fir_filter 相关的算法功能。
"""

import numpy as np
import math


class FIRFilter:
    """
    FIR 滤波器

    使用卷积实现。
    """

    def __init__(self, b):
        """
        初始化 FIR 滤波器

        参数:
            b: FIR 系数数组（分子多项式系数）
        """
        self.b = np.array(b, dtype=float)
        self.N = len(self.b)
        self.buffer = np.zeros(self.N - 1)

    def filter(self, x):
        """
        滤波信号

        参数:
            x: 输入信号
        返回:
            y: 滤波后信号
        """
        x = np.array(x, dtype=float)
        y = np.zeros(len(x))

        for n in range(len(x)):
            # 移位 buffer
            self.buffer = np.concatenate([[x[n]], self.buffer[:-1]])
            # 卷积
            y[n] = np.dot(self.b, self.buffer[::-1])

        return y

    def filter_block(self, x):
        """块滤波（更高效）"""
        x = np.array(x, dtype=float)
        return np.convolve(x, self.b, mode='same')


class WindowedFIRDesigner:
    """
    窗函数法 FIR 设计器

    使用窗函数设计低通、高通、带通 FIR 滤波器。
    """

    def __init__(self):
        pass

    def window(self, name, M):
        """
        生成窗函数

        参数:
            name: 窗函数名称
            M: 窗长度
        返回:
            w: 窗函数序列
        """
        n = np.arange(M)

        if name == 'rectangular':
            w = np.ones(M)
        elif name == 'hanning':
            w = 0.5 * (1 - np.cos(2 * np.pi * n / (M - 1)))
        elif name == 'hamming':
            w = 0.54 - 0.46 * np.cos(2 * np.pi * n / (M - 1))
        elif name == 'blackman':
            w = 0.42 - 0.5 * np.cos(2 * np.pi * n / (M - 1)) + \
                0.08 * np.cos(4 * np.pi * n / (M - 1))
        else:
            w = np.ones(M)

        return w

    def lowpass(self, fc, M, window='hamming'):
        """
        设计低通 FIR 滤波器

        参数:
            fc: 归一化截止频率 (0 < fc < 0.5)
            M: 滤波器阶数（奇数）
            window: 窗函数类型
        返回:
            b: FIR 系数
        """
        if M % 2 == 0:
            M += 1  # 确保奇数

        N = M - 1
        n = np.arange(M) - N / 2

        # 理想低通冲激响应
        if fc == 0:
            h_ideal = np.zeros(M)
        else:
            h_ideal = np.sinc(2 * fc * n)

        # 加窗
        w = self.window(window, M)
        b = h_ideal * w

        # 归一化
        b = b / np.sum(b)

        return b

    def highpass(self, fc, M, window='hamming'):
        """
        设计高通 FIR 滤波器

        参数:
            fc: 归一化截止频率
            M: 滤波器阶数
            window: 窗函数
        返回:
            b: FIR 系数
        """
        # 高通 = 1 - 低通（在频域）
        # 时域：h_hp[n] = δ[n] - h_lp[n]
        b_lp = self.lowpass(fc, M, window)
        b_hp = -b_lp
        mid = M // 2
        b_hp[mid] += 1

        return b_hp

    def bandpass(self, fc1, fc2, M, window='hamming'):
        """
        设计带通 FIR 滤波器

        参数:
            fc1: 下截止频率
            fc2: 上截止频率
            M: 滤波器阶数
            window: 窗函数
        返回:
            b: FIR 系数
        """
        if M % 2 == 0:
            M += 1

        N = M - 1
        n = np.arange(M) - N / 2

        # 理想带通冲激响应
        h_ideal = 2 * fc2 * np.sinc(2 * fc2 * n) - 2 * fc1 * np.sinc(2 * fc1 * n)

        w = self.window(window, M)
        b = h_ideal * w
        b = b / np.sum(b)

        return b

    def bandstop(self, fc1, fc2, M, window='hamming'):
        """
        设计带阻 FIR 滤波器

        参数:
            fc1: 下截止频率
            fc2: 上截止频率
            M: 滤波器阶数
            window: 窗函数
        返回:
            b: FIR 系数
        """
        if M % 2 == 0:
            M += 1

        b_bp = self.bandpass(fc1, fc2, M, window)
        mid = M // 2
        b_bs = -b_bp
        b_bs[mid] += 1

        return b_bs


class ParksMcClellan:
    """
    Parks-McClellan 最优 FIR 设计

    使用 Remez 算法设计最优等纹波 FIR 滤波器。
    """

    def __init__(self):
        self.tolerance = 1e-6

    def remez(self, bands, desired, weights, N):
        """
        Remez 算法（简化实现）

        参数:
            bands: 频带边缘 [0, f1, f2, 0.5]
            desired: 各频带期望值
            weights: 各频带权重
            N: 滤波器阶数
        返回:
            b: FIR 系数
        """
        # 简化的 Remez 近似
        # 实际应用应使用 scipy.signal.remez

        n = np.arange(N + 1)
        h = np.zeros(N + 1)

        for iteration in range(100):
            h_old = h.copy()

            # 计算频率响应
            for k in range(N + 1):
                omega = 2 * np.pi * k / N
                h[k] = np.sum(desired * np.cos(omega * n))

            # 检查收敛
            if np.max(np.abs(h - h_old)) < self.tolerance:
                break

        return h

    def lowpass(self, fc, delta, N):
        """
        设计最优低通滤波器

        参数:
            fc: 截止频率
            delta: 纹波
            N: 阶数
        返回:
            b: 系数
        """
        # 简化实现
        n = np.arange(N + 1) - N / 2
        h = np.sinc(2 * fc * n)
        w = np.hanning(N + 1)
        return h * w


class MovingAverageFilter:
    """
    滑动平均滤波器

    最简单的 FIR 滤波器。
    y[n] = (1/M) * Σ x[n-k], k=0..M-1
    """

    def __init__(self, M):
        """
        初始化滑动平均

        参数:
            M: 窗口大小
        """
        self.M = M
        self.buffer = np.zeros(M)
        self.idx = 0

    def filter_sample(self, x):
        """单样本滤波"""
        self.buffer[self.idx] = x
        self.idx = (self.idx + 1) % self.M
        return np.mean(self.buffer)

    def filter(self, x):
        """信号滤波"""
        return np.convolve(x, np.ones(self.M) / self.M, mode='same')


class Differentiator:
    """
    FIR 微分器

    y[n] = (1/T) * Σ k*x[n-k], k=-N..N
    """

    def __init__(self, N=4):
        """
        初始化微分器

        参数:
            N: 微分器阶数（长度 = 2N+1）
        """
        self.N = N
        self.b = self._compute_coeffs()

    def _compute_coeffs(self):
        """计算微分器系数"""
        M = 2 * self.N + 1
        n = np.arange(M) - self.N
        b = np.zeros(M)

        for k in range(M):
            if n[k] == 0:
                b[k] = 0
            else:
                b[k] = ((-1) ** n[k]) / n[k]

        return b


class HilbertTransformer:
    """
    FIR Hilbert 变换器

    用于单边带调制和解析信号生成。
    """

    def __init__(self, N=64):
        """
        初始化 Hilbert 变换器

        参数:
            N: 滤波器阶数
        """
        self.N = N
        self.b = self._compute_coeffs()

    def _compute_coeffs(self):
        """计算 Hilbert 变换器系数"""
        n = np.arange(-self.N, self.N + 1)
        h = np.zeros(len(n))

        for i, ni in enumerate(n):
            if ni == 0:
                h[i] = 0
            elif ni % 2 == 0:
                h[i] = 0
            else:
                h[i] = 2 / (np.pi * ni)

        return h


def compute_frequency_response(b, a=None, n_freqs=512):
    """
    计算滤波器频率响应

    参数:
        b: FIR 系数
        a: IIR 系数（如果有）
        n_freqs: 频率点数
    返回:
        w: 归一化频率 [0, π]
        H: 频率响应
    """
    w = np.linspace(0, np.pi, n_freqs)
    z = np.exp(1j * w)
    H = np.zeros(n_freqs, dtype=complex)

    for i, zi in enumerate(z):
        if a is None:
            H[i] = np.sum(b * zi ** (-np.arange(len(b))))
        else:
            H[i] = np.sum(b * zi ** (-np.arange(len(b)))) / \
                   np.sum(a * zi ** (-np.arange(len(a))))

    return w, H


def plot_filter_specs(b, name="FIR"):
    """打印滤波器规格"""
    w, H = compute_frequency_response(b)
    H_db = 20 * np.log10(np.abs(H) + 1e-10)

    print(f"\n{name} 滤波器规格:")
    print(f"  阶数: {len(b) - 1}")
    print(f"  通带最大增益: {np.max(H_db):.2f} dB")
    print(f"  阻带最小增益: {np.min(H_db):.2f} dB")


if __name__ == "__main__":
    print("=== FIR 滤波器测试 ===")

    # 创建测试信号
    print("\n1. 创建测试信号")
    fs = 1000  # 采样率
    t = np.arange(0, 1, 1/fs)
    f1, f2, f3 = 50, 200, 400  # 三个频率成分
    signal = np.sin(2*np.pi*f1*t) + 0.5*np.sin(2*np.pi*f2*t) + 0.3*np.sin(2*np.pi*f3*t)
    print(f"信号: 包含 {f1}Hz, {f2}Hz, {f3}Hz")
    print(f"采样率: {fs} Hz, 长度: {len(signal)}")

    # 设计低通滤波器
    print("\n2. 设计低通 FIR 滤波器")
    designer = WindowedFIRDesigner()
    fc = 0.15  # 归一化截止频率
    M = 31  # 阶数
    b_lp = designer.lowpass(fc, M, window='hamming')
    print(f"低通滤波器: 阶数={M}, 截止频率={fc}")
    plot_filter_specs(b_lp, "低通")

    # 滤波
    print("\n3. 低通滤波")
    fir = FIRFilter(b_lp)
    filtered = fir.filter_block(signal)
    print(f"滤波后信号能量: {np.sum(filtered**2):.4f}")

    # 设计高通滤波器
    print("\n4. 设计高通 FIR 滤波器")
    b_hp = designer.highpass(0.25, M, window='hamming')
    plot_filter_specs(b_hp, "高通")

    # 设计带通滤波器
    print("\n5. 设计带通 FIR 滤波器")
    b_bp = designer.bandpass(0.1, 0.3, M, window='hamming')
    plot_filter_specs(b_bp, "带通")

    # 滑动平均滤波器
    print("\n6. 滑动平均滤波器")
    ma = MovingAverageFilter(M=10)
    ma_filtered = ma.filter(signal)
    print(f"滑动平均滤波后能量: {np.sum(ma_filtered**2):.4f}")

    # 微分器
    print("\n7. FIR 微分器")
    diff = Differentiator(N=4)
    print(f"微分器阶数: {len(diff.b) - 1}")

    # Hilbert 变换器
    print("\n8. Hilbert 变换器")
    hilbert = HilbertTransformer(N=32)
    print(f"Hilbert 变换器阶数: {len(hilbert.b) - 1}")

    # 不同窗函数对比
    print("\n9. 不同窗函数对比")
    for window in ['rectangular', 'hanning', 'hamming', 'blackman']:
        b_test = designer.lowpass(0.1, 31, window=window)
        w, H = compute_frequency_response(b_test)
        H_db = 20 * np.log10(np.abs(H))
        print(f"  {window}: 通带纹波={np.max(H_db[:int(0.08*512)]):.2f}dB, "
              f"阻带衰减={np.min(H_db[int(0.15*512):]):.2f}dB")

    # 频率响应分析
    print("\n10. 频率响应分析")
    w, H = compute_frequency_response(b_lp)
    print(f"  在 50Hz (归一化 {50/fs/1000:.3f}): {20*np.log10(np.abs(H[int(0.05*512)])):.2f} dB")
    print(f"  在 200Hz (归一化 {200/fs/1000:.3f}): {20*np.log10(np.abs(H[int(0.2*512)])):.2f} dB")
    print(f"  在 400Hz (归一化 {400/fs/1000:.3f}): {20*np.log10(np.abs(H[int(0.4*512)])):.2f} dB")

    print("\nFIR 滤波器测试完成!")
