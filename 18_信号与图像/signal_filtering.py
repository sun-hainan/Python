# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / signal_filtering



本文件实现 signal_filtering 相关的算法功能。

"""



import numpy as np



def moving_average(signal, window=5):

    result = np.zeros_like(signal)

    for i in range(len(signal)):

        start = max(0, i-window+1)

        result[i] = np.mean(signal[start:i+1])

    return result



def exponential_smoothing(signal, alpha=0.3):

    result = np.zeros_like(signal)

    result[0] = signal[0]

    for i in range(1,len(signal)):

        result[i] = alpha*signal[i] + (1-alpha)*result[i-1]

    return result



def median_filter(signal, window=3):

    result = np.zeros_like(signal)

    h = window//2

    for i in range(len(signal)):

        start,end = max(0,i-h), min(len(signal),i+h+1)

        result[i] = np.median(signal[start:end])

    return result



if __name__ == "__main__":

    np.random.seed(42)

    sig = np.sin(2*np.pi*5*np.linspace(0,1,200)) + np.random.randn(200)*0.2

    ma = moving_average(sig, 10)

    ema = exponential_smoothing(sig, 0.3)

    med = median_filter(sig, 5)

    print(f"MA std: {np.std(ma):.4f}, EMA: {np.std(ema):.4f}, Median: {np.std(med):.4f}")

    print("\n信号滤波测试完成!")

