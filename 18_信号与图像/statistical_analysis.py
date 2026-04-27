# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / statistical_analysis



本文件实现 statistical_analysis 相关的算法功能。

"""



import numpy as np



def skewness(data):

    n = len(data)

    m = np.mean(data)

    s = np.std(data)

    if s == 0: return 0

    return np.mean(((data - m) / s) ** 3)



def kurtosis(data):

    n = len(data)

    m = np.mean(data)

    s = np.std(data)

    if s == 0: return 0

    return np.mean(((data - m) / s) ** 4) - 3



def entropy(data, bins=256):

    hist, _ = np.histogram(data, bins=bins, range=(data.min(), data.max()))

    hist = hist / hist.sum() + 1e-10

    return -np.sum(hist * np.log2(hist))



def covariance_matrix(data):

    return np.cov(data.T)



def pearson_correlation(x, y):

    mx, my = np.mean(x), np.mean(y)

    sx, sy = np.std(x), np.std(y)

    if sx == 0 or sy == 0: return 0

    return np.mean((x-mx)*(y-my)) / (sx*sy)



if __name__ == "__main__":

    np.random.seed(42)

    data = np.random.randn(1000) + 2

    print(f"Skewness: {skewness(data):.4f}")

    print(f"Kurtosis: {kurtosis(data):.4f}")

    print(f"Entropy: {entropy(data):.4f}")

    print("\n统计分析测试完成!")

