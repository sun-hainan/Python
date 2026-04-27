# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / fft_convolution

本文件实现 fft_convolution 相关的算法功能。
"""

import numpy as np
import math


class FFT:
    """
    快速傅里叶变换（Cooley-Tukey 算法）

    实现基-2 DIT FFT。
    """

    @staticmethod
    def fft(x):
        """
        FFT

        参数:
            x: 输入信号（长度应为 2 的幂）
        返回:
            X: 频域信号
        """
        x = np.array(x, dtype=complex)
        n = len(x)

        if n == 1:
            return x

        # 检查是否为 2 的幂
        if n & (n - 1):
            # 补零到 2 的幂
            new_n = 2 ** int(np.ceil(np.log2(n)))
            x = np.pad(x, (0, new_n - n))
            n = new_n

        # 递归 DIT FFT
        return FFT._cooley_tukey(x)

    @staticmethod
    def _cooley_tukey(x):
        """Cooley-Tukey FFT 实现"""
        n = len(x)
        if n <= 16:  # 小规模直接计算
            return FFT._dft(x)

        # 分离偶数和奇数
        even = FFT._cooley_tukey(x[::2])
        odd = FFT._cooley_tukey(x[1::2])

        # 旋转因子
        w = np.exp(-2j * np.pi / n * np.arange(n // 2))
        t = w * odd

        # 合并
        return np.concatenate([even + t, even - t])

    @staticmethod
    def _dft(x):
        """朴素 DFT 实现"""
        n = len(x)
        X = np.zeros(n, dtype=complex)
        for k in range(n):
            for n_val in range(n):
                X[k] += x[n_val] * np.exp(-2j * np.pi * k * n_val / n)
        return X

    @staticmethod
    def ifft(X):
        """
        逆 FFT

        参数:
            X: 频域信号
        返回:
            x: 时域信号
        """
        X = np.array(X, dtype=complex)
        n = len(X)

        # 共轭 -> FFT -> 共轭 -> 除以 n
        X_conj = np.conj(X)
        x_conj = FFT.fft(X_conj)
        x = np.conj(x_conj) / n

        return x


class FFTConvolution:
    """
    FFT 卷积

    使用 FFT 实现高效卷积。
    """

    def __init__(self, filter_kernel):
        """
        初始化 FFT 卷积

        参数:
            filter_kernel: 滤波器核
        """
        self.kernel = np.array(filter_kernel, dtype=float)

    def convolve(self, signal):
        """
        卷积

        参数:
            signal: 输入信号
        返回:
            result: 卷积结果
        """
        signal = np.array(signal, dtype=float)

        # 确定 FFT 大小
        n = len(signal) + len(self.kernel) - 1
        n_fft = 2 ** int(np.ceil(np.log2(n)))

        # FFT
        X = FFT.fft(signal)
        H = FFT.fft(self.kernel)

        # 频域相乘
        Y = X * H

        # 逆 FFT
        y = FFT.ifft(Y)

        # 取实部
        result = np.real(y)

        # 裁剪到正确长度
        return result[:n]


def fft_convolve_1d(signal, kernel):
    """
    使用 FFT 进行一维卷积

    参数:
        signal: 输入信号
        kernel: 卷积核
    返回:
        result: 卷积结果
    """
    signal = np.array(signal, dtype=float)
    kernel = np.array(kernel, dtype=float)

    n = len(signal) + len(kernel) - 1
    n_fft = 2 ** int(np.ceil(np.log2(n)))

    # FFT
    X = np.fft.fft(signal, n_fft)
    H = np.fft.fft(kernel, n_fft)

    # 乘积
    Y = X * H

    # 逆 FFT
    result = np.fft.ifft(Y).real

    return result


def fft_convolve_2d(image, kernel):
    """
    使用 FFT 进行二维卷积

    参数:
        image: 2D 图像
        kernel: 2D 卷积核
    返回:
        result: 卷积结果
    """
    image = np.array(image, dtype=float)
    kernel = np.array(kernel, dtype=float)

    # 翻转核（卷积定义）
    kernel = np.flipud(np.fliplr(kernel))

    # 填充
    h, w = image.shape
    kh, kw = kernel.shape
    out_h, out_w = h + kh - 1, w + kw - 1
    n_fft_h = 2 ** int(np.ceil(np.log2(out_h)))
    n_fft_w = 2 ** int(np.ceil(np.log2(out_w)))

    # FFT
    X = np.fft.fft2(image, (n_fft_h, n_fft_w))
    H = np.fft.fft2(kernel, (n_fft_h, n_fft_w))

    # 乘积
    Y = X * H

    # 逆 FFT
    result = np.fft.ifft2(Y).real

    return result


def fft_correlate_1d(signal1, signal2):
    """
    使用 FFT 计算互相关

    参数:
        signal1, signal2: 输入信号
    返回:
        correlation: 互相关
    """
    s1 = np.array(signal1, dtype=float)
    s2 = np.array(signal2, dtype=float)

    # 反转 s2 用于互相关
    n = len(s1) + len(s2) - 1
    n_fft = 2 ** int(np.ceil(np.log2(n)))

    S1 = np.fft.fft(s1, n_fft)
    S2 = np.fft.fft(s2[::-1], n_fft)

    R = S1 * S2
    result = np.fft.ifft(R).real

    return result


def overlap_add_convolution(signal, kernel, block_size=1024):
    """
    重叠相加法卷积（用于超长信号）

    参数:
        signal: 输入信号
        kernel: 卷积核
        block_size: 分块大小
    返回:
        result: 卷积结果
    """
    signal = np.array(signal, dtype=float)
    kernel = np.array(kernel, dtype=float)

    # FFT 卷积器
    conv = FFTConvolution(kernel)

    # 分块处理
    n_blocks = int(np.ceil(len(signal) / block_size))
    result = []

    for i in range(n_blocks):
        start = i * block_size
        end = min((i + 1) * block_size, len(signal))
        block = signal[start:end]

        # 卷积当前块
        y_block = conv.convolve(block)

        # 重叠相加
        if i == 0:
            result.extend(y_block)
        else:
            overlap = len(kernel) - 1
            for j, val in enumerate(y_block):
                if j < overlap:
                    result[start + j] = result[start + j] + val
                else:
                    result.append(val)

    return np.array(result)


def fft_gaussian_blur(image, sigma=1.0):
    """
    FFT 高斯模糊

    参数:
        image: 输入图像
        sigma: 高斯标准差
    返回:
        blurred: 模糊后图像
    """
    # 生成高斯核
    size = int(6 * sigma + 1)
    if size % 2 == 0:
        size += 1
    x = np.arange(size) - size // 2
    gauss_1d = np.exp(-x**2 / (2 * sigma**2))
    gauss_2d = np.outer(gauss_1d, gauss_1d)
    gauss_2d /= gauss_2d.sum()

    return fft_convolve_2d(image, gauss_2d)


if __name__ == "__main__":
    print("=== FFT 卷积测试 ===")

    # 1D FFT 卷积
    print("\n1. 1D FFT 卷积")
    signal = np.random.randn(1000)
    kernel = np.array([0.2, 0.5, 0.3])

    import time

    # FFT 卷积
    start = time.time()
    for _ in range(100):
        result_fft = fft_convolve_1d(signal, kernel)
    fft_time = time.time() - start

    # 直接卷积
    start = time.time()
    for _ in range(100):
        result_direct = np.convolve(signal, kernel, mode='same')
    direct_time = time.time() - start

    print(f"FFT 卷积耗时: {fft_time*10:.2f} ms")
    print(f"直接卷积耗时: {direct_time*10:.2f} ms")
    print(f"结果差异: {np.max(np.abs(result_fft - result_direct)):.10f}")

    # 2D FFT 卷积
    print("\n2. 2D FFT 卷积")
    image = np.random.rand(256, 256)
    kernel = np.array([[0, 1, 0], [1, 2, 1], [0, 1, 0]]) / 6.0

    start = time.time()
    for _ in range(10):
        result_2d = fft_convolve_2d(image, kernel)
    fft2d_time = time.time() - start

    start = time.time()
    for _ in range(10):
        result_2d_direct = np.convolve(image, kernel, mode='same')
    direct2d_time = time.time() - start

    print(f"2D FFT 卷积耗时: {fft2d_time*100:.2f} ms")
    print(f"2D 直接卷积耗时: {direct2d_time*100:.2f} ms")

    # 高斯模糊
    print("\n3. FFT 高斯模糊")
    blurred = fft_gaussian_blur(image, sigma=3.0)
    print(f"原图均值: {np.mean(image):.4f}")
    print(f"模糊后均值: {np.mean(blurred):.4f}")
    print(f"模糊后方差: {np.var(blurred):.4f}")

    # 互相关
    print("\n4. FFT 互相关")
    s1 = np.random.randn(500)
    s2 = np.roll(s1, 20) + np.random.randn(500) * 0.1

    corr = fft_correlate_1d(s1, s2)
    peak_idx = np.argmax(np.abs(corr))
    print(f"相关峰值位置: {peak_idx}")
    print(f"预期偏移: 20")

    # 重叠相加法
    print("\n5. 重叠相加法卷积")
    long_signal = np.random.randn(10000)
    kernel = np.ones(100) / 100

    result_oa = overlap_add_convolution(long_signal, kernel)
    result_direct_oa = np.convolve(long_signal, kernel, mode='same')
    print(f"长度差异: {len(result_oa)} vs {len(result_direct_oa)}")
    print(f"结果差异: {np.max(np.abs(result_oa - result_direct_oa[:len(result_oa)])):.6f}")

    # 频谱分析
    print("\n6. FFT 频谱")
    t = np.arange(0, 1, 0.001)
    signal = np.sin(2*np.pi*50*t) + 0.5*np.sin(2*np.pi*120*t)
    spectrum = np.fft.fft(signal)
    freqs = np.fft.fftfreq(len(signal), 0.001)
    positive_freqs = freqs[:len(freqs)//2]
    positive_spectrum = np.abs(spectrum[:len(freqs)//2])
    peak_idx = np.argmax(positive_spectrum)
    print(f"主频率: {positive_freqs[peak_idx]:.0f} Hz")
    print(f"预期: 50 Hz")

    print("\nFFT 卷积测试完成!")
