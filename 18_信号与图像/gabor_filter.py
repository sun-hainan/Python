# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / gabor_filter



本文件实现 gabor_filter 相关的算法功能。

"""



import numpy as np



def gabor_kernel(sigma, theta, lam, psi=0, gamma=1):

    sigma_x = sigma

    sigma_y = sigma/gamma

    x = np.arange(-3*sigma,3*sigma+1)

    y = np.arange(-3*sigma_y,3*sigma_y+1)

    X, Y = np.meshgrid(x, y)

    X_theta = X*np.cos(theta) + Y*np.sin(theta)

    Y_theta = -X*np.sin(theta) + Y*np.cos(theta)

    kernel = np.exp(-0.5*(X_theta**2/sigma_x**2 + Y_theta**2/sigma_y**2))

    kernel *= np.cos(2*np.pi*lam*X_theta + psi)

    return kernel



def gabor_filter(image, kernels):

    from scipy.ndimage import convolve

    responses = []

    for k in kernels:

        resp = convolve(image, k, mode='reflect')

        responses.append(resp)

    return np.stack(responses, axis=-1)



if __name__ == "__main__":

    np.random.seed(42)

    img = np.random.randint(0,256,(40,40))

    kernels = [gabor_kernel(3, theta, 0.5) for theta in [0, np.pi/4, np.pi/2, 3*np.pi/4]]

    resp = gabor_filter(img, kernels)

    print(f"Gabor response shape: {resp.shape}")

    print("\nGabor 滤波器测试完成!")

