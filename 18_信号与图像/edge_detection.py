# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / edge_detection

本文件实现 edge_detection 相关的算法功能。
"""

import numpy as np

def sobel(image):
    gx = np.array([[-1,0,1],[-2,0,2],[-1,0,1]])
    gy = np.array([[-1,-2,-1],[0,0,0],[1,2,1]])
    h,w = image.shape
    out_x = np.zeros_like(image)
    out_y = np.zeros_like(image)
    for y in range(1,h-1):
        for x in range(1,w-1):
            patch = image[y-1:y+2,x-1:x+2]
            out_x[y,x] = np.sum(patch * gx)
            out_y[y,x] = np.sum(patch * gy)
    magnitude = np.sqrt(out_x**2 + out_y**2)
    return magnitude

def prewitt(image):
    gx = np.array([[-1,0,1],[-1,0,1],[-1,0,1]])
    gy = np.array([[-1,-1,-1],[0,0,0],[1,1,1]])
    h,w = image.shape
    out = np.zeros_like(image)
    for y in range(1,h-1):
        for x in range(1,w-1):
            patch = image[y-1:y+2,x-1:x+2]
            out[y,x] = np.sum(patch * (gx + gy))
    return out

def laplacian(image):
    kernel = np.array([[0,1,0],[1,-4,1],[0,1,0]])
    h,w = image.shape
    out = np.zeros_like(image)
    for y in range(1,h-1):
        for x in range(1,w-1):
            patch = image[y-1:y+2,x-1:x+2]
            out[y,x] = np.sum(patch * kernel)
    return out

if __name__ == "__main__":
    np.random.seed(42)
    img = np.random.randint(0,256,(50,50))
    img[20:30,20:30] = 200
    print(f"Sobel max: {np.max(sobel(img)):.2f}")
    print(f"Prewitt max: {np.max(prewitt(img)):.2f}")
    print(f"Laplacian max: {np.max(np.abs(laplacian(img))):.2f}")
    print("\n边缘检测测试完成!")
