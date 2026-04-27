# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / fourier_descriptors

本文件实现 fourier_descriptors 相关的算法功能。
"""

import numpy as np

def contour_to_fourier(contour, n_harmonics=10):
    contour = np.array(contour, dtype=complex)
    n = len(contour)
    harmonics = np.zeros(n_harmonics, dtype=complex)
    for k in range(n_harmonics):
        for n_idx in range(n):
            harmonics[k] += contour[n_idx] * np.exp(-2j*np.pi*k*n_idx/n)
        harmonics[k] /= n
    return harmonics

def fourier_to_contour(harmonics, n_points=100):
    contour = np.zeros(n_points, dtype=complex)
    n = len(harmonics)
    for i in range(n_points):
        for k in range(n):
            contour[i] += harmonics[k] * np.exp(2j*np.pi*k*i/n_points)
    return np.column_stack((contour.real, contour.imag))

if __name__ == "__main__":
    theta = np.linspace(0, 2*np.pi, 50)
    contour = np.column_stack((10*np.cos(theta)+25, 10*np.sin(theta)+25))
    h = contour_to_fourier(contour, 10)
    print(f"Harmonics magnitudes: {np.abs(h[:5]).round(2)}")
    print("\n傅里叶描述子测试完成!")
