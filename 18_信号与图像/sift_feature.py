# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / sift_feature



本文件实现 sift_feature 相关的算法功能。

"""



import numpy as np

import math





# compute_gradient 算法

def compute_gradient(image):

    """计算图像梯度"""

    h, w = image.shape

    gx = np.zeros_like(image)

    gy = np.zeros_like(image)

    for y in range(1, h-1):

        for x in range(1, w-1):

            gx[y,x] = image[y,x+1] - image[y,x-1]

            gy[y,x] = image[y+1,x] - image[y-1,x]

    return gx, gy





# harris_response 算法

def harris_response(image, k=0.04):

    """Harris 角点响应"""

    gx, gy = compute_gradient(image)

    Ixx = gx**2

    Iyy = gy**2

    Ixy = gx*gy

    from scipy.ndimage import gaussian_filter

    Ixx = gaussian_filter(Ixx, sigma=1)

    Iyy = gaussian_filter(Iyy, sigma=1)

    Ixy = gaussian_filter(Ixy, sigma=1)

    R = Ixx*Iyy - Ixy**2 - k*(Ixx+Iyy)**2

    return R





# detect_corners 算法

def detect_corners(image, threshold=1000):

    """检测角点"""

    R = harris_response(image)

    corners = []

    h, w = R.shape

    for y in range(2, h-2):

        for x in range(2, w-2):

            if R[y,x] > threshold:

                is_max = True

                for dy in range(-2, 3):

                    for dx in range(-2, 3):

                        if dy==0 and dx==0: continue

                        if R[y,x] < R[y+dy,x+dx]:

                            is_max = False

                            break

                if is_max:

                    corners.append((x, y, R[y,x]))

    return sorted(corners, key=lambda c: c[2], reverse=True)





if __name__ == "__main__":

    np.random.seed(42)

    img = np.zeros((50, 50))

    img[20:30, 20:30] = 200

    img += np.random.randn(50, 50)*5



    corners = detect_corners(img, threshold=5000)

    print(f"检测到 {len(corners)} 个角点")

    for i, (x, y, r) in enumerate(corners[:5]):

        print(f"  角点{i+1}: ({x},{y}), R={r:.0f}")

    print("\nSIFT 特征测试完成!")

