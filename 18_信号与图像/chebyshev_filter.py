# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / chebyshev_filter

本文件实现 chebyshev_filter 相关的算法功能。
"""

import numpy as np
import math


class ChebyshevFilter:
    """
    Chebyshev I 型滤波器

    通带等纹波，阻带单调。
    """

    def __init__(self, order=4, cutoff=0.5, rp=0.5):
        """
        初始化 Chebyshev I 型滤波器

        参数:
            order: 滤波器阶数
            cutoff: 归一化截止频率
            rp: 通带纹波 (dB)
        """
        self.order = order
        self.cutoff = cutoff
        self.rp = rp
        self.b = None
        self.a = None
        self._design()

    def _design(self):
        """设计 Chebyshev I 型滤波器"""
        n = self.order
        rp = self.rp

        # 计算纹波因子
        eps = np.sqrt(10**(rp/10) - 1)

        # 计算极点
        theta = np.pi * (2*np.arange(1, n+1) - 1) / (2*n)
        u_sinh = np.arcsinh(1/eps) / n
        v_cosh = np.arccosh(1/eps) / n

        poles = []
        for th in theta:
            sigma = -np.sinh(u_sinh) * np.sin(th)
            omega = np.cosh(u_sinh) * np.cos(th)
            poles.append(complex(sigma, omega))

        # 双线性变换
        T = 1.0
        wc = self.cutoff * np.pi
        k_analog = 2 / T

        z_poles = []
        for p in poles:
            z_p = (1 + k_analog * p / (2*wc)) / (1 - k_analog * p / (2*wc))
            z_poles.append(z_p)

        # 构建多项式
        b = [1.0]
        a = np.poly(z_poles).real

        # 增益调整（在 z=1 处）
        z1_pow_b = np.array([1 ** k for k in range(len(b))]).T
        z1_pow_a = np.array([1 ** k for k in range(len(a))]).T
        H_z1 = np.dot(z1_pow_b, b) / np.dot(z1_pow_a, a)
        gain = 1.0 / abs(H_z1)
        b = [x * gain for x in b]

        self.b = np.array(b)
        self.a = a

    def filter(self, x):
        """滤波信号"""
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
        w = np.linspace(0, np.pi, n_points)
        z = np.exp(1j * w)
        z_pow_b = np.array([z ** k for k in range(len(self.b))]).T
        z_pow_a = np.array([z ** k for k in range(len(self.a))]).T
        H = np.dot(z_pow_b, self.b) / np.dot(z_pow_a, self.a)
        return w, H


class Chebyshev2Filter:
    """
    Chebyshev II 型滤波器

    通带单调，阻带等纹波。
    """

    def __init__(self, order=4, cutoff=0.5, rs=40):
        """
        初始化 Chebyshev II 型滤波器

        参数:
            order: 阶数
            cutoff: 归一化截止频率
            rs: 阻带衰减 (dB)
        """
        self.order = order
        self.cutoff = cutoff
        self.rs = rs
        self.b = None
        self.a = None
        self._design()

    def _design(self):
        """设计 Chebyshev II 型滤波器"""
        n = self.order
        rs = self.rs

        # 阻带纹波因子
        eps = 1 / np.sqrt(10**(rs/10) - 1)

        # 计算极点
        theta = np.pi * (2*np.arange(1, n+1) - 1) / (2*n)
        u_sinh = np.arcsinh(1/eps) / n
        v_cosh = np.arccosh(1/eps) / n

        # 虚轴极点（用于阻带）
        poles = []
        zeros = []
        for th in theta:
            sigma = -np.sinh(u_sinh) * np.sin(th)
            omega = np.cosh(u_sinh) * np.cos(th)
            poles.append(complex(-sigma, omega))
            zeros.append(complex(0, 1/np.tan(th/2)))

        # 双线性变换
        T = 1.0
        wc = self.cutoff * np.pi
        k_analog = 2 / T

        z_poles = []
        for p in poles:
            z_p = (1 + k_analog * p / (2*wc)) / (1 - k_analog * p / (2*wc))
            z_poles.append(z_p)

        z_zeros = []
        for z in zeros:
            z_z = (1 + k_analog * z / (2*wc)) / (1 - k_analog * z / (2*wc))
            z_zeros.append(z_z)

        b = np.poly(z_zeros).real
        a = np.poly(z_poles).real

        self.b = b
        self.a = a

    def filter(self, x):
        """滤波"""
        return ChebyshevFilter(self.order, self.cutoff, self.rs).filter(x)


def chebyshev1_lowpass(signal, cutoff, order=4, rp=0.5):
    """
    Chebyshev I 型低通滤波

    参数:
        signal: 输入信号
        cutoff: 归一化截止频率
        order: 阶数
        rp: 通带纹波 (dB)
    返回:
        filtered: 滤波后信号
    """
    filt = ChebyshevFilter(order, cutoff, rp)
    return filt.filter(signal)


def chebyshev2_lowpass(signal, cutoff, order=4, rs=40):
    """
    Chebyshev II 型低通滤波

    参数:
        signal: 输入信号
        cutoff: 归一化截止频率
        order: 阶数
        rs: 阻带衰减 (dB)
    返回:
        filtered: 滤波后信号
    """
    filt = Chebyshev2Filter(order, cutoff, rs)
    return filt.filter(signal)


class FilterComparator:
    """
    滤波器比较器

    比较 Butterworth 和 Chebyshev 滤波器的特性。
    """

    @staticmethod
    def compare_ripple():
        """比较纹波特性"""
        print("=== 滤波器纹波对比 ===")

        signals = [
            ("Butterworth 4阶", "butterworth"),
            ("Chebyshev I 4阶 1dB纹波", "chebyshev1_1db"),
            ("Chebyshev I 4阶 3dB纹波", "chebyshev1_3db"),
            ("Chebyshev II 4阶 40dB衰减", "chebyshev2"),
        ]

        for name, ftype in signals:
            print(f"\n{name}:")
            if ftype == "butterworth":
                filt = __import__('butterworth_filter', fromlist=['ButterworthFilter']).ButterworthFilter(4, 0.15)
            elif "chebyshev1_1db" in ftype:
                filt = ChebyshevFilter(4, 0.15, 1.0)
            elif "chebyshev1_3db" in ftype:
                filt = ChebyshevFilter(4, 0.15, 3.0)
            else:
                filt = Chebyshev2Filter(4, 0.15, 40)

            w, H = filt.freq_response()
            H_db = 20 * np.log10(np.abs(H))
            print(f"  通带(0.10)最大纹波: {np.max(H_db[:int(0.10*512)]) - np.min(H_db[:int(0.10*512)]):.2f} dB")
            print(f"  截止(0.15)衰减: {H_db[int(0.15*512)]:.2f} dB")
            print(f"  阻带(0.20)衰减: {H_db[int(0.20*512)]:.2f} dB")


if __name__ == "__main__":
    print("=== Chebyshev 滤波器测试 ===")

    # 创建测试信号
    print("\n1. 创建测试信号")
    fs = 1000
    t = np.arange(0, 1, 1/fs)
    signal = np.sin(2*np.pi*50*t) + 0.5*np.sin(2*np.pi*150*t) + 0.3*np.sin(2*np.pi*300*t)
    print(f"信号包含: 50Hz, 150Hz, 300Hz")

    # Chebyshev I 型
    print("\n2. Chebyshev I 型滤波器")
    cheb1 = ChebyshevFilter(order=4, cutoff=0.12, rp=1.0)
    w, H = cheb1.freq_response()
    H_db = 20 * np.log10(np.abs(H))
    print(f"阶数: {cheb1.order}, 截止: {cheb1.cutoff}, 纹波: {cheb1.rp}dB")
    print(f"通带(0.10)最大增益: {np.max(H_db[:int(0.10*512)]):.2f} dB")
    print(f"通带(0.10)纹波: {np.max(H_db[:int(0.10*512)]) - np.min(H_db[:int(0.10*512)]):.4f} dB")

    # 滤波
    print("\n3. Chebyshev I 滤波")
    filtered1 = cheb1.filter(signal)
    print(f"原始能量: {np.sum(signal**2):.4f}")
    print(f"滤波后能量: {np.sum(filtered1**2):.4f}")

    # Chebyshev II 型
    print("\n4. Chebyshev II 型滤波器")
    cheb2 = Chebyshev2Filter(order=4, cutoff=0.12, rs=40)
    w2, H2 = cheb2.freq_response()
    H2_db = 20 * np.log10(np.abs(H2))
    print(f"阻带衰减: {H2_db[int(0.15*512)]:.2f} dB")

    # 不同纹波对比
    print("\n5. 不同纹波对比")
    for rp in [0.5, 1.0, 2.0, 3.0]:
        filt = ChebyshevFilter(4, 0.12, rp)
        w, H = filt.freq_response()
        H_db = 20 * np.log10(np.abs(H))
        print(f"  Chebyshev I rp={rp}dB: "
              f"通带纹波={np.max(H_db[:int(0.10*512)]) - np.min(H_db[:int(0.10*512)]):.2f}dB, "
              f"阻带={H_db[int(0.15*512)]:.2f}dB")

    # 不同阶数对比
    print("\n6. 不同阶数对比 (Chebyshev I)")
    for order in [2, 4, 6, 8]:
        filt = ChebyshevFilter(order, 0.12, 1.0)
        w, H = filt.freq_response()
        H_db = 20 * np.log10(np.abs(H))
        print(f"  阶数 {order}: 阻带衰减={H_db[int(0.15*512)]:.2f}dB")

    # 简化函数测试
    print("\n7. 简化函数测试")
    filtered_cheb1 = chebyshev1_lowpass(signal, 0.12, 4, 1.0)
    filtered_cheb2 = chebyshev2_lowpass(signal, 0.12, 4, 40)
    print(f"Chebyshev I 滤波后能量: {np.sum(filtered_cheb1**2):.4f}")
    print(f"Chebyshev II 滤波后能量: {np.sum(filtered_cheb2**2):.4f}")

    # 稳定性检查
    print("\n8. 稳定性检查")
    poles = np.roots(cheb1.a)
    print(f"Chebyshev I 极点模最大值: {np.max(np.abs(poles)):.4f}")
    print(f"稳定: {np.all(np.abs(poles) < 1)}")

    print("\nChebyshev 滤波器测试完成!")
