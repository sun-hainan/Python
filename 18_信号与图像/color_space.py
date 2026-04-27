# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / color_space



本文件实现 color_space 相关的算法功能。

"""



import numpy as np



def rgb_to_hsv(rgb):

    r,g,b = rgb[:,:,0]/255.0, rgb[:,:,1]/255.0, rgb[:,:,2]/255.0

    mx = np.maximum(np.maximum(r,g),b)

    mn = np.minimum(np.minimum(r,g),b)

    v = mx

    s = np.where(mx==0, 0, (mx-mn)/mx)

    diff = mx-mn

    h = np.zeros_like(mx)

    mask = (mx==r)

    h[mask] = (60*((g[mask]-b[mask])/diff[mask])) % 360

    mask = (mx==g)

    h[mask] = 60*((b[mask]-r[mask])/diff[mask]) + 120

    mask = (mx==b)

    h[mask] = 60*((r[mask]-g[mask])/diff[mask]) + 240

    return np.stack([h,s,v],axis=-1)*255



def rgb_to_ycbcr(rgb):

    r,g,b = rgb[:,:,0].astype(float),rgb[:,:,1].astype(float),rgb[:,:,2].astype(float)

    y = 0.299*r + 0.587*g + 0.114*b

    cb = 128 - 0.168736*r - 0.331264*g + 0.5*b

    cr = 128 + 0.5*r - 0.418688*g - 0.081312*b

    return np.stack([y,cb,cr],axis=-1)



if __name__ == "__main__":

    np.random.seed(42)

    rgb = np.random.randint(0,256,(20,20,3))

    hsv = rgb_to_hsv(rgb)

    ycbcr = rgb_to_ycbcr(rgb)

    print(f"RGB shape: {rgb.shape}, HSV: {hsv.shape}, YCbCr: {ycbcr.shape}")

    print("\n颜色空间测试完成!")

