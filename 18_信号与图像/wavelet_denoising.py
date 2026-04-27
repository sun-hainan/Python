# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / wavelet_denoising



本文件实现 wavelet_denoising 相关的算法功能。

"""



import numpy as np



def simple_wavelet_transform(signal, wavelet='haar'):

    n = len(signal)

    if n <= 1: return signal, np.array([0])

    half = n // 2

    ca = (signal[::2] + signal[1::2]) / np.sqrt(2)

    cd = (signal[::2] - signal[1::2]) / np.sqrt(2)

    return ca, cd



def inverse_wavelet(ca, cd):

    n = len(ca)

    signal = np.zeros(2*n)

    signal[::2] = (ca + cd) / np.sqrt(2)

    signal[1::2] = (ca - cd) / np.sqrt(2)

    return signal



def wavelet_threshold(ca, cd, threshold):

    cd_thresh = np.where(np.abs(cd) > threshold, cd, 0)

    return ca, cd_thresh



def denoise_wavelet(signal, threshold=0.5, levels=3):

    ca = signal.copy()

    all_cd = []

    for _ in range(levels):

        ca_new, cd = simple_wavelet_transform(ca)

        cd, cd_th = wavelet_threshold(ca_new, cd, threshold)

        all_cd.append(cd_th)

        ca = ca_new

    for cd in reversed(all_cd):

        ca = inverse_wavelet(ca, cd)

    return ca



if __name__ == "__main__":

    np.random.seed(42)

    sig = np.sin(2*np.pi*5*np.linspace(0,1,256)) + np.random.randn(256)*0.3

    denoised = denoise_wavelet(sig, 0.2, 3)

    print(f"Original std: {np.std(sig):.4f}, Denoised std: {np.std(denoised):.4f}")

    print("\n小波去噪测试完成!")

