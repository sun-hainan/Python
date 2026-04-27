# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / mean_threshold



本文件实现 mean_threshold 相关的算法功能。

"""



from PIL import Image



"""

Mean thresholding algorithm for image processing

https://en.wikipedia.org/wiki/Thresholding_(image_processing)

"""





def mean_threshold(image: Image) -> Image:

    """

    image: is a grayscale PIL image object

    """

    height, width = image.size

    mean = 0

    pixels = image.load()

    for i in range(width):

        for j in range(height):

            pixel = pixels[j, i]

            mean += pixel

    mean //= width * height



    for j in range(width):

        for i in range(height):

            pixels[i, j] = 255 if pixels[i, j] > mean else 0

    return image





if __name__ == "__main__":

    image = mean_threshold(Image.open("path_to_image").convert("L"))

    image.save("output_image_path")

