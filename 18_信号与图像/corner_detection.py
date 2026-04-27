# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / corner_detection

本文件实现 corner_detection 相关的算法功能。
"""

import numpy as np

def harris_corner(image, k=0.04, threshold=1000):
    Ix = np.array([[-1,0,1],[-2,0,2],[-1,0,1]])
    Iy = Ix.T
    from scipy.ndimage import convolve
    Ixx = convolve(image, Ix*Ix)
    Iyy = convolve(image, Iy*Iy)
    Ixy = convolve(image, Ix*Iy)
    Ixx = convolve(Ixx, np.ones((3,3))/9)
    Iyy = convolve(Iyy, np.ones((3,3))/9)
    Ixy = convolve(Ixy, np.ones((3,3))/9)
    R = Ixx*Iyy - Ixy**2 - k*(Ixx+Iyy)**2
    corners = []
    h,w = R.shape
    for y in range(1,h-1):
        for x in range(1,w-1):
            if R[y,x] > threshold:
                is_max = all(R[y,x] >= R[y+dy,x+dx] for dy,dx in [(-1,-1),(-1,1),(1,-1),(1,1)])
                if is_max:
                    corners.append((x,y,R[y,x]))
    return sorted(corners, key=lambda c: c[2], reverse=True)

if __name__ == "__main__":
    np.random.seed(42)
    img = np.zeros((50,50))
    img[20:30,20:30] = 200
    img += np.random.randn(50,50)*5
    corners = harris_corner(img, threshold=5000)
    print(f"Found {len(corners)} corners")
    print("\n角点检测测试完成!")
