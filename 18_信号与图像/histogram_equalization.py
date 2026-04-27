# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / histogram_equalization



本文件实现 histogram_equalization 相关的算法功能。

"""



import numpy as np



def equalize(image):

    h,w = image.shape

    hist,bins = np.histogram(image.flatten(),256,[0,256])

    cdf = hist.cumsum()

    cdf_m = np.ma.masked_equal(cdf,0)

    cdf_m = (cdf_m - cdf_m.min())*255/(cdf_m.max()-cdf_m.min())

    cdf = np.ma.filled(cdf_m,0).astype('uint8')

    return cdf[image]



def match(source, reference):

    s_hist,b = np.histogram(source.flatten(),256,[0,256])

    r_hist,b = np.histogram(reference.flatten(),256,[0,256])

    s_cdf = s_hist.cumsum().astype(float)

    r_cdf = r_hist.cumsum().astype(float)

    s_cdf = 255*s_cdf/s_cdf[-1]

    r_cdf = 255*r_cdf/r_cdf[-1]

    lut = np.interp(s_cdf,r_cdf,np.arange(256))

    return lut[source].astype('uint8')



if __name__ == "__main__":

    np.random.seed(42)

    img = np.random.randint(50,150,(50,50))

    eq = equalize(img)

    print(f"Original std: {np.std(img):.2f}, Equalized std: {np.std(eq):.2f}")

    print("\n直方图均衡化测试完成!")

