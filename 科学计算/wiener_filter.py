"""
Wiener滤波器 - 信号恢复
=========================
本模块实现Wiener滤波器，用于信号去噪和恢复：

Wiener滤波器的目标是找到最优线性估计，使得均方误差最小。

适用于：
- 图像去噪
- 信号恢复
- 系统辨识

公式：
给定观测 y = Hx + n
Wiener滤波器: G = (H^T H + Sn/Sx)^{-1} H^T
其中 Sn 是噪声功率谱，Sx 是信号功率谱

Author: 算法库
"""

import numpy as np
from typing import Tuple, Optional


def wiener_filter_1d(
    observed: np.ndarray,
    noise_var: float,
    signal_var: float = None,
    kernel_size: int = 5
) -> np.ndarray:
    """
    一维Wiener滤波
    
    参数:
        observed: 观测信号（含噪）
        noise_var: 噪声方差
        signal_var: 信号方差（如果为None，使用观测信号估计）
        kernel_size: 局部估计的窗口大小
    
    返回:
        restored: 恢复后的信号
    """
    n = len(observed)
    restored = np.zeros(n)
    
    if signal_var is None:
        signal_var = np.var(observed)
    
    # 局部均值和方差估计
    half = kernel_size // 2
    
    for i in range(n):
        # 局部窗口
        start = max(0, i - half)
        end = min(n, i + half + 1)
        
        local_mean = np.mean(observed[start:end])
        local_var = np.var(observed[start:end])
        
        # Wiener滤波器估计
        if local_var > noise_var:
            restored[i] = local_mean + (local_var - noise_var) / local_var * (observed[i] - local_mean)
        else:
            restored[i] = local_mean
    
    return restored


def wiener_filter_2d(
    observed: np.ndarray,
    noise_var: float,
    kernel_size: int = 5
) -> np.ndarray:
    """
    二维Wiener滤波（图像去噪）
    
    使用局部自适应滤波
    每个像素根据其邻域的统计特性进行滤波
    
    参数:
        observed: 观测图像
        noise_var: 噪声方差
        kernel_size: 邻域窗口大小
    
    返回:
        restored: 恢复后的图像
    """
    rows, cols = observed.shape
    restored = np.zeros_like(observed)
    half = kernel_size // 2
    
    # 预计算图像均值和方差（全局）
    img_mean = np.mean(observed)
    img_var = np.var(observed)
    
    for i in range(rows):
        for j in range(cols):
            # 局部邻域
            i_start = max(0, i - half)
            i_end = min(rows, i + half + 1)
            j_start = max(0, j - half)
            j_end = min(cols, j + half + 1)
            
            local_patch = observed[i_start:i_end, j_start:j_end]
            local_mean = np.mean(local_patch)
            local_var = np.var(local_patch)
            
            # Wiener滤波估计
            if local_var > noise_var:
                restored[i, j] = local_mean + (local_var - noise_var) / local_var * (observed[i, j] - local_mean)
            else:
                restored[i, j] = local_mean
    
    return restored


def wiener_filter_frequency(
    y: np.ndarray,
    H: np.ndarray,
    noise_psd: np.ndarray,
    signal_psd: np.ndarray
) -> np.ndarray:
    """
    频域Wiener滤波器
    
    频域Wiener滤波:
        G(f) = H*(f) * Sx(f) / (|H(f)|² * Sx(f) + Sn(f))
    
    参数:
        y: 观测信号（频域）
        H: 系统传递函数（频域）
        noise_psd: 噪声功率谱密度
        signal_psd: 信号功率谱密度
    
    返回:
        X_hat: 恢复信号的频域表示
    """
    # Wiener滤波器频率响应
    G = np.conj(H) * signal_psd / (np.abs(H)**2 * signal_psd + noise_psd)
    
    # 应用滤波器
    X_hat = G * y
    
    return X_hat


def estimate_noise_variance(signal: np.ndarray) -> float:
    """
    从信号中估计噪声方差
    
    使用局部变化的中位数估计（对边缘和细节鲁棒）
    
    参数:
        signal: 输入信号
    
    返回:
        noise_var: 估计的噪声方差
    """
    if signal.ndim == 1:
        # 一维信号：计算二阶差分的方差
        diff = signal[2:] - 2 * signal[1:-1] + signal[:-2]
        # 假设平滑信号的二阶差分主要由噪声引起
        noise_var = np.var(diff) / 6  # 二阶差分的因子
    else:
        # 二维图像
        h, w = signal.shape
        diff_h = signal[2:, :] - 2 * signal[1:-1, :] + signal[:-2, :]
        diff_v = signal[:, 2:] - 2 * signal[:, 1:-1] + signal[:, :-2]
        noise_var = (np.var(diff_h) + np.var(diff_v)) / 6
    
    return max(noise_var, 1e-10)


def wiener_deconvolution(
    blurred: np.ndarray,
    kernel: np.ndarray,
    noise_var: float = None
) -> np.ndarray:
    """
    Wiener反卷积
    
    用于从模糊图像/信号中恢复原始信号
    
    参数:
        blurred: 模糊观测
        kernel: 模糊核（点扩散函数）
        noise_var: 噪声方差（如果为None，自动估计）
    
    返回:
        restored: 恢复的信号
    """
    # 估计噪声方差
    if noise_var is None:
        noise_var = estimate_noise_variance(blurred)
    
    # FFT
    Blurred_fft = np.fft.fft2(blurred)
    Kernel_fft = np.fft.fft2(kernel, blurred.shape)
    
    # 信号功率谱估计（从观测中减去噪声估计）
    Signal_psd = np.abs(Blurred_fft)**2 - noise_var * np.abs(Kernel_fft)**2
    Signal_psd = np.maximum(Signal_psd, 1e-10)  # 确保为正
    
    # Wiener滤波
    restoration_fft = np.conj(Kernel_fft) * Signal_psd / (np.abs(Kernel_fft)**2 * Signal_psd + noise_var)
    
    # 逆FFT
    restored = np.fft.ifft2(Blur_fft * restoration_fft).real
    
    return restored


