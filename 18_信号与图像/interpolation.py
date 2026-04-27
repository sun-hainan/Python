# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / interpolation

本文件实现 interpolation 相关的算法功能。
"""

import numpy as np

def bilinear_interp(image, x, y):
    x0, y0 = int(x), int(y)
    fx, fy = x - x0, y - y0
    if 0<=x0<image.shape[1]-1 and 0<=y0<image.shape[0]-1:
        v00 = image[y0,x0]
        v01 = image[y0+1,x0]
        v10 = image[y0,x0+1]
        v11 = image[y0+1,x0+1]
        return (1-fx)*(1-fy)*v00 + fx*(1-fy)*v10 + (1-fx)*fy*v01 + fx*fy*v11
    return 0

def resize_nearest(image, scale):
    oh,ow = int(image.shape[0]*scale), int(image.shape[1]*scale)
    out = np.zeros((oh,ow))
    for y in range(oh):
        for x in range(ow):
            src_y = int(y/scale)
            src_x = int(x/scale)
            out[y,x] = image[src_y,src_x]
    return out

def resize_bilinear(image, scale):
    oh,ow = int(image.shape[0]*scale), int(image.shape[1]*scale)
    out = np.zeros((oh,ow))
    for y in range(oh):
        for x in range(ow):
            src_y = y/scale
            src_x = x/scale
            out[y,x] = bilinear_interp(image, src_x, src_y)
    return out

if __name__ == "__main__":
    np.random.seed(42)
    img = np.random.randint(0,256,(20,20))
    resized = resize_bilinear(img, 2.0)
    print(f"Resized shape: {resized.shape}")
    print("\n插值测试完成!")
