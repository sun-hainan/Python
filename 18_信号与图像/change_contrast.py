# -*- coding: utf-8 -*-

"""

算法实现：18_信号与图像 / change_contrast



本文件实现 change_contrast 相关的算法功能。

"""



from PIL import Image





def change_contrast(img: Image, level: int) -> Image:

    # change_contrast function



    # change_contrast function

    # change_contrast 函数实现

    """

    Function to change contrast

    """

    factor = (259 * (level + 255)) / (255 * (259 - level))



    def contrast(c: int) -> int:

    # contrast function



    # contrast function

    # contrast 函数实现

        """

        Fundamental Transformation/Operation that'll be performed on

        every bit.

        """

        return int(128 + factor * (c - 128))



    return img.point(contrast)





if __name__ == "__main__":

    # Load image

    with Image.open("image_data/lena.jpg") as img:

        # Change contrast to 170

        cont_img = change_contrast(img, 170)

        cont_img.save("image_data/lena_high_contrast.png", format="png")

