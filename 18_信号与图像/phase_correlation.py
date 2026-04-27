# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / phase_correlation



本文件实现 phase_correlation 相关的算法功能。

"""



import numpy as np



def phase_correlation(img1, img2):

    """相位相关图像对齐"""

    F1 = np.fft.fft2(img1.astype(float))

    F2 = np.fft.fft2(img2.astype(float))

    R = F1 * np.conj(F2)

    R /= np.abs(R) + 1e-10

    cross_power = np.abs(np.fft.ifft2(R))

    shift = np.unravel_index(np.argmax(cross_power), cross_power.shape)

    return shift



def cross_correlation(img, template):

    """归一化互相关"""

    ih,iw = img.shape

    th,tw = template.shape

    result = np.zeros((ih-th+1, iw-tw+1))

    for y in range(ih-th+1):

        for x in range(iw-tw+1):

            patch = img[y:y+th, x:x+tw]

            m1,m2 = patch.mean(),template.mean()

            s1,s2 = patch.std()+1e-8, template.std()+1e-8

            result[y,x] = np.sum((patch-m1)*(template-m2))/(s1*s2*th*tw)

    return result



if __name__ == "__main__":

    np.random.seed(42)

    img1 = np.random.randint(0,256,(40,40))

    shift = (3, 5)

    img2 = np.zeros_like(img1)

    img2[shift[0]:,shift[1]:] = img1[:-shift[0],:-shift[1]]

    detected = phase_correlation(img1, img2)

    print(f"True shift: {shift}, Detected: {detected}")

    print("\n相位相关测试完成!")

