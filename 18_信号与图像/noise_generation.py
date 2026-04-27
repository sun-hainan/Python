# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / noise_generation



本文件实现 noise_generation 相关的算法功能。

"""



import numpy as np



def gaussian_noise(image, mean=0, std=25):

    return np.clip(image + np.random.randn(*image.shape)*std, 0, 255).astype(np.uint8)



def salt_pepper_noise(image, prob=0.05):

    out = image.copy()

    mask = np.random.rand(*image.shape)

    out[mask < prob/2] = 0

    out[mask > 1-prob/2] = 255

    return out



def poisson_noise(image):

    vals = 4 + image/30.0 * 6.0

    out = np.random.poisson(vals) / 6.0 * 30

    return np.clip(out, 0, 255).astype(np.uint8)



def speckle_noise(image):

    noise = np.random.randn(*image.shape)

    return np.clip(image + image*noise*0.1, 0, 255).astype(np.uint8)



if __name__ == "__main__":

    np.random.seed(42)

    img = np.random.randint(0,256,(30,30))

    print(f"Original mean: {np.mean(img):.2f}")

    gnoise = gaussian_noise(img, 0, 30)

    sp = salt_pepper_noise(img, 0.1)

    print(f"Gaussian noise: {np.std(gnoise.astype(float)-img.astype(float)):.2f}")

    print(f"Salt&Pepper: {np.std(sp.astype(float)-img.astype(float)):.2f}")

    print("\n噪声生成测试完成!")

