# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / filter_bank



本文件实现 filter_bank 相关的算法功能。

"""



import numpy as np



def gabor_filter_bank(n_orientations=8, n_scales=4, size=49):

    from scipy.ndimage import gaussian_filter

    filters = []

    sigmas = [2, 4, 6, 8]

    for orientation in np.linspace(0, np.pi, n_orientations, endpoint=False):

        for sigma in sigmas:

            kernel = gabor_kernel_2d(size, sigma, orientation)

            filters.append(kernel)

    return filters



def gabor_kernel_2d(size, sigma, theta, lambd=10.0, psi=0, gamma=1.0):

    half = size // 2

    y, x = np.meshgrid(np.arange(-half,half+1), np.arange(-half,half+1))

    x_theta = x*np.cos(theta) + y*np.sin(theta)

    y_theta = -x*np.sin(theta) + y*np.cos(theta)

    kernel = np.exp(-.5*(x_theta**2 + gamma**2*y_theta**2)/sigma**2) * np.cos(2*np.pi*x_theta/lambd + psi)

    return kernel



def apply_filter_bank(image, bank):

    from scipy.ndimage import convolve

    responses = []

    for k in bank:

        resp = convolve(image, k, mode='constant')

        responses.append(np.abs(resp))

    return np.stack(responses, axis=-1)



if __name__ == "__main__":

    np.random.seed(42)

    img = np.random.randint(0,256,(64,64))

    bank = gabor_filter_bank(4, 2)

    resp = apply_filter_bank(img, bank)

    print(f"Filter bank: {len(bank)} filters, Response shape: {resp.shape}")

    print("\n滤波器组测试完成!")

