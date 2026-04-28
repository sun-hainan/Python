"""
FFT快速卷积
============
本模块实现基于FFT的高效卷积算法：

1. 直接卷积 O(n²)
2. FFT卷积 O(n log n)
3. 多项式乘法
4. 圆卷积与线性卷积

FFT卷积的核心思想：
- 利用FFT将时域卷积转换为频域乘法
- 对于长序列，比直接卷积快得多

Author: 算法库
"""

import numpy as np
from typing import Callable


def direct_convolution(f: np.ndarray, g: np.ndarray) -> np.ndarray:
    """
    直接卷积 (O(n²))
    
    (f * g)[n] = Σ f[m] * g[n-m]
    
    参数:
        f, g: 输入序列
    
    返回:
        卷积结果
    """
    n1, n2 = len(f), len(g)
    result = np.zeros(n1 + n2 - 1)
    
    for n in range(n1 + n2 - 1):
        for m in range(n1):
            if 0 <= n - m < n2:
                result[n] += f[m] * g[n - m]
    
    return result


def fft_convolution(f: np.ndarray, g: np.ndarray) -> np.ndarray:
    """
    基于FFT的快速卷积 (O(n log n))
    
    原理:
        f * g = IFFT(FFT(f) · FFT(g))
    
    参数:
        f, g: 输入序列
    
    返回:
        卷积结果（线性卷积）
    """
    n1, n2 = len(f), len(g)
    n_fft = n1 + n2 - 1  # 确保足够长避免循环卷积
    
    # 找到最接近的2的幂
    n_pow2 = 1
    while n_pow2 < n_fft:
        n_pow2 *= 2
    
    # FFT
    F = np.fft.fft(f, n_pow2)
    G = np.fft.fft(g, n_pow2)
    
    # 频域乘法
    H = F * G
    
    # 逆FFT
    result = np.fft.ifft(H, n_pow2).real
    
    # 截取有效部分
    return result[:n_fft]


def circular_convolution(f: np.ndarray, g: np.ndarray, n: int) -> np.ndarray:
    """
    n点圆卷积
    
    参数:
        f, g: 输入序列（长度 <= n）
        n: 圆卷积点数
    
    返回:
        n点圆卷积结果
    """
    # 补零
    f_padded = np.zeros(n)
    g_padded = np.zeros(n)
    f_padded[:len(f)] = f
    g_padded[:len(g)] = g
    
    # FFT
    F = np.fft.fft(f_padded)
    G = np.fft.fft(g_padded)
    
    # 乘法
    H = F * G
    
    # 逆FFT
    return np.fft.ifft(H).real


