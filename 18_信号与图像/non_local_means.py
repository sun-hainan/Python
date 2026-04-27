# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / non_local_means



本文件实现 non_local_means 相关的算法功能。

"""



import numpy as np

import math





# nlm_denoise 算法

def nlm_denoise(image, h=10, patch_size=7, search_size=21):

    """非局部均值去噪"""

    img = np.array(image, dtype=float)

    h_img, w_img = img.shape

    pad = search_size // 2

    padded = np.pad(img, pad, mode='reflect')

    out = np.zeros_like(img)

    ps2 = patch_size // 2



    for y in range(h_img):

        for x in range(w_img):

            cy, cx = y + pad, x + pad

            center_patch = padded[cy-ps2:cy+ps2+1, cx-ps2:cx+ps2+1]

            w_sum, v_sum = 0.0, 0.0

            for dy in range(-pad, pad+1, 2):

                for dx in range(-pad, pad+1, 2):

                    ny, nx = cy+dy, cx+dx

                    if 0<=ny<h_img+2*pad and 0<=nx<w_img+2*pad:

                        n_patch = padded[ny-ps2:ny+ps2+1, nx-ps2:nx+ps2+1]

                        if n_patch.shape == center_patch.shape:

                            diff = center_patch - n_patch

                            d2 = np.sum(diff**2) / (patch_size**2)

                            w = math.exp(-d2 / h**2)

                            w_sum += w

                            v_sum += w * padded[ny, nx]

            out[y,x] = v_sum / (w_sum + 1e-10)

    return out





if __name__ == "__main__":

    np.random.seed(42)

    base = np.zeros((40,40))

    base[15:25,15:25] = 200

    noisy = base + np.random.randn(40,40)*20

    denoised = nlm_denoise(noisy, h=15, patch_size=5, search_size=15)

    mse_orig = np.mean((noisy-base)**2)

    mse_denoised = np.mean((denoised-base)**2)

    print(f"原始MSE: {mse_orig:.2f}, 去噪后MSE: {mse_denoised:.2f}")

    print(f"改善: {(mse_orig-mse_denoised)/mse_orig*100:.1f}%")

    print("\n非局部均值测试完成!")

