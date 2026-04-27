# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / curve_fitting

本文件实现 curve_fitting 相关的算法功能。
"""

import numpy as np

def linear_fit(x, y):
    n = len(x)
    x_mean, y_mean = np.mean(x), np.mean(y)
    num = np.sum((x-x_mean)*(y-y_mean))
    denom = np.sum((x-x_mean)**2)
    a = num/denom if denom != 0 else 0
    b = y_mean - a*x_mean
    return a, b

def exponential_fit(x, y):
    y_pos = np.maximum(y, 1e-10)
    log_y = np.log(y_pos)
    a,b = linear_fit(x, log_y)
    return np.exp(b), a

def gaussian_fit(x, y):
    mu = np.sum(x*y)/np.sum(y)
    sigma = np.sqrt(np.sum(y*(x-mu)**2)/np.sum(y))
    A = np.max(y)
    return A, mu, sigma

def spline_interpolation(x, y, x_new):
    from scipy.interpolate import interp1d
    f = interp1d(x, y, kind='cubic', fill_value='extrapolate')
    return f(x_new)

if __name__ == "__main__":
    np.random.seed(42)
    x = np.linspace(0, 10, 20)
    y = 2*x + 1 + np.random.randn(20)*0.5
    a, b = linear_fit(x, y)
    print(f"Linear fit: y = {a:.3f}x + {b:.3f}")
    print("\n曲线拟合测试完成!")