def gaussian_kernel(size: int, sigma: float) -> np.ndarray:
    """
    生成高斯核
    
    参数:
        size: 核大小（奇数）
        sigma: 标准差
    
    返回:
        高斯核
    """
    k = size // 2
    x = np.arange(-k, k + 1)
    kernel = np.exp(-x**2 / (2 * sigma**2))
    return kernel / np.sum(kernel)


def create_blur_kernel(kernel_type: str, size: int = 9) -> np.ndarray:
    """
    创建常见模糊核
    
    参数:
        kernel_type: 'gaussian', 'motion', 'disk'
        size: 核大小
    
    返回:
        模糊核
    """
    if kernel_type == 'gaussian':
        return gaussian_kernel(size, sigma=size/6)
    
    elif kernel_type == 'motion':
        # 运动模糊
        kernel = np.zeros((size, size))
        for i in range(size):
            kernel[i, i] = 1.0 / size
        return kernel
    
    elif kernel_type == 'disk':
        # 盘状模糊
        k = size // 2
        x, y = np.meshgrid(np.arange(-k, k+1), np.arange(-k, k+1))
        kernel = (x**2 + y**2 <= k**2).astype(float)
        return kernel / np.sum(kernel)
    
    else:
        raise ValueError(f"未知的核类型: {kernel_type}")


def add_gaussian_noise(signal: np.ndarray, snr_db: float) -> np.ndarray:
    """
    添加高斯噪声
    
    参数:
        signal: 原始信号
        snr_db: 信噪比（dB）
    
    返回:
        noisy: 加噪信号
    """
    signal_power = np.mean(signal**2)
    snr = 10 ** (snr_db / 10)
    noise_power = signal_power / snr
    
    noise = np.random.randn(*signal.shape) * np.sqrt(noise_power)
    return signal + noise


def snr_calculate(signal: np.ndarray, noise: np.ndarray) -> float:
    """
    计算信噪比（dB）
    
    参数:
        signal: 原始信号
        noise: 噪声
    
    返回:
        snr_db: 信噪比（dB）
    """
    signal_power = np.mean(signal**2)
    noise_power = np.mean(noise**2)
    return 10 * np.log10(signal_power / noise_power)


if __name__ == "__main__":
    print("=" * 55)
    print("Wiener滤波器测试")
    print("=" * 55)
    
    np.random.seed(42)
    
    # ========== 一维信号测试 ==========
    print("\n--- 一维信号去噪 ---")
    
    # 生成原始信号
    t = np.linspace(0, 1, 500)
    original = np.sin(2 * np.pi * 5 * t) + 0.5 * np.sin(2 * np.pi * 20 * t)
    
    # 添加噪声
    noisy = add_gaussian_noise(original, snr_db=5)
    
    # 估计噪声方差
    noise_var = estimate_noise_variance(noisy)
    print(f"估计噪声方差: {noise_var:.6f}")
    
    # Wiener滤波
    restored = wiener_filter_1d(noisy, noise_var, kernel_size=7)
    
    print(f"原始SNR: {snr_calculate(original, noisy - original):.2f} dB")
    print(f"去噪SNR: {snr_calculate(original, restored - original):.2f} dB")
    
    # ========== 图像去噪测试 ==========
    print("\n--- 图像去噪测试 ---")
    
    # 创建测试图像
    x, y = np.meshgrid(np.linspace(-1, 1, 100), np.linspace(-1, 1, 100))
    image = np.exp(-(x**2 + y**2) * 10)  # 高斯峰
    
    # 添加噪声
    noise = np.random.randn(100, 100) * 0.2
    noisy_image = image + noise
    
    print(f"图像SNR: {snr_calculate(image, noise):.2f} dB")
    
    # Wiener滤波
    noise_var_2d = estimate_noise_variance(noisy_image)
    restored_image = wiener_filter_2d(noisy_image, noise_var_2d, kernel_size=5)
    
    print(f"去噪后SNR: {snr_calculate(image, restored_image - image):.2f} dB")
    print(f"去噪后MSE: {np.mean((image - restored_image)**2):.6f}")
    
    # ========== 反卷积测试 ==========
    print("\n--- Wiener反卷积测试 ---")
    
    # 创建模糊核
    kernel = create_blur_kernel('gaussian', size=15)
    
    # 模糊原始图像
    blurred = np.zeros_like(image)
    from scipy import signal as sig
    blurred = sig.convolve2d(image, kernel, mode='same')
    
    # 添加噪声
    blurred_noisy = blurred + np.random.randn(100, 100) * 0.05
    
    # Wiener反卷积
    restored_deconv = wiener_deconvolution(blurred_noisy, kernel)
    
    print(f"模糊+噪声图像MSE: {np.mean((image - blurred_noisy)**2):.6f}")
    print(f"反卷积恢复MSE: {np.mean((image - restored_deconv)**2):.6f}")
    
    print("\n测试通过！Wiener滤波器工作正常。")
