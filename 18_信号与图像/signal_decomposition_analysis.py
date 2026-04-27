# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / signal_decomposition_analysis

本文件实现 signal_decomposition_analysis 相关的算法功能。
"""

import numpy as np

def empirical_mode_decomposition(signal, tolerance=0.05, max_iter=10):
    imfs = []
    residual = signal.copy()
    for _ in range(max_iter):
        # 简单经验模式分解
        up, down = np.zeros_like(residual), np.zeros_like(residual)
        for i in range(1,len(residual)-1):
            up[i] = max(residual[i-1], residual[i], residual[i+1])
            down[i] = min(residual[i-1], residual[i], residual[i+1])
        envelope = (up+down)/2
        diff = residual - envelope
        residual = residual - diff.mean()
        imfs.append(diff)
        if np.std(diff) < tolerance:
            break
    return imfs, residual

def variational_mode_decomposition(signal, K=3, alpha=2000):
    # 简化VMD
    return np.array([signal[K*i%len(signal)] for i in range(K)])

def hilbert_transform(signal):
    from scipy.signal import hilbert as scipy_hilbert
    return scipy_hilbert(signal).real

if __name__ == "__main__":
    np.random.seed(42)
    t = np.linspace(0, 1, 500)
    sig = np.sin(2*np.pi*5*t) + 0.5*np.sin(2*np.pi*10*t) + 0.2*np.random.randn(500)
    imfs, res = empirical_mode_decomposition(sig, max_iter=5)
    print(f"EMD produced {len(imfs)} IMFs")
    print("\n信号分解测试完成!")
