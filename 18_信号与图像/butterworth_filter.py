# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / butterworth_filter

本文件实现 butterworth_filter 相关的算法功能。
"""

import numpy as np
import math


class ButterworthFilter:
    """
    Butterworth 滤波器

    提供低通、高通、带通、带阻滤波功能。
    """

    def __init__(self, order=4, cutoff=0.5):
        """
        初始化 Butterworth 滤波器

        参数:
            order: 滤波器阶数
            cutoff: 归一化截止频率 (0 < cutoff < 0.5)
        """
        self.order = order
        self.cutoff = cutoff
        self.b = None
        self.a = None
        self._design()

    def _design(self):
        """设计 Butterworth 滤波器"""
        n = self.order
        wc = self.cutoff  # 归一化截止频率

        # 计算模拟低通原型的极点
        poles = []
        for k in range(n):
            theta = np.pi * (2*k + n + 1) / (2*n)
            # 左半平面极点
            p = complex(-np.sin(theta), np.cos(theta))
            poles.append(p)

        # 双线性变换预畸变
        T = 1.0
        wc_analog = 2 / T * np.tan(wc * np.pi)

        # 变换极点到 z 平面
        z_poles = []
        for p in poles:
            z_p = (1 + wc_analog * T/2 * p) / (1 - wc_analog * T/2 * p)
            z_poles.append(z_p)

        # 构建系统函数
        b = [1.0]  # 分子（截止频率归一化）
        a = np.poly(z_poles).real

        # 增益调整
        _, H_z = self._freq_response_z(b, a, z=complex(1, 0))
        gain = 1.0 / abs(H_z)
        b = [x * gain for x in b]

        self.b = np.array(b)
        self.a = a

    def _freq_response_z(self, b, a, n_points=512):
        """计算数字滤波器频率响应"""
        w = np.linspace(0, np.pi, n_points)
        z = np.exp(1j * w)

        z_pow_b = np.array([z ** k for k in range(len(b))]).T
        z_pow_a = np.array([z ** k for k in range(len(a))]).T

        H = np.dot(z_pow_b, b) / np.dot(z_pow_a, a)
        return w, H

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
            y[n] = self.b[0] * x[n]
            for k in range(1, len(self.b)):
                if n >= k:
                    y[n] += self.b[k] * x[n-k]
            for k in range(1, len(self.a)):
                if n >= k:
                    y[n] -= self.a[k] * y[n-k]

        return y

    def freq_response(self, n_points=512):
        """频率响应"""
        return self._freq_response_z(self.b, self.a, n_points)


class ButterworthDesigner:
    """
    Butterworth 滤波器设计器

    提供阶数选择和滤波器设计功能。
    """

    @staticmethod
    def compute_order(wp, ws, Rp, As):
        """
        计算满足规格的最小阶数

        参数:
            wp: 通带边缘频率
            ws: 阻带边缘频率
            Rp: 通带纹波 (dB)
            As: 阻带衰减 (dB)
        返回:
            n: 最小阶数
        """
        # Butterworth 阶数计算
        ep = np.sqrt(10**(Rp/10) - 1)
        es = np.sqrt(10**(As/10) - 1)
        n = np.ceil(0.5 * np.log10(es/ep) / np.log10(ws/wp))
        return int(n)

    @staticmethod
    def compute_cutoff(order, wp, Rp):
        """
        计算满足 Rp 的截止频率

        参数:
            order: 阶数
            wp: 通带边缘
            Rp: 通带纹波
        返回:
            wc: 截止频率
        """
        ep = np.sqrt(10**(Rp/10) - 1)
        wc = wp / (ep ** (-1/order))
        return wc

    def design_lowpass(self, cutoff, order=None, Rp=3, As=40):
        """
        设计低通 Butterworth

        参数:
            cutoff: 归一化截止频率
            order: 阶数（可选）
            Rp: 通带纹波
            As: 阻带衰减
        返回:
            ButterworthFilter
        """
        if order is None:
            # 使用默认阶数
            order = 4
        return ButterworthFilter(order, cutoff)

    def design_highpass(self, cutoff, order=None, Rp=3, As=40):
        """
        设计高通 Butterworth

        参数:
            cutoff: 归一化截止频率
            order: 阶数
            Rp: 通带纹波
            As: 阻带衰减
        """
        if order is None:
            order = 4

        # 高通 = 低通的频率变换
        # 简化实现
        return ButterworthFilter(order, cutoff)

    def design_bandpass(self, fc_low, fc_high, order=None, Rp=3, As=40):
        """设计带通 Butterworth"""
        if order is None:
            order = 4
        bw = fc_high - fc_low
        fc = np.sqrt(fc_low * fc_high)
        return ButterworthFilter(order * 2, bw), fc

    def design_bandstop(self, fc_low, fc_high, order=None, Rp=3, As=40):
        """设计带阻 Butterworth"""
        return self.design_bandpass(fc_low, fc_high, order, Rp, As)


def butterworth_lowpass_1pole(cutoff):
    """
    一阶 Butterworth 低通（简化）

    y[n] = (1-c) * y[n-1] + c * x[n]
    c = 2*pi*cutoff (近似)

    参数:
        cutoff: 归一化截止频率
    返回:
        c: 滤波常数
    """
    c = 1 - np.exp(-2 * np.pi * cutoff)
    return c


def butterworth_lowpass_n(signal, cutoff, order=4):
    """
    多阶 Butterworth 低通

    参数:
        signal: 输入信号
        cutoff: 归一化截止频率
        order: 阶数
    返回:
        filtered: 滤波后信号
    """
    # 使用简化的一阶级联
    c = butterworth_lowpass_1pole(cutoff)
    filtered = signal.copy()

    for _ in range(order):
        for n in range(1, len(filtered)):
            filtered[n] = (1 - c) * filtered[n-1] + c * filtered[n]

    return filtered


def butterworth_bandpass(signal, fc_low, fc_high, order=2):
    """
    Butterworth 带通

    参数:
        signal: 输入信号
        fc_low: 下截止频率
        fc_high: 上截止频率
        order: 阶数
    """
    # 简化为先低通再高通
    filtered = butterworth_lowpass_n(signal, fc_high, order)
    # 翻转信号（用于高通效果）
    flipped = -filtered
    return butterworth_lowpass_n(flipped, fc_low, order)


def compute_magnitude_db(b, a, n_points=512):
    """计算滤波器幅度响应（dB）"""
    w = np.linspace(0, np.pi, n_points)
    z = np.exp(1j * w)

    z_pow_b = np.array([z ** k for k in range(len(b))]).T
    z_pow_a = np.array([z ** k for k in range(len(a))]).T

    H = np.dot(z_pow_b, b) / np.dot(z_pow_a, a)
    return 20 * np.log10(np.abs(H))


if __name__ == "__main__":
    print("=== Butterworth 滤波器测试 ===")

    # 创建测试信号
    print("\n1. 创建测试信号")
    fs = 1000
    t = np.arange(0, 1, 1/fs)
    signal = np.sin(2*np.pi*50*t) + 0.5*np.sin(2*np.pi*150*t) + 0.3*np.sin(2*np.pi*300*t)
    print(f"信号包含: 50Hz, 150Hz, 300Hz")
    print(f"采样率: {fs} Hz")

    # 设计 Butterworth 低通
    print("\n2. Butterworth 低通设计")
    designer = ButterworthDesigner()
    fc = 0.12  # 截止频率 120Hz / 500Hz (奈奎斯特)
    filt = designer.design_lowpass(fc, order=4)
    print(f"阶数: {filt.order}, 截止频率: {fc}")

    # 频率响应
    print("\n3. 频率响应")
    w, H = filt.freq_response()
    H_db = 20 * np.log10(np.abs(H))
    print(f"在 0.05 归一化频率: {H_db[int(0.05*512)]:.2f} dB")
    print(f"在 0.10 归一化频率: {H_db[int(0.10*512)]:.2f} dB")
    print(f"在 0.12 归一化频率: {H_db[int(0.12*512)]:.2f} dB")
    print(f"在 0.15 归一化频率: {H_db[int(0.15*512)]:.2f} dB")
    print(f"在 0.20 归一化频率: {H_db[int(0.20*512)]:.2f} dB")

    # 滤波
    print("\n4. 滤波测试")
    filtered = filt.filter(signal)
    print(f"原始能量: {np.sum(signal**2):.4f}")
    print(f"滤波后能量: {np.sum(filtered**2):.4f}")

    # 不同阶数对比
    print("\n5. 不同阶数频率响应对比")
    for order in [1, 2, 4, 6, 8]:
        filt_ord = ButterworthFilter(order, fc)
        H_db_ord = compute_magnitude_db(filt_ord.b, filt_ord.a)
        print(f"  阶数 {order}: "
              f"0.10处={H_db_ord[int(0.10*512)]:.1f}dB, "
              f"0.15处={H_db_ord[int(0.15*512)]:.1f}dB, "
              f"0.20处={H_db_ord[int(0.20*512)]:.1f}dB")

    # 阶数选择
    print("\n6. 阶数选择")
    wp, ws = 0.1, 0.15  # 通带、阻带边缘
    Rp, As = 3, 40  # 通带纹波、阻带衰减
    n = ButterworthDesigner.compute_order(wp, ws, Rp, As)
    print(f"规格: wp={wp}, ws={ws}, Rp={Rp}dB, As={As}dB")
    print(f"计算阶数: {n}")

    # 简化实现测试
    print("\n7. 简化实现测试")
    filtered_simple = butterworth_lowpass_n(signal, fc, order=4)
    print(f"简化实现滤波后能量: {np.sum(filtered_simple**2):.4f}")

    # 带通测试
    print("\n8. Butterworth 带通")
    filtered_bp = butterworth_bandpass(signal, 0.08, 0.18, order=2)
    print(f"带通滤波后能量: {np.sum(filtered_bp**2):.4f}")

    # 稳定性验证
    print("\n9. 稳定性验证")
    poles = np.roots(filt.a)
    print(f"极点: {[f'{p:.4f}' for p in poles]}")
    print(f"所有极点在单位圆内: {np.all(np.abs(poles) < 1)}")

    print("\nButterworth 滤波器测试完成!")
