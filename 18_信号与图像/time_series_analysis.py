# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / time_series_analysis

本文件实现 time_series_analysis 相关的算法功能。
"""

import numpy as np

def autocorrelation(signal, max_lag=20):
    n = len(signal)
    mean = np.mean(signal)
    var = np.var(signal)
    acf = np.zeros(max_lag)
    for lag in range(1, max_lag+1):
        cov = np.mean((signal[:-lag] - mean) * (signal[lag:] - mean))
        acf[lag-1] = cov / var if var > 0 else 0
    return acf

def partial_autocorrelation(signal, max_lag=10):
    from numpy.linalg import solve
    n = len(signal)
    pacf = np.zeros(max_lag)
    for k in range(1, max_lag+1):
        gamma = autocorrelation(signal, k)
        R = np.zeros((k,k))
        for i in range(k):
            for j in range(k):
                R[i,j] = gamma[abs(i-j)]
        pacf[k-1] = solve(R, gamma[:k])[k-1] if k>0 else 0
    return pacf

def ar_model(signal, order=5):
    n = len(signal) - order
    X = np.zeros((n, order))
    y = signal[order:]
    for i in range(n):
        X[i] = signal[i:i+order][::-1]
    coeffs, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    return coeffs

if __name__ == "__main__":
    np.random.seed(42)
    t = np.arange(100)
    sig = 0.8*np.sin(0.1*t) + 0.2*np.cos(0.3*t) + 0.1*np.random.randn(100)
    acf = autocorrelation(sig, 15)
    print(f"ACF[0]: {acf[0]:.4f}, ACF[5]: {acf[4]:.4f}")
    ar = ar_model(sig, 3)
    print(f"AR coeffs: {ar.round(3)}")
    print("\n时间序列分析测试完成!")
