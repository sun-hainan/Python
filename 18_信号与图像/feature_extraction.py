# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / feature_extraction



本文件实现 feature_extraction 相关的算法功能。

"""



import numpy as np



def haardwt(signal):

    # haardwt function



    # haardwt function

    n = len(signal)

    if n <= 1: return signal, np.array([0])

    even = signal[::2]

    odd = signal[1::2]

    a = (even + odd) / np.sqrt(2)

    d = (even - odd) / np.sqrt(2)

    return a, d



def ihaardwt(a, d):

    # ihaardwt function



    # ihaardwt function

    n = len(a)

    result = np.zeros(2*n)

    for i in range(n):

        result[2*i] = (a[i] + d[i]) / np.sqrt(2)

        result[2*i+1] = (a[i] - d[i]) / np.sqrt(2)

    return result



def HaarWaveletTransform(signal, levels=3):

    # HaarWaveletTransform function



    # HaarWaveletTransform function

    coeffs = []

    cA = signal

    for _ in range(levels):

        cA, cD = haardwt(cA)

        coeffs.append(cD)

    return [cA] + coeffs[::-1]



if __name__ == "__main__":

    np.random.seed(42)

    sig = np.sin(2*np.pi*5*np.linspace(0,1,128)) + 0.3*np.random.randn(128)

    coeffs = HaarWaveletTransform(sig, levels=4)

    print(f"Levels: {len(coeffs)}, Coeff sizes: {[len(c) for c in coeffs]}")

    print("\nHaar小波测试完成!")

