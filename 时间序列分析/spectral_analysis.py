# -*- coding: utf-8 -*-
"""
算法实现：时间序列分析 / spectral_analysis

本文件实现 spectral_analysis 相关的算法功能。
"""

import numpy as np
from typing import Tuple, Optional


def periodogram(y: np.ndarray, fs: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
    """
    计算Periodogram功率谱密度估计
    
    参数:
        y: 时间序列
        fs: 采样频率
    
    返回:
        (频率数组, 功率谱密度数组)
    """
    n = len(y)
    
    # 去均值
    y_centered = y - np.mean(y)
    
    # 离散傅里叶变换
    fft_result = np.fft.fft(y_centered)
    
    # 取正频率部分
    n_freq = n // 2
    freq = np.fft.fftfreq(n, 1 / fs)[:n_freq]
    psd = (np.abs(fft_result) ** 2)[:n_freq] / n
    
    return freq, psd


def welch_psd(y: np.ndarray, fs: float = 1.0, 
              window: str = 'hann', nperseg: Optional[int] = None,
              noverlap: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Welch方法计算功率谱密度
    
    Welch方法将信号分段，对每段计算周期图后取平均
    优点：减小方差，缺点：分辨率降低
    
    参数:
        y: 时间序列
        fs: 采样频率
        window: 窗口类型 ('hann', 'hamming', 'blackman')
        nperseg: 每段采样点数
        noverlap: 重叠采样点数
    
    返回:
        (频率数组, 功率谱密度数组)
    """
    n = len(y)
    
    if nperseg is None:
        nperseg = min(256, n // 4)
    
    if noverlap is None:
        noverlap = nperseg // 2
    
    # 窗口函数
    if window == 'hann':
        win = np.hanning(nperseg)
    elif window == 'hamming':
        win = np.hamming(nperseg)
    elif window == 'blackman':
        win = np.blackman(nperseg)
    else:
        win = np.ones(nperseg)
    
    # 计算窗口能量修正因子
    win_energy = np.sum(win ** 2)
    
    # 分段
    n_segments = (n - nperseg) // (nperseg - noverlap) + 1
    
    psd_sum = np.zeros(nperseg)
    
    for i in range(n_segments):
        start = i * (nperseg - noverlap)
        end = start + nperseg
        
        if end > n:
            break
        
        segment = y[start:end] - np.mean(y[start:end])
        
        # 加窗后FFT
        windowed = segment * win
        fft_result = np.fft.fft(windowed, nperseg)
        
        psd_sum += np.abs(fft_result) ** 2
    
    # 归一化
    psd = psd_sum / (n_segments * win_energy * fs)
    
    # 频率轴
    freq = np.fft.fftfreq(nperseg, 1 / fs)
    
    # 取正频率
    pos_mask = freq >= 0
    return freq[pos_mask], psd[pos_mask]


def LombScarglePeriodogram(y: np.ndarray, t: np.ndarray, 
                           freq: Optional[np.ndarray] = None,
                           n_freq: int = 500) -> Tuple[np.ndarray, np.ndarray]:
    """
    Lomb-Scargle周期图 - 适用于不等间隔采样数据
    
    参数:
        y: 时间序列
        t: 时间戳数组
        freq: 预定义的频率数组（可选）
        n_freq: 如果freq=None，生成的频率点数
    
    返回:
        (频率数组, 功率数组)
    """
    n = len(y)
    
    if freq is None:
        t_range = t[-1] - t[0]
        f_min = 1 / (10 * t_range)
        f_max = n / (2 * t_range)
        freq = np.linspace(f_min, f_max, n_freq)
    
    # 去均值
    y_centered = y - np.mean(y)
    
    power = np.zeros_like(freq)
    
    for i, f in enumerate(freq):
        # 计算Lomb-Scargle统计量
        omega = 2 * np.pi * f
        
        # 构造设计矩阵
        sin_omega_t = np.sin(omega * t)
        cos_omega_t = np.cos(omega * t)
        
        # 简化的Lomb-Scargle公式
        tau = np.arctan2(np.sum(sin_2t := 2 * sin_omega_t * cos_omega_t), 
                        np.sum(cos_2t := 2 * cos_omega_t ** 2 - 1)) / (4 * omega)
        
        sin_term = np.sin(omega * (t - tau))
        cos_term = np.cos(omega * (t - tau))
        
        tau_correction = np.sum(cos_term)
        tau_sine = np.sum(sin_term)
        tau_cossin = np.sum(cos_term * sin_term)
        y_cos = np.sum(y_centered * cos_term)
        y_sin = np.sum(y_centered * sin_term)
        
        # 归一化功率
        power[i] = (tau_cos ** 2 + tau_sine ** 2) / \
                   (np.sum(y_centered ** 2) * 
                    (np.sum(cos_term ** 2) + np.sum(sin_term ** 2)))
    
    return freq, power


def dominant_frequency(freq: np.ndarray, psd: np.ndarray, 
                      n_peaks: int = 3) -> Tuple[np.ndarray, np.ndarray]:
    """
    找出功率谱中的主频率
    
    参数:
        freq: 频率数组
        psd: 功率谱密度数组
        n_peaks: 找出的峰值数
    
    返回:
        (主频率数组, 对应功率数组)
    """
    # 找峰值
    peaks_idx = []
    for i in range(1, len(psd) - 1):
        if psd[i] > psd[i - 1] and psd[i] > psd[i + 1]:
            peaks_idx.append(i)
    
    # 按功率排序
    peaks_idx.sort(key=lambda x: psd[x], reverse=True)
    
    top_peaks = peaks_idx[:n_peaks]
    
    return freq[top_peaks], psd[top_peaks]


def spectral_entropy(psd: np.ndarray, eps: float = 1e-10) -> float:
    """
    计算功率谱的谱熵
    
    谱熵衡量信号的不确定性/复杂性
    
    参数:
        psd: 功率谱密度
        eps: 数值稳定项
    
    返回:
        谱熵值
    """
    # 归一化功率谱
    psd_norm = psd / (np.sum(psd) + eps)
    
    # 熵
    entropy = -np.sum(psd_norm * np.log2(psd_norm + eps))
    
    # 归一化（最大熵 = log2(n)）
    n = len(psd)
    max_entropy = np.log2(n)
    
    return entropy / max_entropy if max_entropy > 0 else 0


class SpectralAnalyzer:
    """频谱分析器类"""
    
    def __init__(self, fs: float = 1.0):
        self.fs = fs
        self.freq = None
        self.psd = None
        self.method = None
    
    def fit_periodogram(self, y: np.ndarray):
        """使用Periodogram拟合"""
        self.freq, self.psd = periodogram(y, self.fs)
        self.method = 'periodogram'
    
    def fit_welch(self, y: np.ndarray, nperseg: int = 128, noverlap: int = 64):
        """使用Welch方法拟合"""
        self.freq, self.psd = welch_psd(y, self.fs, nperseg=nperseg, noverlap=noverlap)
        self.method = 'welch'
    
    def get_dominant_frequencies(self, n: int = 3) -> np.ndarray:
        """获取主频率"""
        if self.freq is None:
            raise ValueError("未拟合模型")
        dom_freq, _ = dominant_frequency(self.freq, self.psd, n)
        return dom_freq
    
    def get_spectral_entropy(self) -> float:
        """获取谱熵"""
        if self.psd is None:
            raise ValueError("未拟合模型")
        return spectral_entropy(self.psd)
    
    def bandwidth_estimation(self, psd_threshold: float = 0.5) -> float:
        """
        估计信号带宽
        
        参数:
            psd_threshold: 功率阈值（相对于峰值）
        
        返回:
            带宽估计值
        """
        if self.psd is None:
            raise ValueError("未拟合模型")
        
        peak_power = np.max(self.psd)
        threshold = peak_power * psd_threshold
        
        above_threshold = np.where(self.psd >= threshold)[0]
        
        if len(above_threshold) < 2:
            return 0
        
        bandwidth = self.freq[above_threshold[-1]] - self.freq[above_threshold[0]]
        return bandwidth
    
    def print_summary(self):
        """打印分析摘要"""
        print("=" * 50)
        print(f"频谱分析 - {self.method.upper()}")
        print("=" * 50)
        print(f"采样频率: {self.fs}")
        print(f"频率范围: [{self.freq[0]:.4f}, {self.freq[-1]:.4f}]")
        print(f"主频率: {self.get_dominant_frequencies(3)}")
        print(f"谱熵: {self.get_spectral_entropy():.4f}")
        print(f"带宽估计: {self.bandwidth_estimation():.4f}")


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("频谱分析测试 - Periodogram & Welch")
    print("=" * 50)
    
    np.random.seed(42)
    fs = 100  # 采样频率100Hz
    
    # 生成复合信号
    n = 1024
    t = np.arange(n) / fs
    
    # 信号构成：50Hz正弦 + 120Hz正弦 + 噪声
    signal = (np.sin(2 * np.pi * 50 * t) * 2 + 
              np.sin(2 * np.pi * 120 * t) * 1.5 + 
              np.random.randn(n) * 0.5)
    
    print(f"\n信号生成: n={n}, 采样率={fs}Hz")
    print(f"信号长度: {n / fs:.2f}秒")
    
    # Periodogram
    print("\n--- Periodogram ---")
    analyzer1 = SpectralAnalyzer(fs=fs)
    analyzer1.fit_periodogram(signal)
    dom_freq1 = analyzer1.get_dominant_frequencies(3)
    print(f"检测到的频率: {dom_freq1}")
    
    # Welch方法
    print("\n--- Welch方法 ---")
    analyzer2 = SpectralAnalyzer(fs=fs)
    analyzer2.fit_welch(signal, nperseg=128, noverlap=64)
    dom_freq2 = analyzer2.get_dominant_frequencies(3)
    print(f"检测到的频率: {dom_freq2}")
    
    # 谱熵
    print("\n--- 谱熵分析 ---")
    print(f"Periodogram谱熵: {analyzer1.get_spectral_entropy():.4f}")
    print(f"Welch谱熵: {analyzer2.get_spectral_entropy():.4f}")
    
    # 带宽估计
    print("\n--- 带宽估计 ---")
    print(f"Periodogram带宽: {analyzer1.bandwidth_estimation():.2f} Hz")
    print(f"Welch带宽: {analyzer2.bandwidth_estimation():.2f} Hz")
    
    # 非均匀采样Lomb-Scargle
    print("\n--- Lomb-Scargle (不等间隔采样) ---")
    t_irregular = np.sort(np.random.uniform(0, 10, 200))
    y_irregular = np.sin(2 * np.pi * 30 * t_irregular) + np.random.randn(200) * 0.3
    
    freq_ls, power_ls = LombScarglePeriodogram(y_irregular, t_irregular, n_freq=200)
    dom_freq_ls, dom_power_ls = dominant_frequency(freq_ls, power_ls, 3)
    print(f"检测到的频率: {dom_freq_ls}")
    
    print("\n" + "=" * 50)
    print("测试完成")
