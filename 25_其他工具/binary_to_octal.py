# -*- coding: utf-8 -*-

"""

算法实现：25_其他工具 / binary_to_octal



本文件实现 binary_to_octal 相关的算法功能。

"""



# bin_to_octal 函数实现

def bin_to_octal(bin_string: str) -> str:

    if not all(char in "01" for char in bin_string):

    # 条件判断

        raise ValueError("Non-binary value was passed to the function")

    if not bin_string:

    # 条件判断

        raise ValueError("Empty string was passed to the function")

    oct_string = ""

    while len(bin_string) % 3 != 0:

    # 条件循环

        bin_string = "0" + bin_string

    bin_string_in_3_list = [

        bin_string[index : index + 3]

        for index in range(len(bin_string))

        if index % 3 == 0

    ]

    for bin_group in bin_string_in_3_list:

    # 遍历循环

        oct_val = 0

        for index, val in enumerate(bin_group):

    # 遍历循环

            oct_val += int(2 ** (2 - index) * int(val))

        oct_string += str(oct_val)

    return oct_string

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    from doctest import testmod



    testmod()

