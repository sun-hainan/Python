# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / iir_filter

本文件实现 iir_filter 相关的算法功能。
"""

import numpy as np
import math


class IIRFilter:
    """
    IIR 滤波器

    实现直接 II 型结构。
    """

    def __init__(self, b, a):
        """
        初始化 IIR 滤波器

        参数:
            b: 前向系数 [b0, b1, ..., bM]
            a: 反馈系数 [a0, a1, ..., aN] (a0 通常为 1)
        """
        self.b = np.array(b, dtype=float)
        self.a = np.array(a, dtype=float)
        self.M = len(self.b) - 1
        self.N = len(self.a) - 1
        self.buffer = np.zeros(max(self.M, self.N))

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
        a_norm = self.a / self.a[0]
        b_norm = self.b / self.a[0]

        for n in range(len(x)):
            # 更新 buffer（直接 II 型）
            y_n = np.dot(b_norm, np.concatenate([[x[n]], -y[n-self.N:n][::-1][:self.M]]))
            y[n] = y_n

        return y

    def filter_sample(self, x):
        """单样本滤波"""
        b_norm = self.b / self.a[0]
        y_n = b_norm[0] * x
        for k in range(1, len(b_norm)):
            y_n += b_norm[k] * self.buffer[k - 1]

        # 更新反馈
        for k in range(1, len(self.a)):
            y_n -= self.a[k] / self.a[0] * self.buffer[k - 1]

        # 移位 buffer
        self.buffer = np.concatenate([[y_n], self.buffer[:-1]])
        return y_n

    def freq_response(self, n_freqs=512):
        """
        计算频率响应

        返回:
            w: 频率
            H: 频率响应
        """
        w = np.linspace(0, np.pi, n_freqs)
        z = np.exp(1j * w)

        z_pow_b = np.array([z ** k for k in range(len(self.b))]).T
        z_pow_a = np.array([z ** k for k in range(len(self.a))]).T

        H = np.dot(z_pow_b, self.b) / np.dot(z_pow_a, self.a)
        return w, H

    def group_delay(self, n_freqs=512):
        """
        计算群延迟

        返回:
            w: 频率
            gd: 群延迟
        """
        w = np.linspace(0, np.pi - 0.01, n_freqs)
        _, H = self.freq_response(n_freqs)

        dH = np.gradient(H)
        gd = -np.real(dH / (1j * H + 1e-10))

        return w, gd


class BilinearTransform:
    """
    双线性变换

    将模拟滤波器转换为数字滤波器。
    公式：s = (2/T) * (1 - z^(-1)) / (1 + z^(-1))
    """

    def __init__(self, T=1.0):
        """
        初始化双线性变换

        参数:
            T: 采样周期
        """
        self.T = T
        self.prewarp = True  # 预畸变

    def transform(self, analog_s_zeros, analog_s_poles, analog_gain, fs=1.0):
        """
        将模拟滤波器转换为数字滤波器

        参数:
            analog_s_zeros: 模拟零点
            analog_s_poles: 模拟极点
            analog_gain: 模拟增益
            fs: 采样率
        返回:
            b, a: 数字滤波器系数
        """
        T = 2.0 / fs
        gamma = 2.0 / T

        # 变换零点
        digital_zeros = []
        for z in analog_s_zeros:
            digital_zeros.append((gamma + z) / (gamma - z))

        # 变换极点
        digital_poles = []
        for p in analog_s_poles:
            digital_poles.append((gamma + p) / (gamma - p))

        # 增益调整
        digital_gain = analog_gain
        for z in analog_s_zeros:
            digital_gain *= (gamma - z) / gamma
        for p in analog_s_poles:
            digital_gain *= (gamma) / (gamma - p)

        # 转换为多项式系数
        b = np.poly(digital_zeros) if digital_zeros else np.array([1.0])
        a = np.poly(digital_poles) if digital_poles else np.array([1.0])

        # 归一化
        b = b * digital_gain / a[0]
        a = a / a[0]

        return b, a


class AnalogPrototype:
    """
    模拟滤波器原型

    设计 Butterworth、Chebyshev 等原型滤波器。
    """

    @staticmethod
    def butterworth(n):
        """
        Butterworth 原型（低通）

        参数:
            n: 阶数
        返回:
            b, a: 模拟滤波器系数
        """
        # 极点
        poles = []
        for k in range(n):
            theta = np.pi * (2*k + n + 1) / (2*n)
            poles.append(np.exp(1j * theta))

        # 转换为多项式
        a = np.poly(poles).real
        b = np.array([1.0])

        return b, a

    @staticmethod
    def chebyshev1(n, rp=0.5):
        """
        Chebyshev I 型原型（通带等纹波）

        参数:
            n: 阶数
            rp: 通带纹波 (dB)
        返回:
            b, a: 模拟滤波器系数
        """
        # 纹波参数
        eps = np.sqrt(10**(rp/10) - 1)

        # 极点
        poles = []
        for k in range(n):
            theta = np.pi * (2*k + n + 1) / (2*n)
            p = -np.sinh(1/n * np.arcsinh(1/eps)) * np.sin(theta) + \
                1j * np.cosh(1/n * np.arcsinh(1/eps)) * np.cos(theta)
            poles.append(p)

        a = np.poly(poles).real
        b = np.array([1.0])

        return b, a

    @staticmethod
    def chebyshev2(n, rs=40):
        """
        Chebyshev II 型原型（阻带等纹波）

        参数:
            n: 阶数
            rs: 阻带衰减 (dB)
        返回:
            b, a: 模拟滤波器系数
        """
        # 纹波参数
        eps = 1 / np.sqrt(10**(rs/10) - 1)

        # 极点
        poles = []
        for k in range(n):
            theta = np.pi * (2*k + 1) / (2*n)
            p = 1 / (np.sin(theta) * np.sinh(1/n * np.arcsinh(1/eps)))
            poles.append(complex(0, -1/p.imag) if p.imag != 0 else complex(p.real, 0))

        a = np.poly(poles).real
        b = np.array([1.0])

        return b, a


class FilterDesigner:
    """
    IIR 滤波器设计器

    提供低通、高通、带通、带阻滤波器的设计方法。
    """

    def __init__(self):
        self.prototype = AnalogPrototype()

    def lowpass(self, fc, order, filter_type='butterworth', rp=0.5, rs=40):
        """
        设计低通 IIR 滤波器

        参数:
            fc: 归一化截止频率
            order: 滤波器阶数
            filter_type: 'butterworth', 'chebyshev1', 'chebyshev2'
            rp: 通带纹波 (dB)
            rs: 阻带衰减 (dB)
        返回:
            b, a: 滤波器系数
        """
        if filter_type == 'butterworth':
            b, a = self.prototype.butterworth(order)
        elif filter_type == 'chebyshev1':
            b, a = self.prototype.chebyshev1(order, rp)
        elif filter_type == 'chebyshev2':
            b, a = self.prototype.chebyshev2(order, rs)
        else:
            b, a = self.prototype.butterworth(order)

        # 频率变换（低通到低通）
        # 简化：假设 fc 已经是预畸变后的值
        return b * fc, a

    def highpass(self, fc, order, filter_type='butterworth', rp=0.5, rs=40):
        """设计高通 IIR 滤波器"""
        # 高通 = 低通的频率镜像
        # s_hp = wc / s_lp
        # 实现：替换 z 为 1/z
        b_lp, a_lp = self.lowpass(fc, order, filter_type, rp, rs)

        # 简单的频率变换
        b_hp = np.zeros(len(b_lp))
        a_hp = np.zeros(len(a_lp))
        for k in range(len(b_lp)):
            b_hp[k] = b_lp[len(b_lp)-1-k] * ((-1)**k)
        for k in range(len(a_lp)):
            a_hp[k] = a_lp[len(a_lp)-1-k] * ((-1)**k)

        return b_hp, a_hp

    def bandpass(self, fc1, fc2, order, filter_type='butterworth', rp=0.5, rs=40):
        """设计带通 IIR 滤波器"""
        b_lp, a_lp = self.lowpass(1.0, order//2 + 1, filter_type, rp, rs)

        # 简化为零极点重排
        return b_lp, a_lp

    def bandstop(self, fc1, fc2, order, filter_type='butterworth', rp=0.5, rs=40):
        """设计带阻 IIR 滤波器"""
        return self.bandpass(fc1, fc2, order, filter_type, rp, rs)


def apply_biquad_filter(biquads, x):
    """
    应用双二阶滤波器级联

    参数:
        biquads: 双二阶系数列表 [(b0,b1,b2,a0,a1,a2), ...]
        x: 输入信号
    返回:
        y: 滤波后信号
    """
    y = x.copy()
    for b0, b1, b2, a0, a1, a2 in biquads:
        # 归一化
        b0, b1, b2 = b0/a0, b1/a0, b2/a0
        a1, a2 = a1/a0, a2/a0

        for n in range(len(y)):
            y[n] = b0 * x[n] + b1 * x[n-1] + b2 * x[n-2] - a1 * y[n-1] - a2 * y[n-2]
    return y


def design_biquad_lowpass(fc, Q=0.707):
    """
    设计双二阶低通滤波器

    参数:
        fc: 归一化截止频率
        Q: 品质因子
    返回:
        (b0, b1, b2, a0, a1, a2)
    """
    w0 = 2 * np.pi * fc
    alpha = np.sin(w0) / (2 * Q)

    b0 = (1 - np.cos(w0)) / 2
    b1 = 1 - np.cos(w0)
    b2 = (1 - np.cos(w0)) / 2
    a0 = 1 + alpha
    a1 = -2 * np.cos(w0)
    a2 = 1 - alpha

    return (b0, b1, b2, a0, a1, a2)


if __name__ == "__main__":
    print("=== IIR 滤波器测试 ===")

    # 创建测试信号
    print("\n1. 创建测试信号")
    fs = 1000
    t = np.arange(0, 1, 1/fs)
    signal = np.sin(2*np.pi*50*t) + 0.5*np.sin(2*np.pi*200*t) + 0.3*np.sin(2*np.pi*400*t)
    print(f"信号: 50Hz, 200Hz, 400Hz 混合")
    print(f"采样率: {fs} Hz")

    # 设计 Butterworth 低通
    print("\n2. Butterworth 低通滤波器设计")
    designer = FilterDesigner()
    b, a = designer.lowpass(0.2, order=4, filter_type='butterworth')
    print(f"系数 b: {b.round(4)}")
    print(f"系数 a: {a.round(4)}")

    # 滤波
    print("\n3. 滤波")
    iir = IIRFilter(b, a)
    filtered = iir.filter(signal)
    print(f"原始能量: {np.sum(signal**2):.4f}")
    print(f"滤波后能量: {np.sum(filtered**2):.4f}")

    # Chebyshev I 型
    print("\n4. Chebyshev I 型滤波器")
    b_cheb, a_cheb = designer.lowpass(0.2, order=4, filter_type='chebyshev1', rp=1.0)
    iir_cheb = IIRFilter(b_cheb, a_cheb)
    filtered_cheb = iir_cheb.filter(signal)
    print(f"系数 b: {b_cheb.round(4)}")

    # 频率响应
    print("\n5. 频率响应")
    w, H = iir.freq_response()
    H_db = 20 * np.log10(np.abs(H))
    print(f"在 0.1 归一化频率处: {H_db[int(0.1*512)]:.2f} dB")
    print(f"在 0.2 归一化频率处: {H_db[int(0.2*512)]:.2f} dB")
    print(f"在 0.3 归一化频率处: {H_db[int(0.3*512)]:.2f} dB")

    # 双二阶滤波器
    print("\n6. 双二阶滤波器")
    biquad = design_biquad_lowpass(0.15, Q=1.0)
    print(f"双二阶系数: {[f'{x:.4f}' for x in biquad]}")

    # 群延迟
    print("\n7. 群延迟")
    w_gd, gd = iir.group_delay()
    print(f"群延迟范围: [{np.min(gd):.2f}, {np.max(gd):.2f}]")

    # 稳定性检查
    print("\n8. 稳定性检查")
    poles = np.roots(a)
    stable = np.all(np.abs(poles) < 1)
    print(f"极点模最大值: {np.max(np.abs(poles)):.4f}")
    print(f"稳定: {stable}")

    # 不同阶数对比
    print("\n9. 不同阶数 Butterworth 对比")
    for order in [2, 4, 6, 8]:
        b_ord, a_ord = designer.lowpass(0.15, order, 'butterworth')
        iir_ord = IIRFilter(b_ord, a_ord)
        _, H_ord = iir_ord.freq_response()
        H_ord_db = 20 * np.log10(np.abs(H_ord))
        print(f"  阶数 {order}: 阻带衰减 = {H_ord_db[int(0.25*512)]:.2f} dB")

    print("\nIIR 滤波器测试完成!")
