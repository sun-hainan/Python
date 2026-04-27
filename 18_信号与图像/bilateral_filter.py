# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / bilateral_filter



本文件实现 bilateral_filter 相关的算法功能。

"""



import numpy as np

import math





# 双边滤波器

def bilateral_filter(image, sigma_s=5, sigma_r=50):

    """双边滤波"""

    img = np.array(image, dtype=float)

    h, w = img.shape

    r = int(2*sigma_s)

    out = np.zeros_like(img)



    for y in range(h):

        for x in range(w):

            center = img[y,x]

            w_sum, v_sum = 0.0, 0.0

            for dy in range(-r, r+1):

                for dx in range(-r, r+1):

                    ny, nx = y+dy, x+dx

                    if 0<=ny<h and 0<=nx<w:

                        ds = math.exp(-(dx**2+dy**2)/(2*sigma_s**2))

                        dr = math.exp(-(img[ny,nx]-center)**2/(2*sigma_r**2))

                        w = ds*dr

                        w_sum += w

                        v_sum += w*img[ny,nx]

            out[y,x] = v_sum/(w_sum+1e-10)

    return out





if __name__ == "__main__":

    np.random.seed(42)

    img = np.zeros((40,40))

    img[15:25,15:25] = 200

    img += np.random.randn(40,40)*15



    filtered = bilateral_filter(img, sigma_s=3, sigma_r=30)

    print(f"原始均值: {np.mean(img):.2f}, 滤波后: {np.mean(filtered):.2f}")

    print(f"原始方差: {np.std(img):.2f}, 滤波后: {np.std(filtered):.2f}")

    print("\n双边滤波测试完成!")

