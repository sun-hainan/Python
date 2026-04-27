# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / thresholding



本文件实现 thresholding 相关的算法功能。

"""



import numpy as np



def otsu_threshold(image):

    hist, _ = np.histogram(image, 256, [0,256])

    hist = hist.astype(float) / hist.sum()

    sigma_b = 0.0

    threshold = 0

    for t in range(1, 256):

        w0 = hist[:t].sum()

        w1 = hist[t:].sum()

        if w0 == 0 or w1 == 0: continue

        m0 = np.sum(np.arange(t) * hist[:t]) / w0

        m1 = np.sum(np.arange(t,256) * hist[t:]) / w1

        sigma_b_sq = w0 * w1 * (m0 - m1)**2

        if sigma_b_sq > sigma_b:

            sigma_b = sigma_b_sq

            threshold = t

    return threshold



def adaptive_threshold(image, block_size=11, C=2):

    from scipy.ndimage import uniform_filter

    mean = uniform_filter(image.astype(float), block_size)

    return (image > mean - C).astype(np.uint8) * 255



def double_threshold(image, low=50, high=150):

    high_mask = image > high

    low_mask = (image > low) & (image <= high)

    result = np.zeros_like(image)

    result[high_mask] = 255

    return result



if __name__ == "__main__":

    np.random.seed(42)

    img = np.zeros((50,50))

    img[20:40,20:40] = 200

    img += np.random.randint(0,50,(50,50))

    t = otsu_threshold(img)

    adaptive = adaptive_threshold(img)

    double = double_threshold(img, 80, 150)

    print(f"Otsu threshold: {t}")

    print(f"Adaptive thresholded: {np.sum(adaptive==255)} pixels")

    print("\n阈值分割测试完成!")

