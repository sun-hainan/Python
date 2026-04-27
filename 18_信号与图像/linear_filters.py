# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / linear_filters



本文件实现 linear_filters 相关的算法功能。

"""



import numpy as np



def conv2d(image, kernel):

    kh,kw = kernel.shape

    h,w = image.shape

    out = np.zeros_like(image)

    for y in range(kh//2,h-kh//2):

        for x in range(kw//2,w-kw//2):

            patch = image[y-kh//2:y+kh//2+1,x-kw//2:x+kw//2+1]

            out[y,x] = np.sum(patch * kernel)

    return out



def box_filter(image, size=3):

    return conv2d(image, np.ones((size,size))/size**2)



def gaussian_filter(image, sigma=1.0):

    size = int(6*sigma+1)

    x = np.arange(size)-size//2

    k = np.exp(-x**2/(2*sigma**2))

    kernel = np.outer(k,k)/k.sum()

    return conv2d(image, kernel)



if __name__ == "__main__":

    np.random.seed(42)

    img = np.random.randint(0,256,(30,30))

    box = box_filter(img, 3)

    gauss = gaussian_filter(img, 1.5)

    print(f"Box: {np.mean(box):.2f}, Gaussian: {np.mean(gauss):.2f}")

    print("\n线性滤波器测试完成!")

