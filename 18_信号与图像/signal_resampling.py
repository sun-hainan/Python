# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / signal_resampling

本文件实现 signal_resampling 相关的算法功能。
"""

import numpy as np

def upsample(signal, factor):
    n = len(signal)
    up = np.zeros(n*factor)
    for i in range(n):
        for f in range(factor):
            up[i*factor+f] = signal[i]
    from scipy.signal import filtfilt, butter
    b,a = butter(factor//2, 0.9, btype='low')
    return filtfilt(b,a,up)[:n*factor:factor//2] if factor>1 else signal

def downsample(signal, factor):
    from scipy.signal import decimate
    return decimate(signal, factor)

def resample_signal(signal, new_length):
    from scipy.signal import resample
    return resample(signal, new_length)

if __name__ == "__main__":
    np.random.seed(42)
    sig = np.sin(2*np.pi*5*np.linspace(0,1,100))
    up = upsample(sig[:20], 4)
    print(f"Upsampled length: {len(up)}")
    down = downsample(sig, 4)
    print(f"Downsampled length: {len(down)}")
    print("\n信号重采样测试完成!")
