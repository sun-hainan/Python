# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / image_inpainting

本文件实现 image_inpainting 相关的算法功能。
"""

import numpy as np

def fill_holes(mask):
    h,w = mask.shape
    result = mask.copy()
    while np.any(result==0):
        for y in range(1,h-1):
            for x in range(1,w-1):
                if result[y,x]==0:
                    neighbors = [result[y-1,x],result[y+1,x],result[y,x-1],result[y,x+1]]
                    if all(n>0 for n in neighbors):
                        result[y,x] = sum(neighbors)//4
        if np.all(result>0):
            break
    return result

def texture_synthesis_simple(texture, output_size=(50,50)):
    oh,ow = output_size
    th,tw = texture.shape
    output = np.zeros(output_size)
    for y in range(oh):
        for x in range(ow):
            sy = y % th
            sx = x % tw
            output[y,x] = texture[sy,sx]
    return output

if __name__ == "__main__":
    np.random.seed(42)
    mask = np.ones((20,20))
    mask[8:12,8:12] = 0
    filled = fill_holes(mask)
    print(f"Holes filled: {np.sum(filled==0)}")
    tex = np.random.randint(0,256,(10,10))
    syn = texture_synthesis_simple(tex, (30,30))
    print(f"Synthesized texture mean: {np.mean(syn):.2f}")
    print("\n图像修复测试完成!")
