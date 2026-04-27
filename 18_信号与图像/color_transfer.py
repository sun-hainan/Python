# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / color_transfer



本文件实现 color_transfer 相关的算法功能。

"""



import numpy as np



def match_colors(source, reference):

    s_mean = np.mean(source, axis=(0,1))

    r_mean = np.mean(reference, axis=(0,1))

    s_std = np.std(source, axis=(0,1))

    r_std = np.std(reference, axis=(0,1))

    matched = (source - s_mean) * (r_std / (s_std + 1e-8)) + r_mean

    return np.clip(matched, 0, 255).astype(np.uint8)



def grayscale_to_color(gray, ref_color):

    h,w = gray.shape

    colored = np.zeros((h,w,3))

    for c in range(3):

        mean_c = np.mean(gray)

        colored[:,:,c] = gray * (ref_color[c] / (mean_c + 1e-8))

    return np.clip(colored, 0, 255).astype(np.uint8)



if __name__ == "__main__":

    np.random.seed(42)

    src = np.random.randint(0,256,(20,20,3))

    ref = np.random.randint(0,256,(20,20,3))

    matched = match_colors(src, ref)

    print(f"Matched mean: {np.mean(matched, axis=(0,1)).round(2)}")

    print("\n颜色迁移测试完成!")

