# -*- coding: utf-8 -*-

"""

算法实现：14_信息论 / peak_signal_to_noise_ratio



本文件实现 peak_signal_to_noise_ratio 相关的算法功能。

"""



import math

import os



import cv2

import numpy as np



PIXEL_MAX = 255.0





def peak_signal_to_noise_ratio(original: float, contrast: float) -> float:

    # peak_signal_to_noise_ratio function



    # peak_signal_to_noise_ratio function

    mse = np.mean((original - contrast) ** 2)

    if mse == 0:

        return 100



    return 20 * math.log10(PIXEL_MAX / math.sqrt(mse))





def main() -> None:

    # main function



    # main function

    dir_path = os.path.dirname(os.path.realpath(__file__))

    # Loading images (original image and compressed image)

    original = cv2.imread(os.path.join(dir_path, "image_data/original_image.png"))

    contrast = cv2.imread(os.path.join(dir_path, "image_data/compressed_image.png"), 1)



    original2 = cv2.imread(os.path.join(dir_path, "image_data/PSNR-example-base.png"))

    contrast2 = cv2.imread(

        os.path.join(dir_path, "image_data/PSNR-example-comp-10.jpg"), 1

    )



    # Value expected: 29.73dB

    print("-- First Test --")

    print(f"PSNR value is {peak_signal_to_noise_ratio(original, contrast)} dB")



    # # Value expected: 31.53dB (Wikipedia Example)

    print("\n-- Second Test --")

    print(f"PSNR value is {peak_signal_to_noise_ratio(original2, contrast2)} dB")





if __name__ == "__main__":

    main()

