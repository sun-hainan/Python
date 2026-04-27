# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / dft



本文件实现 dft 相关的算法功能。

"""



import numpy as np



def dft(signal):

    N = len(signal)

    X = np.zeros(N, dtype=complex)

    for k in range(N):

        for n in range(N):

            X[k] += signal[n] * np.exp(-2j*np.pi*k*n/N)

    return X



def idft(X):

    N = len(X)

    x = np.zeros(N, dtype=complex)

    for n in range(N):

        for k in range(N):

            x[n] += X[k] * np.exp(2j*np.pi*k*n/N)

    return x.real / N



def fft(signal):

    N = len(signal)

    if N <= 1: return signal

    even = fft(signal[::2])

    odd = fft(signal[1::2])

    k = np.arange(N//2)

    factor = np.exp(-2j*np.pi*k/N)

    return np.concatenate([even + factor*odd, even - factor*odd])



def fftfreq(N, d=1.0):

    return np.fft.fftfreq(N, d)



if __name__ == "__main__":

    np.random.seed(42)

    sig = np.sin(2*np.pi*5*np.arange(0,1,1/128)) + 0.5*np.sin(2*np.pi*20*np.arange(0,1,1/128))

    F = fft(sig)

    freqs = fftfreq(len(F), 1/128)

    pos = np.argmax(np.abs(F[len(F)//2:]))

    print(f"Peak freq bin: {pos}")

    print("\nDFT测试完成!")

