# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / audio_features

本文件实现 audio_features 相关的算法功能。
"""

import numpy as np

def mfcc(signal, sample_rate=16000, n_mfcc=13):
    from scipy.fft import fft
    n = len(signal)
    m = int(sample_rate * 0.025)
    hop = int(sample_rate * 0.010)
    n_fft = m
    frames = []
    for i in range(0, n-m, hop):
        frame = signal[i:i+m] * np.hanning(m)
        spectrum = np.abs(fft(frame, n_fft)[:n_fft//2+1])
        frames.append(spectrum)
    frames = np.array(frames)
    mel = np.log(1 + np.abs(frames) @ np.ones((n_fft//2+1, 20)) / 20)
    from scipy.fft import dct
    mfccs = dct(mel, type=2, axis=1, norm='ortho')[:,:n_mfcc]
    return mfccs

def zero_crossing_rate(signal):
    zcr = np.sum(np.abs(np.diff(np.sign(signal)))) / (2*len(signal))
    return zcr

def rms_energy(signal):
    return np.sqrt(np.mean(signal**2))

if __name__ == "__main__":
    np.random.seed(42)
    sig = np.random.randn(16000)
    sig[:4000] *= 0.1
    zcr = zero_crossing_rate(sig)
    rms = rms_energy(sig)
    print(f"ZCR: {zcr:.4f}, RMS: {rms:.4f}")
    print("\n音频特征测试完成!")
