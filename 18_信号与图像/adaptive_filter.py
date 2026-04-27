# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / adaptive_filter



本文件实现 adaptive_filter 相关的算法功能。

"""



import numpy as np



class LMSFilter:

    def __init__(self, order=32, mu=0.01):

        self.order = order

        self.mu = mu

        self.w = np.zeros(order)

    def filter(self, x, d):

        y = np.dot(self.w, x)

        e = d - y

        self.w += self.mu * e * x

        return y, e

    def predict(self, x):

        return np.dot(self.w, x)



if __name__ == "__main__":

    np.random.seed(42)

    lms = LMSFilter(32, 0.05)

    signal = np.sin(2*np.pi*0.1*np.arange(1000)) + 0.1*np.random.randn(1000)

    noise = np.random.randn(1000) * 0.5

    for i in range(100, 1000):

        x = signal[max(0,i-31):i][::-1]

        padded = np.zeros(32)

        padded[:len(x)] = x

        y, e = lms.filter(padded, signal[i]+noise[i])

    print(f"LMS final error: {np.mean(lms.w**2):.4f}")

    print("\n自适应滤波器测试完成!")

