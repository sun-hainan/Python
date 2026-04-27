# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / power_spectrum

本文件实现 power_spectrum 相关的算法功能。
"""

import numpy as np


# periodogram 算法
def periodogram(signal, nfft=None):
    """Periodogram 功率谱"""
    N = len(signal)
    nfft = nfft or N
    X = np.fft.fft(signal, nfft)
    psd = np.abs(X)**2 / N
    freqs = np.arange(nfft) / nfft
    return freqs[:nfft//2], psd[:nfft//2]


# welch_psd 算法
def welch_psd(signal, fs=1.0, nperseg=256):
    """Welch 方法功率谱"""
    N = len(signal)
    step = nperseg // 2
    psd_sum = np.zeros(nperseg)
    count = 0
    for i in range(0, N - nperseg, step):
        seg = signal[i:i+nperseg]
        windowed = seg * np.hanning(nperseg)
        X = np.fft.fft(windowed, nperseg)
        psd_sum += np.abs(X)**2
        count += 1
    psd = psd_sum / count / nperseg
    freqs = np.arange(nperseg) * fs / nperseg
    return freqs[:nperseg//2], psd[:nperseg//2]


# cross_power 算法
def cross_power(s1, s2):
    """互功率谱"""
    n = min(len(s1), len(s2))
    X = np.fft.fft(s1[:n])
    Y = np.fft.fft(s2[:n])
    cpsd = X * np.conj(Y)
    return np.abs(cpsd)**2


if __name__ == "__main__":
    np.random.seed(42)
    t = np.arange(0, 1, 1/1024)
    s = np.sin(2*np.pi*50*t) + 0.5*np.sin(2*np.pi*120*t) + np.random.randn(len(t))*0.1

    freqs, psd = periodogram(s)
    peak = freqs[np.argmax(psd)]
    print(f"Periodogram 主峰: {peak*1024:.1f} Hz")

    freqs_w, psd_w = welch_psd(s, fs=1024, nperseg=256)
    peak_w = freqs_w[np.argmax(psd_w)]
    print(f"Welch 主峰: {peak_w:.1f} Hz")
    print("\n功率谱测试完成!")