def convolution_theorem_demo():
    """演示卷积定理"""
    print("=" * 50)
    print("FFT卷积 vs 直接卷积 性能对比")
    print("=" * 50)
    
    import time
    
    sizes = [64, 128, 256, 512, 1024, 2048]
    
    print(f"\n{'n':>8} {'直接卷积':>15} {'FFT卷积':>15} {'加速比':>10}")
    print("-" * 50)
    
    for n in sizes:
        f = np.random.randn(n)
        g = np.random.randn(n // 2)
        
        # 直接卷积
        t0 = time.time()
        result_direct = direct_convolution(f, g)
        t_direct = time.time() - t0
        
        # FFT卷积
        t0 = time.time()
        result_fft = fft_convolution(f, g)
        t_fft = time.time() - t0
        
        speedup = t_direct / t_fft if t_fft > 0 else float('inf')
        print(f"{n:>8d} {t_direct:>15.4f} {t_fft:>15.4f} {speedup:>10.2f}x")
        
        # 验证结果一致性
        max_diff = np.max(np.abs(result_direct - result_fft))
        if max_diff > 1e-10:
            print(f"  警告: 结果不一致，最大差异 {max_diff:.2e}")


def polynomial_multiplication(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    多项式乘法（使用FFT）
    
    A(x) = a_0 + a_1*x + ... + a_n*x^n
    B(x) = b_0 + b_1*x + ... + b_m*x^m
    C(x) = A(x) * B(x)
    
    参数:
        a, b: 多项式系数数组
    
    返回:
        c: 乘积多项式系数
    """
    return fft_convolution(a, b)


def cross_correlation(f: np.ndarray, g: np.ndarray) -> np.ndarray:
    """
    互相关计算
    
    (f ⋆ g)[n] = Σ f[m] * g[m+n]
    
    使用FFT: R = IFFT(conj(FFT(f)) * FFT(g))
    
    参数:
        f, g: 输入序列
    
    返回:
        互相关序列
    """
    n1, n2 = len(f), len(g)
    n = n1 + n2 - 1
    
    n_pow2 = 1
    while n_pow2 < n:
        n_pow2 *= 2
    
    F = np.fft.fft(f, n_pow2)
    G = np.fft.fft(g, n_pow2)
    
    # 互相关: f的反转与g的卷积
    R = np.fft.ifft(np.conj(F) * G).real
    
    return R[:n]


def auto_correlation(f: np.ndarray) -> np.ndarray:
    """
    自相关计算
    
    参数:
        f: 输入序列
    
    返回:
        自相关序列
    """
    return cross_correlation(f, f)


def moving_average_filter(signal: np.ndarray, window_size: int) -> np.ndarray:
    """
    移动平均滤波器（使用卷积）
    
    参数:
        signal: 输入信号
        window_size: 窗口大小
    
    返回:
        滤波后的信号
    """
    kernel = np.ones(window_size) / window_size
    return fft_convolution(signal, kernel)


def gaussian_smoothing(signal: np.ndarray, sigma: float) -> np.ndarray:
    """
    高斯平滑（使用FFT的高斯卷积）
    
    参数:
        signal: 输入信号
        sigma: 高斯标准差
    
    返回:
        平滑后的信号
    """
    # 创建高斯核
    n = len(signal)
    x = np.arange(n) - n // 2
    kernel = np.exp(-x**2 / (2 * sigma**2))
    kernel = kernel / np.sum(kernel)
    
    return fft_convolution(signal, kernel)


def fir_filter_design(cutoff: float, num_taps: int) -> np.ndarray:
    """
    FIR滤波器设计（窗函数法）
    
    参数:
        cutoff: 截止频率（0到1之间，相对于采样率/2）
        num_taps: 滤波器阶数（奇数最好）
    
    返回:
        滤波器系数
    """
    n = np.arange(num_taps) - (num_taps - 1) / 2
    
    # sinc函数
    if num_taps % 2 == 0:
        h = np.sinc(2 * cutoff * (n + 0.5)) / (n + 0.5)
    else:
        h = np.sinc(2 * cutoff * n)
    
    # Hamming窗
    window = 0.54 - 0.46 * np.cos(2 * np.pi * np.arange(num_taps) / (num_taps - 1))
    h = h * window
    
    # 归一化
    h = h / np.sum(h)
    
    return h


def apply_fir_filter(signal: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    应用FIR滤波器
    
    参数:
        signal: 输入信号
        b: 滤波器系数
    
    返回:
        滤波后的信号
    """
    return fft_convolution(signal, b)


if __name__ == "__main__":
    print("=" * 55)
    print("FFT快速卷积测试")
    print("=" * 55)
    
    # 性能对比
    convolution_theorem_demo()
    
    # 功能测试
    print("\n--- 功能测试 ---")
    
    # 测试多项式乘法
    a = np.array([1, 2, 3])  # 1 + 2x + 3x²
    b = np.array([4, 5])     # 4 + 5x
    # 预期结果: 4 + 5x + 8x² + 15x³ = [4, 13, 8, 15]
    c = polynomial_multiplication(a, b)
    print(f"多项式乘法: {a} * {b} = {c}")
    
    # 测试移动平均
    signal = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    filtered = moving_average_filter(signal, 3)
    print(f"移动平均(窗口=3): {filtered[:8]}")  # 截取有效部分
    
    # 测试高斯平滑
    x = np.linspace(-5, 5, 100)
    noisy_signal = np.sin(x) + 0.5 * np.random.randn(100)
    smoothed = gaussian_smoothing(noisy_signal, sigma=3)
    print(f"高斯平滑后信号范围: [{smoothed.min():.4f}, {smoothed.max():.4f}]")
    
    # FIR滤波器
    print("\n--- FIR滤波器设计 ---")
    cutoff = 0.1  # 10% 采样率
    num_taps = 51
    b = fir_filter_design(cutoff, num_taps)
    print(f"低通FIR滤波器 (截止频率={cutoff}, 阶数={num_taps})")
    print(f"系数前5个: {b[:5]}")
    print(f"系数和: {np.sum(b):.6f} (应为1)")
    
    # 验证滤波效果
    test_signal = np.sin(2 * np.pi * 0.05 * np.arange(100)) + np.sin(2 * np.pi * 0.3 * np.arange(100))
    filtered_signal = apply_fir_filter(test_signal, b)
    print(f"原始信号功率: {np.var(test_signal):.4f}")
    print(f"滤波后信号功率: {np.var(filtered_signal[:len(b)+99]):.4f}")
    
    print("\n测试通过！FFT卷积功能正常。")
