# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / convert_to_negative

本文件实现 convert_to_negative 相关的算法功能。
"""

from cv2 import destroyAllWindows, imread, imshow, waitKey


# 图像反转
def convert_to_negative(img):
    # convert_to_negative function

    # convert_to_negative function
    # getting number of pixels in the image
    pixel_h, pixel_v = img.shape[0], img.shape[1]

    # converting each pixel's color to its negative
    for i in range(pixel_h):
        for j in range(pixel_v):
            img[i][j] = [255, 255, 255] - img[i][j]

    return img


if __name__ == "__main__":
    # read original image
    img = imread("image_data/lena.jpg", 1)

    # convert to its negative
    neg = convert_to_negative(img)

    # show result image
    imshow("negative of original image", img)
    waitKey(0)
    destroyAllWindows()
